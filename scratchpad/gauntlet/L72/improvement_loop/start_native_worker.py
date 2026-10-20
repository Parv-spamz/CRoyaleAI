"""Start one owner-authorized isolated native replay worker without policy overrides."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
NATIVE = ROOT/'research/ext/cr-native-sandbox'
sys.path.insert(0, str(NATIVE))
from native_core.worker import HeadlessWorkerPool, WorkerConfig
from native_core.client import request


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    report = HERE/'native_worker_start.json'
    if report.exists():
        raise ValueError('Fresh start receipt required')
    preflight = json.loads((HERE/'native_host_verified.json').read_text())
    manifest = Path(preflight['runtime_manifest'])
    assert sha(manifest) == preflight['runtime_manifest_sha256']
    runtime = json.loads(manifest.read_text(encoding='utf-8-sig'))
    for group, env in (('native_libs','CR_SANDBOX_RUNTIME_DIR'), ('apks','CR_SANDBOX_APKS')):
        for item in runtime[group]:
            assert sha(Path(os.environ[env])/item['name']) == item['sha256']
    for port in preflight['selected_ports']:
        with socket.socket() as sock:
            sock.bind(('127.0.0.1',port))
    cfg = WorkerConfig(data_root=manifest.parents[1], emulator_port=5560,
        service_base_port=37031,direct_base_port=38031,cores=2,memory_mb=4096)
    pool = HeadlessWorkerPool(cfg)
    result = dict(started_at=time.strftime('%Y-%m-%dT%H:%M:%S'),
        manifest_sha256=sha(manifest), driver_sha256=sha(Path(__file__)),
        worker_source_sha256=sha(NATIVE/'native_core/worker.py'),
        service_script_sha256=sha(NATIVE/'scripts/start_direct_service.ps1'),
        native_bridge_sha256=sha(NATIVE/'artifacts/libnative_core_probe.so'),
        native_jar_sha256=sha(NATIVE/'artifacts/lifecycle-probe.jar'),
        emulator_serial=cfg.serial,cores=2,memory_mb=4096,system_policy_changed=False)

    def save():
        report.write_text(json.dumps(result,indent=2))

    try:
        result['vm'] = pool.start_vm(timeout=150)
        save()
        print('ISOLATED_NATIVE_VM_READY',flush=True)
        result['package'] = pool.ensure_package()
        installed = pool._adb('shell','dumpsys','package','com.supercell.clashroyale')
        if 'versionCode=150535029' not in installed:
            raise ValueError('Native AVD package version mismatch')
        result['installed_version_verified'] = True
        save()
        shell = shutil.which('pwsh.exe') or shutil.which('powershell.exe')
        command = [shell,'-NoProfile','-File',str(NATIVE/'scripts/start_direct_service.ps1'),
            '-Adb',str(cfg.adb),'-Serial',cfg.serial,'-Port','37031','-Slot','0',
            '-DataRoot',str(cfg.data_root),'-ReadyTimeoutSeconds','300']
        result['service_command'] = command
        service = subprocess.run(command,cwd=NATIVE,capture_output=True,text=True,
            timeout=420,creationflags=subprocess.CREATE_NO_WINDOW)
        (HERE/'native_service_start.out').write_text(service.stdout)
        (HERE/'native_service_start.err').write_text(service.stderr)
        result['service_exit_code'] = service.returncode
        result['service_stdout_sha256'] = sha(HERE/'native_service_start.out')
        result['service_stderr_sha256'] = sha(HERE/'native_service_start.err')
        save()
        if service.returncode:
            raise ValueError('Native service start failed; inspect preserved stdout/stderr')
        state = request({'op':'observe'},port=37031,timeout=10)['state']
        result['attestation'] = pool._attest(0,state,started=True)
        result['direct_transport'] = pool.configure_direct_ports(1)
        result['complete'] = True
        save()
        print(json.dumps(result['attestation']),flush=True)
        print('ISOLATED_NATIVE_WORKER_ATTESTED',flush=True)
    except Exception as error:
        result.update(complete=False,error=repr(error))
        save()
        raise


if __name__ == '__main__':
    main()
