"""Independent training membership, label join and primary-window recount."""
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    path = HERE/'train_defence_cycle.json'
    report = json.loads(path.read_text())
    output = HERE/'train_defence_cycle_verified.json'
    assert not output.exists()
    data = ROOT/'icebow/data/pipeline/gen_dataset_v31_public.npz'
    assert sha(data) == report['source_dataset_sha256']
    rows_path = Path(report['rows_file'])
    assert sha(rows_path) == report['rows_sha256']
    with np.load(data) as z:
        train_tags = set(map(str, z['tags'][np.unique(z['rep'][z['split'] == 0])]))
        heldout_tags = set(map(str, z['tags'][np.unique(z['rep'][z['split'] != 0])]))
    labels_path = ROOT/'.foreman/codex_autopilot/runs/public_labels_full_reconstructed/labels.jsonl'
    assert sha(labels_path) == report['labels_sha256']
    labels = {}
    for line in labels_path.open():
        label = json.loads(line)
        if label['tag'] in train_tags:
            labels[(label['tag'],label['side'],label['tick'],label['card'])] = label
    groups = defaultdict(list)
    summary = defaultdict(Counter)
    for line in rows_path.open():
        row = json.loads(line)
        assert row['tag'] in train_tags and row['tag'] not in heldout_tags and row['split'] == 0
        key = (row['tag'],row['side'],row['tick'])
        groups[key].append(row['window_s'])
        bow = labels[key+('x-bow',)]
        assert row['kind'] == ('defensive' if bow['defensive_xbow'] else 'other')
        targets = Counter()
        for tick in row['princess_rocket_ticks']:
            assert row['tick'] < tick <= row['tick']+row['window_s']*20
            rocket = labels[(row['tag'],row['side'],tick,'rocket')]
            hits = {tuple(h['tower']) for h in rocket['tower_hits']
                    if h['tower'][1] == 'princess' and h['hp_confirmed']}
            assert hits
            targets.update(hits)
        assert row['repeated_same_princess'] == any(n >= 2 for n in targets.values())
        if row['window_s'] != 30:
            continue
        count = summary[row['kind']]
        count['windows'] += 1
        if row['full_coverage']:
            count['covered'] += 1
            count['with_princess_rocket'] += bool(row['princess_rocket_ticks'])
            count['same_tower_repeat'] += row['repeated_same_princess']
            if row['spending_own_opponent'] is not None:
                count['spending_known'] += 1
                count['own_spent'] += row['spending_own_opponent'][0]
                count['opponent_spent'] += row['spending_own_opponent'][1]
            count['damage_known'] += row['own_princess_hp_drop'] is not None
            count['own_princess_hp_drop'] += row['own_princess_hp_drop'] or 0
    assert all(sorted(v) == [10,30,60] for v in groups.values())
    assert len(groups)*3 == report['windows']
    for kind, count in summary.items():
        assert all(report['summaries'][kind+'/30s'][key] == value for key,value in count.items())
    output.write_text(json.dumps(dict(report_sha256=sha(path), verifier_sha256=sha(Path(__file__)),
        matched=True, unique_bows=len(groups), windows=report['windows'],
        primary={k:dict(v) for k,v in summary.items()},
        scope='Membership, raw cache recount and existing label joins. Not independent re-simulation or causal proof.'),indent=2))
    print(json.dumps(dict(unique_bows=len(groups),windows=report['windows'],matched=True)))
    print('TRAIN_DEFENCE_CYCLE_RECOUNT_VERIFIED')


if __name__ == '__main__':
    main()
