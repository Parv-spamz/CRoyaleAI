"""Prepare historical training row references only; no model/optimizer imports."""
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
DATA = ROOT / 'icebow/data/pipeline/gen_dataset_v31_public.npz'
CONTEXT = ROOT / 'icebow/data/bench/context_teaching_20261005/cohorts.npz'
CACHE = ROOT / 'icebow/data/bench/defence_sequence_prep_20261005'
PRE_TICKS, POST_TICKS = 40, 600


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def array_sha(value):
    value = np.ascontiguousarray(value)
    h = hashlib.sha256()
    h.update(json.dumps([value.dtype.str, list(value.shape)]).encode())
    h.update(value.tobytes())
    return h.hexdigest()


def index_windows(rows, train_pool, windows):
    """Every original row within each interval; overlapping unions are unique."""
    grouped = defaultdict(list)
    for i in np.flatnonzero(train_pool):
        grouped[(int(rows['rep'][i]), int(rows['side'][i]))].append(int(i))
    for key, ids in grouped.items():
        ids = np.array(ids, dtype=np.int64)
        grouped[key] = ids[np.lexsort((ids, rows['tick'][ids]))]
    chunks, offsets = [], [0]
    unions = {False: set(), True: set()}
    for w in windows:
        ids = grouped[(w['rep'], w['side'])]
        times = rows['tick'][ids]
        lo = np.searchsorted(times, max(0, w['tick'] - PRE_TICKS), side='left')
        hi = np.searchsorted(times, w['tick'] + POST_TICKS, side='right')
        selected = ids[lo:hi]
        if not len(selected):
            raise ValueError('Empty bow window')
        chunks.append(selected)
        offsets.append(offsets[-1] + len(selected))
        unions[w['defensive']].update(map(int, selected))
    return dict(pool_rows=np.flatnonzero(train_pool).astype(np.int64),
                window_offsets=np.array(offsets, np.int64),
                window_rows=np.concatenate(chunks),
                defensive_rows=np.array(sorted(unions[True]), np.int64),
                other_rows=np.array(sorted(unions[False]), np.int64))


def main():
    output = HERE / 'defence_sequence_prepared.json'
    if output.exists() or CACHE.exists():
        raise ValueError('Fresh output required')
    audit_path = HERE / 'train_defence_cycle.json'
    verified_path = HERE / 'train_defence_cycle_verified.json'
    audit = json.loads(audit_path.read_bytes())
    verified = json.loads(verified_path.read_bytes())
    assert verified['matched'] and verified['report_sha256'] == sha(audit_path)
    assert audit['training_only'] and audit['no_model_calls']
    assert sha(DATA) == audit['source_dataset_sha256']
    assert sha(CONTEXT) == audit['context_sha256']
    window_path = Path(audit['rows_file'])
    assert sha(window_path) == audit['rows_sha256']
    with np.load(DATA, allow_pickle=False) as z:
        meta = json.loads(str(z['meta']))
        rows = {k: z[k] for k in ('rep', 'side', 'tick', 'split', 'tags', 'deck_id', 'y_gate', 'y_card')}
        target_keys = sorted(k for k in z.files if k.startswith('y_'))
    assert meta['feature_version'] == 4 and meta['shift_ticks'] == 0
    with np.load(CONTEXT, allow_pickle=False) as z:
        pool = z['pool']
    icebow = {'ice-wizard', 'knight', 'rocket', 'skeletons', 'tesla', 'the-log', 'tornado', 'x-bow'}
    deck_ids = [d['id'] for d in meta['decks'] if set(d['cards']) == icebow]
    assert np.array_equal(pool, np.isin(rows['deck_id'], deck_ids))
    train_pool = pool & (rows['split'] == 0)
    heldout_reps = set(rows['rep'][rows['split'] != 0])
    assert not set(rows['rep'][train_pool]) & heldout_reps
    tag_to_rep = {str(tag): i for i, tag in enumerate(rows['tags'])}
    assert len(tag_to_rep) == len(rows['tags'])
    windows, annotations = [], []
    with window_path.open(encoding='utf-8') as stream:
        for line in stream:
            w = json.loads(line)
            if w['window_s'] != 30:
                continue
            assert w['split'] == 0
            windows.append(dict(tag=w['tag'], rep=tag_to_rep[w['tag']], side=int(w['side']),
                                tick=int(w['tick']), defensive=w['kind'] == 'defensive'))
            annotations.append(w)
    assert len(windows) == verified['unique_bows']
    assert len({(w['rep'], w['side'], w['tick']) for w in windows}) == len(windows)
    packed = index_windows(rows, train_pool, windows)
    bow_card = meta['card_vocab'].index('x-bow')
    largest_gaps = []
    for j, w in enumerate(windows):
        ids = packed['window_rows'][packed['window_offsets'][j]:packed['window_offsets'][j+1]]
        anchors = (rows['tick'][ids] == w['tick']) & (rows['y_gate'][ids] == 1) & (rows['y_card'][ids] == bow_card)
        assert anchors.sum() == 1
        largest_gaps.append(int(np.diff(rows['tick'][ids]).max(initial=0)))
    union = np.union1d(packed['defensive_rows'], packed['other_rows'])
    target_hashes = {}
    # Bind original supervision without copying or transforming it into the index.
    with np.load(DATA, allow_pickle=False) as z:
        for key in target_keys:
            values = z[key]
            target_hashes[key] = dict(pool=array_sha(values[packed['pool_rows']]),
                                      sequence_union=array_sha(values[union]))
    packed.update(window_rep=np.array([w['rep'] for w in windows], np.int32),
                  window_side=np.array([w['side'] for w in windows], np.int8),
                  window_tick=np.array([w['tick'] for w in windows], np.int32),
                  window_defensive=np.array([w['defensive'] for w in windows], bool))
    summaries = {}
    for name, ids in (('ordinary', packed['pool_rows']), ('defensive', packed['defensive_rows']),
                      ('other', packed['other_rows']), ('all_windows', union)):
        play = rows['y_gate'][ids] == 1
        summaries[name] = dict(unique_rows=len(ids), play_rows=int(play.sum()),
            wait_rows=int((~play).sum()), replays=len(np.unique(rows['rep'][ids])),
            cards=dict(Counter(meta['card_vocab'][int(c)] for c in rows['y_card'][ids[play]])))
    descriptions = {}
    for kind in ('defensive', 'other'):
        group = [w for w in annotations if w['kind'] == kind]
        descriptions[kind] = dict(windows=len(group),
            no_princess_rocket=int(sum(not w['princess_rocket_ticks'] for w in group)),
            incomplete_coverage=int(sum(not w['full_coverage'] for w in group)),
            own_princess_damage=int(sum((w['own_princess_hp_drop'] or 0) > 0 for w in group)),
            unknown_princess_damage=int(sum(w['own_princess_hp_drop'] is None for w in group)))
    CACHE.mkdir(parents=True)
    np.savez_compressed(CACHE / 'index.npz', **packed)
    report = dict(schema=1, training_only=True, training_launched=False,
        trainable=False, release_block='N2 fresh-cohort and experiment-design prerequisites unmet',
        predictions_run=False, policy_inputs_changed=False,
        pre_ticks=PRE_TICKS, post_ticks=POST_TICKS, ticks_per_second=20,
        sources={str(p.relative_to(ROOT)): sha(p) for p in
                 (DATA, CONTEXT, audit_path, verified_path, Path(__file__), HERE/'DEFENCE_SEQUENCE_PREP_PLAN.md')},
        windows_sha256=sha(window_path), index_path=str(CACHE/'index.npz'),
        index_sha256=sha(CACHE/'index.npz'), original_target_hashes=target_hashes,
        summaries=summaries, descriptive_window_outcomes=descriptions,
        window_count=len(windows), window_row_references=len(packed['window_rows']),
        internal_row_gaps=dict(max_ticks=max(largest_gaps),
            windows_with_gap_over_one_second=sum(g > 20 for g in largest_gaps),
            note='Existing sparse supervision; no rows synthesized or windows excluded.'),
        defensive_other_shared_rows=len(np.intersect1d(packed['defensive_rows'], packed['other_rows'])),
        limitations=['Historical v4 training only; changed feature datasets require a validated row crosswalk and new binding.',
          'Original sparse per-decision rows and causal history retained; not a recurrent sequence model or complete timeline.',
          'Future outcomes are descriptive only, never selection criteria or model inputs.',
          'Overlapping windows are not independent trials; unions avoid repeated-row weighting.',
          'No successor training, sampling ratio or acceptance claim.'])
    output.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(dict(windows=len(windows), summaries=summaries, outcomes=descriptions)), flush=True)
    print('DEFENCE_SEQUENCE_INDEX_PREPARED')


if __name__ == '__main__':
    main()
