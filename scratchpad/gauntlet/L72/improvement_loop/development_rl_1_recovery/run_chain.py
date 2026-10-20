import msvcrt,os,subprocess
from recovery import *
def main():
    assert not (RECOVERY/'chain_started.json').exists();check_recovery()
    lock=(g.BASE/'chain.lock').open('r+b');lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
    write(RECOVERY/'chain_started.json',dict(pid=os.getpid(),utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),verified_sha256=sha(RECOVERY/'verified.json')))
    jobs=[('train-v2',RECOVERY/'train_v2.py','OUTCOME_RL_TRAIN_COMPLETE'),('eval',HERE/'evaluate.py','OUTCOME_RL_EVALUATED'),('independent',RECOVERY/'verify_v2.py','OUTCOME_RL_VERIFIED')]
    for name,script,token in jobs:
        if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime(2026,10,6,4,tzinfo=datetime.timezone.utc):write(RECOVERY/'cutoff.json',dict(next_job=name));return
        check_recovery();print('START',name,flush=True)
        r=subprocess.run([sys.executable,str(ROOT/'scratchpad/gauntlet/L71/integration/run_check.py'),'--name','l72-outcome-rl-'+name,'--expect',token,'--',sys.executable,str(script)],cwd=ROOT)
        if r.returncode:write(RECOVERY/'chain_failed.json',dict(job=name,returncode=r.returncode));raise SystemExit(r.returncode)
        print('COMPLETE',name,flush=True)
    write(RECOVERY/'chain_complete.json',dict(complete=True));print('OUTCOME_RL_RECOVERY_CHAIN_COMPLETE')
if __name__=='__main__':main()
