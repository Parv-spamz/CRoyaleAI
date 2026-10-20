"""Read-only array access; no model or metric imports."""
import hashlib,json
from pathlib import Path
from zipfile import ZipFile
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
OUT=ROOT/'icebow/data/bench/frozen_branch_rocket_20261005'
BASE=ROOT/'icebow/data/bench/development_iteration_1_20261005'
DATA=ROOT/'icebow/data/bench/spawner_identity_20261005/gen_dataset_v5_public.npz'
ROWS=ROOT/'icebow/data/bench/match_adaptation_20261005/rows.npz'
MASKS=ROOT/'icebow/data/bench/development_iteration_4_20261005/development_masks.npz'
LABELS='y_gate y_card y_hand_pos y_xy y_wait_card y_wait_dt y_crowns y_cell'.split()
FIELDS=LABELS+['rep','side','tick','split','sc','projectiles']
CACHE={a:BASE/(a+('_eval' if a=='r1e_corrected' else '_eval_v2'))/'predictions.npz' for a in ('r1e_corrected','ordinary_v5','ordinary_v6')}
CACHE['frozen_base_projectile_v6']=ROOT/'icebow/data/bench/development_iteration_7_20261005/frozen_base_projectile_v6_eval/predictions.npz'
def read(p):return json.loads(p.read_text())
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def take(z,key,ids):
    with z.open(key+'.npy') as f:
        v=np.lib.format.read_magic(f);shape,order,dtype=(np.lib.format.read_array_header_1_0(f) if v==(1,0) else np.lib.format.read_array_header_2_0(f))
        assert not order and not dtype.hasobject
        width=int(np.prod(shape[1:]))*dtype.itemsize;step=max(1,(16<<20)//width)
        out=np.empty((len(ids),)+shape[1:],dtype)
        for lo in range(0,shape[0],step):
            n=min(step,shape[0]-lo);raw=f.read(n*width);assert len(raw)==n*width
            a,b=np.searchsorted(ids,[lo,lo+n])
            if b>a:out[a:b]=np.frombuffer(raw,dtype).reshape((n,)+shape[1:])[ids[a:b]-lo]
        return out
def inputs():
    paths=[DATA,ROWS,MASKS,BASE/'indices.npz',HERE.parent/'development_iteration_1/prepared.json',HERE.parent/'match_adaptation/prepared.json',HERE.parent/'development_iteration_7/results_verified_v2.json',HERE.parent/'development_iteration_7/reviewed_results.json',ROOT/'pipeline/model_gen.py',ROOT/'pipeline/model_v3.py']+list(CACHE.values())+list(HERE.glob('*.py'))+[HERE/'PLAN.md',HERE/'METRICS.md']
    return {str(p.relative_to(ROOT)):sha(p) for p in paths}
def load():
    with np.load(BASE/'indices.npz') as z:ids=z['development']
    assert len(ids)==54723 and np.all(np.diff(ids)>0)
    with ZipFile(DATA) as z:s={k:take(z,k,ids) for k in FIELDS}
    assert np.all(s['split']==0) and len(set(s['rep']))==405
    with np.load(ROWS) as z:
        at=np.searchsorted(z['ids'],ids);assert np.array_equal(z['ids'][at],ids)
        for k in FIELDS:
            if k!='projectiles':assert np.array_equal(z[k][at],s[k]),k
    cv=read(HERE.parent/'match_adaptation/prepared.json')['card_vocab']
    with np.load(MASKS) as z:
        assert np.array_equal(ids,z['ids']);m={k[5:]:z[k] for k in z.files if k.startswith('mask_')}
    proof=read(HERE.parent/'development_iteration_7/results_verified_v2.json');ps={}
    for a,p in CACHE.items():
        assert sha(p)==proof['hashes'][a]['cache']
        with np.load(p) as z:
            assert np.array_equal(z['ids'],ids);ps[a]={k:z[k] for k in z.files if k!='ids'}
    return ids,s,cv,m,ps
