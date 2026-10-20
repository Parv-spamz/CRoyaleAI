import msvcrt
import os
import subprocess
from shared import *


def main():
    cutoff(); assert not (HERE/'chain_started.json').exists()
    with (c.OUT/'chain.lock').open('r+b') as lock:
        lock.seek(0); msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        write(HERE/'chain_started.json',dict(pid=os.getpid(),utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
        jobs=[('prepare','prepare.py','ORDINARY_EXTENDED_PREPARED'),('train','train.py','ORDINARY_EXTENDED_TRAINED'),
            ('training-independent','verify_training.py','ORDINARY_EXTENDED_TRAINING_VERIFIED'),
            ('eval','evaluate.py','ORDINARY_EXTENDED_EVALUATED'),('results-independent','verify_results.py','ORDINARY_EXTENDED_RESULTS_VERIFIED')]
        for stage,script,token in jobs:
            cutoff(); print('START',stage,flush=True)
            r=subprocess.run([sys.executable,str(ROOT/'scratchpad/gauntlet/L71/integration/run_check.py'),
                '--name','l72-development9-'+stage,'--expect',token,'--',sys.executable,str(HERE/script)],cwd=ROOT)
            if r.returncode:
                write(HERE/'chain_failed.json',dict(stage=stage,returncode=r.returncode)); raise SystemExit(r.returncode)
            print('COMPLETE',stage,flush=True)
        write(HERE/'chain_complete.json',dict(complete=True)); print('ORDINARY_EXTENDED_CHAIN_COMPLETE')


if __name__=='__main__': main()
