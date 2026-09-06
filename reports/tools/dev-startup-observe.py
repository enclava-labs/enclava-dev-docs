#!/usr/bin/env python3
"""Bounded DEV startup metadata; no pod logs, exec, environment or event messages."""
import argparse
import datetime
import json
import re
import subprocess
import time

CONTAINERS = {'web', 'enclava-init', 'enclava-tools', 'tenant-ingress', 'attestation-proxy'}


def project_pod(pod):
    status = pod.get('status', {})
    return {
        'uid': pod['metadata']['uid'],
        'created': pod['metadata']['creationTimestamp'],
        'phase': status.get('phase'),
        'conditions': [{k: c.get(k) for k in ('type', 'status', 'lastTransitionTime')}
                       for c in status.get('conditions', [])],
        'containers': [
            {'name': c['name'], 'ready': c.get('ready'), 'restarts': c.get('restartCount'),
             'state': {kind: {k: v[k] for k in ('reason', 'startedAt', 'finishedAt', 'exitCode') if k in v}
                       for kind, v in c.get('state', {}).items()}}
            for c in status.get('initContainerStatuses', []) + status.get('containerStatuses', [])
            if c['name'] in CONTAINERS],
    }


def kube(*args):
    result = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=5',
                             'master.enc-work', 'sudo', '-n', 'kubectl', *args],
                            capture_output=True, timeout=20, check=False)
    if result.returncode:
        return None
    return json.loads(result.stdout)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('name', nargs='?')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        projected = project_pod({'metadata': {'uid': 'u', 'creationTimestamp': 't',
                                              'annotations': {'secret': 'PRIVATE'}},
                                'spec': {'env': 'PRIVATE'},
                                'status': {'containerStatuses': [
                                    {'name': 'enclava-init', 'state': {'terminated': {
                                        'message': 'PRIVATE', 'exitCode': 1}}}]}})
        assert 'PRIVATE' not in json.dumps(projected)
        assert projected['containers'][0]['state']['terminated'] == {'exitCode': 1}
        print('metadata projection check passed')
        return
    if not args.name or not re.fullmatch(r'speed-dev-0905[a-z]', args.name):
        parser.error('only fixed disposable DEV names are permitted')
    ns = 'cap-dev-production-rehearsal-20260905-' + args.name
    deadline = time.monotonic() + 900
    while time.monotonic() < deadline:
        row = {'at': datetime.datetime.now(datetime.timezone.utc).isoformat()}
        pods = kube('-n', ns, 'get', 'pods', '-o', 'json')
        row['pods'] = [project_pod(p) for p in (pods or {}).get('items', [])]
        events = kube('-n', ns, 'get', 'events', '-o', 'json')
        row['events'] = [{k: e.get(k) for k in ('reason', 'firstTimestamp', 'lastTimestamp', 'count')}
                         for e in (events or {}).get('items', [])]
        stats = kube('get', '--raw', '/api/v1/nodes/empire-de-snp-worker/proxy/stats/summary')
        row['cpu'] = [{
            'uid': p['podRef']['uid'],
            'containers': [{'name': c['name'], **{k: c.get('cpu', {}).get(k)
                            for k in ('time', 'usageNanoCores', 'usageCoreNanoSeconds')}}
                           for c in p.get('containers', []) if c['name'] in CONTAINERS],
        } for p in (stats or {}).get('pods', []) if p.get('podRef', {}).get('namespace') == ns]
        print(json.dumps(row), flush=True)
        time.sleep(5)


if __name__ == '__main__':
    main()
