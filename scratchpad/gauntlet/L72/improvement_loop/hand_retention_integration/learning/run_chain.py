import datetime,msvcrt,os,subprocess
from shared import *
def main():
    assert not (HERE/'chain_started.json').exists()
    with (c.OUT/'chain.lock').open('a+b') as lock:
        lock.seek(0);lock.write(b'1');lock.flush();lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        write(HERE/'chain_started.json',dict(pid=os.getpid(),utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
        jobs=[('prepare','HAND_LEARNING_PREPARED'),('train','HAND_LEARNING_TRAINED'),
              ('verify_training','HAND_LEARNING_TRAINING_VERIFIED'),('evaluate','HAND_LEARNING_EVALUATED'),
              ('verify_results','HAND_LEARNING_RESULTS_VERIFIED')]
        for name,token in jobs:
            cmd=[sys.executable,str(ROOT/'scratchpad/gauntlet/L71/integration/run_check.py'),
                '--name','l72-hand-learning-'+name,'--expect',token,'--',sys.executable,str(HERE/(name+'.py'))]
            result=subprocess.run(cmd,cwd=ROOT)
            if result.returncode:
                write(HERE/'chain_failed.json',dict(job=name,returncode=result.returncode));raise SystemExit(result.returncode)
        write(HERE/'chain_complete.json',dict(complete=True,utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),accepted=False,deployed=False))
if __name__=='__main__':main()
