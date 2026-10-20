import datetime
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
sys.path.insert(0,str(ROOT))
spec=importlib.util.spec_from_file_location('collision_original_common',HERE.parent/'development_iteration_1/common.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
OUT=ROOT/'icebow/data/bench/input_collision_audit_20261006'
KEYS=tuple(sorted(('tok mask sc past hand_card hand_form next_card next_form deck_card deck_form '
                  'unit_form opp_past opp_cycle projectiles effects own_ability').split()))
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,d):p.write_text(json.dumps(d,allow_nan=False,separators=(',',':'))+'\n',encoding='utf-8')
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def cutoff():assert datetime.datetime.now(datetime.timezone.utc)<datetime.datetime(2026,10,6,13,tzinfo=datetime.timezone.utc),'Owner cutoff'
def arrays(p):
    with np.load(p,allow_pickle=False) as z:return {k:z[k] for k in z.files}
def sources():
    paths=list((ROOT/'pipeline').glob('*.py'))+list(HERE.glob('*.py'))
    paths += [HERE/'PLAN.md',HERE/'METRICS.md',c.HERE/'common.py',c.OUT/'indices.npz',c.DATA,c.SOURCE,
              HERE.parent/'extended_fit_audit/reviewed.json',HERE.parent/'extended_fit_audit/verified.json']
    return {str(p.relative_to(ROOT)):sha(p) for p in paths}
def check():
    p=read(HERE/'started.json');assert p['sources']==sources();return p

def fixture():
    return dict(ids=np.arange(6,dtype=np.int64),rep=np.arange(6,dtype=np.int64),
        hashes=np.array(['a'*64]*4+['b'*64]*2),gate=np.array([1,1,1,0,1,1],np.float32),
        card=np.array([1,1,2,0,1,1]),form=np.array([0,0,0,3,0,0]),
        xy=np.array([[0,0],[.5,.5],[0,0],[0,0],[0,0],[.02,0]],np.float32),
        cell=np.array([0,1170,0,0,0,1]))
