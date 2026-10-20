"""Record inspected prototype checks with process/output evidence."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).parent
jobs = [
    ['icebow/.venv/Scripts/python.exe', '-m', 'pytest', str(HERE/'test_body_identity.py'), '-q'],
    ['research/ext/Royale/.venv/Scripts/python.exe', str(HERE/'probe_sim.py')],
]
expect = ['13 passed', 'SPAWNER_SIM_WAVES_PASS']
evidence = []
for command, token in zip(jobs, expect):
    p = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    combined = p.stdout + p.stderr
    evidence.append(dict(command=command, cwd=str(ROOT), shell='none; subprocess argument vector',
                         exit_code=p.returncode, expected=token, matched=token in combined,
                         output_sha256=hashlib.sha256(combined.encode()).hexdigest()))
    (HERE/('prototype_check_'+str(len(evidence))+'.out')).write_text(combined)
    if p.returncode != 0 or token not in combined:
        raise RuntimeError(combined)
(HERE/'prototype_checks.json').write_text(json.dumps(evidence, indent=2))
print('SPAWNER_PROTOTYPE_CHECKS_PASS')
