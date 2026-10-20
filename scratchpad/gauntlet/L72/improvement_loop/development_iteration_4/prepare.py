"""Freeze phase-only draws and unchanged historical expert rows; no model import."""
import hashlib,json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[5];HERE=Path(__file__).resolve().parent
DIAG=HERE.parent/'match_adaptation';FIRST=HERE.parent/'development_iteration_1'
OUT=ROOT/'icebow/data/bench/development_iteration_4_20261005'
OLD=ROOT/'icebow/data/bench/development_iteration_1_20261005'
DOUT=ROOT/'icebow/data/bench/match_adaptation_20261005'
PHASES=('single_clock','double_regulation_clock','early_overtime_clock','late_overtime_clock')

def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def main():
    assert not OUT.exists() and not (HERE/'prepared.json').exists()
    verified=json.loads((DIAG/'verified_v2.json').read_text());binding=json.loads((DIAG/'prepared.json').read_text())
    assert verified['complete'] and verified['report_sha256']==sha(DIAG/'report_v2.json')
    assert sha(DOUT/'rows.npz')==binding['rows_sha256']
    with np.load(DOUT/'rows.npz') as z:a={k:z[k] for k in z.files}
    with np.load(OLD/'indices.npz') as z:train,dev=z['train'],z['development']
    assert np.array_equal(np.sort(np.r_[train,dev]),a['ids']) and not np.intersect1d(train,dev).size
    assert np.array_equal(a['ids'][a['part']==0],train) and np.array_equal(a['ids'][a['part']==1],dev)
    phase=np.searchsorted([2400,3600,4800],a['tick'],side='right')
    pools=[a['ids'][(a['part']==0)&(phase==i)] for i in range(4)]
    assert all(len(p) for p in pools)
    rng=np.random.default_rng(20261007);draws=[]
    for _ in range(1000):
        rows=np.concatenate([rng.choice(p,32) for p in pools]);draws.append(rows[rng.permutation(128)])
    draws=np.asarray(draws)
    with np.load(OLD/'draws.npz') as z:mirror=z['mirror'];ordinary=z['rows']
    assert np.isin(draws,train).all() and not np.isin(draws,dev).any()
    cv=binding['card_vocab'];counts={}
    for part,name in enumerate(('training','development')):
        counts[name]={}
        for i,key in enumerate(PHASES):
            mask=(a['part']==part)&(phase==i);play=mask&(a['y_gate']==1)
            rocket=play&(a['y_card']==cv.index('rocket'))
            counts[name][key]=dict(rows=int(mask.sum()),replays=len(set(a['rep'][mask])),
                plays=int(play.sum()),waits=int((mask&(a['y_gate']==0)).sum()),
                expert_rockets=int(rocket.sum()),rocket_replays=len(set(a['rep'][rocket])))
    OUT.mkdir();np.savez_compressed(OUT/'schedule.npz',rows=draws,mirror=mirror,
        ids=a['ids'],phase=phase,part=a['part'])
    paths=[Path(__file__),HERE/'PLAN.md',HERE/'METRICS.md',DIAG/'prepared.json',DIAG/'verified_v2.json',
        DIAG/'report_v2.json',DIAG/'capabilities_verified.json',DOUT/'rows.npz',DOUT/'rows_v2.jsonl',
        OLD/'indices.npz',OLD/'draws.npz',FIRST/'prepared.json',FIRST/'verified.json',FIRST/'results_verified_v2.json']
    report=dict(complete=True,trainable=False,optimizer_allowed=False,counts=counts,
        sources={str(p.relative_to(ROOT)):sha(p) for p in paths},
        schedule=str((OUT/'schedule.npz').relative_to(ROOT)),schedule_sha256=sha(OUT/'schedule.npz'),
        draws=128000,phase_draws=[int(np.isin(draws,p).sum()) for p in pools],
        control_phase_draws=[int(np.isin(ordinary,p).sum()) for p in pools],
        original_labels_preserved=True,model_predictions=0,optimizer_updates=0)
    (HERE/'prepared.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(counts));print('PHASE_SCHEDULE_PREPARED')

if __name__=='__main__':main()
