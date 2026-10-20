"""Owner-requested retry of the same sixteen Rust executables; no policy changes."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    out = HERE / 'rust_retry_owner.json'
    if out.exists():
        raise ValueError('Fresh owner retry report required')
    old = json.loads((HERE / 'sim_rust.json').read_text())
    log = (HERE / 'sim_rust.out').read_text()
    paths = [Path(p) for p in re.findall(r'could not execute process `([^`]+)` \(never executed\)', log)]
    if len(paths) != 16:
        raise ValueError('Expected the original sixteen targets')
    cwd = Path(old['cwd'])
    results = []
    env = dict(os.environ, CUDA_VISIBLE_DEVICES='-1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1')
    for exe in paths:
        if not exe.resolve().is_relative_to((cwd / 'target/gate/deps').resolve()):
            raise ValueError('Unexpected executable path')
        before = digest(exe)
        started = time.time()
        name = exe.stem.rsplit('-', 1)[0]
        output = HERE / ('rust_retry_' + name + '.out')
        print('RETRY', name, flush=True)
        try:
            p = subprocess.run([str(exe), '--test-threads=1'], cwd=cwd, env=env,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=180)
            raw, code = p.stdout, p.returncode
        except OSError as error:
            raw, code = str(error).encode(), -1
        output.write_bytes(raw)
        if digest(exe) != before:
            raise ValueError('Executable bytes changed')
        summary = re.findall(r'test result: (\w+)\. (\d+) passed; (\d+) failed; (\d+) ignored;', raw.decode('utf-8', errors='replace'))
        result = dict(target=name, executable=str(exe), executable_sha256=before,
                      command=[str(exe), '--test-threads=1'], exit_code=code,
                      seconds=time.time()-started, output_sha256=digest(output), summaries=summary)
        results.append(result)
        print(name, code, summary, flush=True)
    passed = all(r['exit_code'] == 0 and r['summaries'] and
                 all(s[0] == 'ok' and int(s[2]) == 0 for s in r['summaries']) for r in results)
    out.write_text(json.dumps(dict(owner_requested_retry=True, security_policy_changed_by_agent=False,
        binaries_modified=False, all_targets_passed=passed, results=results), indent=2))
    print('OWNER_RUST_RETRY_PASS' if passed else 'OWNER_RUST_RETRY_INCOMPLETE')
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
