#!/usr/bin/env python3
"""Project one disposable DEV pod's CRI lifecycle from k0s journal JSON.

stdin only; never saves or echoes messages, specs, errors, image names or IDs.
No guest logs/exec or debug logging. Only source-defined containerd lifecycle
messages and bound sandbox/container IDs may produce fixed metadata records.
"""
import argparse
import datetime
import json
import re
import sys
import uuid

CONTAINERS = {'web', 'enclava-tools', 'attestation-proxy', 'tenant-ingress', 'enclava-init'}
HEX = r'[0-9a-f]{64}'
FIELDS = re.compile(r'\b([A-Za-z_]+)=("(?:[^"\\]|\\.)*"|[^\s]+)')


def message(row):
    if row.get('_SYSTEMD_UNIT') != 'k0sworker.service' or row.get('_COMM') != 'k0s':
        return None
    value = row.get('MESSAGE')
    source = False
    for _ in range(3):
        if not isinstance(value, str):
            return None
        fields = {}
        for key, raw in FIELDS.findall(value):
            if key in fields:
                return None
            fields[key] = json.loads(raw) if raw.startswith('"') else raw
        source |= fields.get('component') == 'containerd'
        if 'msg' not in fields:
            return value if source else None
        value = fields['msg']
    return None


class Collector:
    def __init__(self, app, pod_uid):
        if not re.fullmatch(r'speed-dev-0905[a-z]', app):
            raise ValueError('invalid disposable app')
        self.uid = str(uuid.UUID(pod_uid))
        ns = 'cap-dev-production-rehearsal-20260905-' + app
        meta = '&PodSandboxMetadata{Name:' + app + '-0,Uid:' + self.uid + ',Namespace:' + ns + ',Attempt:'
        self.pod = re.compile(re.escape('RunPodSandbox for ' + meta) + r'([0-9]+),\}(.*)')
        self.sandboxes = set()
        self.containers = {}

    def record(self, row):
        msg = message(row)
        if msg is None:
            return None
        phase = boundary = container = None
        match = self.pod.fullmatch(msg)
        if match:
            tail = match[2]
            end = re.fullmatch(r' returns sandbox id "(' + HEX + r')"', tail)
            if end:
                self.sandboxes.add(end[1])
                boundary = 'success'
            elif tail == '':
                boundary = 'start'
            elif tail == ' failed, error':
                boundary = 'error'
            phase = 'run_sandbox'
        else:
            match = re.fullmatch(r'CreateContainer within sandbox "(' + HEX + r')" for (container )?&ContainerMetadata\{Name:([^,]+),Attempt:([0-9]+),\}(.*)', msg)
            if match and match[1] in self.sandboxes and match[3] in CONTAINERS:
                container = match[3]
                tail = match[5]
                end = re.fullmatch(r' returns container id "(' + HEX + r')"', tail)
                if end and not match[2]:
                    self.containers[end[1]] = container
                    boundary = 'success'
                elif tail == '' and match[2]:
                    boundary = 'start'
                elif tail == ' failed' and not match[2]:
                    boundary = 'error'
                phase = 'create_container'
            else:
                match = re.fullmatch(r'StartContainer for "(' + HEX + r')"(.*)', msg)
                if match and match[1] in self.containers:
                    container = self.containers[match[1]]
                    boundary = {'': 'start', ' returns successfully': 'success', ' failed': 'error'}.get(match[2])
                    phase = 'start_container'
        if phase is None or boundary is None:
            return None
        micros = row['__REALTIME_TIMESTAMP']
        if not isinstance(micros, str) or not re.fullmatch(r'[0-9]{1,17}', micros):
            raise ValueError('invalid timestamp')
        at = datetime.datetime.fromtimestamp(int(micros) / 1_000_000, datetime.timezone.utc).isoformat()
        result = {'at': at, 'phase': phase, 'boundary': boundary}
        if container:
            result['container'] = container
        return result


def self_test():
    app, uid, sid, cid = 'speed-dev-0905s', str(uuid.UUID(int=1)), 'a' * 64, 'b' * 64
    collector = Collector(app, uid)
    def row(msg, component='containerd'):
        return {'_SYSTEMD_UNIT': 'k0sworker.service', '_COMM': 'k0s', '__REALTIME_TIMESTAMP': '1788757200000000',
                'MESSAGE': 'level=info component=' + component + ' msg=' + json.dumps(msg) + ' error="PRIVATE"'}
    pod = f'RunPodSandbox for &PodSandboxMetadata{{Name:{app}-0,Uid:{uid},Namespace:cap-dev-production-rehearsal-20260905-{app},Attempt:0,}}'
    messages = [pod, pod + f' returns sandbox id "{sid}"',
                f'CreateContainer within sandbox "{sid}" for container &ContainerMetadata{{Name:enclava-init,Attempt:0,}}',
                f'CreateContainer within sandbox "{sid}" for &ContainerMetadata{{Name:enclava-init,Attempt:0,}} returns container id "{cid}"',
                f'StartContainer for "{cid}"', f'StartContainer for "{cid}" returns successfully']
    records = [collector.record(row(msg)) for msg in messages]
    assert [r['boundary'] for r in records] == ['start', 'success'] * 3
    assert 'PRIVATE' not in json.dumps(records) and sid not in json.dumps(records)
    for msg in [pod.replace(uid, str(uuid.UUID(int=2))), messages[2].replace(sid, 'c' * 64),
                messages[-1].replace(cid, 'd' * 64), messages[-1] + ' PRIVATE', 'payload PRIVATE']:
        assert collector.record(row(msg)) is None
    assert collector.record(row(messages[-1], 'kubelet')) is None
    bad = row(messages[-1]); bad['_SYSTEMD_UNIT'] = 'other.service'
    assert collector.record(bad) is None
    nested = row(json.dumps('not lifecycle'))
    assert collector.record(nested) is None
    bad = row(messages[-1]); bad['MESSAGE'] += ' msg="PRIVATE"'
    assert collector.record(bad) is None
    print('CRI lifecycle projection self-test passed')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--app')
    parser.add_argument('--pod-uid')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    if not args.app or not args.pod_uid:
        parser.error('--app and --pod-uid required')
    collector = Collector(args.app, args.pod_uid)
    invalid = emitted = 0
    for line in sys.stdin:
        try:
            record = collector.record(json.loads(line))
        except (ValueError, KeyError, TypeError, OverflowError, AttributeError):
            invalid += 1
            continue
        if record:
            print(json.dumps(record), flush=True)
            emitted += 1
    print(f'projected={emitted} malformed={invalid}', file=sys.stderr)
    if invalid or not emitted:
        sys.exit(2)


if __name__ == '__main__':
    main()
