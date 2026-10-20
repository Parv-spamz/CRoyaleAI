"""Run the relevant CPU tests and retain exit status and output provenance."""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
command = [str(ROOT/'research/ext/Royale/.venv/Scripts/python.exe'), '-m', 'pytest',
           'pipeline/tests/test_decision_options.py', 'pipeline/tests/test_live_gen_afford.py',
           'pipeline/tests/test_e1_batch.py', 'pipeline/tests/test_e1_eval_gen.py',
           'pipeline/tests/test_search_s0.py', '-q']
result = subprocess.run(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
print(result.stdout, end='')
(HERE/'tests.out').write_text(result.stdout)
(HERE/'tests_verification.json').write_text(json.dumps(dict(command=command, cwd=str(ROOT),
    shell='PowerShell invoking Python direct subprocess', exit_code=result.returncode,
    output_sha256=hashlib.sha256(result.stdout.encode()).hexdigest()), indent=2)+'\n')
if result.returncode:
    raise SystemExit(result.returncode)
print('DECISION_TESTS_VERIFIED')
