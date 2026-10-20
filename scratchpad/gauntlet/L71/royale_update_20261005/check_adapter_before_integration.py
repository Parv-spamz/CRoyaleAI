"""New-engine compatibility of the frozen main adapter; CPU-only baseline."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).parent
TESTS = [
    'test_royale_forms.py', 'test_royale_selfplay.py', 'test_hero_abilities.py',
    'test_ability_policy_sim.py', 'test_public_observation.py',
    'test_projectile_observation.py', 'test_projectile_motion.py',
    'test_rl_royale.py', 'test_rl_gen.py', 'test_rl_terminal_gap.py',
    'gen_v3/test_sim_contract.py',
]


def main():
    output = HERE/'adapter_before.out'
    receipt = HERE/'adapter_before.json'
    assert not receipt.exists()
    sources = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
               for p in sorted((ROOT/'pipeline').glob('*.py'))}
    env = dict(os.environ, PYTHONPATH=os.pathsep.join([str(ROOT/'research/ext/Royale-20261005/runtime'), str(ROOT)]),
               CUDA_VISIBLE_DEVICES='-1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1')
    command = [str(ROOT/'research/ext/Royale/.venv/Scripts/python.exe'), '-m', 'pytest', '-q',
               *['pipeline/tests/'+name for name in TESTS]]
    start = time.time()
    with output.open('w', encoding='utf-8') as stream:
        result = subprocess.run(command, cwd=ROOT, env=env, stdout=stream, stderr=subprocess.STDOUT)
    receipt.write_text(json.dumps(dict(command=command,cwd=str(ROOT),sources=sources,
        exit_code=result.returncode,seconds=time.time()-start,
        output_sha256=hashlib.sha256(output.read_bytes()).hexdigest()),indent=2))
    print('ADAPTER_BASELINE_CHECK_COMPLETE',result.returncode,flush=True)


if __name__ == '__main__':
    main()
