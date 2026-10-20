import datetime,msvcrt,os,subprocess
from shared import *
def main():
    assert not (HERE/'chain_started.json').exists()
    with (ROOT/'icebow/data/bench/development_iteration_1_20261005/chain.lock').open('a+b') as lock:
        lock.seek(0);lock.write(b'1');lock.flush();lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        write(HERE/'chain_started.json',dict(pid=os.getpid(),utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
        for name,token in [('collect','HAND_SEQUENCE_COLLECTED'),('verify','HAND_SEQUENCE_VERIFIED')]:
            cmd=[sys.executable,str(ROOT/'scratchpad/gauntlet/L71/integration/run_check.py'),
                '--name','l72-hand-sequence-'+name,'--expect',token,'--',sys.executable,str(HERE/(name+'.py'))]
            result=subprocess.run(cmd,cwd=ROOT)
            if result.returncode:
                write(HERE/'chain_failed.json',dict(job=name,returncode=result.returncode));raise SystemExit(result.returncode)
        write(HERE/'chain_complete.json',dict(complete=True,utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
if __name__=='__main__':main()
