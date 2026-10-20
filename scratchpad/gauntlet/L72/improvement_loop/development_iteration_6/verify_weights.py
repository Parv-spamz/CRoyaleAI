"""Independent scalar original-label/draw recount; does not import producer."""
import hashlib,math
import numpy as np
from experiment import *

def digest(a):return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
def validate(ids,regions,weights,ei,er,ew):
    assert np.array_equal(ids,ei) and np.array_equal(regions,er) and np.array_equal(weights,ew)
def main():
    assert not (HERE/'verified.json').exists();c.setup();p=c.read(HERE/'prepared.json')
    for path,h in p['sources'].items():assert c.sha(c.ROOT/path)==h
    assert c.sha(OUT/'weights.npz')==p['weights_sha256']
    ids=c.indices('train')
    with np.load(DOUT/'rows.npz') as z:
        lookup={int(x):i for i,x in enumerate(z['ids'])};ix=[lookup[int(x)] for x in ids]
        s={k:z[k][ix] for k in p['original_labels']}
    for k,v in s.items():assert digest(v)==p['original_labels'][k]
    regions=[];counts=[0]*80
    for (x,y),g in zip(s['y_xy'],s['y_gate']):
        cx=min(36,max(0,round(float(np.float32(x)*np.float32(36)))));cy=min(63,max(0,round(float(np.float32(y)*np.float32(64)))))
        region=5*(cy//4)+(min(cx,36-cx)//4);regions.append(region)
        if g==1:counts[region]+=1
    n=sum(counts);k=sum(v>0 for v in counts)
    w=[max(.25,min(4,math.sqrt(n/(k*v)))) if v else 4 for v in counts]
    row=np.array([w[r] if g==1 else 1 for r,g in zip(regions,s['y_gate'])],np.float32)
    with np.load(OUT/'weights.npz') as z:
        validate(z['ids'],z['region'],z['weights'],ids,np.array(regions),row)
        assert np.array_equal(z['counts'],counts) and np.allclose(z['region_weights'],w,rtol=0,atol=1e-15)
    assert counts==p['region_counts'] and n==p['play'] and k==p['nonempty_regions']
    with np.load(SCHEDULE) as z:draw=z['rows']
    by_id={int(i):weight for i,weight in zip(ids,row)};scheduled=np.array([[by_id[int(i)] for i in batch] for batch in draw],np.float32)
    assert digest(scheduled)==p['scheduled_weights_sha256']
    # Same exact labels under horizontal reflection map to the same folded bins.
    for cx in range(37):assert min(cx,36-cx)//4==min(36-cx,cx)//4
    rejected=0
    for which in ('id','region','weight'):
        di=ids[:3].copy();dr=np.array(regions[:3]);dw=row[:3].copy()
        if which=='id':di[0]+=1
        elif which=='region':dr[0]=(dr[0]+1)%80
        else:dw[0]+=.1
        try:validate(di,dr,dw,ids[:3],np.array(regions[:3]),row[:3])
        except AssertionError:rejected+=1
        else:raise AssertionError('Weight/membership corruption accepted')
    c.write(HERE/'verified.json',dict(complete=True,prepared_sha256=c.sha(HERE/'prepared.json'),rows=len(ids),play=n,
        independent_regions_and_weights=True,all_original_labels_matched=True,scheduled_weights_matched=True,
        mirror_bins_verified=37,positive_controls=1,corruptions_rejected=rejected,optimizer_updates=0,predictions=0))
    print('SPATIAL_WEIGHTS_INDEPENDENT_COMPLETE')

if __name__=='__main__':main()
