import msvcrt
import os
import subprocess
from shared import *


def main():
    cutoff(); assert not (HERE/'chain_started.json').exists()
    with (c.OUT/'chain.lock').open('r+b') as lock:
        lock.seek(0); msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        write(HERE/'chain_started.json',dict(pid=os.getpid(),utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
        jobs=[('prepare','prepare.py','LOCAL_CELL_FIT_PREPARED'),('train','train.py','LOCAL_CELL_FIT_TRAINED'),
            ('training-independent','verify_training.py','LOCAL_CELL_FIT_TRAINING_VERIFIED'),
            ('eval','evaluate.py','LOCAL_CELL_FIT_EVALUATED'),('results-independent','verify_results.py','LOCAL_CELL_FIT_RESULTS_VERIFIED')]
        for stage,script,token in jobs:
            cutoff(); print('START',stage,flush=True)
            r=subprocess.run([sys.executable,str(ROOT/'scratchpad/gauntlet/L71/integration/run_check.py'),
                '--name','l72-local-cell-fit-'+stage,'--expect',token,'--',sys.executable,str(HERE/script)],cwd=ROOT)
            if r.returncode:
                write(HERE/'chain_failed.json',dict(stage=stage,returncode=r.returncode)); raise SystemExit(r.returncode)
            print('COMPLETE',stage,flush=True)
        write(HERE/'chain_complete.json',dict(complete=True)); print('LOCAL_CELL_FIT_CHAIN_COMPLETE')


if __name__=='__main__': main()
