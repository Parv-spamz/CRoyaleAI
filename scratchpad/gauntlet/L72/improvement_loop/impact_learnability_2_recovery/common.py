import datetime, gzip, hashlib, itertools, json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
OUT = ROOT/'icebow/data/bench/impact_learnability_2_20261005'
VELOCITY = (17,18,21,22,26,27)
FIELDS = ('uid','team','kind','card_id','x','y','hp','max_hp','radius','footprint','level')
NAMES = ('Rocket','Knight','Giant','Log','Tesla','IceWizard','Tornado','Xbow')

def read(p):
    return json.loads(p.read_text(encoding='utf-8'))

def write(p,x):
    p.write_text(json.dumps(x,allow_nan=False,separators=(',',':'))+'\n',encoding='utf-8')

def sha(p):
    with p.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()

def digest(x):
    return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def cutoff():
    if datetime.datetime.now(datetime.timezone.utc) >= datetime.datetime(2026,10,6,13,tzinfo=datetime.timezone.utc):
        raise RuntimeError('Owner extended overnight cutoff; preserve partial output')

def sources():
    paths=list(HERE.glob('*.py'))+list((HERE.parent/'impact_learnability_2').glob('*.py'))+[HERE/'PLAN.md',HERE/'METRICS.md',HERE.parent/'impact_learnability_2/PLAN.md',HERE.parent/'impact_learnability_2/METRICS.md',
        HERE.parent/'impact_learnability_2/prepared.json', HERE.parent/'impact_learnability_2/preparation_verified.json', HERE.parent/'impact_learnability_2_restore/report.json', ROOT/'scratchpad/gauntlet/L71/integration/checks/l72-impact-learning2-collect.json', HERE.parent/'OWNER_OVERNIGHT_EXTENSION_20261005.md', HERE.parent/'impact_learnability_1_failure/report.json', HERE.parent/'moving_impact_readiness_v4/collect.py',HERE.parent/'moving_impact_readiness_v4/verified.json',
        ROOT/'pipeline/royale_runtime.py',ROOT/'scratchpad/gauntlet/L71/royale_update_20261005/build_manifest.json']
    return {str(p.relative_to(ROOT)):sha(p) for p in paths}

def specs():
    result=[]
    for i,(x,y,n,side,lane,level) in enumerate(itertools.product((3.5,4.5,5.5,6.5),(2.5,3.5,4.5),(1,2),(0,1),(0,1),(11,14))):
        result.append(dict(index=i,root_id=f'r{i:03}',seed=2026101300+i,x=x,y=y,count=n,side=side,lane=lane,level=level,
                           family=f'{x}_{y}_{n}',split='development' if y==3.5 else 'training'))
    return result

def public_snapshot(f):
    return dict(tick=f['tick'],entities=[{k:e[k] for k in FIELDS} for e in f['entities']])

def projected(history,side,level):
    return dict(side=side,own_level=level,history=[public_snapshot(f) for f in history])

def features(public,aim,uid,cat):
    assert set(public)=={'side','own_level','history'}
    old,new=public['history'];assert old['tick']==230 and new['tick']==240
    for f in (old,new):
        assert set(f)=={'tick','entities'} and all(set(e)==set(FIELDS) for e in f['entities'])
    prev={e['uid']:e for e in old['entities']};now={e['uid']:e for e in new['entities']}
    def xy(e):
        return (324000-e['x'],576000-e['y']) if public['side']==0 else (e['x'],e['y'])
    def motion(e):
        x,y=xy(e);px,py=xy(prev[e['uid']]);return ((x-px)/18000,(y-py)/18000)
    e=now[uid];x,y=xy(e);a,b=xy(dict(x=aim[0],y=aim[1]));vx,vy=motion(e)
    foot=e['footprint'];width=0 if foot is None else (foot[2]-foot[0])/18000;height=0 if foot is None else (foot[3]-foot[1])/18000
    out=[x/324000,y/576000,a/324000,b/576000,(a-x)/324000,(b-y)/576000,e['radius']/18000,width,height,e['hp']/10000,
         e['level']/14,int(e['kind']==0),int(e['kind']==2),int(e['kind']==3),int(e['card_id']==cat['Knight']['card_id']),
         int(e['card_id']==cat['Giant']['card_id']),public['own_level']/14,vx,vy]
    bodies=sorted((q for q in now.values() if q['card_id']!=-1),key=lambda q:q['card_id'])
    assert 1<=len(bodies)<=2 and len({q['card_id'] for q in bodies})==len(bodies)
    for i in range(2):
        if i:out.append(int(len(bodies)>i))
        if len(bodies)<=i:out.extend([0,0,0,0]);continue
        xx,yy=xy(bodies[i]);dx,dy=motion(bodies[i]);out.extend([xx/324000,yy/576000,dx,dy])
    assert len(out)==28
    return out

def metrics(prob,labels,rows):
    import numpy as np
    p=np.asarray(prob,dtype=np.float64);y=np.asarray(labels,dtype=np.float64)
    result={}
    for split in ('training','development'):
      for kind in ('all','body','crown'):
        ix=np.array([r['split']==split and (kind=='all' or r['kind']==kind) for r in rows])
        yy=y[ix];pp=p[ix];positive=yy==1;negative=yy==0
        assert positive.any() and negative.any()
        result[split+'_'+kind]=dict(rows=int(ix.sum()),positive=int(positive.sum()),negative=int(negative.sum()),
            brier=float(np.mean((pp-yy)**2)),balanced_brier=float((np.mean((pp[positive]-1)**2)+np.mean(pp[negative]**2))/2),
            recall=float(np.mean(pp[positive]>=.5)),false_positive_rate=float(np.mean(pp[negative]>=.5)))
    return result

def filters(results):
    import numpy as np
    def avg(arm,group):return float(np.mean([x['metrics'][group]['balanced_brier'] for x in results if x['arm']==arm]))
    static=avg('static_public','development_body');motion=avg('motion_public','development_body')
    pairs={s:{x['arm']:x for x in results if x['seed']==s} for s in (2026101200,2026101201,2026101202)}
    wins=sum(p['motion_public']['metrics']['development_body']['balanced_brier']<p['static_public']['metrics']['development_body']['balanced_brier'] for p in pairs.values())
    return dict(body_absolute=motion<=.10,body_relative=motion<=.8*static,seed_improvements=wins>=2,
        crown_protection=avg('motion_public','development_crown')<=avg('static_public','development_crown')+.01)
