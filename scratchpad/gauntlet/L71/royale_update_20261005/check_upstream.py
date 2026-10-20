"""CPU-only upstream acceptance; never installs into the frozen runtime."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).parent
STACK = ROOT / 'research/ext/Royale-20261005'
PY = ROOT / 'research/ext/Royale/.venv/Scripts/python.exe'


def main():
    while not (HERE / 'build_manifest.json').exists():
        time.sleep(10)
    manifest = json.loads((HERE / 'build_manifest.json').read_text())
    runtime = STACK / 'runtime'
    for name, digest in manifest['files'].items():
        assert hashlib.sha256((runtime / name).read_bytes()).hexdigest() == digest, name
    env = dict(os.environ, PYTHONPATH=str(runtime), CUDA_VISIBLE_DEVICES='-1',
               CARGO_BUILD_JOBS='2', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1')
    jobs = [
        ('wheel_smoke', [PY, STACK / 'RoyaleSim/tools/wheel_smoke.py'], STACK),
        ('sim_python', [PY, '-m', 'pytest', '-q'], STACK / 'RoyaleSim'),
        ('gym_python', [PY, '-m', 'pytest', '-q'], STACK / 'RoyaleGym'),
        ('sim_rust', ['cargo', 'test', '--profile', 'gate', '--no-fail-fast'],
         STACK / 'RoyaleSim/crates/royalesim'),
    ]
    outcomes = {}
    for name, command, cwd in jobs:
        receipt = HERE / (name + '.json')
        if receipt.exists():
            raise ValueError('Fresh receipt required: ' + name)
        output = HERE / (name + '.out')
        print('START', name, flush=True)
        start = time.time()
        with output.open('w', encoding='utf-8') as stream:
            result = subprocess.run([str(s) for s in command], cwd=cwd, env=env,
                                    stdout=stream, stderr=subprocess.STDOUT)
        data = dict(command=[str(s) for s in command], cwd=str(cwd),
                    exit_code=result.returncode, seconds=time.time()-start,
                    output_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
                    runtime_manifest_sha256=hashlib.sha256((HERE/'build_manifest.json').read_bytes()).hexdigest())
        receipt.write_text(json.dumps(data, indent=2))
        outcomes[name] = result.returncode
        print('DONE', name, 'exit', result.returncode, flush=True)
    (HERE / 'upstream_checks.json').write_text(json.dumps(outcomes, indent=2))
    print('UPSTREAM_CHECKS_COMPLETE', outcomes, flush=True)


if __name__ == '__main__':
    main()
