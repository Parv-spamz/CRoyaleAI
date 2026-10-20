import hashlib,importlib.util,json,sys
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent;BASE=HERE.parent;ROOT=HERE.parents[4]
OUT=ROOT/'icebow/data/bench/rl_gradient_audit_20261005'
TRAIN=ROOT/'icebow/data/bench/development_rl_1_20261005'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def arrays(p):
    with np.load(p,allow_pickle=False) as z:return {k:z[k] for k in z.files}
def original():
    p=BASE/'development_rl_1/shared.py';spec=importlib.util.spec_from_file_location('gradient_original_shared',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def sources():
    paths=list(HERE.glob('*.py'))+[HERE/'PLAN.md',BASE/'rl_failure_audit/verified.json',BASE/'development_rl_1/trained.json',BASE/'development_rl_1/prepared.json',TRAIN/'train.jsonl']
    return {str(p.relative_to(ROOT)):sha(p) for p in paths}
def metrics(pg,vf,det,names,shapes,reach):
    # Producer torch reductions; the verifier does not call this function.
    import torch
    rows=[];offset=0;gp=gv=dot=0.
    for name,shape,flag in zip(names,shapes,reach):
        n=int(np.prod(shape));a=torch.from_numpy(pg[offset:offset+n]).double();b=torch.from_numpy(vf[offset:offset+n]).double();d=torch.from_numpy(det[offset:offset+n]).double()
        pp=float((a*a).sum());vv=float((b*b).sum());pv=float((a*b).sum());dd=float((d*d).sum());shared=bool(flag and not name.startswith('value_head.'))
        rows.append(dict(name=name,shape=shape,size=n,critic_reachable=bool(flag),shared=shared,pg_sq=pp,vf_sq=vv,dot=pv,detached_sq=dd))
        if shared:gp+=pp;gv+=vv;dot+=pv
        if not name.startswith('value_head.'):assert dd==0
        else:assert pp==0
        offset+=n
    assert offset==len(pg)==len(vf)==len(det)
    npg=gp**.5;nv=gv**.5
    return dict(tensors=rows,pg_norm=npg,vf_norm=nv,dot=dot,cosine=dot/(npg*nv) if npg and nv else None,vf_share=nv/(nv+npg) if nv+npg else None,critic_larger=nv>npg,opposed=dot<0)
