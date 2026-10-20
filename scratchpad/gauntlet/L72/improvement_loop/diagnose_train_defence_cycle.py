"""Training-only observational resource/sequence audit; no model or GPU calls."""
from bisect import bisect_right
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
HERE = Path(__file__).resolve().parent
DATA = ROOT/'icebow/data/pipeline/gen_dataset_v31_public.npz'
CONTEXT = ROOT/'icebow/data/bench/context_teaching_20261005/cohorts.npz'
LABELS = ROOT/'.foreman/codex_autopilot/runs/public_labels_full_reconstructed/labels.jsonl'
MANIFEST = LABELS.with_name('manifest.json')


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    out = HERE/'train_defence_cycle.json'
    cache = ROOT/'icebow/data/bench/defence_cycle_train_20261005'
    if out.exists() or cache.exists():
        raise ValueError('Fresh output required')
    with np.load(DATA) as z, np.load(CONTEXT) as c:
        split, rep, side, tags = [z[k] for k in ('split', 'rep', 'side', 'tags')]
        mask = (split == 0) & c['pool']
        allowed = {(str(tags[r]), int(s)) for r, s in zip(rep[mask], side[mask])}
        assert not set(rep[mask]).intersection(rep[split != 0])
    manifest = json.loads(MANIFEST.read_text())
    sources = {s['tag']: s for s in manifest['sources']}
    grouped = defaultdict(list)
    for line in LABELS.open():
        row = json.loads(line)
        if (row['tag'], row['side']) in allowed:
            grouped[row['tag']].append(row)
    cache.mkdir(parents=True)
    rows_file = cache/'windows.jsonl'
    summaries = defaultdict(Counter)
    evidence = []
    total = 0
    with rows_file.open('x') as stream:
        for tag, labels in sorted(grouped.items()):
            bows = [p for p in labels if p['card'] == 'x-bow']
            if not bows:
                continue
            src = sources[tag]
            path = ROOT/src['path']
            assert sha(path) == src['sha256']
            rec = json.loads(path.read_text())
            evidence.append(src)
            frames = {f['tick']: f for f in rec['frames']+rec.get('play_frames', [])}
            ticks = sorted(frames)
            plays = [p for p in rec['log'] if p.get('accepted') and 'side' in p]

            def at(t):
                i = bisect_right(ticks, t)-1
                return frames[ticks[i]] if i >= 0 and t-ticks[i] <= 10 else None

            for bow in bows:
                t, s = bow['tick'], bow['side']
                before = at(t)
                if bow['defensive_xbow'] is None:
                    raise ValueError('Uncalibrated defensive label')
                rockets = [p for p in labels if p['card'] == 'rocket' and p['side'] == s and p['tick'] > t]
                kind = 'defensive' if bow['defensive_xbow'] else 'other'
                phase = 'single' if t < 2400 else 'double' if t < 3600 else 'overtime'
                deep = kind == 'defensive' and abs(bow['y']-16000) >= 3000
                for seconds in (10, 30, 60):
                    end_tick = t+seconds*20
                    after = at(end_tick)
                    coverage = before is not None and after is not None and ticks[-1] >= end_tick
                    seq = [r for r in rockets if r['tick'] <= end_tick]
                    target_counts = Counter()
                    princess_casts = []
                    for rocket in seq:
                        targets = {tuple(h['tower']) for h in rocket['tower_hits']
                                   if h['tower'][1] == 'princess' and h['hp_confirmed']}
                        if targets:
                            target_counts.update(targets)
                            princess_casts.append(rocket['tick'])
                    charged = [p for p in plays if t <= p['tick'] <= end_tick]
                    known_costs = all(isinstance(p.get('cost'), (int, float)) for p in charged)
                    spending = [sum(p['cost'] for p in charged if p['side'] == j)
                                for j in (s, 1-s)] if known_costs and coverage else None
                    damage = None
                    if coverage:
                        initial = {(v[0], v[1], v[3], v[4]): v[5] for v in before['towers']
                                   if v[0] == s and v[1] == 'princess'}
                        final = {(v[0], v[1], v[3], v[4]): v[5] for v in after['towers']
                                 if v[0] == s and v[1] == 'princess'}
                        if len(initial) == 2 and initial.keys() == final.keys():
                            damage = sum(max(0, hp-final[k]) for k, hp in initial.items())
                    elixir = after['elixir'][s] if coverage and after.get('elixir') is not None else None
                    row = dict(tag=tag, side=s, tick=t, split=0, kind=kind, deep=deep,
                        phase=phase, window_s=seconds, full_coverage=coverage,
                        own_elixir_before=before['elixir'][s] if before and before.get('elixir') is not None else None,
                        princess_rocket_ticks=princess_casts,
                        repeated_same_princess=any(n >= 2 for n in target_counts.values()),
                        rocket_impact_unknown=sum(r['tower_rocket'] is None for r in seq),
                        spending_own_opponent=spending, own_elixir_after=elixir,
                        own_princess_hp_drop=damage)
                    stream.write(json.dumps(row)+'\n')
                    total += 1
                    for key in (f'{kind}/{seconds}s', f'{kind}/{phase}/{seconds}s',
                                f'{kind}/deep={deep}/{seconds}s'):
                        summary = summaries[key]
                        summary['windows'] += 1
                        summary['covered'] += coverage
                        if coverage:
                            summary['with_princess_rocket'] += bool(princess_casts)
                            summary['princess_rockets'] += len(princess_casts)
                            summary['same_tower_repeat'] += row['repeated_same_princess']
                            summary['unknown_rocket_impacts'] += row['rocket_impact_unknown']
                            if spending is not None:
                                summary['spending_known'] += 1
                                summary['own_spent'] += spending[0]
                                summary['opponent_spent'] += spending[1]
                            if damage is not None:
                                summary['damage_known'] += 1
                                summary['own_princess_hp_drop'] += damage
                                summary['damage_free'] += damage == 0
                            if elixir is not None:
                                summary['elixir_known'] += 1
                                summary['own_elixir_after_sum'] += elixir
    result = dict(training_only=True, no_model_calls=True, windows=total,
        replay_count=len(evidence), train_pairs=len(allowed), source_dataset_sha256=sha(DATA),
        context_sha256=sha(CONTEXT), labels_sha256=sha(LABELS), source_manifest_sha256=sha(MANIFEST),
        script_sha256=sha(__file__), plan_sha256=sha(HERE/'DEFENCE_CYCLE_PLAN.md'),
        rows_file=str(rows_file), rows_sha256=sha(rows_file), sources=evidence,
        summaries={k:dict(v) for k,v in summaries.items()},
        limitations=['Training-only associations, no causal/gameplay improvement claim.',
          'Repeated overlapping windows are not independent trials; cluster future inference by replay.',
          'Spending balance is not measured positive elixir trades or attribution to X-Bow.',
          'HP-confirmed tower labels can include concurrent damage; no exact damage attribution.',
          'Missing coverage/costs/impacts remain unknown. No new targets or policy rules.'])
    out.write_text(json.dumps(result, indent=2))
    print(json.dumps(dict(replays=len(evidence), windows=total,
                         primary={k:dict(v) for k,v in summaries.items() if k in ('defensive/30s','other/30s')})))
    print('TRAIN_DEFENCE_CYCLE_AUDIT_COMPLETE')


if __name__ == '__main__':
    main()
