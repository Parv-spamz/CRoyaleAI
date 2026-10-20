"""Reproduce then patch public body identities, preserving every expert target.

Only class/form token arrays and metadata can change. All other NPZ members are
copied byte for byte. A nonzero --limit is a smoke artifact and cannot be trained.
No pipeline source mutation, GPU work or live state changes.
"""
import argparse
from collections import Counter, defaultdict
import ctypes
import hashlib
import json
from pathlib import Path
import shutil
import sys
import time
from zipfile import ZipFile, ZIP_DEFLATED

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from pipeline import vocab
from pipeline.native_recording import tag_native_recording
from pipeline.obs_contract import from_engine, load_deck, to_tokens, to_unit_forms
from pipeline.public_observation import body_only_board
from pipeline.rocket_teaching import sha
from body_identity import resolve, FAMILIES, CATALOG

DATA = ROOT/'icebow/data/pipeline/gen_dataset_v31_public.npz'
SOURCES = ROOT/'.foreman/codex_autopilot/runs/public_labels_full_reconstructed/manifest.json'


def corrected_frame(frame):
    entities, forms = [], []
    for entity, form in zip(frame['entities'], frame['unit_forms']):
        if not isinstance(entity, list):
            raise ValueError('This reconstruction requires the verified native list schema')
        row = list(entity)
        if row[4] > 0 and row[3] != '-1':
            identity = resolve(row[3], row[5], form)
            old = vocab.engine_unit_id(row[3], row[5])
            if identity.cls != old or identity.form != form:
                if identity.cls is None:
                    raise ValueError('Correction must not delete a body')
                row[3] = vocab.UNIT_VOCAB[identity.cls]
                form = identity.form
        entities.append(row)
        forms.append(form)
    return dict(frame, entities=entities, unit_forms=forms)


def tokens(frame, side, deck):
    bs = body_only_board(from_engine(frame, side, deck, unmapped=set(), feature_version=4))
    tok, mask, _ = to_tokens(bs)
    return tok[mask], to_unit_forms(bs)[mask]


def digest_array(a):
    h = hashlib.sha256()
    for lo in range(0, len(a), 100000):
        h.update(a[lo:lo+100000].tobytes())
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--limit', type=int, default=0)
    args = ap.parse_args()
    if args.limit < 0 or args.out.exists():
        raise ValueError('Fresh output directory and nonnegative limit required')
    args.out.mkdir(parents=True)
    try:
        ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x4000)
    except AttributeError:
        pass
    start = time.time()
    hashes = {'dataset': sha(DATA), 'sources': sha(SOURCES), 'catalog': sha(CATALOG),
              'resolver': sha(Path(__file__).with_name('body_identity.py')), 'builder': sha(__file__)}
    sources = {x['tag']: x for x in json.loads(SOURCES.read_text())['sources']}
    print('Extracting immutable token source', flush=True)
    with ZipFile(DATA) as z:
        with z.open('tok.npy') as src, (args.out/'original_tok.npy').open('wb') as dst:
            shutil.copyfileobj(src, dst, 16 << 20)
    shutil.copyfile(args.out/'original_tok.npy', args.out/'corrected_tok.npy')
    original = np.load(args.out/'original_tok.npy', mmap_mode='r')
    modified = np.load(args.out/'corrected_tok.npy', mmap_mode='r+')
    with np.load(DATA) as z:
        values = {k: z[k] for k in ('off', 'rep', 'tags', 'tick', 'side', 'y_gate', 'unit_form', 'meta')}
    old_forms = values['unit_form']
    forms = old_forms.copy()
    offsets = values['off']
    affected_tokens = np.flatnonzero(np.isin(original[:, 0], [vocab.unit_id(k) for k in FAMILIES]))
    affected_rows = np.unique(np.searchsorted(offsets, affected_tokens, side='right')-1)
    if not len(affected_rows):
        raise ValueError('Missing positive control: no parent-labelled tokens')
    by_replay = defaultdict(list)
    for row in affected_rows:
        by_replay[int(values['rep'][row])].append(int(row))
    entries = sorted(by_replay.items())
    if args.limit:
        entries = entries[:args.limit]
    stats = Counter()
    evidence = []
    changed_rows = []
    deck = load_deck('icebow')  # token identities do not use own hand/deck
    print(f'Reconstructing {len(entries)} replays / {len(affected_rows)} affected rows', flush=True)
    for number, (rep, rows) in enumerate(entries):
        tag = str(values['tags'][rep])
        src = sources[tag]
        path = ROOT/src['path']
        if sha(path) != src['sha256']:
            raise ValueError('Source hash mismatch: ' + tag)
        rec = tag_native_recording(json.loads(path.read_text()), {})
        frames = defaultdict(list)
        for source, gate in (('frames', 0), ('play_frames', 1)):
            for frame in rec[source]:
                frames[int(frame['tick']), gate].append(frame)
        cache = {}
        local = Counter()
        for row in rows:
            start_tok, end_tok = offsets[row:row+2]
            old = original[start_tok:end_tok]
            old_f = old_forms[start_tok:end_tok]
            key = int(values['tick'][row]), int(values['y_gate'][row]), int(values['side'][row])
            if key not in cache:
                cache[key] = []
                for frame in frames[key[:2]]:
                    base_tok, base_f = tokens(frame, key[2], deck)
                    new_tok, new_f = tokens(corrected_frame(frame), key[2], deck)
                    if base_tok.shape != new_tok.shape or not np.array_equal(base_tok[:, 1:], new_tok[:, 1:]):
                        raise ValueError('Correction changed non-identity columns: ' + tag)
                    cache[key].append((base_tok, base_f, new_tok, new_f))
            matches = [(new_t, new_f) for base_t, base_f, new_t, new_f in cache[key]
                       if np.array_equal(old, base_t) and np.array_equal(old_f, base_f)]
            if not matches:
                raise ValueError(f'Original row not reproduced: tag={tag} row={row} key={key}')
            if any(not np.array_equal(matches[0][0], t) or not np.array_equal(matches[0][1], f)
                   for t, f in matches[1:]):
                raise ValueError('Ambiguous frame reconstruction: ' + tag)
            new, new_f = matches[0]
            changed = (old[:, 0] != new[:, 0]) | (old_f != new_f)
            local['reproduced_rows'] += 1
            if changed.any():
                changed_rows.append(row)
                local['changed_rows'] += 1
                local['changed_tokens'] += int(changed.sum())
                local['changed_forms'] += int((old_f != new_f).sum())
                for cid in old[changed, 0]:
                    local['from:' + vocab.UNIT_VOCAB[int(cid)]] += 1
                modified[start_tok:end_tok] = new
                forms[start_tok:end_tok] = new_f
        evidence.append(dict(tag=tag, source_sha256=src['sha256'], **dict(local)))
        stats.update(local)
        if (number+1) % 100 == 0:
            print(f'[{time.time()-start:.0f}s] {number+1}/{len(entries)} {dict(stats)}', flush=True)
    modified.flush()
    np.save(args.out/'corrected_forms.npy', forms, allow_pickle=False)
    np.save(args.out/'changed_rows.npy', np.asarray(changed_rows, np.int64), allow_pickle=False)
    metadata = json.loads(str(values['meta']))
    metadata.update(feature_version=5, body_identity_contract='catalog_spawner_bodies_v1',
                    body_identity_families=sorted(FAMILIES), body_identity_source_sha256=hashes['dataset'],
                    trainable=args.limit == 0, spawner_identity_hashes=hashes)
    destination = args.out/'gen_dataset_v5_public.npz'
    preserved = {}
    print('Writing corrected archive; copying all other array members unchanged', flush=True)
    with ZipFile(DATA) as source, ZipFile(destination, 'w', compression=ZIP_DEFLATED, compresslevel=3, allowZip64=True) as target:
        for info in source.infolist():
            with target.open(info.filename, 'w', force_zip64=True) as dst:
                if info.filename == 'tok.npy':
                    np.lib.format.write_array(dst, modified, allow_pickle=False)
                elif info.filename == 'unit_form.npy':
                    np.lib.format.write_array(dst, forms, allow_pickle=False)
                elif info.filename == 'meta.npy':
                    np.lib.format.write_array(dst, np.asarray(json.dumps(metadata)), allow_pickle=False)
                else:
                    h = hashlib.sha256()
                    with source.open(info) as src:
                        for block in iter(lambda: src.read(16 << 20), b''):
                            h.update(block)
                            dst.write(block)
                    preserved[info.filename] = h.hexdigest()
    if sha(Path(__file__).with_name('body_identity.py')) != hashes['resolver'] or sha(CATALOG) != hashes['catalog']:
        raise ValueError('Source changed during reconstruction')
    report = dict(trainable=args.limit == 0, feature_version=5, hashes=hashes,
                  output=str(destination), output_sha256=sha(destination),
                  preserved_members_sha256=preserved, stats=dict(stats),
                  expected_affected_rows=len(affected_rows), replay_evidence=evidence,
                  changed_rows_sha256=sha(args.out/'changed_rows.npy'),
                  corrected_tokens_sha256=digest_array(modified), corrected_forms_sha256=digest_array(forms),
                  seconds=time.time()-start)
    if args.limit == 0 and stats['reproduced_rows'] != len(affected_rows):
        raise ValueError('Incomplete reconstruction')
    (args.out/'manifest.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(dict(stats=report['stats'], trainable=report['trainable'], seconds=report['seconds'])))
    print('SPAWNER_DATASET_RECONSTRUCTION_PASS', flush=True)


if __name__ == '__main__':
    main()
