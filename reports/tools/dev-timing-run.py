#!/usr/bin/env python3
"""Run one fresh DEV CLI timing canary using existing normal-auth credentials.

Raw CLI output stays in a mode-700 private directory. This does not delete apps
or bypass auth. --preflight is read-only. Root starts observers before deployment.
"""
import argparse
import datetime
import json
import os
from pathlib import Path
import re
import subprocess
import time
import tomllib
import urllib.error
import urllib.parse
import urllib.request

BASE = Path('/home/user/private/dev-production-rehearsal-20260905')
# The normal CLI DTO/state uses the mapped CAP organization ID, not the PaaS DB ID.
ORG = 'c47855a0-e9e3-4756-a89a-e62eed9bd2e0'


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def observation_done(exit_code, running, seconds_after_exit):
    return exit_code is not None and (exit_code != 0 or running or seconds_after_exit >= 300)


def self_test():
    assert not observation_done(None, True, 999)
    assert not observation_done(0, False, 299)
    assert observation_done(0, False, 300)
    assert observation_done(0, True, 0)
    assert observation_done(1, False, 0)
    print('runner observation self-test passed')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('name', nargs='?')
    parser.add_argument('--preflight', action='store_true')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    if not args.name or not re.fullmatch(r'speed-dev-0905[a-z]', args.name):
        parser.error('only this experiment disposable app naming pattern is allowed')
    state = BASE / 'auth/cli-state'
    config = tomllib.loads((state / 'config.toml').read_text())
    creds = tomllib.loads((state / 'credentials.toml').read_text())
    api = config['api_url'].rstrip('/')
    parsed = urllib.parse.urlsplit(api)
    assert parsed.scheme == 'https' and parsed.hostname == 'app.dev.enclava.work'
    assert parsed.port in (None, 443) and not parsed.username and not parsed.query and not parsed.fragment
    assert config['org_id'] == ORG and config['org'] == 'dev-production-rehearsal-20260905'
    token = creds.get('session_token') or creds.get('api_key')
    assert token and creds['active_org_id'] == ORG
    opener = urllib.request.build_opener(NoRedirect)
    headers = {'Authorization': 'Bearer ' + token, 'X-Enclava-Org': config['org']}
    with opener.open(urllib.request.Request(api + '/users/me', headers=headers), timeout=10) as response:
        identity = json.load(response)
        # /users/me intentionally omits email. The mapped ID was independently
        # checked against aljaz@ceru.si with a read-only PaaS DB existence check.
        assert identity.get('user_id') == '75be09f6-0cda-4da4-9b67-3f6aabfe911b', 'normal-auth user mismatch'
        assert identity['active_org']['id'] == ORG

    def status():
        req = urllib.request.Request(api + '/apps/' + args.name, headers=headers)
        try:
            with opener.open(req, timeout=10) as response:
                value = json.load(response)
                return {'http_status': response.status, 'app_status': value.get('status')}
        except urllib.error.HTTPError as error:
            return {'http_status': error.code}
        except (OSError, ValueError):
            return {'http_status': 0}

    def https_status():
        # Owned disposable app only. Never forward PaaS authentication headers.
        url = f'https://{args.name}.0a9e784d.dev.enclava.work/healthz'
        try:
            with opener.open(urllib.request.Request(url), timeout=2) as response:
                return response.status
        except urllib.error.HTTPError as error:
            return error.code
        except (OSError, ValueError):
            return 0

    before = status()
    assert before['http_status'] == 404, 'fresh-name check failed (must be authenticated 404)'
    print(json.dumps({'at': now(), 'name': args.name, 'preflight': before}), flush=True)
    if args.preflight:
        return
    os.umask(0o077)
    output = BASE / args.name
    output.mkdir(mode=0o700)  # Never overwrite a previous run.
    env = dict(os.environ, ENCLAVA_STATE_DIR=str(state), COSIGN_BIN='/tmp/enclava-cosign-v3.1.2/cosign')
    command = [str(BASE / 'cli-target/debug/enclava'), 'template', 'deploy', 'debian-ssh-frp',
               '--name', args.name, '--ssh-public-key-file', str(BASE / 'bootstrap/ssh/id_ed25519.pub'),
               '--storage-password-file', str(BASE / 'bootstrap/storage-password'),
               '--ssh-timeout-seconds', '1800', '--timings', '--json']
    with (output / 'stdout.json').open('xb') as stdout, (output / 'stderr.log').open('xb') as stderr, (output / 'api-status.jsonl').open('x') as samples, (output / 'https-status.jsonl').open('x') as https_samples:
        start = time.monotonic()
        started_at = now()
        process = subprocess.Popen(command, stdout=stdout, stderr=stderr, env=env)
        exit_seen = None
        while True:
            exit_code = process.poll()
            if exit_code is not None and exit_seen is None:
                exit_seen = time.monotonic()
            sample = dict(status(), at=now(), elapsed_ms=(time.monotonic()-start)*1000)
            samples.write(json.dumps(sample) + '\n')
            samples.flush()
            running = sample.get('http_status') == 200 and sample.get('app_status') == 'running'
            public_status = https_status()
            https_samples.write(json.dumps({'at': now(), 'elapsed_ms': (time.monotonic()-start)*1000,
                                           'http_status': public_status}) + '\n')
            https_samples.flush()
            after_exit = time.monotonic() - exit_seen if exit_seen is not None else 0
            if observation_done(exit_code, running and public_status == 200, after_exit):
                break
            time.sleep(2)
        result = {'name': args.name, 'started_at': started_at, 'finished_at': now(),
                  'elapsed_ms': (time.monotonic()-start)*1000, 'exit_code': process.returncode,
                  'cli_exit_observed_ms': (exit_seen-start)*1000,
                  'api_running_at_finish': running,
                  'https_ok_at_finish': public_status == 200,
                  'convergence_timed_out': exit_code == 0 and not (running and public_status == 200)}
        # Wrapper elapsed includes API convergence observation (up to 300s tail),
        # not deployment duration. CLI monotonic total remains authoritative.
        (output / 'run.json').write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
