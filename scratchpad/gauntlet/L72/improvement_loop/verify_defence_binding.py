"""Independent row/label crosswalk oracle; no builder import or model calls."""
import argparse
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent


def file_hash(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def array_hash(a):
    value = np.ascontiguousarray(a)
    return hashlib.sha256(json.dumps([value.dtype.str, list(value.shape)]).encode()+value.tobytes()).hexdigest()


def exact(a, b):
    assert a.dtype == b.dtype and a.shape == b.shape
    np.testing.assert_array_equal(a, b)


def check(old, new, original, bound, crosswalk, target_hashes, before, after):
    assert set(crosswalk) == {'source_rows','corrected_rows'}
    assert set(original) == set(bound)
    assert set(original) == {'pool_rows','window_offsets','window_rows','defensive_rows','other_rows',
                            'window_rep','window_side','window_tick','window_defensive'}
    for k in original:
        exact(original[k], bound[k])
    pool = original['pool_rows']
    exact(pool, np.unique(pool))
    exact(crosswalk['source_rows'], pool)
    exact(crosswalk['corrected_rows'], pool)
    assert before['feature_version'] == 4 and after['feature_version'] == 5
    assert after['body_identity_contract'] == 'catalog_spawner_bodies_v1'
    for k in ('card_vocab','decks','grid','shift_ticks','public_observation',
              'public_timing_contract','opponent_elixir'):
        assert before[k] == after[k], k
    for k in ('tags','rep','side','tick','split','deck_id','off','v3val'):
        exact(old[k], new[k])
    icebow = {'ice-wizard','knight','rocket','skeletons','tesla','the-log','tornado','x-bow'}
    deck_ids = [d['id'] for d in after['decks'] if set(d['cards']) == icebow]
    split, rep, deck = new['split'], new['rep'], new['deck_id']
    side, tick = new['side'], new['tick']
    exact(pool, np.flatnonzero((split == 0) & np.isin(deck, deck_ids)))
    assert not set(rep[pool]) & set(rep[split != 0])
    # Explicit row-ID map, independently resolved for all repeated references.
    mapping = dict(zip(map(int,crosswalk['source_rows']), map(int,crosswalk['corrected_rows'])))
    for k in ('pool_rows','window_rows','defensive_rows','other_rows'):
        mapped = np.array([mapping[int(i)] for i in original[k]], dtype=bound[k].dtype)
        exact(mapped, bound[k])
    offsets = bound['window_offsets']
    assert offsets[0] == 0 and offsets[-1] == len(bound['window_rows'])
    assert len(offsets) == len(bound['window_rep'])+1 and (np.diff(offsets) > 0).all()
    for j, (r,s,t) in enumerate(zip(bound['window_rep'],bound['window_side'],bound['window_tick'])):
        ids = bound['window_rows'][offsets[j]:offsets[j+1]]
        assert (rep[ids] == r).all() and (side[ids] == s).all()
        assert ((tick[ids] >= max(0,t-40)) & (tick[ids] <= t+600)).all()
    union = np.unique(np.concatenate((bound['defensive_rows'],bound['other_rows'])))
    keys = {k for k in old if k.startswith('y_')}
    assert keys == {k for k in new if k.startswith('y_')} == set(target_hashes)
    for k in sorted(keys):
        a,b = old[k], new[k]
        exact(a,b)
        assert target_hashes[k] == dict(pool=array_hash(b[pool]), sequence_union=array_hash(b[union])), k
    return union


def self_test():
    old = dict(tags=np.array(['train','heldout']),rep=np.array([0,0,0,1]),
        side=np.array([0,0,0,0]),tick=np.array([60,100,700,100]),split=np.array([0,0,0,1]),
        deck_id=np.array([1,1,1,1]),off=np.array([0,1,2,3,4]),v3val=np.array([False]*3+[True]),
        y_gate=np.array([0,1,0,1]),y_xy=np.array([[.1,.2],[.2,.3],[.3,.4],[.4,.5]],np.float32))
    p=dict(pool_rows=np.arange(3),window_offsets=np.array([0,3]),window_rows=np.arange(3),
        defensive_rows=np.arange(3),other_rows=np.array([],np.int64),window_rep=np.array([0]),
        window_side=np.array([0]),window_tick=np.array([100]),window_defensive=np.array([True]))
    m=dict(source_rows=np.arange(3),corrected_rows=np.arange(3))
    before=dict(feature_version=4,card_vocab=['x-bow'],decks=[dict(id=1,cards=[
        'ice-wizard','knight','rocket','skeletons','tesla','the-log','tornado','x-bow'])],
        grid='lattice',shift_ticks=0,public_observation=True,public_timing_contract='causal',opponent_elixir='counter')
    after=dict(before,feature_version=5,body_identity_contract='catalog_spawner_bodies_v1')
    hashes={k:dict(pool=array_hash(v[:3]),sequence_union=array_hash(v[:3])) for k,v in old.items() if k.startswith('y_')}
    args=[old,copy.deepcopy(old),p,copy.deepcopy(p),m,hashes,before,after]
    check(*args)
    # A second positive includes duplicated decision keys; row ordinal remains authoritative.
    duplicate=copy.deepcopy(args); duplicate[0]['tick'][0]=100; duplicate[1]['tick'][0]=100
    check(*duplicate)
    rejected=[]
    def reject(name,mutate):
        bad=copy.deepcopy(args); mutate(bad)
        try: check(*bad)
        except (AssertionError,KeyError,ValueError,IndexError): rejected.append(name)
        else: raise AssertionError('Accepted corruption: '+name)
    for k in ('source_rows','corrected_rows'):
        reject('reordered_'+k,lambda a,k=k:a[4].__setitem__(k,a[4][k][::-1]))
        reject('missing_'+k,lambda a,k=k:a[4].__setitem__(k,a[4][k][:-1]))
    reject('duplicate_mapping',lambda a:a[4]['corrected_rows'].__setitem__(0,1))
    for k in ('rep','side','tick','split','deck_id','off','v3val','y_gate','y_xy'):
        reject('changed_'+k,lambda a,k=k:a[1][k].__setitem__(0,a[1][k][0]+1))
    reject('changed_tag',lambda a:a[1]['tags'].__setitem__(0,'other'))
    reject('heldout_mapping',lambda a:a[4]['corrected_rows'].__setitem__(0,3))
    reject('lost_reference',lambda a:a[3].__setitem__('window_rows',a[3]['window_rows'][:-1]))
    reject('future_input',lambda a:a[3].__setitem__('future_rocket',np.array([True])))
    reject('vocabulary',lambda a:a[7].__setitem__('card_vocab',['rocket']))
    reject('timing',lambda a:a[7].__setitem__('shift_ticks',1))
    reject('release_contract',lambda a:a[7].__setitem__('body_identity_contract','unknown'))
    print(json.dumps(dict(positive_checks=2,rejected_corruptions=rejected)))
    print('DEFENCE_BINDING_CONTROLS_PASS')


def main():
    out=HERE/'defence_crosswalk_verified.json'
    if out.exists(): raise ValueError('Fresh verification output required')
    path=HERE/'defence_crosswalk_bound.json'; report=json.loads(path.read_bytes())
    assert report['training_only'] and not report['trainable'] and report['activation']=='none'
    assert not any(report[k] for k in ('training_launched','predictions_run','policy_inputs_changed'))
    for path_string,expected in {**report['sources'],**report['artifacts']}.items():
        assert file_hash(ROOT/path_string)==expected,path_string
    prepared=json.loads((HERE/'defence_sequence_prepared.json').read_bytes())
    verified=json.loads((HERE/'defence_sequence_verified.json').read_bytes())
    assert verified['matched'] and verified['report_sha256']==file_hash(HERE/'defence_sequence_prepared.json')
    folder=ROOT/'icebow/data/bench/defence_sequence_v5_binding_20261005'
    with np.load(prepared['index_path'],allow_pickle=False) as z: original={k:z[k] for k in z.files}
    with np.load(folder/'index.npz',allow_pickle=False) as z: bound={k:z[k] for k in z.files}
    with np.load(folder/'crosswalk.npz',allow_pickle=False) as z: crosswalk={k:z[k] for k in z.files}
    assert file_hash(folder/'index.npz')==prepared['index_sha256']
    old_path=ROOT/'icebow/data/pipeline/gen_dataset_v31_public.npz'
    new_path=ROOT/report['dataset']
    with np.load(old_path,allow_pickle=False) as old,np.load(new_path,allow_pickle=False) as new:
        before,after=json.loads(str(old['meta'])),json.loads(str(new['meta']))
        union=check(old,new,original,bound,crosswalk,prepared['original_target_hashes'],before,after)
        assert report['original_target_hashes']==prepared['original_target_hashes']
        for k,h in report['identity_array_hashes'].items(): assert array_hash(new[k])==h,k
        rep,gate,card=new['rep'],new['y_gate'],new['y_card']
        summaries={}
        for name,ids in [('ordinary',bound['pool_rows']),('defensive',bound['defensive_rows']),
                         ('other',bound['other_rows']),('all_windows',union)]:
            plays=gate[ids]==1
            summaries[name]=dict(unique_rows=len(ids),play_rows=int(plays.sum()),
                wait_rows=int((gate[ids]==0).sum()),replays=len(np.unique(rep[ids])),
                cards=dict(Counter(after['card_vocab'][int(v)] for v in card[ids[plays]])))
        assert summaries==prepared['summaries']==verified['summaries']
        assert report['dataset_rows']==len(rep)
    counts=dict(mapped_pool_rows=len(bound['pool_rows']),sequence_rows=len(union),
        windows=len(bound['window_rep']),window_row_references=len(bound['window_rows']))
    assert all(report[k]==v for k,v in counts.items())
    result=dict(matched=True,report_sha256=file_hash(path),verifier_sha256=file_hash(__file__),
        **counts,summaries=summaries,original_target_arrays_verified=len(prepared['original_target_hashes']),
        trainable=False,training_launched=False,predictions_run=False,
        scope='Independent complete identity/label and explicit reference mapping; no new mechanics or model claim.')
    out.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(counts)); print('DEFENCE_BINDING_INDEPENDENT_PASS')


if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--self-test',action='store_true')
    if ap.parse_args().self_test: self_test()
    else: main()
