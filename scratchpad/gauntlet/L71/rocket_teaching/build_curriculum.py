"""CPU-only, hash-verified public replay annotation. No policy or live mutations."""
import argparse
from collections import Counter, defaultdict
import ctypes
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
import numpy as np
from pipeline.rocket_teaching import (ICEBOW, PublicBodies, catalog, card_key, groups,
                                     sampling_probabilities, scaled_stat, sequence_rows, sha)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', type=Path, default=ROOT/'icebow/data/pipeline/gen_dataset_v31_public.npz')
    ap.add_argument('--labels', type=Path, default=ROOT/'.foreman/codex_autopilot/runs/public_labels_full_reconstructed/labels.jsonl')
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--max-replays', type=int, default=0, help='Development sample only; not trainable.')
    a = ap.parse_args()
    try:
        ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x4000)
    except AttributeError:
        pass
    started = time.time()
    with np.load(a.data, allow_pickle=False) as z:
        meta = json.loads(str(z['meta']))
        v = {k: z[k] for k in ('tags', 'rep', 'side', 'tick', 'split', 'deck_id', 'y_gate', 'y_card')}
    if meta.get('feature_version') != 4 or meta.get('shift_ticks') != 0:
        raise ValueError('Requires the current unshifted public-v4 dataset')
    deck_ids = [d['id'] for d in meta['decks'] if set(d['cards']) == ICEBOW]
    if not deck_ids:
        raise ValueError('Missing Icebow deck')
    n = len(v['rep'])
    cohort = dict(pool=np.isin(v['deck_id'], deck_ids), opportunity=np.zeros(n, bool),
                  compact=np.zeros(n, bool), pull=np.zeros(n, bool), known=np.zeros(n, bool),
                  sequence=np.zeros(n, bool), combo=np.zeros(n, bool), finish=np.zeros(n, bool))
    by_rep = defaultdict(list)
    for i in np.flatnonzero(cohort['pool']):
        by_rep[int(v['rep'][i])].append(int(i))
    by_tag = defaultdict(list)
    for line in a.labels.open():
        e = json.loads(line)
        if e['card'] == 'rocket':
            by_tag[e['tag']].append(e)
    source_manifest = a.labels.with_name('manifest.json')
    sources = {s['tag']: s for s in json.loads(source_manifest.read_text())['sources']}
    a.out.mkdir(parents=True, exist_ok=False)
    counts = Counter()
    diagnostics = Counter()
    per_replay = []
    for number, (rep, indices) in enumerate(sorted(by_rep.items())):
        if a.max_replays and number >= a.max_replays:
            break
        tag = str(v['tags'][rep])
        source = sources[tag]
        path = ROOT / source['path']
        if sha(path) != source['sha256']:
            raise ValueError('Replay differs from reviewed labels: ' + tag)
        rec = json.loads(path.read_text())
        ids = np.array(indices)
        ticks, sides = v['tick'][ids], v['side'][ids]
        seq, combo, finish = sequence_rows(ticks, sides, by_tag[tag])
        cohort['sequence'][ids], cohort['combo'][ids], cohort['finish'][ids] = seq, combo, finish
        plays = []
        for index, e in enumerate(rec['log']):
            if e.get('accepted') and not e.get('skipped') and not e.get('ability') and e.get('card'):
                key = card_key(e['card'])
                # Public catalog cost; never opponent hand/elixir or future state.
                if key in catalog():
                    plays.append(dict(side=int(e['side']), card=key, tick=int(e.get('engine_tick', e['tick'])),
                                      x=e['x'], y=e['y'], cost=catalog()[key]['elixir'], deployment=index))
        level = rec.get('level')
        if level is None:
            counts['unknown_level_replays'] += 1
            continue
        rocket, log = scaled_stat('rocket', 'damage', level), scaled_stat('the-log', 'damage', level)
        observer = PublicBodies(plays, level)
        frames = {int(f['tick']): f for f in rec['frames'] + rec.get('play_frames', [])}
        requested = defaultdict(list)
        for i in ids:
            requested[int(v['tick'][i])].append(int(i))
        previous, previous_tick = [], -1000
        for tick in sorted(set(frames) | set(requested)):
            if tick in frames:
                previous = observer.read(frames[tick])
                previous_tick = tick
            for side in set(int(v['side'][i]) for i in requested.get(tick, [])):
                rows = [i for i in requested[tick] if int(v['side'][i]) == side]
                if tick - previous_tick > 20:
                    counts['stale_frame_rows'] += len(rows)
                    continue
                enemy = [b for b in previous if b['side'] != side]
                g = groups(enemy, rocket, log,
                           catalog()['rocket']['area_damage_radius_milli'],
                           catalog()['tornado']['spell']['radius_milli'])
                cohort['known'][rows] = True
                cohort['compact'][rows] = g['rocket_only']
                cohort['pull'][rows] = g['pull_candidate']
                cohort['opportunity'][rows] = g['rocket_only'] or g['pull_candidate']
        diagnostics.update(observer.stats)
        counts['replays'] += 1
        per_replay.append(dict(tag=tag, source_sha256=source['sha256'], rows=len(ids),
                               compact=int(cohort['compact'][ids].sum()), pull=int(cohort['pull'][ids].sum())))
        if (number + 1) % 100 == 0:
            print(f'[{time.time()-started:.0f}s] {number+1}/{len(by_rep)} replays', flush=True)
    summary = {}
    for name, mask in cohort.items():
        summary[name] = {split: dict(rows=int((mask & (v['split'] == code)).sum()),
                                    pro_play=int((mask & (v['split'] == code) & (v['y_gate'] == 1)).sum()),
                                    pro_wait=int((mask & (v['split'] == code) & (v['y_gate'] == 0)).sum()),
                                    cards=dict(Counter(meta['card_vocab'][int(c)] for c in
                                               v['y_card'][mask & (v['split'] == code) & (v['y_gate'] == 1)])))
                         for split, code in [('train', 0), ('validation', 1)]}
    np.savez_compressed(a.out/'cohorts.npz', **cohort)
    mass = {}
    if not a.max_replays:
        p = sampling_probabilities(cohort['pool'], cohort['opportunity'], cohort['sequence'], v['split'])
        mass = {k: float(p[m].sum()) for k, m in cohort.items()}
    manifest = dict(schema=1, dataset_sha256=sha(a.data), labels_sha256=sha(a.labels),
                    source_manifest_sha256=sha(source_manifest), cohorts_sha256=sha(a.out/'cohorts.npz'),
                    annotator_sha256=sha(ROOT/'pipeline/rocket_teaching.py'), builder_sha256=sha(__file__),
                    catalog_sha256=sha(ROOT/'research/ext/Royale/RoyaleSim/data/derived/cards.json'),
                    rows=n, expert_targets_unchanged=True, public_only=True, trainable=not bool(a.max_replays),
                    mixture={'ordinary_icebow': .8, 'geometric_opportunity': .1, 'expert_sequence': .1},
                    counts=dict(counts), exclusions_body_observations=dict(diagnostics),
                    cohorts=summary, sampling_mass=mass, replay_evidence=per_replay,
                    seconds=round(time.time()-started, 1),
                    limits=['Geometric candidates do not prove successful pull or damage.',
                            'Unsupported forms, shields, spawned children and ambiguous births excluded.',
                            'Known means fresh frame; exclusions can make false-negative cohorts.',
                            'Only real expert actions are supervised; no synthetic Rocket/Tornado targets.',
                            'Future outcomes affect offline sampling membership only.'])
    (a.out/'manifest.json').write_text(json.dumps(manifest, indent=2))
    print(json.dumps(dict(counts=dict(counts), sampling_mass=mass, cohorts=summary)), flush=True)
    print('ROCKET_CURRICULUM_BUILT', flush=True)


if __name__ == '__main__':
    main()
