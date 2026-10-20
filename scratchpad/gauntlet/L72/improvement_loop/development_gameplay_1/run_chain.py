"""One shared resource lock through collection and independent verification."""
import datetime,msvcrt,subprocess,os
from common import *
def main():
    assert not (HERE/'chain_started.json').exists();check()
    lock=(BASE/'chain.lock').open('r+b');lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
    write(HERE/'chain_started.json',dict(pid=os.getpid(),utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
    for name,script,token in [('collection','collect.py','DEVELOPMENT_GAMEPLAY_COLLECTION_COMPLETE'),('independent','verify_results.py','DEVELOPMENT_GAMEPLAY_INDEPENDENT_COMPLETE')]:
        if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime(2026,10,6,4,tzinfo=datetime.timezone.utc):
            write(HERE/'cutoff.json',dict(next_job=name,active_jobs_preserved=True));return
        check();print('START',name,flush=True)
        result=subprocess.run([sys.executable,str(ROOT/'scratchpad/gauntlet/L71/integration/run_check.py'),'--name','l72-development-gameplay1-'+name,'--expect',token,'--',sys.executable,str(HERE/script)],cwd=ROOT)
        if result.returncode:
            write(HERE/'chain_failed.json',dict(job=name,returncode=result.returncode));raise SystemExit(result.returncode)
        print('COMPLETE',name,flush=True)
    write(HERE/'chain_complete.json',dict(complete=True,utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deployment_accepted=False))
    print('DEVELOPMENT_GAMEPLAY_CHAIN_COMPLETE')
if __name__=='__main__':main()
