"""Remaining original jobs with separately verified metadata-only portability."""
from datetime import datetime,timezone
import os
import subprocess
import sys
import common as c
from recovery_common import check_recovery


def main():
    c.check_prepared();check_recovery()
    started=c.HERE/'resume_started.json'
    if started.exists():raise ValueError('Existing continuation: inspect before any new action')
    import msvcrt
    with (c.OUT/'chain.lock').open('r+b') as lock:
        lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        c.write(started,dict(pid=os.getpid(),utc=datetime.now(timezone.utc).isoformat(),
            recovery_sha256=c.sha(c.HERE/'recovery_bound.json')))
        jobs=[('v5-eval-portable','evaluate_v2.py',['--arm','ordinary_v5'],'DEVELOPMENT_1_EVALUATION_COMPLETE'),
          ('v6-train','train.py',['--arm','ordinary_v6'],'DEVELOPMENT_1_FULL_ARM_COMPLETE'),
          ('v6-portable','portable_checkpoint.py',['--arm','ordinary_v6'],'DEVELOPMENT_1_PORTABLE_CHECKPOINT_VERIFIED'),
          ('v6-eval-portable','evaluate_v2.py',['--arm','ordinary_v6'],'DEVELOPMENT_1_EVALUATION_COMPLETE'),
          ('independent-portable','recount_v2.py',[],'DEVELOPMENT_1_INDEPENDENT_RECOUNT_COMPLETE')]
        for name,script,args,token in jobs:
            check_recovery()
            if datetime.now(timezone.utc)>=datetime(2026,10,6,4,tzinfo=timezone.utc):
                c.write(c.HERE/'resume_cutoff.json',dict(next_job=name));return
            c.write(c.HERE/'resume_progress.json',dict(job=name,status='running',utc=datetime.now(timezone.utc).isoformat()))
            print('START',name,flush=True)
            r=subprocess.run([sys.executable,str(c.ROOT/'scratchpad/gauntlet/L71/integration/run_check.py'),
                '--name','l72-development1-'+name,'--expect',token,'--',sys.executable,str(c.HERE/script),*args],cwd=c.ROOT)
            if r.returncode:
                c.write(c.HERE/'resume_failed.json',dict(job=name,returncode=r.returncode));raise SystemExit(r.returncode)
            print('COMPLETE',name,flush=True)
        c.write(c.HERE/'resume_complete.json',dict(complete=True,utc=datetime.now(timezone.utc).isoformat(),
            model_reports_pending_review=True,deployment_accepted=False))
        print('DEVELOPMENT_1_RECOVERY_CHAIN_COMPLETE',flush=True)


if __name__=='__main__':main()
