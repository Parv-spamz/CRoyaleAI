"""New geometry diagnosis of saved small-set assay predictions; no inference."""
import datetime
import hashlib
import json
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
BASE=HERE.parent/'small_set_fit'
CACHE=ROOT/'icebow/data/bench/small_set_fit_20261006'
OUT=ROOT/'icebow/data/bench/small_set_aim_audit_20261006'
KEYS=('rows','exact','aim','miss_same_patch','miss_other_patch','miss_le2','miss_le4','miss_gt4','floor_aim')

def read(p): return json.loads(p.read_text(encoding='utf-8'))
def sha(p):
    with p.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,d): p.write_text(json.dumps(d,allow_nan=False,separators=(',',':'))+'\n',encoding='utf-8')
def sources():
    paths=list(HERE.glob('*.py'))+[HERE/'PLAN.md',BASE/'reviewed_results.json',BASE/'results_verified.json',BASE/'evaluated.json',
        BASE/'prepared.json',ROOT/'pipeline/model_gen.py',ROOT/'pipeline/model_v3.py',CACHE/'candidate.pt',CACHE/'schedule.npz',
        ROOT/'icebow/data/bench/spawner_identity_20261005/gen_dataset_v5_public.npz',ROOT/'icebow/data/pipeline/gen_dataset_v31_public.npz']
    paths += [CACHE/f for f in read(BASE/'evaluated.json')['artifacts']]
    return {str(p.relative_to(ROOT)):sha(p) for p in paths}

def main():
    assert datetime.datetime.now(datetime.timezone.utc)<datetime.datetime(2026,10,6,13,tzinfo=datetime.timezone.utc)
    assert not (HERE/'started.json').exists(); OUT.mkdir(exist_ok=False)
    binding=sources(); write(HERE/'started.json',dict(sources=binding))
    r=read(BASE/'results_verified.json'); e=read(BASE/'evaluated.json'); closed=read(BASE/'reviewed_results.json')
    assert r['complete'] and closed['complete'] and r['quarantined'] and not r['diagnostic_fit']
    rows=[]; totals={}; cv=e['card_vocab']
    for filename,h in e['artifacts'].items():
        assert sha(CACHE/filename)==h
        with np.load(CACHE/filename,allow_pickle=False) as f: z={k:f[k] for k in f.files}
        key=filename[:-4]; mir=key.endswith('_mirrored'); ix=np.where(z['y_gate']==1)[0]
        xy=z['y_xy'][ix]; pred=z['expert_cell'][ix].astype(np.int64)
        target=np.clip((xy[:,0]*36).astype(np.int64),0,35)+36*np.clip((xy[:,1]*64).astype(np.int64),0,63)
        pp=(pred//36//4)*9+(pred%36//4); tp=(target//36//4)*9+(target%36//4)
        dist=np.linalg.norm((np.c_[pred%36/36,pred//36/64]-xy)*[18,32],axis=1)
        fd=np.linalg.norm((np.c_[target%36/36,target//36/64]-xy)*[18,32],axis=1)
        assert np.isfinite(xy).all() and (xy>=0).all() and (xy<=1).all()
        flags=dict(rows=np.ones(len(ix),bool),exact=pred==target,aim=dist<=1,
            miss_same_patch=(dist>1)&(pp==tp),miss_other_patch=(dist>1)&(pp!=tp),
            miss_le2=(dist>1)&(dist<=2),miss_le4=(dist>2)&(dist<=4),miss_gt4=dist>4,floor_aim=fd<=1)
        groups=dict(play=np.ones(len(ix),bool),rocket=z['y_card'][ix]==cv.index('rocket'),
            late_rocket=(z['y_card'][ix]==cv.index('rocket'))&(z['tick'][ix]>=4800))
        groups.update({'card/'+cv[int(card)]:z['y_card'][ix]==card for card in np.unique(z['y_card'][ix])})
        totals[key]={}
        for group,m in groups.items():
            reps,inv=np.unique(z['rep'][ix][m],return_inverse=True)
            t={k:int(v[m].sum()) for k,v in flags.items()}; by={str(int(rep)):{} for rep in reps}
            for k,v in flags.items():
                vals=np.bincount(inv,weights=v[m],minlength=len(reps)).astype(int)
                for rep,value in zip(reps,vals): by[str(int(rep))][k]=int(value)
            totals[key][group]=dict(t,replays=len(reps),by_replay=by)
        for j,i in enumerate(ix):
            rows.append(dict(cache=key,mirrored=mir,id=int(z['ids'][i]),rep=int(z['rep'][i]),tick=int(z['tick'][i]),
                card=cv[int(z['y_card'][i])],xy=xy[j].tolist(),pred=int(pred[j]),target=int(target[j]),
                pred_patch=int(pp[j]),target_patch=int(tp[j]),distance=float(dist[j]),floor_distance=float(fd[j])))
    assert len(rows)==3072 and binding==sources()
    with (OUT/'rows.jsonl').open('x',encoding='utf-8') as f:
        for row in rows: f.write(json.dumps(row,allow_nan=False)+'\n')
    write(OUT/'counts.json',totals)
    write(HERE/'collected.json',dict(complete=True,sources=binding,rows=3072,rows_sha256=sha(OUT/'rows.jsonl'),
        counts_sha256=sha(OUT/'counts.json'),inference=0,optimizer_updates=0,accepted=False,deployed=False))
    print('SMALL_SET_AIM_COLLECTED')

if __name__=='__main__': main()
