"""Single serialized development chain. Fail closed; never resume or deploy."""
from datetime import datetime,timezone
import os
import subprocess
import sys
from common import *


def main():
    check_prepared();check_frozen()
    started=HERE/'chain_started.json'
    if started.exists():raise ValueError('Existing chain; inspect it, do not duplicate')
    # A held file lock spans subprocess gaps and remains owned by this chain.
    import msvcrt
    with (OUT/'chain.lock').open('a+b') as lock:
        lock.seek(0);lock.write(b'1');lock.flush();lock.seek(0)
        msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        write(started,dict(pid=os.getpid(),utc=datetime.now(timezone.utc).isoformat(),
            prelaunch_sha256=sha(HERE/'prelaunch.json'),serial=True))
        jobs=[('r1e-eval','evaluate.py',['--arm','r1e_corrected'],'DEVELOPMENT_1_EVALUATION_COMPLETE')]
        for version in (5,6):
            jobs.extend([(f'v{version}-train','train.py',['--arm',f'ordinary_v{version}'],'DEVELOPMENT_1_FULL_ARM_COMPLETE'),
                (f'v{version}-eval','evaluate.py',['--arm',f'ordinary_v{version}'],'DEVELOPMENT_1_EVALUATION_COMPLETE')])
        jobs.append(('independent','recount.py',[],'DEVELOPMENT_1_INDEPENDENT_RECOUNT_COMPLETE'))
        for name,script,args,token in jobs:
            check_frozen()
            if datetime.now(timezone.utc)>=datetime(2026,10,6,4,tzinfo=timezone.utc):
                write(HERE/'chain_cutoff.json',dict(next_job=name,active_jobs_preserved=True));return
            write(HERE/'chain_progress.json',dict(job=name,status='running',utc=datetime.now(timezone.utc).isoformat()))
            command=[sys.executable,str(ROOT/'scratchpad/gauntlet/L71/integration/run_check.py'),
                '--name','l72-development1-'+name,'--expect',token,'--',sys.executable,str(HERE/script),*args]
            print('START',name,flush=True)
            result=subprocess.run(command,cwd=ROOT)
            if result.returncode:
                write(HERE/'chain_failed.json',dict(job=name,returncode=result.returncode));raise SystemExit(result.returncode)
            print('COMPLETE',name,flush=True)
        write(HERE/'chain_complete.json',dict(complete=True,utc=datetime.now(timezone.utc).isoformat(),
            model_reports_pending_review=True,deployment_accepted=False))
        print('DEVELOPMENT_1_CHAIN_COMPLETE',flush=True)


if __name__=='__main__':main()
