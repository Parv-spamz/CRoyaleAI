"""Build current native capture sources separately; preserve the original binaries."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
NATIVE = ROOT / 'research/ext/cr-native-sandbox'
OUT = ROOT / 'icebow/data/bench/native_confirmation_20261005/runtime/build_current'
sys.path.insert(0, str(NATIVE))
from native_core.client import request
from native_core.worker import HeadlessWorkerPool, WorkerConfig


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    if OUT.exists():
        raise ValueError('Fresh build output required')
    OUT.mkdir(parents=True)
    report = dict(started_at=time.strftime('%Y-%m-%dT%H:%M:%S'), commands=[],
                  original_bridge_sha256=sha(NATIVE/'artifacts/libnative_core_probe.so'),
                  original_jar_sha256=sha(NATIVE/'artifacts/lifecycle-probe.jar'))
    receipt = HERE/'native_worker_rebuild.json'

    def save():
        receipt.write_text(json.dumps(report, indent=2))

    def run(name, command, timeout=120):
        result = subprocess.run([str(x) for x in command], capture_output=True,
                                timeout=timeout, creationflags=subprocess.CREATE_NO_WINDOW)
        (HERE/(name+'.out')).write_bytes(result.stdout)
        (HERE/(name+'.err')).write_bytes(result.stderr)
        report['commands'].append(dict(name=name, argv=[str(x) for x in command],
            exit_code=result.returncode, stdout_sha256=sha(HERE/(name+'.out')),
            stderr_sha256=sha(HERE/(name+'.err'))))
        save()
        if result.returncode:
            raise ValueError(f'{name} failed: {result.returncode}')
        return result

    try:
        source = NATIVE/'android_probe/native/jni_bridge.cpp'
        copied = OUT/'jni_bridge.cpp'
        copied.write_bytes(source.read_bytes())
        report['source_sha256'] = sha(copied)
        compiler = Path(os.environ['CR_SANDBOX_NDK'])/'toolchains/llvm/prebuilt/windows-x86_64/bin/clang++.exe'
        bridge = OUT/'libnative_core_probe.so'
        run('native_bridge_build', [compiler,'--target=x86_64-linux-android23',
            '-std=c++20','-fPIC','-shared','-O2','-g','-Wall','-Wextra','-Werror',
            copied,'-ldl','-o',bridge])
        java_sources = sorted((NATIVE/'android_probe/java').rglob('*.java'))
        report['java_sources'] = {str(p.relative_to(NATIVE)):sha(p) for p in java_sources}
        classes = OUT/'classes'
        classes.mkdir()
        jdk = Path(os.environ['CR_SANDBOX_JDK'])/'bin'
        android_jar = os.environ['CR_SANDBOX_ANDROID_JAR']
        run('native_java_build', [jdk/'javac.exe','--release','8','-g','-classpath',
            android_jar,'-d',classes,*java_sources])
        jar = OUT/'lifecycle-probe.jar'
        run('native_dex_build', [jdk/'java.exe','-cp',
            Path(os.environ['CR_SANDBOX_ANDROID_TOOLS'])/'lib/r8.jar',
            'com.android.tools.r8.D8','--debug','--min-api','23','--lib',android_jar,
            '--output',jar,*sorted(classes.rglob('*.class'))])
        report['bridge_sha256'] = sha(bridge)
        report['jar_sha256'] = sha(jar)
        original = NATIVE/'scripts/start_direct_service.ps1'
        script = original.read_text()
        replacements = {
            '$ProjectRoot = Split-Path -Parent $PSScriptRoot': f"$ProjectRoot = '{NATIVE}'",
            '$Jar = Join-Path $ProjectRoot "artifacts\\lifecycle-probe.jar"': f"$Jar = '{jar}'",
            '$Bridge = Join-Path $ProjectRoot "artifacts\\libnative_core_probe.so"': f"$Bridge = '{bridge}'",
            '$AssetArchive = Join-Path $ProjectRoot "artifacts\\runtime-assets.tar"': f"$AssetArchive = '{OUT/'runtime-assets.tar'}'",
        }
        for before, after in replacements.items():
            assert script.count(before) == 1, before
            script = script.replace(before, after)
        service = OUT/'start_direct_service.ps1'
        service.write_text(script)
        report['original_service_sha256'] = sha(original)
        report['service_sha256'] = sha(service)
        run('native_rebuilt_service_start', ['pwsh','-NoProfile','-File',service,
            '-Serial','emulator-5560','-Port','37031','-Slot','0',
            '-DataRoot',OUT.parent,'-ReadyTimeoutSeconds','60'], timeout=180)
        pool = HeadlessWorkerPool(WorkerConfig(data_root=OUT.parent,emulator_port=5560,
            service_base_port=37031,direct_base_port=38031,cores=2,memory_mb=4096))
        state = request({'op':'observe'},port=37031,timeout=10)['state']
        report['attestation'] = pool._attest(0,state,started=True)
        report['direct_transport'] = pool.configure_direct_ports(1)
        assert sha(NATIVE/'artifacts/libnative_core_probe.so') == report['original_bridge_sha256']
        assert sha(NATIVE/'artifacts/lifecycle-probe.jar') == report['original_jar_sha256']
        report['complete'] = True
        save()
        print('REBUILT_NATIVE_WORKER_ATTESTED', flush=True)
    except Exception as error:
        report.update(complete=False,error=repr(error))
        save()
        raise


if __name__ == '__main__':
    main()
