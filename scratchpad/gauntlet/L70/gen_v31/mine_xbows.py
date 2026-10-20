"""Public pre-cast X-Bow census; geometry is not strategic intent or hit truth.

Uses the already verified native Rocket manifest and candidate rows. No model,
live process, corpus, private opponent field or acceptance rule is modified.
"""
import argparse
from bisect import bisect_right
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import sys
import time

from mine_rockets import describe, tiebreak

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def xy(x, y, side):
    if side == 1:
        x, y = 18000-x, 32000-y
    return x / 18000, 1-y / 32000


def lane(x):
    return 'left' if x < .5 else 'right' if x > .5 else 'center'


def event_tick(p):
    return int(p['engine_tick'] if p.get('engine_tick') is not None else p['tick'])


def mine(rec, rocket_rows):
    frames = sorted(rec.get('frames', []), key=lambda f: int(f['tick']))
    ticks = [int(f['tick']) for f in frames]
    before = {f['play_index']: f for f in rec.get('play_frames', [])}
    plays = [p for p in rec.get('log', []) if p.get('accepted') and not p.get('ability')]
    bows = sorted([p for p in plays if str(p.get('card', '')).lower().replace('-', '') == 'xbow'],
                  key=lambda p: (event_tick(p), p['play_index']))
    rows = []
    for p in bows:
        tick, side = event_tick(p), int(p['side'])
        x, y = xy(p['x'], p['y'], side)
        f = before.get(p['play_index'])
        i = bisect_right(ticks, tick)-1
        if f is None or int(f['tick']) != tick:
            f = frames[i] if i >= 0 else None
        towers = f.get('towers', []) if f else []
        hp = {}
        for t in towers:
            if t[1] == 'princess':
                key = ('own_' if int(t[0]) == side else 'enemy_') + lane(xy(t[3], t[4], side)[0])
                if key in hp:
                    raise ValueError('Duplicate princess lane in public tower context')
                hp[key] = t[5]
        complete = all(k in hp for k in ('own_left', 'own_right', 'enemy_left', 'enemy_right'))
        kings = {int(t[0]): t[5] for t in towers if t[1] == 'king'}
        crowns = None
        if complete and len(kings) == 2:
            crowns = [3 if kings[1-side] <= 0 else sum(hp['enemy_'+l] <= 0 for l in ('left', 'right')),
                      3 if kings[side] <= 0 else sum(hp['own_'+l] <= 0 for l in ('left', 'right'))]
        enemy_known = all('enemy_'+l in hp for l in ('left', 'right'))
        target_hp = hp.get('enemy_'+lane(x))
        follows = [r for r in rocket_rows if r['side'] == side and r['targets'] and
                   ((r['tick'], r['play_index']) > (tick, p['play_index'])) and 0 <= r['tick']-tick <= 200]
        rows.append(dict(tag=str(rec['tag']), play_index=p['play_index'], tick=tick, side=side,
            xy=[x, y], lane=lane(x), river_distance_tiles=(y-.5)*32,
            legacy_y_gt_058=y > .58, context_tick=int(f['tick']) if f else None,
            context_age_s=(tick-int(f['tick']))*.05 if f else None,
            tower_hp=hp, crowns_ours_enemy=crowns,
            enemy_princess_down=any(hp['enemy_'+l] <= 0 for l in ('left', 'right')) if enemy_known else None,
            lane_state='unknown' if target_hp is None else 'dead' if target_hp <= 0 else 'alive',
            elapsed_s=tick*.05, phase='overtime' if tick >= 3600 else 'double' if tick >= 2400 else 'single',
            phase_seconds_left=max(0, (6000-tick if tick >= 3600 else 3600-tick)*.05),
            own_elixir_before=f.get('elixir', [None, None])[side] if f else None,
            tiebreaker=tiebreak(rec)[0],
            tower_rocket_candidates_within_10s=[dict(play_index=r['play_index'], gap_s=(r['tick']-tick)*.05,
                towers=[t['tower'] for t in r['targets']]) for r in follows]))
    return rows, len(plays)


def rate(rows, eligible, success):
    # Replay-cluster bootstrap; pooled play rate, never one independent trial per play.
    groups = defaultdict(lambda: [0, 0])
    for r in rows:
        if eligible(r):
            groups[r['tag']][1] += 1
            groups[r['tag']][0] += int(success(r))
    n = sum(v[1] for v in groups.values())
    k = sum(v[0] for v in groups.values())
    ci = None
    if len(groups) >= 2:
        import numpy as np
        a = np.asarray(list(groups.values()), dtype=float)
        rng = np.random.default_rng(20261003)
        samples = []
        for _ in range(2000):
            s = a[rng.integers(0, len(a), len(a))].sum(axis=0)
            samples.append(100*s[0]/s[1])
        ci = np.percentile(samples, [2.5, 97.5]).tolist()
    return dict(count=k, n=n, percent=100*k/n if n else None, ci95_percent=ci, replay_clusters=len(groups))


def summarize(rows):
    fresh = [r for r in rows if r['context_age_s'] is not None and r['context_age_s'] <= .5]
    return dict(placements=len(rows), replay_sides=len({(r['tag'], r['side']) for r in rows}),
        fresh_tower_context_placements=len(fresh),
        y_rows=dict(sorted(Counter(str(r['xy'][1]) for r in rows).items())),
        lanes=dict(Counter(r['lane'] for r in rows)),
        crowns=dict(Counter(':'.join(map(str, r['crowns_ours_enemy'])) if r['crowns_ours_enemy'] is not None else 'unknown'
                            for r in fresh)),
        phases=dict(Counter(r['phase'] for r in rows)),
        context_age_s=describe(r['context_age_s'] for r in rows),
        own_elixir=describe(r['own_elixir_before'] for r in fresh),
        phase_seconds_left=describe(r['phase_seconds_left'] for r in rows),
        river_distance_tiles=describe(r['river_distance_tiles'] for r in rows),
        legacy_deeper_than_y058=rate(rows, lambda r: True, lambda r: r['legacy_y_gt_058']),
        dead_lane_when_enemy_princess_down=rate(fresh,
            lambda r: r['enemy_princess_down'] is True and r['lane_state'] != 'unknown',
            lambda r: r['lane_state'] == 'dead'),
        followed_by_tower_rocket_candidate_10s=rate(rows, lambda r: True,
            lambda r: bool(r['tower_rocket_candidates_within_10s'])),
        legacy_deeper_row_followed_by_tower_rocket_candidate_10s=rate(rows, lambda r: r['legacy_y_gt_058'],
            lambda r: bool(r['tower_rocket_candidates_within_10s'])))


def run(out, pace_ms=50):
    if not math.isfinite(pace_ms) or pace_ms < 0:
        raise ValueError('Invalid pacing')
    from audit_runtime import lower_own_priority
    lower_own_priority()
    sys.path.insert(0, str(ROOT/'.foreman/codex_autopilot'))
    from native_audits import ready_receipt, verify_mined_manifest
    ready = ready_receipt()
    if ready is None:
        raise ValueError('Verified native receipt required')
    receipt_path, source = ready
    base = HERE/'native_mining_1552'
    inputs = {str(p.relative_to(ROOT)): sha(p) for p in
              (base/'manifest.json', base/'rockets.jsonl', Path(__file__), HERE/'mine_rockets.py')}
    count = verify_mined_manifest(base/'manifest.json', source)
    manifest = json.loads((base/'manifest.json').read_text())
    rockets = defaultdict(list)
    for line in (base/'rockets.jsonl').read_text().splitlines():
        r = json.loads(line)
        rockets[r['tag']].append(r)
    out.mkdir(exist_ok=False)
    rows = []
    plays = 0
    with (out/'xbows.jsonl').open('x', encoding='utf-8') as stream:
        for i, entry in enumerate(manifest):
            path = ROOT/entry['path']
            raw = path.read_bytes()
            if hashlib.sha256(raw).hexdigest() != entry['sha256']:
                raise ValueError('Native source changed: '+entry['path'])
            rec = json.loads(raw)
            if str(rec['tag']) != entry['tag'] or not rec.get('record_native') or not rec.get('record_full'):
                raise ValueError('Native identity/recording mismatch')
            found, n = mine(rec, rockets[entry['tag']])
            plays += n
            for r in found:
                r['corpus'] = str(path.parent.relative_to(ROOT)).replace('\\', '/')
                stream.write(json.dumps(r, separators=(',', ':'))+'\n')
            rows.extend(found)
            if (i+1) % 500 == 0:
                print('MINED', i+1, 'XBOWS', len(rows), flush=True)
            time.sleep(pace_ms/1000)
    groups = dict(all=rows, late_double_or_overtime=[r for r in rows if r['tick'] >= 2400],
                  overtime=[r for r in rows if r['tick'] >= 3600])
    for score in ([1, 0], [0, 1], [1, 1]):
        groups['crowns_'+''.join(map(str, score))] = [r for r in rows if r['crowns_ours_enemy'] == score and
                                                   r['context_age_s'] is not None and r['context_age_s'] <= .5]
    report = dict(status='MEASURED_PUBLIC_PLACEMENT_CENSUS_NOT_INTENT_OR_HIT_TRUTH',
        selected_replays=count, accepted_plays=plays, accepted_xbows=len(rows),
        input_hashes=inputs, vm_receipt=str(receipt_path.relative_to(ROOT)),
        row_sha256=sha(out/'xbows.jsonl'),
        bootstrap=dict(seed=20261003, replicates=2000, unit='replay_tag', paired_policy_comparison=False),
        groups={k: summarize(v) for k, v in groups.items()},
        corpus_placements=dict(Counter(r['corpus'] for r in rows)),
        strategic_defensive_share=None,
        limitations=[
            'Forward is decreasing normalized y for BOTH sides; exact row and river-distance distributions are primary.',
            'The inherited y>0.58 bucket is geometric, not validated strategic defense or bridge intent; no new decision rule.',
            'Fresh context means recorded at or before the accepted cast, at most 0.5 seconds old. Missing towers stay unknown.',
            'Tower Rockets are the existing 3.5-tile candidates, not confirmed hits; sequences share a side and occur within 10s.',
            'Multiple X-Bows may precede one Rocket; sequence denominator is X-Bow placements, not independent Rocket events.',
            'Public state only; future same-side casts and terminal labels are offline outcomes, never model inputs.',
            'Native reconstructed pro corpus, both sides and mixed decks; not gen_v1/u0155/gen_v3 policy baselines.',
            'No trained context classifier, loss weights, live deployment or acceptance threshold is established.'])
    if any(sha(ROOT/p) != digest for p, digest in inputs.items()):
        raise ValueError('Audit source changed during run')
    (out/'manifest.json').write_text(json.dumps(manifest, indent=1)+'\n')
    (out/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print('XBOW_CENSUS_VERIFIED', count, len(rows), plays, flush=True)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True, type=Path)
    ap.add_argument('--pace-ms', type=float, default=50)
    args = ap.parse_args()
    run(args.out, args.pace_ms)
