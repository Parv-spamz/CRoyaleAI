"""Independent phase schedule regeneration from original dataset ticks/labels."""
import hashlib,json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[5];HERE=Path(__file__).resolve().parent
OLD=ROOT/'icebow/data/bench/development_iteration_1_20261005'

def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def phase_of(t):return (t>=2400).astype(int)+(t>=3600).astype(int)+(t>=4800).astype(int)

def validate(actual,ids,parts,ticks,train,dev,mirrors):
    phase=phase_of(ticks);assert np.array_equal(actual['ids'],ids)
    assert np.array_equal(actual['phase'],phase) and np.array_equal(actual['part'],parts)
    pools=[sorted(ids[(parts==0)&(phase==i)].tolist()) for i in range(4)]
    rng=np.random.default_rng(20261007);expected=[]
    for _ in range(len(actual['rows'])):
        chosen=[]
        for pool in pools:chosen.extend(rng.choice(pool,32).tolist())
        order=rng.permutation(128);expected.append([chosen[i] for i in order])
    assert np.array_equal(actual['rows'],expected) and np.array_equal(actual['mirror'],mirrors)
    assert np.isin(actual['rows'],train).all() and not np.isin(actual['rows'],dev).any()
    assert all(np.isin(actual['rows'],pool).sum()==32*len(expected) for pool in pools)

def controls():
    ids=np.arange(12);parts=np.r_[np.zeros(8,int),np.ones(4,int)]
    ticks=np.array([0,2399,2400,3599,3600,4799,4800,6000,1,2400,3600,4800])
    rng=np.random.default_rng(20261007);draw=[]
    for _ in range(2):
        x=np.concatenate([rng.choice([2*i,2*i+1],32) for i in range(4)]);draw.append(x[rng.permutation(128)])
    good=dict(ids=ids,part=parts,phase=np.array([0,0,1,1,2,2,3,3,0,1,2,3]),rows=np.array(draw),mirror=np.array([0,1]))
    validate(good,ids,parts,ticks,ids[:8],ids[8:],np.array([0,1]))
    for field in ('ids','part','phase','rows','mirror'):
        bad={k:v.copy() for k,v in good.items()};bad[field].flat[0]=9
        try:validate(bad,ids,parts,ticks,ids[:8],ids[8:],np.array([0,1]))
        except AssertionError:pass
        else:raise AssertionError('Corruption passed')
    return dict(positive=1,negative=5,phase_boundaries=True)

def main():
    assert not (HERE/'verified.json').exists();fixtures=controls()
    report=json.loads((HERE/'prepared.json').read_text())
    for path,h in report['sources'].items():assert sha(ROOT/path)==h,path
    assert sha(ROOT/report['schedule'])==report['schedule_sha256']
    with np.load(OLD/'indices.npz') as z:train,dev=z['train'],z['development']
    ids=np.sort(np.concatenate([train,dev]));parts=np.isin(ids,dev).astype(int)
    with np.load(ROOT/'icebow/data/bench/spawner_identity_20261005/gen_dataset_v5_public.npz') as z:
        a={k:z[k][ids] for k in ('tick','rep','side','split','y_gate','y_card','y_xy','y_wait_card','y_wait_dt','y_crowns','y_cell','y_hand_pos')}
        cv=json.loads(str(z['meta']))['card_vocab']
    with np.load(ROOT/'icebow/data/bench/match_adaptation_20261005/rows.npz') as z:
        assert np.array_equal(ids,z['ids'])
        for k,v in a.items():assert np.array_equal(v,z[k]),k
    assert (a['split']==0).all()
    with np.load(ROOT/report['schedule']) as z:actual={k:z[k] for k in z.files}
    with np.load(OLD/'draws.npz') as z:mirror=z['mirror'];ordinary=z['rows']
    validate(actual,ids,parts,a['tick'],train,dev,mirror)
    phases=phase_of(a['tick']);names=('single_clock','double_regulation_clock','early_overtime_clock','late_overtime_clock')
    for part,name in enumerate(('training','development')):
        for i,key in enumerate(names):
            mask=(parts==part)&(phases==i);play=mask&(a['y_gate']==1);rocket=play&(a['y_card']==cv.index('rocket'))
            count=dict(rows=int(mask.sum()),replays=len(set(a['rep'][mask])),plays=int(play.sum()),waits=int((mask&~play).sum()),
                expert_rockets=int(rocket.sum()),rocket_replays=len(set(a['rep'][rocket])))
            assert count==report['counts'][name][key]
    assert report['phase_draws']==[32000]*4
    assert report['control_phase_draws']==[int(np.isin(ordinary,ids[(parts==0)&(phases==i)]).sum()) for i in range(4)]
    result=dict(complete=True,prepared_sha256=sha(HERE/'prepared.json'),verifier_sha256=sha(__file__),
        controls=fixtures,counts=report['counts'],schedule_reproduced=True,all_original_labels_equal=True,optimizer_updates=0)
    (HERE/'verified.json').write_text(json.dumps(result,indent=2));print('PHASE_SCHEDULE_VERIFIED')

if __name__=='__main__':main()
