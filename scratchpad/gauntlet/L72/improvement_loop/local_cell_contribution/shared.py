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
FIT=HERE.parent/'local_cell_fit'
spec=importlib.util.spec_from_file_location('contribution_fit',FIT/'shared.py')
f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
c=f.c
spec=importlib.util.spec_from_file_location('contribution_model',FIT/'model.py')
model_code=importlib.util.module_from_spec(spec);spec.loader.exec_module(model_code)
OUT=ROOT/'icebow/data/bench/local_cell_contribution_20261006'
CKPT=f.OUT/'candidate.pt'

def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,d):p.write_text(json.dumps(d,allow_nan=False,separators=(',',':'))+'\n',encoding='utf-8')
def sha(p):
    with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def arrays(p):
    with np.load(p,allow_pickle=False) as z:return {k:z[k] for k in z.files}
def cutoff():assert datetime.datetime.now(datetime.timezone.utc)<datetime.datetime(2026,10,6,13,tzinfo=datetime.timezone.utc)
def sources():
    files=list(HERE.glob('*.py'))+[HERE/'PLAN.md',HERE/'METRICS.md',FIT/'model.py',FIT/'shared.py',FIT/'reviewed_results.json',
        FIT/'evaluated.json',FIT/'results_verified.json',f.OUT/'train.jsonl',f.OUT/'schedule.npz',CKPT,c.DATA,c.SOURCE,
        f.OUT/'local_cell_final_native.npz',f.OUT/'local_cell_final_mirrored.npz']
    return dict(read(FIT/'prepared.json')['sources'],**{str(p.relative_to(ROOT)):sha(p) for p in files})
def floor_cells(xy):
    return np.clip((xy[:,1]*np.float32(64)).astype(np.int64),0,63)*36+np.clip((xy[:,0]*np.float32(36)).astype(np.int64),0,35)
def row_values(z):
    n=len(z['ids']);ix=np.arange(n);target=floor_cells(z['xy'])
    on=z['full'].argmax(1);off=z['base'].argmax(1)
    vals={}
    patch=lambda x:(x//36//4)*9+(x%36//4)
    for name,pred in [('on',on),('off',off)]:
        xy=np.c_[pred%36/36,pred//36/64]
        aim=np.linalg.norm((xy-z['xy'])*[18,32],axis=1)<=1
        vals[name+'_aim']=aim;vals[name+'_exact']=pred==target
        vals[name+'_miss_same_patch']=~aim&(patch(pred)==patch(target))
        vals[name+'_miss_other_patch']=~aim&(patch(pred)!=patch(target))
        a=z['full' if name=='on' else 'base'].astype(np.float64)
        vmax=a.max(1);vals[name+'_ce']=vmax+np.log(np.exp(a-vmax[:,None]).sum(1))-a[ix,target]
        others=a.copy();others[ix,target]=-np.inf
        vals[name+'_target_margin']=a[ix,target]-others.max(1)
    vals['choice_changed']=on!=off
    vals['aim_gain']=vals['on_aim']&~vals['off_aim'];vals['aim_loss']=~vals['on_aim']&vals['off_aim']
    vals['aim_tie']=vals['on_aim']==vals['off_aim']
    patches=patch(np.arange(2304));mask=patches[None,:]==patch(target)[:,None]
    r=z['residual'].astype(np.float64)
    vals['residual_expert_patch_span']=np.where(mask,r,-np.inf).max(1)-np.where(mask,r,np.inf).min(1)
    vals['residual_target_vs_base_winner']=r[ix,target]-r[ix,off]
    vals['base_winner_vs_target_gap']=z['base'][ix,off].astype(np.float64)-z['base'][ix,target].astype(np.float64)
    return vals
def summarize(z,cv):
    vals=row_values(z);groups={'all':np.ones(len(z['ids']),bool),'rocket':z['card']==cv.index('rocket'),
        'late_rocket':(z['card']==cv.index('rocket'))&(z['tick']>=4800)}
    groups.update({'card/'+cv[int(k)]:z['card']==k for k in np.unique(z['card'])})
    result={}
    for name,mask in groups.items():
        integers={k:int(v[mask].sum()) for k,v in vals.items() if v.dtype==bool}
        numeric={k:{'mean':float(v[mask].mean()),'median':float(np.median(v[mask]))} for k,v in vals.items() if v.dtype!=bool}
        by_replay={str(int(rep)):{k:int(v[mask&(z['rep']==rep)].sum()) for k,v in vals.items() if v.dtype==bool} for rep in np.unique(z['rep'][mask])}
        result[name]=dict(rows=int(mask.sum()),replays=len(by_replay),counts=integers,values=numeric,by_replay=by_replay)
    return result
