"""Independent interval/label oracle; no simulation, inference or optimization."""
import argparse
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def digest_array(value):
    h = hashlib.sha256(json.dumps([value.dtype.str, list(value.shape)]).encode())
    h.update(value.tobytes(order='C'))
    return h.hexdigest()


def check_membership(rows, pool, bows, packed):
    required = {'pool_rows', 'window_offsets', 'window_rows', 'defensive_rows', 'other_rows',
                'window_rep', 'window_side', 'window_tick', 'window_defensive'}
    assert set(packed) == required, 'Unexpected index fields'
    train = pool & (rows['split'] == 0)
    assert not set(rows['rep'][train]) & set(rows['rep'][rows['split'] != 0]), 'Replay split leakage'
    np.testing.assert_array_equal(packed['pool_rows'], np.flatnonzero(train))
    offsets = packed['window_offsets']
    assert len(offsets) == len(bows)+1 and offsets[0] == 0
    assert offsets[-1] == len(packed['window_rows']) and np.all(np.diff(offsets) > 0)
    seen = set()
    defensive, other = set(), set()
    # Independent group lookup avoids repeatedly scanning the whole dataset.
    by_pair = {}
    for i in np.flatnonzero(train):
        key = (int(rows['rep'][i]), int(rows['side'][i]))
        by_pair.setdefault(key, []).append(int(i))
    for j in range(len(bows)):
        key = tuple(int(packed[k][j]) for k in ('window_rep', 'window_side', 'window_tick'))
        assert key in bows and key not in seen
        seen.add(key)
        assert bool(packed['window_defensive'][j]) == bows[key]
        rep, side, tick = key
        candidates = by_pair.get((rep,side), [])
        # Intentionally no import of builder, searchsorted, or audit outcome data.
        expect = [int(i) for i in candidates if max(0, tick-40) <= int(rows['tick'][i]) <= tick+600]
        expect.sort(key=lambda i: (int(rows['tick'][i]), i))
        actual = packed['window_rows'][offsets[j]:offsets[j+1]]
        np.testing.assert_array_equal(actual, expect)
        assert len(actual) == len(set(map(int, actual)))
        (defensive if bows[key] else other).update(expect)
    assert seen == set(bows)
    np.testing.assert_array_equal(packed['defensive_rows'], sorted(defensive))
    np.testing.assert_array_equal(packed['other_rows'], sorted(other))
    return np.array(sorted(defensive | other), dtype=np.int64)


def check_targets(z, packed, union, recorded):
    assert set(recorded) == {k for k in z if k.startswith('y_')}
    for key, hashes in recorded.items():
        values = z[key]
        assert hashes == dict(pool=digest_array(values[packed['pool_rows']]),
                              sequence_union=digest_array(values[union])), key


def self_test():
    rows = dict(rep=np.array([0]*8+[1, 2]), side=np.array([0]*7+[1, 0, 0]),
                tick=np.array([59, 60, 100, 300, 700, 701, 750, 100, 100, 100]),
                split=np.array([0]*9+[1]))
    pool = np.array([True]*8+[False, True])
    bows = {(0, 0, 100): True, (0, 0, 300): False}
    p = dict(pool_rows=np.arange(8), window_offsets=np.array([0,4,8]),
        window_rows=np.array([1,2,3,4,3,4,5,6]), defensive_rows=np.array([1,2,3,4]),
        other_rows=np.array([3,4,5,6]), window_rep=np.array([0,0]), window_side=np.array([0,0]),
        window_tick=np.array([100,300]), window_defensive=np.array([True,False]))
    union = check_membership(rows, pool, bows, p)
    targets = dict(y_gate=np.array([0,0,1,1,0,0,0,1,0,1]),
                   y_xy=np.arange(20, dtype=np.float32).reshape(10,2))
    bound = {k:dict(pool=digest_array(v[p['pool_rows']]), sequence_union=digest_array(v[union]))
             for k,v in targets.items()}
    check_targets(targets, p, union, bound)
    failures = []
    def rejected(name, fn):
        try:
            fn()
        except (AssertionError, ValueError, IndexError):
            failures.append(name)
        else:
            raise AssertionError('Corruption accepted: '+name)
    for name, index in [('before_left_boundary',0), ('after_right_boundary',5),
                        ('wrong_side',7), ('outside_pool',8), ('heldout_row',9), ('duplicate_row',2)]:
        bad = copy.deepcopy(p)
        bad['window_rows'][0] = index
        rejected(name, lambda bad=bad: check_membership(rows, pool, bows, bad))
    bad = copy.deepcopy(p); bad['defensive_rows'] = bad['defensive_rows'][:-1]
    rejected('omitted_union_row', lambda: check_membership(rows, pool, bows, bad))
    bad = copy.deepcopy(p); bad['future_rocket'] = np.ones(2)
    rejected('unexpected_future_input', lambda: check_membership(rows, pool, bows, bad))
    bad_bows = dict(bows); bad_bows[(0,0,100)] = False
    rejected('changed_bow_class', lambda: check_membership(rows, pool, bad_bows, p))
    bad_rows = copy.deepcopy(rows); bad_rows['split'][7] = 1
    rejected('within_replay_split_leak', lambda: check_membership(bad_rows, pool, bows, p))
    for key in targets:
        damaged = copy.deepcopy(targets); damaged[key][2] += 1
        rejected('altered_'+key, lambda damaged=damaged: check_targets(damaged, p, union, bound))
    print(json.dumps(dict(positive_checks=2, rejected_corruptions=failures)))
    print('DEFENCE_SEQUENCE_CONTROLS_PASS')


def main():
    out = HERE/'defence_sequence_verified.json'
    if out.exists():
        raise ValueError('Fresh output required')
    report_path = HERE/'defence_sequence_prepared.json'
    report = json.loads(report_path.read_bytes())
    assert report['training_only'] and not report['trainable']
    assert not report['training_launched'] and not report['predictions_run']
    assert report['pre_ticks'] == 40 and report['post_ticks'] == 600
    for path, expected in report['sources'].items():
        assert sha(ROOT/path) == expected, path
    index_path = Path(report['index_path'])
    assert sha(index_path) == report['index_sha256']
    data = ROOT/'icebow/data/pipeline/gen_dataset_v31_public.npz'
    with np.load(data, allow_pickle=False) as z:
        meta = json.loads(str(z['meta']))
        rows = {k:z[k] for k in ('rep','side','tick','split','deck_id','tags','y_gate','y_card')}
    icebow = {'ice-wizard','knight','rocket','skeletons','tesla','the-log','tornado','x-bow'}
    deck_ids = [d['id'] for d in meta['decks'] if set(d['cards']) == icebow]
    pool = np.isin(rows['deck_id'], deck_ids)
    train = pool & (rows['split'] == 0)
    allowed = {(str(rows['tags'][r]),int(s)) for r,s in zip(rows['rep'][train],rows['side'][train])}
    tag_to_rep = {str(tag):i for i,tag in enumerate(rows['tags'])}
    audit = json.loads((HERE/'train_defence_cycle.json').read_bytes())
    label_path = ROOT/'.foreman/codex_autopilot/runs/public_labels_full_reconstructed/labels.jsonl'
    assert sha(label_path) == audit['labels_sha256']
    bows = {}
    with label_path.open(encoding='utf-8') as stream:
        for line in stream:
            v = json.loads(line)
            if v['card'] != 'x-bow' or (v['tag'],v['side']) not in allowed:
                continue
            key = (tag_to_rep[v['tag']],int(v['side']),int(v['tick']))
            assert key not in bows and isinstance(v['defensive_xbow'],bool)
            bows[key] = v['defensive_xbow']
    with np.load(index_path, allow_pickle=False) as z:
        packed = {k:z[k] for k in z.files}
    union = check_membership(rows, pool, bows, packed)
    with np.load(data, allow_pickle=False) as z:
        check_targets(z, packed, union, report['original_target_hashes'])
    summaries = {}
    for name, ids in (('ordinary', packed['pool_rows']),('defensive',packed['defensive_rows']),
                      ('other',packed['other_rows']),('all_windows',union)):
        gates = rows['y_gate'][ids]
        summaries[name] = dict(unique_rows=len(ids), play_rows=int((gates==1).sum()),
            wait_rows=int((gates==0).sum()), replays=len(np.unique(rows['rep'][ids])),
            cards=dict(Counter(meta['card_vocab'][int(rows['y_card'][i])] for i in ids if rows['y_gate'][i]==1)))
    assert report['summaries'] == summaries
    assert report['window_count'] == len(bows)
    assert report['window_row_references'] == len(packed['window_rows'])
    assert report['defensive_other_shared_rows'] == len(np.intersect1d(packed['defensive_rows'],packed['other_rows']))
    gaps = []
    for j in range(len(bows)):
        ids = packed['window_rows'][packed['window_offsets'][j]:packed['window_offsets'][j+1]]
        times = [int(rows['tick'][i]) for i in ids]
        gaps.append(max((b-a for a,b in zip(times,times[1:])),default=0))
    assert report['internal_row_gaps']['max_ticks'] == max(gaps)
    assert report['internal_row_gaps']['windows_with_gap_over_one_second'] == sum(g > 20 for g in gaps)
    result = dict(matched=True, report_sha256=sha(report_path), verifier_sha256=sha(__file__),
        labels_sha256=sha(label_path), original_target_arrays_verified=len(report['original_target_hashes']),
        window_count=len(bows), window_row_references=len(packed['window_rows']),
        unique_sequence_rows=len(union), summaries=summaries,
        scope='Independent original-label join, row intervals, unions and unchanged source supervision; no model claim.')
    out.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(dict(windows=len(bows), unique_sequence_rows=len(union), matched=True)))
    print('DEFENCE_SEQUENCE_INDEPENDENTLY_VERIFIED')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--self-test',action='store_true')
    if ap.parse_args().self_test:
        self_test()
    else:
        main()
