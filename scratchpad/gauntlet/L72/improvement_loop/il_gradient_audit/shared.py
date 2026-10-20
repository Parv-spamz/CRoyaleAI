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
spec=importlib.util.spec_from_file_location('il_gradient_original_common',HERE.parent/'development_iteration_1/common.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
OUT=ROOT/'icebow/data/bench/il_gradient_audit_20261006'
TRAIN=ROOT/'icebow/data/bench/development_iteration_10_20261006'
MODELS={'ordinary_v5':c.OUT/'ordinary_v5/candidate_portable.pt','ordinary_no_dropout_v5':TRAIN/'candidate.pt'}
SELECT=np.arange(0,8000,500)
HEADS=('cell','card','wait','gate','value')
LABELS=('rep','split','y_gate','y_card','y_hand_pos','y_xy','y_wait_card','y_crowns','hand_card','hand_form','deck_card','deck_form')
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,d):p.write_text(json.dumps(d,allow_nan=False,separators=(',',':'))+'\n',encoding='utf-8')
def arrays(p):
    with np.load(p,allow_pickle=False) as z:return {k:z[k] for k in z.files}
def cutoff():assert datetime.datetime.now(datetime.timezone.utc)<datetime.datetime(2026,10,6,13,tzinfo=datetime.timezone.utc),'Owner cutoff'
def sources():
    files=list((ROOT/'pipeline').glob('*.py'))+list(HERE.glob('*.py'))
    files += [HERE/'PLAN.md',HERE/'METRICS.md',c.HERE/'common.py',c.HERE/'ordinary_v5_portable.json',c.DATA,c.SOURCE,c.OUT/'indices.npz',TRAIN/'schedule.npz',*MODELS.values()]
    files += [HERE.parent/'development_iteration_10'/n for n in ('trained.json','prepared.json','reviewed_results.json')]
    files += [HERE.parent/'input_collision_audit/reviewed.json',HERE.parent/'extended_fit_audit/reviewed.json']
    return {str(p.relative_to(ROOT)):sha(p) for p in files}
def check():
    s=read(HERE/'started.json');assert s['sources']==sources();return s
