"""Training-source/draw capacity with independent scalar recount; no model."""
import hashlib,json,math
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
BASE=ROOT/'icebow/data/bench/development_iteration_1_20261005'
ROWS=ROOT/'icebow/data/bench/match_adaptation_20261005/rows.npz'

def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    assert not (HERE/'exposure.json').exists()
    verified=json.loads((HERE/'verified.json').read_text());assert verified['complete']
    inputs=[ROWS,BASE/'indices.npz',BASE/'draws.npz',HERE/'EXPOSURE_PLAN.md',Path(__file__),HERE/'verified.json']
    hashes={str(p.relative_to(ROOT)):sha(p) for p in inputs}
    with np.load(BASE/'indices.npz') as z:ids=z['train'];dev=z['development']
    with np.load(ROWS) as z:
        ix=np.searchsorted(z['ids'],ids);assert np.array_equal(z['ids'][ix],ids)
        s={k:z[k][ix] for k in ('rep','tick','split','y_gate','y_card','y_xy','sc')}
    assert len(ids)==213995 and np.all(s['split']==0) and not np.isin(ids,dev).any()
    with np.load(BASE/'draws.npz') as z:draw=z['rows'].reshape(-1)
    positions=np.searchsorted(ids,draw)
    assert len(draw)==128000 and np.array_equal(ids[positions],draw)
    cv=json.loads((HERE.parent/'match_adaptation/prepared.json').read_text())['card_vocab'];play=s['y_gate']==1
    anchors=np.array([[3.5/18,6.5/32],[14.5/18,6.5/32]])
    dist=np.linalg.norm((s['y_xy'].astype(np.float64)[:,None]-anchors)*[18,32],axis=2)
    close=((dist<=1)&(s['sc'][:,68:70]>.5)).any(1)&play
    scalar=[]
    for (x,y),sc,g in zip(s['y_xy'],s['sc'],play):
        hit=False
        for slot,tx in ((68,3.5/18),(69,14.5/18)):
            dx=(float(x)-tx)*18;dy=(float(y)-6.5/32)*32
            hit=hit or (bool(g) and sc[slot]>.5 and math.sqrt(dx*dx+dy*dy)<=1)
        scalar.append(hit)
    assert np.array_equal(close,scalar)
    freq=np.bincount(positions,minlength=len(ids));indfreq={int(x):0 for x in ids}
    for row in draw:indfreq[int(row)]+=1
    assert np.array_equal(freq,[indfreq[int(x)] for x in ids])
    groups=dict(all=np.ones(len(ids),bool),play=play,wait=~play,rocket=play&(s['y_card']==cv.index('rocket')),near=close)
    groups['rocket_near']=groups['rocket']&close;groups['rocket_other']=groups['rocket']&~close
    groups['other_card_near']=close&~groups['rocket']
    for phase,(lo,hi) in enumerate(((0,2400),(2400,3600),(3600,4800),(4800,2**31))):
        groups['rocket_near_phase'+str(phase)]=groups['rocket_near']&(s['tick']>=lo)&(s['tick']<hi)
    result={}
    for key,m in groups.items():
        selected=m&(freq>0)
        result[key]=dict(rows=int(m.sum()),replays=len(set(s['rep'][m].tolist())),draws=int(freq[m].sum()),
            unique_drawn_rows=int(selected.sum()),drawn_replays=len(set(s['rep'][selected].tolist())),
            multiplicity={str(n):int((freq[m]==n).sum()) for n in sorted(set(freq[m].tolist()))})
        assert result[key]['draws']==sum(indfreq[int(row)] for row in ids[m])
    # Boundary validator rejects three concrete source/draw corruptions.
    rejected=0
    for altered in (np.r_[draw[:-1],dev[0]],np.r_[draw,ids[0]],draw[:-1]):
        try:assert len(altered)==128000 and np.isin(altered,ids).all()
        except AssertionError:rejected+=1
        else:raise AssertionError('Unregistered draw accepted')
    assert rejected==3 and hashes=={str(p.relative_to(ROOT)):sha(p) for p in inputs}
    report=dict(complete=True,inputs=hashes,groups=result,independent_scalar_classification=True,
        independent_draw_histogram=True,draw_corruptions_rejected=3,predictions=0,optimizer_updates=0,
        narrow_geometry_not_physical_impact=True)
    (HERE/'exposure.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(result));print('TOWER_TRAINING_EXPOSURE_COMPLETE')

if __name__=='__main__':main()
