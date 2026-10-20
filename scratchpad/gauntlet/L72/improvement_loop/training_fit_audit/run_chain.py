import msvcrt
import os
import subprocess
from shared import *


def main():
    cutoff(); assert not (HERE/'chain_started.json').exists()
    with (BASE/'chain.lock').open('r+b') as lock:
        lock.seek(0); msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        write(HERE/'chain_started.json', dict(pid=os.getpid(), utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
        for stage, script, token in [('prepare', 'prepare.py', 'TRAINING_FIT_PREPARED'),
                                      ('collect', 'collect.py', 'TRAINING_FIT_COLLECTED'),
                                      ('independent', 'verify.py', 'TRAINING_FIT_VERIFIED')]:
            cutoff(); print('START', stage, flush=True)
            result = subprocess.run([sys.executable, str(ROOT/'scratchpad/gauntlet/L71/integration/run_check.py'),
                '--name', 'l72-training-fit-'+stage, '--expect', token, '--', sys.executable, str(HERE/script)], cwd=ROOT)
            if result.returncode:
                write(HERE/'chain_failed.json', dict(stage=stage, returncode=result.returncode)); raise SystemExit(result.returncode)
            print('COMPLETE', stage, flush=True)
        write(HERE/'chain_complete.json', dict(complete=True)); print('TRAINING_FIT_CHAIN_COMPLETE')


if __name__ == '__main__': main()
