#!/usr/bin/env python3
"""DEV-only paired HTTPS metadata probes; no auth, bodies, redirects or TLS bypass.

Run alongside dev-timing-run.py. Join absolute timestamps to the deployment's
started_at; this observer's elapsed time has its own origin.
"""
import argparse
import concurrent.futures
import datetime
import ipaddress
import json
import math
import subprocess
import time

# Verified against worker.enc-work's public interface and preserved canary DNS
# on 2026-09-06. Reverify before use; never substitute an untrusted edge address.
EDGE_IP = '13.140.128.15'


def command(host, pinned):
    args = ['/usr/bin/curl', '-q', '--silent', '--noproxy', '*', '--proto', '=https',
            '--connect-timeout', '2', '--max-time', '2', '--output', '/dev/null',
            '--write-out', '%{http_code}|%{ssl_verify_result}|%{remote_ip}|%{time_namelookup}|%{time_connect}|%{time_appconnect}|%{time_total}']
    if pinned:
        args += ['--resolve', f'{host}:443:{EDGE_IP}']
    return args + [f'https://{host}/healthz']


def metadata(value, exit_code):
    status, verify, remote, *timings = value.strip().split('|')
    assert len(timings) == 4
    status, verify = int(status), int(verify)
    assert status == 0 or 100 <= status <= 599
    assert 0 <= verify <= 65535 and 0 <= exit_code <= 255
    if remote:
        ipaddress.ip_address(remote)
    durations = [float(x) for x in timings]
    assert all(math.isfinite(x) and x >= 0 for x in durations)
    return dict(zip(('dns_s', 'connect_s', 'tls_s', 'total_s'), durations),
                http_status=status, tls_verify_result=verify, remote_ip=remote,
                exit_code=exit_code)


def probe(host, mode):
    started_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    # Do not inherit SSLKEYLOGFILE, proxy variables or CA trust overrides.
    result = subprocess.run(command(host, mode == 'pinned'), capture_output=True,
                            text=True, timeout=5,
                            env={'PATH': '/usr/bin:/bin', 'LC_ALL': 'C'})
    return dict(metadata(result.stdout, result.returncode), mode=mode,
                started_at=started_at,
                at=datetime.datetime.now(datetime.timezone.utc).isoformat())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('name', nargs='?')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        row = metadata('200|0|13.140.128.15|0.001|0.02|0.03|0.04', 0)
        assert row['http_status'] == 200 and row['tls_s'] == 0.03
        assert metadata('000|0||0|0|0|0.1', 6)['remote_ip'] == ''
        for bad in ('200|0|SECRET|0|0|0|0', '200|0||nan|0|0|0',
                    '999|0||0|0|0|0', '200|0||0|0|0', '200|0||-1|0|0|0'):
            try:
                metadata(bad, 0)
            except (ValueError, AssertionError):
                pass
            else:
                raise AssertionError('invalid probe metadata accepted')
        host = 'speed-dev-0905i.0a9e784d.dev.enclava.work'
        assert '--resolve' not in command(host, False)
        assert command(host, True)[-3:] == ['--resolve', f'{host}:443:{EDGE_IP}', f'https://{host}/healthz']
        assert not any(x in command(host, True) for x in ('-k', '--insecure', '-L'))
        print('paired HTTPS metadata self-test passed')
        return
    import re
    if not args.name or not re.fullmatch(r'speed-dev-0905[a-z]', args.name):
        parser.error('only disposable DEV experiment names are allowed')
    host = f'{args.name}.0a9e784d.dev.enclava.work'
    start = time.monotonic()
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        while time.monotonic() - start < 900:
            rows = list(pool.map(lambda mode: probe(host, mode), ('dns', 'pinned')))
            for row in rows:
                print(json.dumps(row), flush=True)
            if all(r['exit_code'] == 0 and r['http_status'] == 200
                   and r['tls_verify_result'] == 0 for r in rows):
                return
            time.sleep(2)
    raise SystemExit('paired HTTPS convergence timed out')


if __name__ == '__main__':
    main()
