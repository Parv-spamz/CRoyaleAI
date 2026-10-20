"""Rerun mock-dependent upstream checks with their required source raw tables."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).parent
STACK = ROOT/'research/ext/Royale-20261005'


def main():
    # This is test-process-local. Production uses the packaged data and refuses overrides.
    env = dict(os.environ, PYTHONPATH=str(STACK/'runtime'),
               ROYALESIM_DATA_DIR=str(STACK/'RoyaleSim/data'), CUDA_VISIBLE_DEVICES='-1',
               OMP_NUM_THREADS='1', MKL_NUM_THREADS='1')
    py = ROOT/'research/ext/Royale/.venv/Scripts/python.exe'
    for name, cwd, args in [('sim_mock_recheck', STACK/'RoyaleSim', ['tests/test_watch_battle.py']),
                             ('gym_python_source_data', STACK/'RoyaleGym', [])]:
        receipt = HERE/(name+'.json')
        assert not receipt.exists()
        output = HERE/(name+'.out')
        cmd = [str(py), '-m', 'pytest', '-q', *args]
        start = time.time()
        print('START', name, flush=True)
        with output.open('w', encoding='utf-8') as stream:
            result = subprocess.run(cmd,cwd=cwd,env=env,stdout=stream,stderr=subprocess.STDOUT)
        receipt.write_text(json.dumps(dict(command=cmd,cwd=str(cwd),data_dir=env['ROYALESIM_DATA_DIR'],
            exit_code=result.returncode,seconds=time.time()-start,
            output_sha256=hashlib.sha256(output.read_bytes()).hexdigest()),indent=2))
        print('DONE',name,'exit',result.returncode,flush=True)


if __name__ == '__main__': main()
