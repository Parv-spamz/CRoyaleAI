import msvcrt
import os
import subprocess
from shared import *
import sys

def main():
    cutoff();assert not (HERE/'chain_started.json').exists()
    with (ROOT/'icebow/data/bench/development_iteration_1_20261005/chain.lock').open('r+b') as lock:
        lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        write(HERE/'chain_started.json',dict(pid=os.getpid(),utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
        for stage,script,token in [('collect','collect.py','LATTICE_LABEL_AUDIT_COLLECTED'),('independent','verify.py','LATTICE_LABEL_AUDIT_VERIFIED')]:
            cutoff();print('START',stage,flush=True)
            r=subprocess.run([sys.executable,str(ROOT/'scratchpad/gauntlet/L71/integration/run_check.py'),'--name',
                'l72-lattice-label-audit-'+stage,'--expect',token,'--',sys.executable,str(HERE/script)],cwd=ROOT)
            if r.returncode:
                write(HERE/'chain_failed.json',dict(stage=stage,returncode=r.returncode));raise SystemExit(r.returncode)
        write(HERE/'chain_complete.json',dict(complete=True));print('LATTICE_LABEL_AUDIT_CHAIN_COMPLETE')

if __name__=='__main__':main()
