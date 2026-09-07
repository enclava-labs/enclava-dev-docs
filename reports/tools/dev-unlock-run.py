#!/usr/bin/env python3
"""Drive the normal CLI unlock prompt for disposable DEV persistence tests.

No raw terminal output is saved or printed. Password is sent only after the
CLI has reached its post-attestation prompt and terminal echo is disabled.
"""
import argparse
import errno
import json
import os
from pathlib import Path
import pty
import select
import signal
import termios
import time

BASE = Path('/home/user/private/dev-production-rehearsal-20260905')


def observed(output):
    return b'Unlock password' in output, b'Storage unlocked. App is starting.' in output


def send_password(fd, password):
    assert 0 < len(password) <= 4096 and b'\n' not in password and b'\r' not in password
    settings = termios.tcgetattr(fd)
    settings[3] &= ~(termios.ECHO | termios.ECHONL)
    termios.tcsetattr(fd, termios.TCSANOW, settings)
    assert not termios.tcgetattr(fd)[3] & (termios.ECHO | termios.ECHONL)
    payload = password + b'\n'
    while payload:
        count = os.write(fd, payload)
        if not count:
            raise OSError('terminal write failed')
        payload = payload[count:]


def drain_success(fd, tail):
    os.set_blocking(fd, False)
    success = observed(tail)[1]
    while True:
        try:
            data = os.read(fd, 4096)
        except BlockingIOError:
            return success
        except OSError as error:
            if error.errno == errno.EIO:
                return success
            raise
        if not data:
            return success
        tail = (tail + data)[-8192:]
        success |= observed(tail)[1]


def run(app):
    pid, fd = pty.fork()
    if pid == 0:
        env = dict(os.environ, ENCLAVA_STATE_DIR=str(BASE / 'auth/cli-state'))
        binary = str(BASE / 'cli-target/debug/enclava')
        os.execve(binary, [binary, 'unlock', '--app', app], env)
    sent = unlocked = False
    tail = b''
    status = None
    deadline = time.monotonic() + 360
    try:
        while time.monotonic() < deadline:
            if select.select([fd], [], [], 1)[0]:
                try:
                    data = os.read(fd, 4096)
                except OSError as error:
                    if error.errno != errno.EIO:
                        raise
                    data = b''
                tail = (tail + data)[-8192:]
                prompt, success = observed(tail)
                unlocked |= success
                if prompt and not sent:
                    password = (BASE / 'bootstrap/storage-password').read_bytes().rstrip(b'\r\n')
                    send_password(fd, password)
                    del password
                    sent = True
            done, child_status = os.waitpid(pid, os.WNOHANG)
            if done:
                status = child_status
                # The exited CLI may still have unread terminal output.
                # Only observe it: never send input after reaping the child.
                unlocked |= drain_success(fd, tail)
                break
        code = os.waitstatus_to_exitcode(status) if status is not None else 124
        result = {'exit_code': code, 'password_sent': sent, 'unlocked': unlocked}
        print(json.dumps(result))
        return 0 if code == 0 and sent and unlocked else 1
    finally:
        if status is None:
            # Exact local CLI child only; never operates on the workload.
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            os.waitpid(pid, 0)
        os.close(fd)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('app', nargs='?', choices=['speed-dev-0905t', 'speed-dev-0905u'])
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        assert observed(b'PRIVATE') == (False, False)
        assert observed(b'Unlock password:') == (True, False)
        assert observed(b'Storage unlocked. App is starting.') == (False, True)
        master, slave = pty.openpty()
        try:
            send_password(master, b'SYNTHETIC')
            assert select.select([slave], [], [], 1)[0]
            assert os.read(slave, 4096) == b'SYNTHETIC\n'
            assert not select.select([master], [], [], 0)[0], 'password echoed'
        finally:
            os.close(master)
            os.close(slave)
        master, slave = pty.openpty()
        try:
            os.write(slave, b'PRIVATE\nStorage unlocked. App is starting.')
            os.close(slave)
            assert drain_success(master, b''), 'queued success output lost'
        finally:
            os.close(master)
        print('unlock metadata self-test passed')
        return 0
    if not args.app:
        parser.error('disposable app required')
    try:
        return run(args.app)
    except Exception:
        print(json.dumps({'error': 'unlock_runner_failed'}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
