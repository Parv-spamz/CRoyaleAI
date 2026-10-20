import datetime,msvcrt,os,subprocess
from common import *
def main():
    assert not (HERE/'chain_started.json').exists()
    lock=(ROOT/'icebow/data/bench/development_iteration_1_20261005/chain.lock').open('r+b');lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
    write(HERE/'chain_started.json',dict(pid=os.getpid(),utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
    for name,script,token in [('producer','audit.py','RL_CREDIT_AUDIT_COMPLETE'),('independent','verify.py','RL_CREDIT_VERIFIED')]:
        if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime(2026,10,6,4,tzinfo=datetime.timezone.utc):raise RuntimeError('Tuesday cutoff before next diagnostic job')
        write(HERE/'chain_progress.json',dict(job=name));print('START',name,flush=True)
        p=subprocess.run([sys.executable,str(ROOT/'scratchpad/gauntlet/L71/integration/run_check.py'),'--name','l72-rl-credit-'+name,'--expect',token,'--',sys.executable,str(HERE/script)],cwd=ROOT)
        if p.returncode:write(HERE/'chain_failed.json',dict(job=name,returncode=p.returncode));raise SystemExit(p.returncode)
    write(HERE/'chain_complete.json',dict(complete=True));print('RL_CREDIT_CHAIN_COMPLETE')
if __name__=='__main__':main()
