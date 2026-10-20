"""Fit only a fixed spatial-frequency weight map from original training labels."""
import hashlib
import numpy as np
from experiment import *

def digest(a):return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
def main():
    assert not OUT.exists() and not (HERE/'prepared.json').exists();c.setup();prerequisites();OUT.mkdir()
    ids=c.indices('train');dev=c.indices('development');binding=c.read(HERE.parent/'match_adaptation/prepared.json')
    raw=DOUT/'rows.npz';assert c.sha(raw)==binding['rows_sha256']
    with np.load(raw) as z:
        take=np.searchsorted(z['ids'],ids);assert np.array_equal(z['ids'][take],ids)
        s={k:z[k][take] for k in ('split','rep','y_gate','y_card','y_xy','y_wait_card','y_wait_dt','y_crowns','y_cell','y_hand_pos')}
    play=s['y_gate']==1;assert np.all(s['split']==0) and not np.isin(ids,dev).any()
    assert len(ids)==213995 and play.sum()==67106
    xy=s['y_xy'];cx=np.clip(np.rint(xy[:,0]*np.float32(36)).astype(int),0,36);cy=np.clip(np.rint(xy[:,1]*np.float32(64)).astype(int),0,63)
    regions=(cy//4)*5+np.minimum(cx,36-cx)//4
    counts=np.bincount(regions[play],minlength=80);nonempty=int((counts>0).sum())
    weights=np.clip(np.sqrt(play.sum()/(nonempty*np.maximum(counts,1))),.25,4);weights[counts==0]=4
    row_weights=np.where(play,weights[regions],1).astype(np.float32)
    np.savez_compressed(OUT/'weights.npz',ids=ids,region=regions,weights=row_weights,counts=counts,region_weights=weights)
    with np.load(SCHEDULE) as z:draw=z['rows'];positions=np.searchsorted(ids,draw);assert np.array_equal(ids[positions],draw)
    sources=[raw,SCHEDULE,HERE/'PLAN.md',HERE/'METRICS.md',Path(__file__),FIRST/'prepared.json',FIRST/'verified.json',HERE.parent/'match_adaptation/prepared.json']
    c.write(HERE/'prepared.json',dict(complete=True,training_rows=len(ids),play=int(play.sum()),wait=int((~play).sum()),
        nonempty_regions=nonempty,region_counts=counts.tolist(),region_weights=weights.tolist(),
        weights_sha256=c.sha(OUT/'weights.npz'),sources={str(p.relative_to(c.ROOT)):c.sha(p) for p in sources},
        original_labels={k:digest(v) for k,v in s.items()},scheduled_weights_sha256=digest(row_weights[positions]),
        development_rows_used_for_weights=0,optimizer_updates=0,predictions=0))
    print('SPATIAL_WEIGHTS_PREPARED')

if __name__=='__main__':main()
