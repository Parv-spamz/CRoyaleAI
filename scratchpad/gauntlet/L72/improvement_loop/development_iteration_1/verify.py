"""Independent index oracle. Does not import the producer, trainer or model."""
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def check(train, dev, split, rep, tags, pool, reserved):
    expected_train, expected_dev = [], []
    for row in np.flatnonzero(pool & (split == 0)):
        tag = str(tags[rep[row]])
        assert tag.lower() not in reserved, 'reserved replay'
        digest = hashlib.sha256(('clashbot-l72-development-1-20261005:'+tag).encode()).hexdigest()
        (expected_dev if int(digest[:16],16)%5 == 0 else expected_train).append(int(row))
    assert train.dtype.kind in 'iu' and dev.dtype.kind in 'iu'
    assert np.array_equal(train, expected_train), 'training membership/order'
    assert np.array_equal(dev, expected_dev), 'development membership/order'
    assert not set(rep[train]) & set(rep[dev]), 'replay leakage'


def controls():
    tags=np.array(['fixture'+str(i) for i in range(20)])
    rep=np.repeat(np.arange(20),2)
    split=np.zeros(40,dtype=int); split[-2:]=1
    pool=np.ones(40,dtype=bool)
    masks=np.array([int.from_bytes(hashlib.sha256(('clashbot-l72-development-1-20261005:'+t).encode()).digest()[:8],'big')%5 for t in tags])
    train=np.flatnonzero((split==0)&(masks[rep]!=0));dev=np.flatnonzero((split==0)&(masks[rep]==0))
    check(train,dev,split,rep,tags,pool,set())
    corruptions=[(np.append(train,dev[0]),dev,set()),(train,np.append(dev,train[0]),set()),
                 (np.append(train,38),dev,set()),(np.append(train,train[0]),dev,set()),
                 (train[1:],dev,set()),(train,dev[1:],set()),(train[::-1],dev,set()),
                 (train,dev,{str(tags[rep[train[0]]])})]
    for args in corruptions:
        try: check(args[0],args[1],split,rep,tags,pool,args[2])
        except AssertionError: pass
        else: raise AssertionError('Corruption passed')
    return dict(positive=1,negative=len(corruptions))


def main():
    out=HERE/'verified.json'
    if out.exists(): raise ValueError('Preserve existing verification')
    fixture=controls()
    manifest=json.loads((HERE/'prepared.json').read_text())
    for path,digest in manifest['sources'].items(): assert sha(ROOT/path)==digest,path
    indices=ROOT/manifest['indices']; assert sha(indices)==manifest['indices_sha256']
    with np.load(ROOT/'icebow/data/bench/spawner_identity_20261005/gen_dataset_v5_public.npz') as z:
        split,rep,tags,gates=z['split'],z['rep'],z['tags'].astype(str),z['y_gate']
    with np.load(ROOT/'icebow/data/bench/context_teaching_20261005/cohorts.npz') as z: pool=z['pool']
    with np.load(indices) as z: train,dev=z['train'],z['development']
    reserve=json.loads((HERE.parent/'replay_reservation.json').read_text())
    with Path(reserve['reservation_file']).open() as stream: reserved={json.loads(line)['tag'].lower() for line in stream}
    check(train,dev,split,rep,tags,pool,reserved)
    counts={}
    assignments={}
    for name,rows in [('training',train),('development',dev)]:
        plays=int((gates[rows]>.5).sum())
        counts[name]=dict(rows=len(rows),replays=len(set(rep[rows])),plays=plays,waits=len(rows)-plays)
        assignments.update({str(tags[r]):name for r in set(rep[rows])})
    assert counts==manifest['counts']
    assert assignments==manifest['assignment']
    assert len(train)+len(dev)==manifest['ordinary_rows']==268718
    assert int((pool&(split!=0)).sum())==manifest['excluded_original_pool_validation']==38317
    assert len(reserved)==manifest['reserved_groups_checked']==239939
    out.write_text(json.dumps(dict(complete=True,counts=counts,controls=fixture,reserved_overlap=0,
        prepared_sha256=sha(HERE/'prepared.json'),script_sha256=sha(__file__),optimizer_updates=0,
        training_launched=False,final_acceptance=False),indent=2))
    print(json.dumps(counts));print('DEVELOPMENT_1_SPLIT_VERIFIED')


if __name__=='__main__': main()
