"""Resume only missing frozen jobs using the previously captured Q3 prerequisite."""
import argparse
from datetime import datetime
import hashlib
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

MAIN = Path(__file__).resolve().parents[4]
ROOT = Path('C:/Users/benpe/.codex/worktrees/learned-defence/ClashBot')
OUT = ROOT/'scratchpad/gauntlet/L71/context_teaching/experiments'
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def verify_receipt(root, folder, job, pinned_hash=None):
    path = folder/(job['name']+'.receipt.json')
    if pinned_hash and sha(path) != pinned_hash:
        raise ValueError('Receipt changed: '+job['name'])
    receipt = read(path)
    if (receipt['command'] != job['command'] or receipt['exit_code'] != 0 or
            set(receipt['outputs']) != set(job['expected']) or
            not receipt.get('marker_matched', True)):
        raise ValueError('Invalid receipt: '+job['name'])
    log = folder/(job['name']+'.out')
    if sha(log) != receipt['output_sha256']:
        raise ValueError('Output log changed: '+job['name'])
    if job.get('marker') and job['marker'] not in log.read_text():
        raise ValueError('Success marker missing: '+job['name'])
    for name, digest in receipt['outputs'].items():
        if sha(root/name) != digest:
            raise ValueError('Completed result changed: '+name)
    return sha(path)


def verify():
    frozen = importlib.import_module('scratchpad.gauntlet.L71.context_teaching.run_experiments')
    assert Path(frozen.__file__).resolve().is_relative_to(ROOT)
    plan = read(OUT/'plan.json')
    if frozen.source_hashes() != plan['sources']:
        raise ValueError('Frozen worktree sources changed')
    if frozen.jobs(Path('scratchpad/gauntlet/L71/context_teaching/experiments')) != plan['jobs']:
        raise ValueError('Frozen job commands changed')
    for name, digest in plan['inputs'].items():
        if sha(ROOT/name) != digest:
            raise ValueError('Frozen training input changed: '+name)
    pin = read(MAIN/'scratchpad/gauntlet/L71/royale_update_20261005/integration_preserved.json')['q3_verified_sha256']
    if sha(OUT/'q3_verified.json') != pin:
        raise ValueError('Captured pre-integration Q3 verification changed')
    historical = read(OUT/'q3_verified.json')
    q3dir = Path(plan['prerequisite'])
    q3plan = read(q3dir/'plan.json')
    if not historical['complete'] or historical['pending'] or sha(q3dir/'plan.json') != historical['plan_sha256']:
        raise ValueError('Q3 prerequisite incomplete or changed')
    if len(q3plan['jobs']) != 20 or set(historical['receipts']) != {j['name'] for j in q3plan['jobs']}:
        raise ValueError('Q3 job inventory changed')
    for job in q3plan['jobs']:
        verify_receipt(MAIN,q3dir,job,historical['receipts'][job['name']])
    completed, pending = {}, []
    for job in plan['jobs']:
        if (OUT/(job['name']+'.receipt.json')).exists():
            completed[job['name']] = verify_receipt(ROOT,OUT,job)
        else:
            if (OUT/(job['name']+'.out')).exists() or any((ROOT/p).exists() for p in job['expected']):
                raise ValueError('Unreceipted partial job needs investigation: '+job['name'])
            pending.append(job)
    return frozen, plan, dict(q3_verified_sha256=pin, plan_sha256=sha(OUT/'plan.json'),
        completed_receipts=completed, pending=[j['name'] for j in pending]), pending


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--verify-only',action='store_true');a=ap.parse_args()
    frozen, plan, evidence, pending = verify()
    print(json.dumps(dict(completed=len(evidence['completed_receipts']), pending=evidence['pending'])), flush=True)
    (HERE/'resume_verification.json').write_text(json.dumps(evidence,indent=2))
    print('FROZEN_RESUME_VERIFIED',flush=True)
    if a.verify_only:
        return
    for job in pending:
        if frozen.source_hashes()!=plan['sources']:
            raise ValueError('Frozen source changed between jobs')
        frozen.idle_gpu()
        print(datetime.now().isoformat(),'START',job['name'],flush=True)
        log=OUT/(job['name']+'.out');start=time.time()
        with log.open('x') as stream:
            p=subprocess.run(job['command'],cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        matched=job['marker'] in log.read_text()
        receipt=dict(command=job['command'],cwd=str(ROOT),exit_code=p.returncode,marker=job['marker'],
            marker_matched=matched,output_sha256=sha(log),seconds=time.time()-start,
            outputs={name:sha(ROOT/name) for name in job['expected'] if (ROOT/name).is_file()})
        with (OUT/(job['name']+'.receipt.json')).open('x') as stream:
            json.dump(receipt,stream,indent=2)
        verify_receipt(ROOT,OUT,job)
        print(datetime.now().isoformat(),'DONE',job['name'],flush=True)
    print('EXPERT_CONTEXT_ALL_JOBS_COMPLETE_REQUIRES_REVIEW',flush=True)


if __name__=='__main__':
    main()
