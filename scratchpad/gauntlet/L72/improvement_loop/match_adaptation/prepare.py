"""Freeze all existing inner rows and native joins before descriptive analysis."""
from io_utils import *

def main():
    if OUT.exists() or (HERE/'prepared.json').exists():raise ValueError('Fresh output required')
    p=read(OLD/'prepared.json');v=read(OLD/'verified.json');r=read(OLD/'results_verified_v2.json')
    assert v['complete'] and v['prepared_sha256']==sha(OLD/'prepared.json')
    assert r['complete'] and sha(DATA)==p['source_binding']['dataset_sha256']
    assert sha(ORIGINAL)==p['source_binding']['source_dataset_sha256']
    assert sha(INDEX)==p['indices_sha256']
    with np.load(INDEX) as z:train,dev=z['train'],z['development']
    ids=np.sort(np.r_[train,dev]);assert len(ids)==268718 and len(np.unique(ids))==len(ids)
    with ZipFile(DATA) as z:rows={k:take(z,k,ids) for k in FIELDS}
    with ZipFile(ORIGINAL) as z:
        for k in FIELDS:
            if k!='sc':np.testing.assert_array_equal(rows[k],take(z,k,ids))
    with np.load(DATA) as z:tags=z['tags'];meta=json.loads(str(z['meta']))
    assert meta['shift_ticks']==0 and np.all(rows['split']==0)
    assignments=p['assignment'];selected={str(tags[i]) for i in rows['rep']}
    assert selected==set(assignments)
    rows.update(ids=ids,part=np.isin(ids,dev).astype(np.int8))
    assert not set(rows['rep'][rows['part']==0]) & set(rows['rep'][rows['part']==1])
    sources={s['tag']:s for s in read(MANIFEST)['sources'] if s['tag'] in selected}
    assert set(sources)==selected
    for rep,part in zip(rows['rep'],rows['part']):
        assert assignments[str(tags[rep])]==('development' if part else 'training')
    caches={}
    for arm in ('r1e_corrected','ordinary_v5','ordinary_v6'):
        folder=ROOT/'icebow/data/bench/development_iteration_1_20261005'/(arm+('_eval' if arm=='r1e_corrected' else '_eval_v2'))
        path=folder/'predictions.npz';assert sha(path)==r['hashes'][arm]['cache']
        with np.load(path) as z:assert np.array_equal(z['ids'],dev)
        caches[arm]=str(path.relative_to(ROOT))
    OUT.mkdir();np.savez_compressed(OUT/'rows.npz',**rows)
    inputs=[DATA,ORIGINAL,INDEX,LABELS,MANIFEST,OLD/'prepared.json',OLD/'verified.json',OLD/'results_verified_v2.json',
            HERE/'PLAN.md',HERE/'METRICS.md',HERE/'prepare.py',HERE/'io_utils.py',
            ROOT/'pipeline/dataset.py',ROOT/'pipeline/obs_contract.py',ROOT/'pipeline/dataset_gen.py',
            ROOT/'research/ext/Royale/RoyaleSim/data/calibration.json']+[ROOT/path for path in caches.values()]
    write(HERE/'prepared.json',dict(complete=True,rows=268718,training_rows=len(train),development_rows=len(dev),
        native_replays=len(sources),inputs={str(x.relative_to(ROOT)):sha(x) for x in inputs},
        rows_sha256=sha(OUT/'rows.npz'),sources=sources,tags=tags.tolist(),card_vocab=meta['card_vocab'],caches=caches,
        predictions_run=False,optimizer_updates=0,exposure=p['exposure']))
    print(json.dumps(dict(rows=len(ids),native_replays=len(sources),training=len(train),development=len(dev))))
    print('MATCH_ADAPTATION_PREPARED')

if __name__=='__main__':main()
