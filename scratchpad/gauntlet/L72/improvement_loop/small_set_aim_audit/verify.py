"""Independent scalar joins/geometry and actual cell-patch algebra checks."""
import copy
import datetime
import hashlib
import json
import math
import sys
from pathlib import Path
import numpy as np
import torch

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
BASE=HERE.parent/'small_set_fit'
CACHE=ROOT/'icebow/data/bench/small_set_fit_20261006'
OUT=ROOT/'icebow/data/bench/small_set_aim_audit_20261006'
KEYS=('rows','exact','aim','miss_same_patch','miss_other_patch','miss_le2','miss_le4','miss_gt4','floor_aim')

def read(p): return json.loads(p.read_text(encoding='utf-8'))
def sha(p):
    with p.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
def validate(row,caches,raw,cv):
    z=caches[row['cache']]; ix=int(np.searchsorted(z['ids'],row['id'])); original=row['id']
    assert int(z['ids'][ix])==original and raw['y_gate'][original]==1
    assert row['rep']==int(raw['rep'][original]) and row['tick']==int(raw['tick'][original])
    assert row['card']==cv[int(raw['y_card'][original])]
    mirrored=row['cache'].endswith('_mirrored'); assert row['mirrored']==mirrored
    expected=raw['y_xy'][original].copy()
    if mirrored: expected[0]=1-expected[0]
    assert row['xy']==expected.tolist() and np.array_equal(expected,z['y_xy'][ix])
    # Float32 multiplication is the registered training-label arithmetic.
    cx=min(35,max(0,int(np.float32(expected[0])*np.float32(36))))
    cy=min(63,max(0,int(np.float32(expected[1])*np.float32(64))))
    assert row['target']==cy*36+cx
    pred=int(z['expert_cell'][ix]); assert row['pred']==pred and 0<=pred<2304
    assert row['pred_patch']==(pred//144)*9+(pred%36)//4
    assert row['target_patch']==(cy//4)*9+cx//4
    dist=math.hypot((pred%36/36-float(expected[0]))*18,(pred//36/64-float(expected[1]))*32)
    fd=math.hypot((cx/36-float(expected[0]))*18,(cy/64-float(expected[1]))*32)
    assert math.isclose(row['distance'],dist,rel_tol=0,abs_tol=1e-12)
    assert math.isclose(row['floor_distance'],fd,rel_tol=0,abs_tol=1e-12)
    return dict(rows=1,exact=int(pred==cy*36+cx),aim=int(dist<=1),
        miss_same_patch=int(dist>1 and row['pred_patch']==row['target_patch']),
        miss_other_patch=int(dist>1 and row['pred_patch']!=row['target_patch']),
        miss_le2=int(1<dist<=2),miss_le4=int(2<dist<=4),miss_gt4=int(dist>4),floor_aim=int(fd<=1))

def main():
    assert datetime.datetime.now(datetime.timezone.utc)<datetime.datetime(2026,10,6,13,tzinfo=datetime.timezone.utc)
    assert not (HERE/'verified.json').exists(); report=read(HERE/'collected.json'); assert report['complete']
    for p,h in report['sources'].items(): assert sha(ROOT/p)==h,p
    assert sha(OUT/'rows.jsonl')==report['rows_sha256'] and sha(OUT/'counts.json')==report['counts_sha256']
    e=read(BASE/'evaluated.json'); cv=e['card_vocab']; caches={}
    for filename,h in e['artifacts'].items():
        assert sha(CACHE/filename)==h
        with np.load(CACHE/filename,allow_pickle=False) as z: caches[filename[:-4]]={k:z[k] for k in z.files}
    with np.load(ROOT/'icebow/data/pipeline/gen_dataset_v31_public.npz',allow_pickle=False) as z:
        raw={k:z[k] for k in ('rep','tick','y_gate','y_card','y_xy')}
    rows=[json.loads(line) for line in (OUT/'rows.jsonl').read_text().splitlines()]
    assert len(rows)==3072
    expected_pairs={(key,int(z['ids'][i])) for key,z in caches.items() for i in np.where(z['y_gate']==1)[0]}
    assert len({(r['cache'],r['id']) for r in rows})==3072 and {(r['cache'],r['id']) for r in rows}==expected_pairs
    counts={}
    for row in rows:
        v=validate(row,caches,raw,cv); groups=['play','card/'+row['card']]
        if row['card']=='rocket':
            groups.append('rocket')
            if row['tick']>=4800: groups.append('late_rocket')
        for group in groups:
            key=row['cache']; dest=counts.setdefault(key,{}).setdefault(group,dict.fromkeys(KEYS,0))
            by=dest.setdefault('by_replay',{}).setdefault(str(row['rep']),dict.fromkeys(KEYS,0))
            for k in KEYS: dest[k]+=v[k]; by[k]+=v[k]
    for groups in counts.values():
        for v in groups.values(): v['replays']=len(v['by_replay'])
    assert counts==read(OUT/'counts.json')
    reference=read(BASE/'results_verified.json')['summaries']
    for key,groups in counts.items():
        name,orientation=key.rsplit('_',1)
        assert groups['play']['aim']==reference[name+'/'+orientation]['play']['aim1']
    negative=0
    for key,value in [('id',-1),('rep',-1),('card','invalid'),('pred',2304),('target',-1),
        ('pred_patch',-1),('target_patch',-1),('distance',float('nan')),('floor_distance',-1),('mirrored',not rows[0]['mirrored'])]:
        bad=copy.deepcopy(rows[0]); bad[key]=value
        try: validate(bad,caches,raw,cv)
        except (AssertionError,IndexError): negative+=1
        else: raise AssertionError('Corruption accepted')
    assert negative==10
    state=torch.load(CACHE/'candidate.pt',map_location='cpu',weights_only=True)['model']
    expected=torch.tensor([(cell//144)*9+(cell%36)//4 for cell in range(2304)])
    assert torch.equal(state['cell_patch'],expected)
    # Actual algebra: same-patch relative logits cannot depend on kp alone.
    sys.path.insert(0,str(ROOT))
    from pipeline.model_gen import GenModel
    import inspect
    source=inspect.getsource(GenModel.cell_logits_gen)
    assert 'kp[:, self.cell_patch] + kc' in source
    rng=np.random.default_rng(2026100611); kp=rng.normal(size=144); kc=rng.normal(size=2304); bias=rng.normal(size=2304)
    cp=expected.numpy(); logits=(kp[cp]+kc)/math.sqrt(128)+bias
    changed=(rng.normal(size=144)[cp]+kc)/math.sqrt(128)+bias
    tested=0
    for patch in range(144):
        cells=np.where(cp==patch)[0]; assert len(cells)==16
        assert np.allclose(logits[cells]-logits[cells[0]],changed[cells]-changed[cells[0]],rtol=0,atol=1e-14); tested+=1
    assert sha(CACHE/'candidate.pt')==report['sources'][str((CACHE/'candidate.pt').relative_to(ROOT))]
    result=dict(complete=True,rows=3072,controls=dict(positive=1,negative=negative),patch_buffer_cells=2304,
        synthetic_same_patch_controls=tested,collected_sha256=sha(HERE/'collected.json'),
        counts_sha256=sha(OUT/'counts.json'),summaries={key:{group:{k:v for k,v in values.items() if k!='by_replay'} for group,values in groups.items()} for key,groups in counts.items()},
        inference=0,optimizer_updates=0,weights_unchanged=True,source_sha256=sha(Path(__file__)))
    (HERE/'verified.json').write_text(json.dumps(result,allow_nan=False)+'\n',encoding='utf-8')
    print('SMALL_SET_AIM_VERIFIED')

if __name__=='__main__': main()
