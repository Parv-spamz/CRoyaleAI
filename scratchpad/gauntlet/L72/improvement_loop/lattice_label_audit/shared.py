import datetime, hashlib, json, sys
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
sys.path.insert(0,str(ROOT))
LOOP=HERE.parent
OUT=ROOT/'icebow/data/bench/lattice_label_audit_20261006'
FIT=ROOT/'icebow/data/bench/local_cell_fit_20261006'
SMALL=ROOT/'icebow/data/bench/small_set_fit_20261006'
CONTRIB=ROOT/'icebow/data/bench/local_cell_contribution_20261006'
DATA=ROOT/'icebow/data/bench/spawner_identity_20261005/gen_dataset_v5_public.npz'
SOURCE=ROOT/'icebow/data/pipeline/gen_dataset_v31_public.npz'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,d):p.write_text(json.dumps(d,allow_nan=False,separators=(',',':'))+'\n',encoding='utf-8')
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def arrays(p):
    with np.load(p,allow_pickle=False) as z:return {k:z[k] for k in z.files}
def cutoff():assert datetime.datetime.now(datetime.timezone.utc)<datetime.datetime(2026,10,6,13,tzinfo=datetime.timezone.utc)
def caches():
    result={}
    for name,h in read(LOOP/'local_cell_fit/evaluated.json')['artifacts'].items():
        p=(FIT if name.startswith('local_cell_final') else SMALL)/name
        assert sha(p)==h;result[name[:-4]]=p
    return result
def sources():
    paths=list(HERE.glob('*.py'))+[HERE/'PLAN.md',HERE/'METRICS.md',DATA,SOURCE,FIT/'candidate.pt',SMALL/'candidate.pt',SMALL/'schedule.npz',
        ROOT/'pipeline/model_v3.py',ROOT/'pipeline/train_gen.py',ROOT/'pipeline/train_rocket_curriculum.py',
        LOOP/'local_cell_contribution/collected.json',LOOP/'local_cell_contribution/verified.json',LOOP/'local_cell_contribution/reviewed.json',
        LOOP/'small_set_aim_audit/collected.json',LOOP/'small_set_aim_audit/verified.json',LOOP/'local_cell_fit/evaluated.json',
        LOOP/'local_cell_fit/reviewed_results.json',LOOP/'small_set_fit/reviewed_results.json',CONTRIB/'native.npz',CONTRIB/'mirrored.npz',
        CONTRIB/'report.json',ROOT/'icebow/data/bench/small_set_aim_audit_20261006/counts.json']+list(caches().values())
    return {str(p.relative_to(ROOT)):sha(p) for p in paths}
COUNTS=('rows','aim','floor_exact','lattice_exact','label_changed','floor_same_miss','floor_other_miss','lattice_same_miss','lattice_other_miss','miss_within_1e5_above_one')
def groups(r):return ['all','card/'+r['card_name']]+(['rocket']+(['late_rocket'] if r['tick']>=4800 else []) if r['card_name']=='rocket' else [])
def aggregate(records):
    result={}
    for r in records:
        for g in groups(r):
            a=result.setdefault(r['cache'],{}).setdefault(g,dict(counts={k:0 for k in COUNTS},by_replay={}))
            rep=a['by_replay'].setdefault(str(r['rep']),{k:0 for k in COUNTS})
            for k in COUNTS:a['counts'][k]+=int(r[k]);rep[k]+=int(r[k])
    for v in result.values():
        for a in v.values():a['replays']=len(a['by_replay'])
    return result
