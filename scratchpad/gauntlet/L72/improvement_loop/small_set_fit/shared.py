"""Frozen small-set assay dependencies, sampling and scoring."""
import ast
import datetime
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
import numpy as np
import torch

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
sys.path.insert(0,str(ROOT))
spec=importlib.util.spec_from_file_location('small_fit_common',HERE.parent/'development_iteration_1/common.py')
c=importlib.util.module_from_spec(spec); spec.loader.exec_module(c)
OUT=ROOT/'icebow/data/bench/small_set_fit_20261006'
INIT=c.OUT/'ordinary_v5/candidate_portable.pt'
SEED=2026100610
STEPS=4096
ARM='small_set_fit_v5_diagnostic_only'

def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,d): p.write_text(json.dumps(d,allow_nan=False,separators=(',',':'))+'\n',encoding='utf-8')
def sha(p):
    with p.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
def arrays(p):
    with np.load(p,allow_pickle=False) as z: return {k:z[k] for k in z.files}
def cutoff():
    assert datetime.datetime.now(datetime.timezone.utc)<datetime.datetime(2026,10,6,13,tzinfo=datetime.timezone.utc),'Owner cutoff'
def sources():
    files=list((ROOT/'pipeline').glob('*.py'))+list(HERE.glob('*.py'))
    files += [HERE/'PLAN.md',HERE/'METRICS.md',c.HERE/'common.py',c.HERE/'metrics.py',c.HERE/'prepared.json',c.HERE/'verified.json',
        c.HERE/'ordinary_v5_portable.json',HERE.parent/'training_fit_audit/shared.py',HERE.parent/'training_fit_audit/verify.py',
        HERE.parent/'training_fit_audit/reviewed.json',HERE.parent/'development_iteration_9/reviewed_results.json',
        INIT,c.INIT,c.DATA,c.SOURCE,c.OUT/'indices.npz']
    return {str(p.relative_to(ROOT)):sha(p) for p in files}
def check():
    p=read(HERE/'prepared.json'); assert p['complete'] and p['sources']==sources()
    assert p['schedule_sha256']==sha(OUT/'schedule.npz')
    assert p['runtime']==dict(torch=str(torch.__version__),python=sys.version,cuda=torch.version.cuda)
    return p
def raw_labels():
    with np.load(c.DATA,allow_pickle=False) as z:
        raw={k:z[k] for k in ('rep','tick','y_gate','y_card','y_xy','hand_card','sc','split')}
        meta=json.loads(str(z['meta']))
    return raw,meta
def select(train,raw):
    rng=np.random.default_rng(SEED)
    cards=sorted(np.unique(raw['y_card'][train][raw['y_gate'][train]==1]).tolist())
    assert len(cards)==8
    selected=[]
    for card in cards+[None]:
        eligible=train[(raw['y_gate'][train]==0) if card is None else ((raw['y_gate'][train]==1)&(raw['y_card'][train]==card))]
        seen=set(); chosen=[]; needed=512 if card is None else 64
        for row in rng.permutation(eligible):
            rep=int(raw['rep'][row])
            if rep not in seen:
                seen.add(rep); chosen.append(int(row))
                if len(chosen)==needed: break
        assert len(chosen)==needed,'Insufficient replay groups in stratum'
        selected.extend(chosen)
    return np.sort(np.array(selected,np.int64))
def validate(sample,train,raw):
    assert sample.shape==(1024,) and sample.dtype.kind in 'iu'
    assert np.all(np.diff(sample)>0) and np.isin(sample,train).all()
    assert np.all(raw['split'][sample]==0)
    play=raw['y_gate'][sample]==1; assert int(play.sum())==512
    cards=np.unique(raw['y_card'][sample][play]); assert len(cards)==8
    for card in [*cards,None]:
        ids=sample[~play if card is None else play&(raw['y_card'][sample]==card)]
        assert len(ids)==(512 if card is None else 64)
        assert len(np.unique(raw['rep'][ids]))==len(ids)
def schedule(sample):
    rng=np.random.default_rng(SEED+1); draws=[]; mirrors=[]
    for _ in range(STEPS):
        draws.append(sample[rng.choice(1024,128)]); mirrors.append(rng.random()<.5)
    return np.asarray(draws),np.asarray(mirrors,bool)
def functions(path,names,ns):
    tree=ast.parse(path.read_text(encoding='utf-8'))
    selected=[x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name in names]
    assert {x.name for x in selected}==set(names)
    exec(compile(ast.Module(body=selected,type_ignores=[]),str(path),'exec'),ns)
    return ns
def scoring():
    from pipeline.opp_elixir_count import card_cost
    ns=dict(np=np,card_cost=card_cost)
    functions(c.HERE/'metrics.py',('allowed',),ns)
    return functions(HERE.parent/'training_fit_audit/shared.py',('values','summarize'),ns)
def labels(ids,sub,mirrored):
    xy=sub['y_xy'].copy()
    if mirrored: xy[:,0]=1-xy[:,0]
    return dict(ids=ids,rep=sub['rep'],tick=sub['tick'],y_gate=sub['y_gate'],y_card=sub['y_card'],y_xy=xy,hand_card=sub['hand_card'])
def criteria(counts):
    p=counts['play']; r=counts['rocket']; a=counts['all']
    return dict(play_fit=p['play_success']/p['play']>=.9,rocket_card_fit=r['card']/r['play']>=.95,
        rocket_aim_fit=r['aim1']/r['play']>=.95,wait_fit=a['wait_correct']/(a['views']-a['play'])>=.95)
