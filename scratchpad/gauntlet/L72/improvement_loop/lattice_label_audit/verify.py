from shared import *
import copy, math, zipfile
import torch
from pipeline.train_rocket_curriculum import take
from pipeline.model_v3 import cell_label
def target(xy):
    x=max(0,min(35,round(float(np.float32(xy[0])*np.float32(36)))))
    y=max(0,min(63,round(float(np.float32(xy[1])*np.float32(64)))))
    return y*36+x
def floor(xy):return min(63,max(0,int(np.float32(xy[1])*np.float32(64))))*36+min(35,max(0,int(np.float32(xy[0])*np.float32(36))))
def patch(cell):return (cell//144)*9+(cell%36)//4
def grid_check(grid):assert grid=='lattice'
def validate_record(r,expected):
    assert set(r)==set(expected)
    for k in r:
        if k=='distance':assert math.isfinite(r[k]) and abs(r[k]-expected[k])<=1e-14
        else:assert r[k]==expected[k],k
def stats_equal(a,b):
    assert a.keys()==b.keys()
    for k in a:
        if isinstance(a[k],dict):stats_equal(a[k],b[k])
        elif isinstance(a[k],float):assert math.isfinite(a[k]) and abs(a[k]-b[k])<=1e-10,k
        else:assert a[k]==b[k],k
def score_equal(a,b):
    assert a.keys()==b.keys()
    for k in a:assert np.isfinite(a[k]).all() and np.allclose(a[k],b[k],atol=1e-10,rtol=0),k
def main():
    cutoff();torch.set_num_threads(1);assert not (HERE/'verified.json').exists()
    col=read(HERE/'collected.json');assert col['complete'];grid_check(col['grid'])
    for p,h in col['sources'].items():assert sha(ROOT/p)==h,p
    for p,h in col['artifacts'].items():assert sha(OUT/p)==h,p
    ids=arrays(SMALL/'schedule.npz')['sample']
    raw={}
    for path in (SOURCE,DATA):
        with zipfile.ZipFile(path) as z:raw[path]={k:take(z,k,ids) for k in ('y_xy','y_gate','y_card','rep','tick','y_cell')}
        with np.load(path,allow_pickle=False) as z:meta=json.loads(str(z['meta']));grid_check(meta['grid'])
    for k in raw[SOURCE]:assert np.array_equal(raw[SOURCE][k],raw[DATA][k]),k
    raw=raw[SOURCE];cv=meta['card_vocab']
    for p in (FIT/'candidate.pt',SMALL/'candidate.pt'):
        st=torch.load(p,map_location='cpu',weights_only=True);grid_check(st['args']['grid']);del st
    original=[json.loads(line) for line in (OUT/'rows.jsonl').read_text().splitlines()];assert len(original)==4096
    expected=[];summaries={};score_summary={};all_cache={}
    for name,p in caches().items():
        z=arrays(p);all_cache[name]=z;assert np.array_equal(z['ids'],ids)
        xy=raw['y_xy'].copy()
        if name.endswith('_mirrored'):xy[:,0]=np.float32(1)-xy[:,0]
        for k in ('rep','tick','y_gate','y_card'):assert np.array_equal(z[k],raw[k])
        assert np.array_equal(z['y_xy'],xy)
        ix=np.flatnonzero(raw['y_gate']==1);labels=[target(xy[i]) for i in ix]
        assert np.array_equal(cell_label(torch.from_numpy(xy[ix]),grid='lattice').numpy(),labels)
        if name.endswith('_native'):assert np.array_equal(raw['y_cell'][ix],labels)
        cache_rows=[]
        for j,i in enumerate(ix):
            point=xy[i];pred=int(z['expert_cell'][i]);f=floor(point);t=labels[j]
            dx=(pred%36/36-float(point[0]))*18;dy=(pred//36/64-float(point[1]))*32
            dist=math.sqrt(dx*dx+dy*dy);aim=dist<=1
            r=dict(cache=name,id=int(ids[i]),rep=int(raw['rep'][i]),tick=int(raw['tick'][i]),card=int(raw['y_card'][i]),card_name=cv[int(raw['y_card'][i])],xy=point.tolist(),pred=pred,floor=f,lattice=t,distance=dist,rows=1,aim=aim,floor_exact=pred==f,lattice_exact=pred==t,label_changed=f!=t,floor_same_miss=not aim and patch(pred)==patch(f),floor_other_miss=not aim and patch(pred)!=patch(f),lattice_same_miss=not aim and patch(pred)==patch(t),lattice_other_miss=not aim and patch(pred)!=patch(t),miss_within_1e5_above_one=1<dist<=1.00001)
            expected.append(r);cache_rows.append(r)
            names=['all','card/'+r['card_name']]
            if r['card_name']=='rocket':names+=['rocket']+(['late_rocket'] if r['tick']>=4800 else [])
            for g in names:
                s=summaries.setdefault(name,{}).setdefault(g,dict(counts=dict.fromkeys(COUNTS,0),by_replay={}))
                by=s['by_replay'].setdefault(str(r['rep']),dict.fromkeys(COUNTS,0))
                for key in COUNTS:s['counts'][key]+=int(r[key]);by[key]+=int(r[key])
        if name.startswith('local_cell_final'):
            orient='mirrored' if name.endswith('_mirrored') else 'native';s=arrays(CONTRIB/(orient+'.npz'));actual=arrays(OUT/(orient+'_scores.npz'))
            assert np.array_equal(s['ids'],ids[ix]) and np.array_equal(s['full'].argmax(1),z['expert_cell'][ix])
            vals={k:[] for k in actual if k not in ('ids','target')}
            for row,t in enumerate(labels):
                for mode,key in [('on','full'),('off','base')]:
                    a=[float(v) for v in s[key][row]];mx=max(a)
                    vals[mode+'_ce'].append(mx+math.log(math.fsum(math.exp(v-mx) for v in a))-a[t])
                    vals[mode+'_margin'].append(a[t]-max(a[:t]+a[t+1:]))
                off=int(np.argmax(s['base'][row]));res=s['residual'][row]
                vals['residual_target_vs_off_winner'].append(float(res[t])-float(res[off]))
                vals['off_winner_target_gap'].append(float(s['base'][row,off])-float(s['base'][row,t]))
                v=[float(res[cell]) for cell in range(2304) if patch(cell)==patch(t)]
                vals['residual_expert_patch_span'].append(max(v)-min(v))
            recons=dict(ids=ids[ix],target=np.array(labels),**{k:np.array(v) for k,v in vals.items()});score_equal(actual,recons)
            score_summary[orient]={}
            for g in summaries[name]:
                indices=[i for i,r in enumerate(cache_rows) if g=='all' or g=='card/'+r['card_name'] or g=='rocket' and r['card_name']=='rocket' or g=='late_rocket' and r['card_name']=='rocket' and r['tick']>=4800]
                score_summary[orient][g]=dict(rows=len(indices),replays=len({cache_rows[i]['rep'] for i in indices}),values={k:dict(mean=math.fsum(v[i] for i in indices)/len(indices),median=float(np.median([v[i] for i in indices]))) for k,v in vals.items()})
    for r,e in zip(original,expected):validate_record(r,e)
    for v in summaries.values():
        for s in v.values():s['replays']=len(s['by_replay'])
    stats_equal(read(OUT/'report.json'),dict(counts=summaries,scores=score_summary))
    fixture=np.array([[0,0],[1,1],[2.5/36,3.5/64],[3.5/36,4.5/64],[4/36-1e-6,8/64-1e-6],[4/36+1e-6,8/64+1e-6]],np.float32)
    assert np.array_equal(cell_label(torch.from_numpy(fixture),grid='lattice').numpy(),[target(p) for p in fixture])
    positive=3;negative=0
    def reject(fn):
        nonlocal negative
        try:fn()
        except (AssertionError,ValueError,TypeError):negative+=1;return
        raise AssertionError('Corruption accepted')
    reject(lambda:grid_check('floor'))
    for key in ('lattice','floor','id','rep','tick','pred'):
        r=copy.deepcopy(expected[0]);r[key]+=1;reject(lambda:validate_record(r,expected[0]))
    r=copy.deepcopy(expected[0]);r['xy'][0]+=.1;reject(lambda:validate_record(r,expected[0]))
    r=copy.deepcopy(expected[0]);r['aim']=not r['aim'];reject(lambda:validate_record(r,expected[0]))
    r=copy.deepcopy(expected[0]);r['distance']=float('nan');reject(lambda:validate_record(r,expected[0]))
    bad={k:v.copy() for k,v in recons.items()};bad['on_ce'][0]=np.nan;reject(lambda:score_equal(bad,recons))
    bad=copy.deepcopy(summaries);next(iter(next(iter(bad.values())).values()))['counts']['aim']+=1;reject(lambda:stats_equal(bad,summaries))
    assert negative==12 and sources()==col['sources']
    write(HERE/'verified.json',dict(complete=True,records=len(expected),grid='lattice',controls=dict(positive=positive,negative=negative),original_aim_unchanged=True,collected_sha256=sha(HERE/'collected.json'),report_sha256=sha(OUT/'report.json'),inference=0,backward=0,optimizer_updates=0,accepted=False,deployed=False))
    print('LATTICE_LABEL_AUDIT_VERIFIED')
if __name__=='__main__':main()
