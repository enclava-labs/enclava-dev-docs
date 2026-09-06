#!/usr/bin/env python3
"""Local-only marker fixtures; production probe has no configurable file paths."""
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

source = Path(__file__).with_name('dev-init-metadata-probe.sh').read_text()
pairs = re.findall(r'^([a-z ]+)\|([a-z_]+)$', source, re.MULTILINE)
assert len(pairs) == 12
with tempfile.TemporaryDirectory(prefix='enclava-init-metadata-test-') as directory:
    stage, ready = Path(directory) / 'stage', Path(directory) / 'ready'
    # Only this local harness substitutes paths in a private in-memory copy.
    fixture = source.replace('/run/enclava/init-stage', str(stage)).replace(
        '/run/enclava/init-ready', str(ready))

    def probe(expected, arguments=()):
        result = subprocess.run(['sh', '-s', '--', *arguments], input=fixture,
                                text=True, capture_output=True, timeout=2)
        assert result.returncode == (2 if arguments else 0)
        assert result.stderr == ''
        assert json.loads(result.stdout) == expected
        assert len(result.stdout.splitlines()) == 1
        assert 'SECRET' not in result.stdout and directory not in result.stdout

    unknown = {'phase': 'unknown', 'ready': False}
    probe(unknown)
    for marker, label in pairs:
        stage.write_text(marker + '\n')
        ready.write_text('ready\n')
        probe({'phase': label, 'ready': True})
    ready.write_text('not-ready\n')
    probe({'phase': 'marking_ready', 'ready': False})
    for malicious in (b'SECRET\n', b'loading config\nSECRET\n', b'loading config\x00\n',
                      b'SECRET' * 100000, b'$(cat /SECRET)\n', b'ready\nSECRET',
                      b'loading config', b'ready'):
        stage.write_bytes(malicious)
        ready.write_bytes(malicious)
        probe(unknown)
    stage.unlink()
    stage.symlink_to(ready)
    probe(unknown)
    stage.unlink()
    stage.mkdir()
    probe(unknown)
    stage.rmdir()
    os.mkfifo(stage)
    probe(unknown)
    probe(unknown, ('/SECRET/arbitrary-path',))
print('init metadata probe self-test passed: 12 phases and hostile/missing/symlink/directory/FIFO inputs')
