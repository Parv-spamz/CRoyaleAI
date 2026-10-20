import hashlib,json,sys
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent;BASE=HERE.parent;ROOT=HERE.parents[4]
TRAIN=ROOT/'icebow/data/bench/development_rl_1_20261005'
OUT=ROOT/'icebow/data/bench/rl_credit_audit_20261005'
KEYS=('tick','played','gate_sampled','slot','cell','lp_gate')
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,x):p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def arrays(p,keys=None):
    with np.load(p,allow_pickle=False) as z:return {k:z[k] for k in (keys or z.files)}
def sources():
    ps=list(HERE.glob('*.py'))+[HERE/'PLAN.md',HERE/'METRICS.md',BASE/'development_rl_1/trained.json',BASE/'development_rl_1/prepared.json',BASE/'development_rl_1/results_verified.json',BASE/'rl_gradient_audit/reviewed.json',ROOT/'pipeline/rl_royale.py',ROOT/'pipeline/e1_eval.py',TRAIN/'train.jsonl']
    return {str(p.relative_to(ROOT)):sha(p) for p in ps}
def logs():
    t=read(BASE/'development_rl_1/trained.json');assert t['complete'] and sha(TRAIN/'train.jsonl')==t['train_log_sha256']
    result=[json.loads(s) for s in (TRAIN/'train.jsonl').read_text().splitlines()]
    assert [x['update'] for x in result]==list(range(1,33));return result
def outcome(r):return {'win':1,'loss':-1,'draw':0}[r['outcome']]
def command_status(c):
    if c.get('accepted') is True:return 'accepted'
    if c.get('reason')=='match_over_before_landing':return 'unlanded'
    if c.get('accepted') is False and c.get('reason'):return 'refused'
    return 'unknown'
