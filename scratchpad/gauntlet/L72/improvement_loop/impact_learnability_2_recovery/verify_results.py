"""Independent saved-probability scoring; no inference or optimization."""
import copy, hashlib, json, math
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def close(a,b):
    if isinstance(a,dict):assert set(a)==set(b);[close(a[k],b[k]) for k in a]
    elif isinstance(a,float):assert math.isfinite(a) and math.isfinite(b) and abs(a-b)<=1e-12
    else:assert a==b

def summary(prob,rows):
    assert len(prob)==len(rows) and all(math.isfinite(p) and 0<=p<=1 for p in prob)
    output={}
    for split in ('training','development'):
      for kind in ('all','body','crown'):
        pairs=[(p,r['label']) for p,r in zip(prob,rows,strict=True) if r['split']==split and (kind=='all' or r['kind']==kind)]
        pos=[p for p,y in pairs if y==1];neg=[p for p,y in pairs if y==0];assert pos and neg
        output[split+'_'+kind]=dict(rows=len(pairs),positive=len(pos),negative=len(neg),brier=math.fsum((p-y)**2 for p,y in pairs)/len(pairs),balanced_brier=.5*(math.fsum((p-1)**2 for p in pos)/len(pos)+math.fsum(p*p for p in neg)/len(neg)),recall=sum(p>=.5 for p in pos)/len(pos),false_positive_rate=sum(p>=.5 for p in neg)/len(neg))
    return output

def decision(results):
    lookup={(r['arm'],r['seed']):r for r in results};assert len(lookup)==len(results)==6
    seeds=(2026101200,2026101201,2026101202)
    assert set(lookup)=={(a,s) for a in ('static_public','motion_public') for s in seeds}
    def avg(a,k):return math.fsum(lookup[a,s]['metrics'][k]['balanced_brier'] for s in seeds)/3
    wins=sum(lookup['motion_public',s]['metrics']['development_body']['balanced_brier']<lookup['static_public',s]['metrics']['development_body']['balanced_brier'] for s in seeds)
    return dict(body_absolute=avg('motion_public','development_body')<=.10,body_relative=avg('motion_public','development_body')<=.8*avg('static_public','development_body'),seed_improvements=wins>=2,crown_protection=avg('motion_public','development_crown')<=avg('static_public','development_crown')+.01)

def main():
    assert not (HERE/'results_verified.json').exists()
    trained=read(HERE/'trained.json');data_report=read(HERE/'collected.json');data=read(ROOT/data_report['data_path']);rows=data['rows']
    assert trained['complete'] and not trained['policy_acceptance'] and not trained['deployed'] and trained['training_updates']==6000
    assert trained['data_sha256']==sha(ROOT/data_report['data_path']) and trained['data_verifier_sha256']==sha(HERE/'data_verified.json')
    for p,h in trained['sources'].items():assert sha(ROOT/p)==h
    expected_ix=np.array([i for i,r in enumerate(rows) if r['split']=='training'],dtype=np.int64)
    recounted=[];first=None;seeds={};paired={}
    for r in trained['results']:
        for prefix in ('checkpoint','probability','trace','draw'):assert sha(ROOT/r[prefix+'_path'])==r[prefix+'_sha256']
        trace=read(ROOT/r['trace_path']);assert len(trace)==r['updates']==1000 and [q['update'] for q in trace]==list(range(1,1001))
        assert all(math.isfinite(q[k]) and q[k]>=0 for q in trace for k in ('loss','gradient_norm'))
        gen=np.random.default_rng(r['seed']+1);expected=expected_ix[np.stack([gen.integers(0,len(expected_ix),size=256,dtype=np.int64) for _ in range(1000)])]
        draw=np.load(ROOT/r['draw_path'],allow_pickle=False);assert np.array_equal(expected,draw)
        if r['seed'] in seeds:assert seeds[r['seed']]==r['initial_tensor_sha256']
        seeds[r['seed']]=r['initial_tensor_sha256'];assert r['final_tensor_sha256']!=r['initial_tensor_sha256']
        p=read(ROOT/r['probability_path']);m=summary(p,rows);close(m,r['metrics'])
        root_brier={rid:math.fsum((pp-row['label'])**2 for pp,row in zip(p,rows,strict=True) if row['root_id']==rid)/sum(row['root_id']==rid for row in rows) for rid in {row['root_id'] for row in rows}}
        close(root_brier,r['per_root_brier'])
        groups={f:math.fsum(root_brier[rid] for rid in root_brier if next(row['family'] for row in rows if row['root_id']==rid)==f)/8 for f in {row['family'] for row in rows}}
        recounted.append(dict(arm=r['arm'],seed=r['seed'],metrics=m,per_family_brier=groups));paired[r['arm'],r['seed']]=root_brier
        if first is None:first=(p,m)
    filters=decision(recounted);assert filters==trained['filters'] and all(filters.values())==trained['continuation_pass']
    negatives=0
    for k in range(6):
        p,m=copy.deepcopy(first)
        if k==0:p.pop()
        if k==1:p[0]=float('nan')
        if k==2:p[0]=1.5
        if k==3:m['development_body']['positive']+=1
        if k==4:m['development_body']['brier']+=.1
        if k==5:m['development_crown']['recall']+=.1
        try:close(summary(p,rows),m)
        except (AssertionError,KeyError,ValueError):negatives+=1
        else:raise AssertionError(f'Unrejected metric corruption{k}')
    for bad in (recounted[:-1],recounted+[recounted[0]]):
        try:decision(bad)
        except AssertionError:negatives+=1
        else:raise AssertionError('Membership corruption not rejected')
    result=dict(complete=True,trained_sha256=sha(HERE/'trained.json'),data_sha256=trained['data_sha256'],results=recounted,filters=filters,continuation_pass=all(filters.values()),controls=dict(positive=6,negative=negatives),updates=6000,predictions=6*len(rows),policy_acceptance=False,deployed=False,source_sha256=sha(Path(__file__)))
    (HERE/'results_verified.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print('IMPACT_LEARNING_RESULTS_VERIFIED',filters)

if __name__=='__main__':main()
