"""Bind the existing training-only index to verified corrected features; no training."""
import hashlib
import json
from pathlib import Path
import shutil

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
OLD = ROOT/'icebow/data/pipeline/gen_dataset_v31_public.npz'
NEW = ROOT/'icebow/data/bench/spawner_identity_20261005/gen_dataset_v5_public.npz'
CORRECTION = NEW.with_name('manifest.json')
DEST = ROOT/'icebow/data/bench/defence_sequence_v5_binding_20261005'
CHECKS = ROOT/'scratchpad/gauntlet/L71/integration/checks'
IDENTITY = ('tags', 'rep', 'side', 'tick', 'split', 'deck_id', 'off', 'v3val')
CONTRACTS = ('card_vocab', 'decks', 'grid', 'shift_ticks', 'public_observation',
             'public_timing_contract', 'opponent_elixir')


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def digest(a):
    h = hashlib.sha256(json.dumps([a.dtype.str, list(a.shape)]).encode())
    h.update(a.tobytes(order='C'))
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def main():
    out = HERE/'defence_crosswalk_bound.json'
    if out.exists() or DEST.exists():
        raise ValueError('Fresh binding output required')
    prepared_path = HERE/'defence_sequence_prepared.json'
    verified_path = HERE/'defence_sequence_verified.json'
    prepared, verified, correction = map(read, (prepared_path, verified_path, CORRECTION))
    assert verified['matched'] and verified['report_sha256'] == sha(prepared_path)
    assert verified['verifier_sha256'] == sha(HERE/'verify_defence_sequences.py')
    assert prepared['training_only'] and not prepared['trainable']
    assert not prepared['training_launched'] and not prepared['predictions_run']
    old_sha, new_sha = sha(OLD), sha(NEW)
    assert old_sha == correction['hashes']['dataset'] == prepared['sources'][str(OLD.relative_to(ROOT))]
    assert new_sha == correction['output_sha256'] and correction['trainable']
    assert correction['stats']['reproduced_rows'] == correction['expected_affected_rows']
    receipts = []
    for name in ('spawner-final-data', 'l72-defence-sequence-verified'):
        receipt, log = CHECKS/(name+'.json'), CHECKS/(name+'.out')
        r = read(receipt)
        assert r['exit_code'] == 0 and r['matched'] and r['expected'] in log.read_text()
        assert r['output_sha256'] == hashlib.sha256(log.read_text().encode()).hexdigest()
        receipts.extend((receipt, log))
    source_index = Path(prepared['index_path'])
    assert sha(source_index) == prepared['index_sha256']
    with np.load(source_index, allow_pickle=False) as z:
        packed = {k:z[k] for k in z.files}
    pool = packed['pool_rows']
    union = np.union1d(packed['defensive_rows'], packed['other_rows'])
    assert np.isin(packed['window_rows'], pool).all() and np.isin(union, pool).all()
    identity_hashes, target_hashes = {}, {}
    with np.load(OLD, allow_pickle=False) as a, np.load(NEW, allow_pickle=False) as b:
        assert set(a.files) == set(b.files)
        am, bm = json.loads(str(a['meta'])), json.loads(str(b['meta']))
        assert am['feature_version'] == 4 and bm['feature_version'] == 5
        assert bm['body_identity_contract'] == 'catalog_spawner_bodies_v1'
        for k in CONTRACTS:
            assert am[k] == bm[k], k
        for k in IDENTITY:
            old, new = a[k], b[k]
            assert old.dtype == new.dtype
            np.testing.assert_array_equal(old, new, err_msg=k)
            identity_hashes[k] = digest(new)
        split, rep, deck = b['split'], b['rep'], b['deck_id']
        icebow = {'ice-wizard','knight','rocket','skeletons','tesla','the-log','tornado','x-bow'}
        deck_ids = [d['id'] for d in bm['decks'] if set(d['cards']) == icebow]
        np.testing.assert_array_equal(pool, np.flatnonzero((split == 0) & np.isin(deck, deck_ids)))
        assert not set(rep[pool]) & set(rep[split != 0])
        for k in sorted(k for k in a.files if k.startswith('y_')):
            old, new = a[k], b[k]
            assert old.dtype == new.dtype
            np.testing.assert_array_equal(old, new, err_msg=k)
            target_hashes[k] = dict(pool=digest(new[pool]), sequence_union=digest(new[union]))
        assert target_hashes == prepared['original_target_hashes']
        row_count = len(rep)
    DEST.mkdir(parents=True)
    shutil.copyfile(source_index, DEST/'index.npz')
    np.savez_compressed(DEST/'crosswalk.npz', source_rows=pool, corrected_rows=pool.copy())
    sources = (OLD, NEW, CORRECTION, prepared_path, verified_path, source_index,
               HERE/'verify_defence_sequences.py', Path(__file__), HERE/'DEFENCE_CROSSWALK_PLAN.md', *receipts)
    result = dict(schema=1, training_only=True, trainable=False, training_launched=False,
        predictions_run=False, policy_inputs_changed=False, activation='none',
        release_block='N2 fresh cohort, power/multiplicity and experiment design unmet',
        mode='strict verified positional identity; row ordinal retained as tie breaker',
        dataset=str(NEW.relative_to(ROOT)), feature_version=5, dataset_rows=row_count,
        mapped_pool_rows=len(pool), sequence_rows=len(union), windows=len(packed['window_rep']),
        window_row_references=len(packed['window_rows']),
        sources={str(p.relative_to(ROOT)):sha(p) for p in sources},
        artifacts={str(p.relative_to(ROOT)):sha(p) for p in (DEST/'index.npz', DEST/'crosswalk.npz')},
        identity_array_hashes=identity_hashes, original_target_hashes=target_hashes,
        public_contracts={k:bm[k] for k in CONTRACTS if k not in ('card_vocab','decks')},
        limitations=['Historical exposed training data, not fresh confirmation.',
          'No reordering support, outcome filtering, mixture selection, new labels or trainer activation.',
          'Reuses verified body-column mechanics; this check only binds sequence references.',
          'Original sparse rows, overlapping windows, unsuccessful defenses and truncated coverage retained.'])
    out.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({k:result[k] for k in ('mapped_pool_rows','sequence_rows','windows','trainable')}))
    print('DEFENCE_SEQUENCE_V5_BOUND_NOT_TRAINABLE')


if __name__ == '__main__':
    main()
