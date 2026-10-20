"""Prepare a paired training-only exposure schedule; no model access."""
import hashlib,json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[5];HERE=Path(__file__).resolve().parent
PREV=HERE.parent/'development_iteration_1'
OUT=ROOT/'icebow/data/bench/development_iteration_2_20261005'


def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def main():
    if (HERE/'prepared.json').exists() or OUT.exists():raise ValueError('Fresh schedule required')
    binding=json.loads((HERE.parent/'defence_crosswalk_bound.json').read_text())
    verified=json.loads((HERE.parent/'defence_crosswalk_verified.json').read_text())
    sources={}
    for path,h in binding['artifacts'].items():
        assert sha(ROOT/path)==h;sources[path]=h
    for name in ('defence_crosswalk_bound.json','defence_crosswalk_verified.json'):
        sources[str((HERE.parent/name).relative_to(ROOT))]=sha(HERE.parent/name)
    prepared=json.loads((PREV/'prepared.json').read_text());check=json.loads((PREV/'verified.json').read_text())
    assert check['prepared_sha256']==sha(PREV/'prepared.json') and check['complete']
    with np.load(ROOT/prepared['indices']) as z:train,dev=z['train'],z['development']
    assert sha(ROOT/prepared['indices'])==prepared['indices_sha256']
    index=ROOT/'icebow/data/bench/defence_sequence_v5_binding_20261005/index.npz'
    with np.load(index) as z:defensive=z['defensive_rows']
    training=np.intersect1d(defensive,train);development=np.intersect1d(defensive,dev)
    assert len(training) and len(development) and not np.intersect1d(training,dev).size
    baseline=ROOT/'icebow/data/bench/development_iteration_1_20261005/draws.npz'
    preflight=json.loads((PREV/'prelaunch.json').read_text());assert sha(baseline)==preflight['draws_sha256']
    with np.load(baseline) as z:ordinary=z['rows'];mirrors=z['mirror']
    rng=np.random.default_rng(20261006);candidate=ordinary.copy();replace=[]
    for i in range(1000):
        mask=rng.random(128)<.2;sample=rng.choice(training,128)
        candidate[i,mask]=sample[mask];replace.append(mask)
    replacement=np.asarray(replace)
    assert np.isin(candidate,train).all() and not np.isin(candidate,dev).any()
    OUT.mkdir();np.savez_compressed(OUT/'schedule.npz',rows=candidate,mirror=mirrors,replace=replacement,
        defensive_training=training,defensive_development=development)
    data=ROOT/'icebow/data/bench/spawner_identity_20261005/gen_dataset_v5_public.npz'
    with np.load(data) as z:
        gates,card,rep=z['y_gate'],z['y_card'],z['rep'];cv=json.loads(str(z['meta']))['card_vocab']
    counts={}
    for name,ids in [('training',training),('development',development)]:
        counts[name]=dict(rows=len(ids),replays=len(set(rep[ids])),plays=int((gates[ids]==1).sum()),
            waits=int((gates[ids]==0).sum()),expert_rockets=int(((gates[ids]==1)&(card[ids]==cv.index('rocket'))).sum()))
    for path in (PREV/'prepared.json',PREV/'verified.json',PREV/'prelaunch.json',ROOT/prepared['indices'],
                 baseline,HERE/'PLAN.md',Path(__file__),data):sources[str(path.relative_to(ROOT))]=sha(path)
    report=dict(complete=True,trainable=False,optimizer_allowed=False,next_gate='C2/C3',sources=sources,
        schedule=str((OUT/'schedule.npz').relative_to(ROOT)),schedule_sha256=sha(OUT/'schedule.npz'),
        counts=counts,draws=int(candidate.size),replacement_draws=int(replacement.sum()),
        ordinary_defensive_draws=int(np.isin(ordinary,training).sum()),
        candidate_defensive_draws=int(np.isin(candidate,training).sum()),
        labels_changed=False,model_predictions=0,optimizer_updates=0)
    (HERE/'prepared.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(counts));print('DEFENCE_DEVELOPMENT_SCHEDULE_PREPARED')


if __name__=='__main__':main()
