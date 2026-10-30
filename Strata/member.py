"""GetGoingFast local launcher for the unmodified official Strata app."""
import ctypes
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parent
BASE = 'http://127.0.0.1:' + os.environ.get('STRATA_PORT', '8798')


def api(path, body=None, timeout=120):
    request = urllib.request.Request(BASE + path, data=None if body is None else json.dumps(body).encode(),
                                     headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        raise RuntimeError(error.read().decode(errors='replace')) from error


def connection_closed(error):
    reason = getattr(error, 'reason', error)
    return isinstance(reason, (ConnectionRefusedError, ConnectionResetError))


def port_listening():
    with socket.socket() as probe:
        probe.settimeout(2)
        return probe.connect_ex(('127.0.0.1', int(os.environ.get('STRATA_PORT', '8798')))) == 0


def start():
    expected = os.path.normcase(os.path.abspath(os.environ['STRATA_WORKSPACE']))
    def own_host():
        result = api('/api/workspaces', timeout=3)
        if not any(os.path.normcase(os.path.abspath(w.get('path', ''))) == expected
                   for w in result.get('workspaces', [])):
            raise RuntimeError('This port belongs to another workspace. Close that app or change STRATA_PORT in the BAT.')
        return True
    try:
        own_host()
        return
    except urllib.error.URLError:
        pass
    (ROOT / 'logs').mkdir(exist_ok=True)
    with (ROOT / 'logs' / 'agent-host.log').open('ab') as log:
        process = subprocess.Popen([str(ROOT / 'app/node/node.exe'), str(ROOT / 'app/host/server/index.mjs'),
                                    '--dist', str(ROOT / 'app/host/dist')], cwd=ROOT,
                                   stdout=log, stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)
    (ROOT / 'state').mkdir(exist_ok=True)
    (ROOT / 'state/host-pid.json').write_text(json.dumps({'pid': process.pid}), encoding='utf-8')
    for _ in range(60):
        if process.poll() is not None:
            raise RuntimeError('Agent host stopped. Read Strata/logs/agent-host.log.')
        try:
            if own_host():
                return
        except urllib.error.URLError:
            time.sleep(1)
    raise RuntimeError('Agent host did not become ready within 60 seconds.')


def stop():
    if not port_listening():
        print('Strata is already stopped.')
        return
    expected = os.path.normcase(os.path.abspath(os.environ['STRATA_WORKSPACE']))
    try:
        workspaces = api('/api/workspaces', timeout=45)
    except OSError as error:
        if not connection_closed(error):
            raise
        print('Strata is already stopped.')
        return
    if not any(os.path.normcase(os.path.abspath(w.get('path', ''))) == expected
               for w in workspaces.get('workspaces', [])):
        raise RuntimeError('This port belongs to another workspace. No process was stopped.')
    if api('/api/agent/status').get('activeTurns', 0):
        raise RuntimeError('Stop the active chat in Strata first, then choose Stop again.')
    state = api('/api/native')
    if any(job.get('state') == 'running' for job in state.get('jobs', [])):
        raise RuntimeError('Finish or cancel the active download or operation in Strata first.')
    for instance in state.get('instances', []):
        api('/api/native/instances/' + instance['id'] + '/unload', {})
    pid = json.loads((ROOT / 'state/host-pid.json').read_text())['pid']
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.OpenProcess.restype = ctypes.c_void_p
    kernel.QueryFullProcessImageNameW.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_ulong)]
    kernel.CloseHandle.argtypes = [ctypes.c_void_p]
    handle = kernel.OpenProcess(0x1000, False, pid)
    if not handle:
        raise ctypes.WinError()
    try:
        buffer = ctypes.create_unicode_buffer(32768)
        length = ctypes.c_ulong(len(buffer))
        if not kernel.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(length)):
            raise ctypes.WinError()
        if Path(buffer.value).resolve() != (ROOT / 'app/node/node.exe').resolve():
            raise RuntimeError('Recorded PID no longer belongs to this Strata app. No process was stopped.')
    finally:
        kernel.CloseHandle(handle)
    result = subprocess.run(['taskkill.exe', '/PID', str(pid), '/T', '/F'], check=False,
                            creationflags=subprocess.CREATE_NO_WINDOW, capture_output=True, text=True)
    for _ in range(20):
        if not port_listening():
            print('This Strata model and agent have stopped. All files are retained.')
            return
        time.sleep(0.25)
    detail = (result.stderr or result.stdout).strip()
    raise RuntimeError('The Strata server is still responding after stop. ' + detail)


def test():
    status = api('/api/agent/status')
    if status.get('state') == 'unavailable':
        raise RuntimeError('Agent runtime unavailable: ' + str(status))
    snapshot = api('/api/native')
    ready = [r for r in snapshot.get('instances', []) if r.get('status') == 'ready']
    if not ready:
        raise RuntimeError('Load a model in Strata before testing tools.')
    stamp = str(time.time_ns())
    filename = 'ggf-agent-test-' + stamp + '.txt'
    marker = time.strftime('%Y-%m-%d') + ' GGF_TOOL_TEST_' + stamp
    body = {'sessionId': 'ggf-test-' + stamp, 'nativeModelId': ready[0]['id'], 'mode': 'manual', 'thinking': 'off',
            'message': f'Use your file tools to create {filename} in the current workspace containing exactly {marker}. '
                       'Then read it back using a file tool and report its content. Do not modify any other file.'}
    request = urllib.request.Request(BASE + '/api/chat/stream', data=json.dumps(body).encode(),
                                     headers={'Content-Type': 'application/json'})
    print('The agent may ask permission. This test permits only creation of its uniquely named test file.')
    print('Any requested write will be displayed here for approval.')
    log_path = ROOT / 'logs' / (body['sessionId'] + '.ndjson')
    read_verified = False
    with urllib.request.urlopen(request, timeout=600) as response, log_path.open('wb') as log:
        for line in response:
            log.write(line)
            log.flush()
            frame = json.loads(line)
            if frame.get('type') in ('error', 'agent-tool'):
                print(json.dumps(frame), flush=True)
            card = frame.get('tool', {})
            if frame.get('type') == 'agent-tool' and card.get('state') == 'proposed':
                if os.environ.get('GGF_AGENT_TEST_AUTO') == '1':
                    arguments = card.get('args', {})
                    proposed = Path(arguments.get('file_path', arguments.get('path', '')))
                    if not proposed.is_absolute():
                        proposed = Path(os.environ['STRATA_WORKSPACE']) / proposed
                    expected = Path(os.environ['STRATA_WORKSPACE']) / filename
                    permitted = card.get('name') == 'write' and proposed.resolve() == expected.resolve() and arguments.get('content', '').strip() == marker
                    decision = 'approve' if permitted else 'deny'
                    print('Scoped test approval: ' + decision, flush=True)
                else:
                    decision = 'approve' if input('Approve this exact tool action once? [y/N] ').strip().lower() == 'y' else 'deny'
                api('/api/chat/approval', {'sessionId': body['sessionId'], 'toolId': card['id'], 'decision': decision})
            if card.get('name') == 'read' and card.get('state') == 'done' and marker in str(card.get('result', '')):
                read_verified = True
    output = Path(os.environ['STRATA_WORKSPACE']) / filename
    if not output.is_file() or output.read_text(encoding='utf-8').strip() != marker:
        raise RuntimeError('Agent file creation did not pass. Read ' + str(log_path))
    if not read_verified:
        raise RuntimeError('The file was created, but tool-based readback was not verified. Read ' + str(log_path))
    print('Verified: agent write and read tools passed. Transcript: ' + str(log_path))


if __name__ == '__main__':
    try:
        command = sys.argv[1]
        if command == 'start': start()
        elif command == 'test': test()
        elif command == 'stop': stop()
        else: raise ValueError('Unknown command')
    except Exception as error:
        print('ERROR:', error, file=sys.stderr)
        sys.exit(1)
