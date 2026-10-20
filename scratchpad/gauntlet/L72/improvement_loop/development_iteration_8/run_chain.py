"""One fail-closed serial chain using the same GPU reservation lock."""
import datetime
import msvcrt
import os
import subprocess
from experiment import *

def main():
    check_active()
    if (HERE/'chain_started.json').exists():raise ValueError('No automatic rerun')
    lock=(c.OUT/'chain.lock').open('r+b');lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
    c.write(HERE/'chain_started.json',dict(pid=os.getpid(),utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),prelaunch_sha256=c.sha(HERE/'prelaunch.json')))
    jobs=[('train','train.py','AIM_HEADS_FULL_ARM_COMPLETE'),('eval','evaluate.py','AIM_HEADS_EVALUATION_COMPLETE'),('independent','recount.py','AIM_HEADS_RECOUNT_COMPLETE')]
    cutoff=datetime.datetime(2026,10,6,4,tzinfo=datetime.timezone.utc)
    for name,script,token in jobs:
        if datetime.datetime.now(datetime.timezone.utc)>=cutoff:
            c.write(HERE/'cutoff.json',dict(next_job=name,active_job_preserved=True));return
        check_active();c.write(HERE/'chain_progress.json',dict(job=name,state='running'))
        print('START',name,flush=True)
        cmd=[sys.executable,str(c.ROOT/'scratchpad/gauntlet/L71/integration/run_check.py'),'--name','l72-development8-'+name,'--expect',token,'--',sys.executable,str(HERE/script)]
        result=subprocess.run(cmd,cwd=c.ROOT)
        if result.returncode:
            c.write(HERE/'chain_failed.json',dict(job=name,returncode=result.returncode));raise SystemExit(result.returncode)
        print('COMPLETE',name,flush=True)
    c.write(HERE/'chain_complete.json',dict(complete=True,utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),model_report_pending=True,deployment_accepted=False))
    print('AIM_HEADS_CHAIN_COMPLETE',flush=True)

if __name__=='__main__':main()
