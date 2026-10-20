"""Bound development-only data and paired augmentation. No live imports."""
import ctypes
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
import torch

ROOT=Path(__file__).resolve().parents[5]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from pipeline.train_expert_context import initialize
from pipeline.train_rocket_curriculum import load_subset, train_step
from pipeline.model_gen import mirror_gen
from pipeline.eval_gen import GenRows

DATA=ROOT/'icebow/data/bench/spawner_identity_20261005/gen_dataset_v5_public.npz'
SOURCE=ROOT/'icebow/data/pipeline/gen_dataset_v31_public.npz'
INIT=ROOT/'icebow/data/bench/rl_royale/rseries_r1e31/rseries_r1e31_u0155.pt'
OUT=ROOT/'icebow/data/bench/development_iteration_1_20261005'
SEED=20261005


def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def read(p):return json.loads(Path(p).read_text())


def write(p,obj):
    Path(p).write_text(json.dumps(obj,indent=2,allow_nan=False))


def setup():
    torch.set_num_threads(1)
    try:ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(),0x4000)
    except AttributeError:pass


def check_prepared():
    p=read(HERE/'prepared.json');v=read(HERE/'verified.json')
    assert v['complete'] and v['prepared_sha256']==sha(HERE/'prepared.json')
    for path,h in p['sources'].items():assert sha(ROOT/path)==h,path
    assert sha(ROOT/p['indices'])==p['indices_sha256']
    return p


def validate_indices(ids,expected):
    if ids.dtype.kind not in 'iu' or not np.array_equal(ids,expected):
        raise ValueError('Unregistered training/development row access')


def indices(part):
    if part not in ('train','development'):raise ValueError('Unregistered split')
    with np.load(OUT/'indices.npz') as z:return z[part]


def load_part(part,device):
    ids=indices(part)
    sub,meta=load_subset(DATA,ids)
    assert np.all(sub['split']==0)
    return ids,sub,meta,GenRows(sub,np.arange(len(ids)),device)


def augment(b,mirror):
    if not mirror:return b
    b=dict(b)
    b['tok'],b['sc'],b['past'],b['xy']=mirror_gen(b['tok'],b['sc'],b['past'],b['xy'])
    op=b['opp_past'].clone();op[...,2]=torch.where(op[...,0]>0,1-op[...,2],op[...,2]);b['opp_past']=op
    for key,cols in (('projectiles',(2,4)),('effects',(2,))):
        obj=b[key].clone()
        for col in cols:
            known=obj[...,0]>0
            if key=='projectiles' and col==4:known=known&(obj[...,4]>=0)&(obj[...,5]>=0)
            obj[...,col]=torch.where(known,1-obj[...,col],obj[...,col])
        b[key]=obj
    return b


def optimizer(model):
    base=[p for k,p in model.named_parameters() if not k.startswith('projectile_target_')]
    target=[p for k,p in model.named_parameters() if k.startswith('projectile_target_')]
    groups=[dict(params=base,lr=1e-5)]
    if target:groups.append(dict(params=target,lr=1e-3))
    return torch.optim.AdamW(groups,weight_decay=.01)


def frozen_sources():
    paths=list((ROOT/'pipeline').glob('*.py'))
    paths += [HERE/n for n in ('common.py','metrics.py','train.py','evaluate.py','verify_prelaunch.py','run_chain.py','recount.py','METRICS.md','PLAN.md','prepared.json','verified.json')]
    paths += [ROOT/'research/ext/Royale/RoyaleSim/data/derived/cards.json',ROOT/'research/ext/Royale/RoyaleSim/data/calibration.json']
    return {str(p.relative_to(ROOT)):sha(p) for p in paths}


def check_frozen():
    p=read(HERE/'prelaunch.json')
    assert p['sources']==frozen_sources(),'Active source drift'
    assert sha(OUT/'draws.npz')==p['draws_sha256']
    assert sha(OUT/'development_masks.npz')==p['masks_sha256']
    assert p['runtime']['torch']==torch.__version__ and p['runtime']['python']==sys.version
    return p
