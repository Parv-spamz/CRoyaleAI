"""Read-only periodic-spawner identity/coverage/policy audit; CPU, one process."""
from collections import Counter, defaultdict
import ctypes
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
import numpy as np
from pipeline import vocab
from pipeline.obs_contract import catalog_card_form
from pipeline.rocket_teaching import card_key, scaled_stat, sha

HERE = Path(__file__).resolve().parent
CHILD = {'witch': 'skeletons', 'furnace': 'fire-spirit', 'night-witch': 'bats',
         'goblin-hut': 'spear-goblins', 'barbarian-hut': 'barbarians', 'tombstone': 'skeletons'}


def class_name(cid):
    return None if cid is None else vocab.DETECTOR_CLASSES[cid] if cid < len(vocab.DETECTOR_CLASSES) else str(cid)


def role(parent, maximum, level):
    if maximum == scaled_stat(parent, 'hitpoints', level):
        return 'parent'
    if maximum == scaled_stat(CHILD[parent], 'hitpoints', level):
        return 'child'
    return 'unknown'


def main():
    try:
        ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x4000)
    except AttributeError:
        pass
    start = time.time()
    manifest_path = ROOT/'.foreman/codex_autopilot/runs/public_labels_full_reconstructed/manifest.json'
    sources = {s['tag']: s for s in json.loads(manifest_path.read_text())['sources']}
    teaching = json.loads((ROOT/'icebow/data/bench/rocket_teaching_20261004/manifest.json').read_text())
    cache_path = ROOT/'icebow/data/bench/decision_options_20261004/r1e.npz'
    cache = np.load(cache_path)
    with np.load(ROOT/'icebow/data/pipeline/gen_dataset_v31_public.npz') as z:
        tags = z['tags']; rep = z['rep'][cache['ids']]; ticks = z['tick'][cache['ids']]; sides = z['side'][cache['ids']]
    rows = defaultdict(list)
    for i, (r, t, s) in enumerate(zip(rep, ticks, sides)):
        rows[str(tags[r])].append((i, int(t), int(s)))
    masks = {k: np.zeros(len(ticks), bool) for k in CHILD}
    counts = defaultdict(Counter)
    classes = defaultdict(Counter)
    examples = defaultdict(list)
    timing = defaultdict(list)
    evidence = []
    for number, item in enumerate(teaching['replay_evidence']):
        tag = item['tag']; src = sources[tag]; path = ROOT/src['path']
        if sha(path) != src['sha256']:
            raise ValueError('Source changed')
        rec = json.loads(path.read_text())
        frames = {int(f['tick']): f for f in rec['frames'] + rec.get('play_frames', [])}
        seen = set(); observed = set(); births = defaultdict(list)
        requested = defaultdict(list)
        for row, tick, side in rows[tag]:
            requested[tick].append((row, side))
        for tick, frame in sorted(frames.items()):
            present = set()
            for e in frame['entities']:
                if not isinstance(e, list) or len(e) != 9 or e[4] <= 0 or e[-2] < 0:
                    continue
                name, form = catalog_card_form(e[-2]); parent = card_key(name) if name else None
                if parent not in CHILD:
                    continue
                s, x, y, native_name, hp, maximum, kind, cid, eid = e
                observed.add(parent)
                present.add((s, parent))
                r = role(parent, maximum, rec['level'])
                counts[parent]['observations:' + r] += 1
                ident = (int(s), int(eid))
                if ident in seen:
                    continue
                seen.add(ident)
                counts[parent]['bodies:' + r] += 1
                counts[parent]['max_hp:' + str(maximum)] += 1
                training_class = class_name(vocab.engine_unit_id(native_name, maximum))
                live_class = class_name(vocab.engine_unit_id(name, maximum))
                classes[parent][f'{r}|native={training_class}|reader={live_class}|form={form}'] += 1
                if r == 'child':
                    births[(s, parent)].append(tick)
                    expected = class_name(vocab.unit_id(CHILD[parent].replace('-', '_')))
                    counts[parent]['child_native_wrong'] += int(training_class != expected)
                    counts[parent]['child_reader_wrong'] += int(live_class != expected)
                    if len(examples[parent]) < 6:
                        examples[parent].append(dict(tag=tag, tick=tick, entity=e, expected=expected,
                                                     native_class=training_class, reader_class=live_class))
            for row, side in requested.get(tick, []):
                for s, parent in present:
                    if s != side:
                        masks[parent][row] = True
        for parent in observed:
            counts[parent]['replays'] += 1
        for (_, parent), b in births.items():
            groups = []
            for tick in sorted(set(b)):
                if not groups or tick-groups[-1] > 20:
                    groups.append(tick)
            timing[parent].extend(np.diff(groups).tolist())
        evidence.append(dict(tag=tag, sha256=src['sha256'], observed=sorted(observed)))
        if (number+1) % 400 == 0:
            print(f'[{time.time()-start:.0f}s] {number+1}/2262 pro replays', flush=True)
    # Historical reader frames are public entity snapshots; never read hidden opponent elixir.
    live_counts = defaultdict(Counter); live_sources = []
    for path in sorted((ROOT/'scratchpad/gauntlet/L68/live_reader').glob('live_play_20261004_*.jsonl')):
        seen = set(); observed = set(); frames = 0
        with path.open(encoding='utf-8') as f:
            for line in f:
                try:
                    frame = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if frame.get('event') != 'frame':
                    continue
                frames += 1
                for e in frame.get('ents', []):
                    if len(e) != 8 or e[3] < 0 or e[4] <= 0 or e[0] == frame['my_side']:
                        continue
                    name, form = catalog_card_form(e[3]); parent = card_key(name) if name else None
                    if parent not in CHILD or (e[0], e[-1]) in seen:
                        continue
                    seen.add((e[0], e[-1])); observed.add(parent)
                    roles = set()
                    for level in range(9, 17):
                        try:
                            roles.add(role(parent, e[5], level))
                        except ValueError:
                            pass
                    known = roles - {'unknown'}
                    r = next(iter(known)) if len(known) == 1 else 'unknown'
                    live_counts[parent]['bodies:'+r] += 1
                    live_counts[parent]['max_hp:'+str(e[5])] += 1
                    if r == 'child':
                        got = class_name(vocab.engine_unit_id(name, e[5]))
                        want = CHILD[parent].replace('-', '_')
                        live_counts[parent]['child_wrong'] += int(got != want)
            for parent in observed:
                live_counts[parent]['matches_with_frames'] += 1
        if frames:
            live_sources.append(dict(path=str(path.relative_to(ROOT)), bytes=path.stat().st_size,
                                     sha256=sha(path), frames=frames))
    predicted = np.where(cache['allowed'], cache['logits'], -np.inf).argmax(1)
    valid = cache['y_play'].astype(bool) & (cache['y_slot'] >= 0) & cache['allowed'].any(1)
    def metrics(mask):
        use = valid & mask
        return dict(pro_play_rows=int(use.sum()), pro_agreement=float((predicted[use] == cache['y_slot'][use]).mean()) if use.any() else None,
                    gate_pass=float((cache['gate'][use] > .35).mean()) if use.any() else None)
    any_spawner = np.logical_or.reduce(list(masks.values()))
    report = dict(source_manifest_sha256=sha(manifest_path), policy_cache_sha256=sha(cache_path),
                  pro_replays=len(evidence), native_counts={k: dict(v) for k, v in counts.items()},
                  body_classes={k: dict(v) for k, v in classes.items()}, examples=dict(examples),
                  reader_counts={k: dict(v) for k, v in live_counts.items()}, live_sources=live_sources,
                  heldout_policy={**{k: metrics(m) for k, m in masks.items()}, 'no_observed_spawner': metrics(~any_spawner)},
                  birth_group_gaps={k: dict(n=len(v), median_ticks=float(np.median(v)), common_ticks=Counter(v).most_common(8))
                                    for k, v in timing.items() if v},
                  limitations=['Role inference uses exact catalog max-HP matches; other bodies remain unknown.',
                               'Held-out agreement is observational, not a causal win comparison.',
                               'Birth-group gaps combine play generations and cadence; not an exact spawn-clock measurement.',
                               'Only historical logs with saved frames are covered; no missed frame becomes zero spawns.'],
                  seconds=round(time.time()-start, 1))
    HERE.mkdir(parents=True, exist_ok=True)
    (HERE/'audit.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(dict(native=report['native_counts'], reader=report['reader_counts'], policy=report['heldout_policy'])), flush=True)
    print('SPAWNER_AUDIT_COMPLETE', flush=True)


if __name__ == '__main__':
    main()
