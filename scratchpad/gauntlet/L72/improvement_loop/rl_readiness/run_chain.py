import datetime,msvcrt,os,subprocess
from common import *
def main():
    assert not (HERE/'chain_started.json').exists()
    lock=(g.BASE/'chain.lock').open('r+b');lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
    write(HERE/'chain_started.json',dict(pid=os.getpid(),utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
    for name,script,token in [('collection','collect.py','RL_READINESS_COLLECTION_COMPLETE'),('independent','verify.py','RL_READINESS_VERIFIED')]:
        if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime(2026,10,6,4,tzinfo=datetime.timezone.utc):write(HERE/'cutoff.json',dict(next_job=name));return
        print('START',name,flush=True)
        r=subprocess.run([sys.executable,str(ROOT/'scratchpad/gauntlet/L71/integration/run_check.py'),'--name','l72-rl-readiness-'+name,'--expect',token,'--',sys.executable,str(HERE/script)],cwd=ROOT)
        if r.returncode:write(HERE/'chain_failed.json',dict(job=name,returncode=r.returncode));raise SystemExit(r.returncode)
        print('COMPLETE',name,flush=True)
    write(HERE/'chain_complete.json',dict(complete=True));print('RL_READINESS_CHAIN_COMPLETE')
if __name__=='__main__':main()
