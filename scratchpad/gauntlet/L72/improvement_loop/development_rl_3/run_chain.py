import msvcrt,os,subprocess
from shared import *
def main():
    cutoff();assert not (HERE/'chain_started.json').exists()
    lock=(g.BASE/'chain.lock').open('r+b');lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
    write(HERE/'chain_started.json',dict(pid=os.getpid(),utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
    jobs=[('prepare','prepare.py','LATE_CURRICULUM_PREPARED'),('train','train.py','LATE_CURRICULUM_TRAINED'),
        ('training-independent','verify_training.py','LATE_CURRICULUM_TRAINING_VERIFIED'),('eval','evaluate.py','LATE_CURRICULUM_EVALUATED'),
        ('results-independent','verify_results.py','LATE_CURRICULUM_RESULTS_VERIFIED')]
    for name,script,token in jobs:
        cutoff();print('START',name,flush=True)
        r=subprocess.run([sys.executable,str(ROOT/'scratchpad/gauntlet/L71/integration/run_check.py'),'--name','l72-late-curriculum-'+name,'--expect',token,'--',sys.executable,str(HERE/script)],cwd=ROOT)
        if r.returncode:write(HERE/'chain_failed.json',dict(job=name,returncode=r.returncode));raise SystemExit(r.returncode)
        print('COMPLETE',name,flush=True)
    write(HERE/'chain_complete.json',dict(complete=True));print('LATE_CURRICULUM_CHAIN_COMPLETE')
if __name__=='__main__':main()
