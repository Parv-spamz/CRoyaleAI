"""Independent schedule replay and exclusion oracle, no producer import."""
import hashlib,json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[5];HERE=Path(__file__).resolve().parent


def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def verify(ordinary,mirrors,train,dev,defensive,actual):
    selected=sorted(set(train.tolist())&set(defensive.tolist()))
    expected=ordinary.copy();bits=np.zeros_like(ordinary,dtype=bool);rng=np.random.default_rng(20261006)
    for i in range(len(ordinary)):
        bits[i]=rng.random(ordinary.shape[1])<.2
        choices=rng.choice(selected,ordinary.shape[1])
        expected[i]=np.where(bits[i],choices,ordinary[i])
    assert np.array_equal(expected,actual['rows'])
    assert np.array_equal(bits,actual['replace']) and np.array_equal(mirrors,actual['mirror'])
    assert np.isin(actual['rows'],train).all() and not np.isin(actual['rows'],dev).any()


def controls():
    train=np.arange(20);dev=np.arange(20,24);defensive=np.array([2,4,6,20])
    ordinary=np.tile(np.arange(8),(3,1));mirror=np.array([0,1,0],bool)
    rng=np.random.default_rng(20261006);rows=ordinary.copy();bits=[]
    for i in range(3):
        bit=rng.random(8)<.2;choices=rng.choice([2,4,6],8);rows[i,bit]=choices[bit];bits.append(bit)
    good=dict(rows=rows,replace=np.asarray(bits),mirror=mirror)
    verify(ordinary,mirror,train,dev,defensive,good)
    for field in ('rows','replace','mirror'):
        bad={k:v.copy() for k,v in good.items()}
        bad[field].flat[0]=20 if field=='rows' else not bad[field].flat[0]
        try:verify(ordinary,mirror,train,dev,defensive,bad)
        except AssertionError:pass
        else:raise AssertionError('Corruption passed')
    return dict(positive=1,negative=3)


def main():
    out=HERE/'verified.json'
    if out.exists():raise ValueError('Preserve existing verification')
    report=json.loads((HERE/'prepared.json').read_text());tested=controls()
    for path,h in report['sources'].items():assert sha(ROOT/path)==h,path
    assert sha(ROOT/report['schedule'])==report['schedule_sha256']
    prev=ROOT/'icebow/data/bench/development_iteration_1_20261005'
    with np.load(prev/'indices.npz') as z:train,dev=z['train'],z['development']
    with np.load(prev/'draws.npz') as z:ordinary,mirror=z['rows'],z['mirror']
    with np.load(ROOT/'icebow/data/bench/defence_sequence_v5_binding_20261005/index.npz') as z:defensive=z['defensive_rows']
    with np.load(ROOT/report['schedule']) as z:actual={k:z[k] for k in z.files}
    verify(ordinary,mirror,train,dev,defensive,actual)
    assert np.array_equal(np.intersect1d(defensive,train),actual['defensive_training'])
    assert np.array_equal(np.intersect1d(defensive,dev),actual['defensive_development'])
    with np.load(ROOT/'icebow/data/bench/spawner_identity_20261005/gen_dataset_v5_public.npz') as z:
        gates,card,rep=z['y_gate'],z['y_card'],z['rep'];cv=json.loads(str(z['meta']))['card_vocab']
    for name in ('training','development'):
        ids=actual['defensive_'+name]
        counts=dict(rows=len(ids),replays=len(set(rep[ids])),plays=int((gates[ids]==1).sum()),waits=int((gates[ids]==0).sum()),
            expert_rockets=int(((gates[ids]==1)&(card[ids]==cv.index('rocket'))).sum()))
        assert counts==report['counts'][name]
    assert int(actual['replace'].sum())==report['replacement_draws']
    assert int(np.isin(actual['rows'],actual['defensive_training']).sum())==report['candidate_defensive_draws']
    assert int(np.isin(ordinary,actual['defensive_training']).sum())==report['ordinary_defensive_draws']
    out.write_text(json.dumps(dict(complete=True,controls=tested,prepared_sha256=sha(HERE/'prepared.json'),
        verifier_sha256=sha(__file__),counts=report['counts'],schedule_reproduced=True,optimizer_updates=0),indent=2))
    print('DEFENCE_DEVELOPMENT_SCHEDULE_VERIFIED')


if __name__=='__main__':main()
