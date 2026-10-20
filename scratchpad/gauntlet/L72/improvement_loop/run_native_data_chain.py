"""Wait for the existing preflight, then collect the single fixed CPU pilot."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    lock=HERE/'native_data_chain_started.json'
    sources=[HERE/name for name in ('run_native_data_chain.py','collect_reserved_pilot.py',
        'native_capture_identity.py','RESERVED_PILOT_PLAN.md','reserved_pilot_prepared.json')]
    frozen={str(p):sha(p) for p in sources}
    with lock.open('x') as stream:
        json.dump(dict(started_at=datetime.datetime.now().isoformat(),sources=frozen,
                       preflight_pid=27036),stream,indent=2)
    receipt=ROOT/'scratchpad/gauntlet/L71/integration/checks/l72-native-capture-v2.json'
    deadline=time.monotonic()+3600
    while not receipt.exists():
        if time.monotonic()>deadline:raise TimeoutError('Existing native preflight receipt not ready after one hour')
        print('WAITING_FOR_EXISTING_NATIVE_PREFLIGHT',datetime.datetime.now().isoformat(),flush=True)
        time.sleep(30)
    for name,digest in frozen.items():assert sha(name)==digest,name
    result=json.loads(receipt.read_text())
    assert result['exit_code']==0 and result['matched'] is True, 'Native preflight failed; collection not started'
    if datetime.datetime.now()>=datetime.datetime(2026,10,6):
        raise RuntimeError('Tuesday cutoff: preserve evidence; no new collection started')
    command=[sys.executable,str(ROOT/'scratchpad/gauntlet/L71/integration/run_check.py'),
        '--name','l72-reserved-pilot-collection','--expect','RESERVED_PILOT_COLLECTION_COMPLETE','--',
        sys.executable,'-u',str(HERE/'collect_reserved_pilot.py')]
    print('NATIVE_PREFLIGHT_COMPLETE_START_FIXED_PILOT',flush=True)
    completed=subprocess.run(command,cwd=ROOT)
    if completed.returncode:raise SystemExit(completed.returncode)
    print('NATIVE_DATA_CHAIN_COMPLETE',flush=True)


if __name__=='__main__':main()
