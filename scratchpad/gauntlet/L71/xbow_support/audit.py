"""Public observations of X-Bow support opportunity cost, not causal blame.

Near-bow spending is a spatial association, not a claim about player intent.
All future information is for offline outcome labels only, never policy input.
"""
from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict
import json
import math
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent.parent/'spawners'))
from body_identity import resolve
from pipeline import vocab
from pipeline.dataset_gen import card_key
from pipeline.obs_contract import catalog_card_form
from pipeline.opp_elixir_count import card_cost
from pipeline.public_geometry import constants, in_xbow_range
from pipeline.rocket_teaching import catalog, sha

HERE = Path(__file__).parent
DISTANCE = 5000
HORIZON = 120  # six seconds; outcome label only


def dist(a, b):
    return math.hypot(a['x']-b['x'], a['y']-b['y'])


def native_frame(frame):
    bodies = []
    for e in frame['entities']:
        side, x, y, name, hp, maximum, kind, cid, eid = e
        if cid < 0 or hp <= 0:
            continue
        _, form = catalog_card_form(cid)
        identity = resolve(name, maximum, form)
        key = vocab.UNIT_VOCAB[identity.cls].replace('_', '-') if identity.cls is not None else None
        record = catalog().get(key, {})
        bodies.append(dict(side=side, x=x, y=y, id=eid, card=card_key(name), hp=hp,
                           ground=record.get('flying_height', 0) == 0))
    return dict(tick=frame['tick'], bodies=bodies,
                towers=[dict(side=t[0], kind=t[1], x=t[3], y=t[4], hp=t[5]) for t in frame['towers']],
                elixir=frame.get('elixir'))


def analyse(tag, frames, plays, bows, source):
    by_tick = {f['tick']: f for f in frames}
    ticks = sorted(by_tick)
    frames = [by_tick[t] for t in ticks]
    out = []
    def at(t):
        i = bisect_right(ticks, t)-1
        return frames[i] if i >= 0 else None
    for bow in bows:
        tick, side = bow['tick'], bow['side']
        initial = at(tick)
        if initial is None:
            continue
        enemy_lane = [t for t in initial['towers'] if t['side'] != side and t['kind'] == 'princess'
                      and (t['x'] < 9000) == (bow['x'] < 9000)]
        if len(enemy_lane) != 1 or enemy_lane[0]['hp'] > 0:
            continue
        # Uniquely link the newly placed bow; ambiguity is not a zero-value bow.
        births = {}
        before_ids = {e['id'] for e in initial['bodies'] if e['side'] == side}
        for f in frames[bisect_left(ticks, tick):bisect_right(ticks, tick+50)]:
            for e in f['bodies']:
                if e['side'] == side and e['card'] == 'x-bow' and dist(e, bow) <= 1000:
                    if e['id'] not in before_ids or source == 'live_confirmed':
                        births.setdefault(e['id'], f['tick'])
        row = dict(tag=tag, source=source, bow=bow, linked=len(births) == 1, support=[])
        if not row['linked']:
            row['possible_bodies'] = len(births)
            out.append(row)
            continue
        eid, birth = next(iter(births.items()))
        # Stop at first observed absence after birth; no assumption of a full
        # catalog lifetime when the recording ends or a frame is missing.
        seen_frames = []
        end_observed = False
        for f in frames[bisect_left(ticks, birth):]:
            if not any(e['id'] == eid and e['side'] == side for e in f['bodies']):
                end_observed = True
                break
            seen_frames.append(f)
        end = seen_frames[-1]['tick'] if seen_frames else birth
        row.update(entity_id=eid, birth=birth, last_seen=end, end_observed=end_observed,
                   crown_reachable=any(t['side'] != side and t['hp'] > 0 and in_xbow_range(bow, t)
                                       for t in initial['towers']),
                   defensive_contact=any(e['side'] != side and e['ground'] and
                       dist(e, bow) <= constants()['xbow_range'] for f in seen_frames for e in f['bodies']))
        for p in plays:
            if p['side'] != side or not birth <= p['tick'] <= end or p['card'] == 'x-bow' or dist(p, bow) > DISTANCE:
                continue
            now = at(p['tick'])
            ahead = frames[bisect_left(ticks, p['tick']):bisect_right(ticks, p['tick']+HORIZON)]
            later = at(p['tick']+HORIZON)
            if now is None:
                continue
            same_x = lambda x: (x < 9000) == (bow['x'] < 9000)
            own_half = lambda y: y <= 16000 if side == 0 else y >= 16000
            targets = [e for e in now['bodies'] if e['side'] != side and e['ground'] and dist(e, bow) <= constants()['xbow_range']]
            threat = next((f['tick'] for f in ahead if any(e['side'] != side and
                not same_x(e['x']) and own_half(e['y']) for e in f['bodies'])), None)
            before_t = [t for t in now['towers'] if t['side'] == side and t['kind'] == 'princess' and not same_x(t['x'])]
            after_t = [t for t in (later or {}).get('towers', []) if t['side'] == side and t['kind'] == 'princess' and not same_x(t['x'])]
            coverage = later is not None and p['tick']+HORIZON-later['tick'] <= 10 and ticks[-1] >= p['tick']+HORIZON
            damage = max(0, before_t[0]['hp']-after_t[0]['hp']) if coverage and len(before_t) == len(after_t) == 1 else None
            elixir = p.get('elixir')
            if elixir is None and now.get('elixir') is not None and p['tick']-now['tick'] <= 10:
                elixir = now['elixir'][side]
            cost = card_cost(p['card'].replace('-', '_'))
            at_threat = at(threat) if threat is not None else None
            future_elixir = (at_threat['elixir'][side] if at_threat and at_threat.get('elixir') is not None else None)
            row['support'].append(dict(tick=p['tick'], card=p['card'], x=p['x'], y=p['y'], cost=cost,
                elixir_before=elixir, approximate_after=max(0, elixir-cost) if elixir is not None and cost is not None else None,
                no_reachable_target_now=not row['crown_reachable'] and not targets,
                next_opposite_threat_tick=threat, elixir_at_threat=future_elixir,
                opposite_tower_hp_drop_6s=damage, outcome_coverage=coverage))
        out.append(row)
    return out


def live(path):
    events = [json.loads(line) for line in path.open()]
    raw_frames = [e for e in events if e.get('event') == 'frame']
    if not raw_frames:
        return None
    side = raw_frames[0]['my_side']
    frames = []
    for frame in raw_frames:
        entities, towers = [], []
        for e in frame['ents']:
            s, x, y, cid, hp, maximum, kind, eid = e
            if cid < 0:
                towers.append([s, 'king' if kind == 12 else 'princess', None, x, y, hp, maximum])
            else:
                name, _ = catalog_card_form(cid)
                if name:
                    entities.append([s, x, y, name, hp, maximum, kind, cid, eid])
        normalized = native_frame(dict(tick=frame['tick'], entities=entities, towers=towers))
        elixir = [None, None]
        elixir[side] = frame['elixir']
        normalized['elixir'] = elixir
        frames.append(normalized)
    plays = []
    pending = None
    for e in events:
        if e.get('event') == 'play':
            pending = e
        elif e.get('event') == 'confirmed' and pending and pending['name'] == e['name']:
            x, y = e['intended']
            plays.append(dict(tick=e['tick'], side=side, card=card_key(e['name']),
                x=(1-x if side else x)*18000, y=(y if side else 1-y)*32000,
                elixir=pending['elixir']))
            pending = None
        elif e.get('event') == 'unconfirmed':
            pending = None
    return analyse(path.stem, frames, plays, [p for p in plays if p['card'] == 'x-bow'], 'live_confirmed')


def summarize(rows):
    c = Counter(dead_lane_bows=len(rows))
    for row in rows:
        c['linked'] += row['linked']
        if not row['linked']:
            continue
        c['crown_reachable'] += row['crown_reachable']
        c['defensive_contact_during_life'] += row['defensive_contact']
        c['no_observed_reachable_target_during_life'] += not row['crown_reachable'] and not row['defensive_contact']
        c['nearby_support_plays'] += len(row['support'])
        c['nearby_support_elixir'] += sum(p['cost'] or 0 for p in row['support'])
        for p in row['support']:
            if p['no_reachable_target_now']:
                c['no_target_support_plays'] += 1
                c['no_target_support_elixir'] += p['cost'] or 0
                c['no_target_support_opposite_threat_6s'] += p['next_opposite_threat_tick'] is not None
                c['no_target_support_opposite_damage_6s'] += (p['opposite_tower_hp_drop_6s'] or 0) > 0
                c['no_target_support_outcome_unknown'] += not p['outcome_coverage']
    return dict(c)


def main():
    start = time.time()
    teaching = json.loads((ROOT/'icebow/data/bench/rocket_teaching_20261004/manifest.json').read_text())
    tags = {x['tag'] for x in teaching['replay_evidence']}
    manifest = ROOT/'.foreman/codex_autopilot/runs/public_labels_full_reconstructed/manifest.json'
    sources = {x['tag']: x for x in json.loads(manifest.read_text())['sources']}
    labels = ROOT/'.foreman/codex_autopilot/runs/public_labels_full_reconstructed/labels.jsonl'
    bows = defaultdict(list)
    for line in labels.open():
        p = json.loads(line)
        if p['card'] == 'x-bow' and p['tag'] in tags and p['lane_state'] == 'dead':
            bows[p['tag']].append(p)
    pro_rows, evidence = [], []
    for tag, selected in bows.items():
        src = sources[tag]
        path = ROOT/src['path']
        assert sha(path) == src['sha256']
        rec = json.loads(path.read_text())
        frames = [native_frame(f) for f in rec['frames']+rec.get('play_frames', [])]
        plays = [dict(p, card=card_key(p['card'])) for p in rec['log']
                 if p.get('accepted') and p.get('card') and not p.get('ability')]
        pro_rows.extend(analyse(tag, frames, plays, selected, 'native_pro'))
        evidence.append(src)
    live_rows, live_sources = [], []
    for path in sorted((ROOT/'scratchpad/gauntlet/L68/live_reader').glob('live_play_20261004_*.jsonl')):
        rows = live(path)
        if rows is not None:
            live_rows.extend(rows)
            live_sources.append(dict(path=str(path.relative_to(ROOT)), sha256=sha(path)))
    report = dict(pro=summarize(pro_rows), live=summarize(live_rows), pro_rows=pro_rows, live_rows=live_rows,
                  source_manifest_sha256=sha(manifest), labels_sha256=sha(labels),
                  pro_sources=evidence, live_sources=live_sources, distance_milli=DISTANCE, horizon_ticks=HORIZON,
                  limitations=['Nearby support is spatial association, not inferred intent.',
                    'Reachable targets are geometry, not proof of hits or useful distraction.',
                    'Subsequent damage and elixir are observational; no counterfactual causal claim.',
                    'Unknown flying classes conservatively count as potential ground targets.',
                    'Live coverage is limited to saved frames and confirmed plays; own hands were not logged.'],
                  seconds=time.time()-start)
    (HERE/'audit.json').write_text(json.dumps(report, indent=2))
    print(json.dumps({k: report[k] for k in ('pro', 'live', 'seconds')}))
    print('XBOW_SUPPORT_AUDIT_COMPLETE')


if __name__ == '__main__':
    main()
