import datetime, msvcrt, os, subprocess, sys
from common import *

def main():
    cutoff();assert not (HERE/'chain_started.json').exists()
    lock=(ROOT/'icebow/data/bench/development_iteration_1_20261005/chain.lock').open('r+b')
    lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
    write(HERE/'chain_started.json',dict(pid=os.getpid(),utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),cpu_only=True))
    jobs=(('prepare','prepare.py','IMPACT_LEARNING_ROOTS_PREPARED'),('preparation-independent','verify_preparation.py','IMPACT_LEARNING_ROOTS_VERIFIED'),('collect','collect.py','IMPACT_LEARNING_DATA_COLLECTED'),('data-independent','verify_data.py','IMPACT_LEARNING_DATA_VERIFIED'),('train','train.py','IMPACT_LEARNING_TRAINED'),('results-independent','verify_results.py','IMPACT_LEARNING_RESULTS_VERIFIED'))
    for name,script,token in jobs:
        cutoff();print('START',name,flush=True)
        r=subprocess.run([sys.executable,str(ROOT/'scratchpad/gauntlet/L71/integration/run_check.py'),'--name','l72-impact-learning2-'+name,'--expect',token,'--',sys.executable,str(HERE/script)],cwd=ROOT)
        if r.returncode:
            write(HERE/'chain_failed.json',dict(job=name,returncode=r.returncode));raise SystemExit(r.returncode)
        print('COMPLETE',name,flush=True)
    write(HERE/'chain_complete.json',dict(complete=True));print('IMPACT_LEARNING_CHAIN_COMPLETE')

if __name__=='__main__':main()
