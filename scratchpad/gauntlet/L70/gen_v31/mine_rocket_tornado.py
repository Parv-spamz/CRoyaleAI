"""Public troop-target candidates and BOTH Rocket/Tornado orders; not hit truth."""
import argparse
from bisect import bisect_right
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import re
import sys
import time

from mine_rockets import describe
from mine_xbows import xy, rate
from audit_runtime import lower_own_priority

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
CATALOG = ROOT/'research/ext/cr-native-sandbox/native_core/data/live_card_catalog.json'
STATS = ROOT/'icebow/config/cards_stats.json'


def key(name):
    return re.sub('[^a-z0-9]', '', str(name).lower())


def tick(p):
    return int(p['engine_tick'] if p.get('engine_tick') is not None else p['tick'])


def unit_values():
    stats = {key(n): v for n, v in json.loads(STATS.read_text())['cards'].items()}
    table = {}
    for c in json.loads(CATALOG.read_text())['cards']:
        stat = stats.get(key(c['display_name']), {})
        count = stat.get('count')
        value = c.get('elixir') / count if isinstance(count, (int, float)) and count > 0 and c.get('elixir') is not None else None
        for field in ('card_id', 'evolution_form_id', 'hero_form_id'):
            if c.get(field) is not None:
                table[int(c[field])] = dict(card=c['display_name'], kind=c['type'],
                                           nominal_base_cost_per_body=value, base_count=count)
    return table


def troops(frame, side, x, y, values):
    found = []
    if frame is None:
        return None
    for e in frame.get('entities', []):
        if len(e) not in (8, 9):
            raise ValueError('Unexpected native entity schema')
        if int(e[0]) == side or e[4] <= 0 or int(e[-2]) < 0:
            continue
        distance = math.hypot(e[1]-x, e[2]-y)/1000
        if distance > 2:
            continue
        info = values.get(int(e[-2]), {})
        found.append(dict(entity_id=int(e[-1]), native_card_id=int(e[-2]), name=e[3],
            hp=e[4], max_hp=e[5], distance_tiles=distance, catalog_card=info.get('card'),
            kind=info.get('kind'), nominal_base_cost_per_body=info.get('nominal_base_cost_per_body')))
    return found


def flight_count(frame, p):
    if frame is None or 'projectiles' not in frame:
        return None
    return sum(isinstance(q, list) and len(q) >= 6 and int(q[0]) == int(p['side']) and
               key(q[5]) == 'rocket' and abs(q[3]-p['x']) <= 1 and abs(q[4]-p['y']) <= 1
               for q in frame['projectiles'])


def mine(rec, rocket_audit, values):
    frames = sorted(rec.get('frames', []), key=lambda f: int(f['tick']))
    ticks = [int(f['tick']) for f in frames]
    by_tick = defaultdict(list)
    for f in frames:
        by_tick[int(f['tick'])].append(f)
    pre = {f['play_index']: f for f in rec.get('play_frames', [])}
    plays = [p for p in rec.get('log', []) if p.get('accepted') and not p.get('ability')]
    rockets = [p for p in plays if key(p.get('card')) == 'rocket']
    nados = [p for p in plays if key(p.get('card')) == 'tornado']
    old = {r['play_index']: r for r in rocket_audit}
    if {p['play_index'] for p in rockets} != set(old):
        raise ValueError('Rocket event identity differs from prior verified census')
    out = []
    for p in rockets:
        t, side = tick(p), int(p['side'])
        i = bisect_right(ticks, t)-1
        f = pre.get(p['play_index'])
        if f is None or int(f['tick']) != t:
            f = frames[i] if i >= 0 else None
        next_cast = min((tick(q) for q in rockets if q['side'] == side and tick(q) > t), default=t+300)
        # An aim-matched projectile already visible before this cast may belong
        # to an older Rocket. Retain the candidate but refuse exact linkage.
        seen, absent, ambiguous = [], None, bool(flight_count(f, p))
        for ff in frames[max(0, i):]:
            if int(ff['tick']) < t:
                continue
            if int(ff['tick']) >= next_cast or int(ff['tick']) > t+300:
                break
            n = flight_count(ff, p)
            if n is None:
                ambiguous = True
                continue
            if n > 1:
                ambiguous = True
            if n:
                seen.append(ff)
            elif seen:
                absent = ff
                break
        last = seen[-1] if seen else None
        before_units = troops(f, side, p['x'], p['y'], values)
        late_units = troops(last, side, p['x'], p['y'], values)
        damage = []
        if late_units is not None and absent is not None:
            after_units = {int(e[-1]): e for e in absent.get('entities', []) if int(e[0]) != side and int(e[-2]) >= 0}
            for u in late_units:
                after = after_units.get(u['entity_id'])
                damage.append(dict(entity_id=u['entity_id'],
                    hp_drop=None if after is None or int(after[-2]) != u['native_card_id'] else u['hp']-after[4],
                    disappearance=after is None))
        combos = []
        for nado in nados:
            if nado['side'] != side or abs(tick(nado)-t) > 100:
                continue
            gap = (tick(nado)-t)*.05
            dist = math.hypot((nado['x']-p['x'])/18000, (nado['y']-p['y'])/32000)
            order = 'rocket_then_tornado' if (t, p['play_index']) < (tick(nado), nado['play_index']) else 'tornado_then_rocket'
            exact = by_tick.get(tick(nado), [])
            in_flight = order == 'rocket_then_tornado' and bool(exact) and all(flight_count(ff, p) == 1 for ff in exact) and not ambiguous
            bounds = None if last is None or absent is None or ambiguous else [
                (int(last['tick'])-tick(nado))*.05, (int(absent['tick'])-tick(nado))*.05]
            combos.append(dict(tornado_play_index=nado['play_index'], order=order, cast_gap_s=abs(gap),
                signed_tornado_minus_rocket_s=gap, normalized_distance=dist,
                distance_tiles=math.hypot(nado['x']-p['x'], nado['y']-p['y'])/1000,
                exact_observed_rocket_in_flight_at_tornado=in_flight,
                disappearance_gap_after_tornado_s=bounds,
                cast_window_prior=abs(gap) <= 2.5 and dist <= .11))
        y = xy(p['x'], p['y'], side)[1]
        out.append(dict(tag=str(rec['tag']), play_index=p['play_index'], side=side, tick=t,
            tower_candidate=bool(old[p['play_index']]['targets']), target_xy=xy(p['x'], p['y'], side),
            target_half='own' if y > .5 else 'enemy' if y < .5 else 'river', phase=old[p['play_index']]['phase'],
            context_tick=int(f['tick']) if f else None, own_elixir_before=old[p['play_index']]['own_elixir_before'],
            enemy_units_at_cast=before_units, enemy_units_last_flight=late_units,
            last_flight_tick=int(last['tick']) if last else None,
            first_absent_tick=int(absent['tick']) if absent else None, flight_ambiguous=ambiguous,
            compatible_hp_changes=damage, confirmed_troop_hits=None, elixir_value_hit=None, combos=combos))
    return out, len(nados)


def summarize(rows):
    result = dict(rockets=len(rows), halves=dict(Counter(r['target_half'] for r in rows)),
        phases=dict(Counter(r['phase'] for r in rows)), own_elixir=describe(r['own_elixir_before'] for r in rows),
        flight_observed=sum(r['last_flight_tick'] is not None for r in rows),
        disappearance_bracket_observed=sum(r['first_absent_tick'] is not None and not r['flight_ambiguous'] for r in rows),
        units_at_cast=dict(Counter(u['name'] for r in rows for u in r['enemy_units_at_cast'] or [])),
        units_last_flight=dict(Counter(u['name'] for r in rows for u in r['enemy_units_last_flight'] or [])),
        rockets_with_enemy_unit_at_cast=rate(rows, lambda r: r['enemy_units_at_cast'] is not None,
                                            lambda r: bool(r['enemy_units_at_cast'])),
        rockets_with_enemy_unit_last_flight=rate(rows, lambda r: r['enemy_units_last_flight'] is not None and not r['flight_ambiguous'],
                                               lambda r: bool(r['enemy_units_last_flight'])),
        nominal_candidate_body_value=describe(sum(u['nominal_base_cost_per_body'] for u in r['enemy_units_last_flight'])
            for r in rows if r['enemy_units_last_flight'] and not r['flight_ambiguous'] and
            all(u['nominal_base_cost_per_body'] is not None for u in r['enemy_units_last_flight'])),
        unknown_nominal_body_cost_count=sum(u['nominal_base_cost_per_body'] is None for r in rows for u in r['enemy_units_last_flight'] or []),
        orders={})
    for order in ('rocket_then_tornado', 'tornado_then_rocket'):
        pairs = [c for r in rows for c in r['combos'] if c['order'] == order]
        result['orders'][order] = dict(candidate_pairs_within_5s=len(pairs),
            gaps_s=describe(c['cast_gap_s'] for c in pairs), normalized_distance=describe(c['normalized_distance'] for c in pairs),
            cast_window_prior_rate=rate(rows, lambda r: True, lambda r: any(c['order'] == order and c['cast_window_prior'] for c in r['combos'])),
            in_flight_prior_rate=rate(rows, lambda r: True, lambda r: any(c['order'] == order and c['cast_window_prior'] and
                c['exact_observed_rocket_in_flight_at_tornado'] for c in r['combos'])),
            disappearance_bracket_upper_within_2_5s=sum(c['normalized_distance'] <= .11 and
                c['disappearance_gap_after_tornado_s'] is not None and 0 <= c['disappearance_gap_after_tornado_s'][0] <=
                c['disappearance_gap_after_tornado_s'][1] <= 2.5 for c in pairs),
            sensitivity={str(window): {str(radius):sum(any(c['order'] == order and c['cast_gap_s'] <= window and
                c['normalized_distance'] <= radius for c in r['combos']) for r in rows)
                for radius in (.055, .11, .165)} for window in (.5, 1, 2.5, 5)})
    return result


def run(out, pace_ms):
    if pace_ms < 50:
        raise ValueError('Use at least50ms pacing')
    lower_own_priority()
    sys.path.insert(0, str(ROOT/'.foreman/codex_autopilot'))
    from native_audits import ready_receipt, verify_mined_manifest
    receipt, source = ready_receipt()
    base = HERE/'native_mining_1552'
    count = verify_mined_manifest(base/'manifest.json', source)
    paths = [Path(__file__), HERE/'mine_xbows.py', HERE/'mine_rockets.py', CATALOG, STATS, base/'manifest.json', base/'rockets.jsonl']
    hashes = {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    manifest = json.loads((base/'manifest.json').read_text())
    old = defaultdict(list)
    for line in (base/'rockets.jsonl').read_text().splitlines():
        r = json.loads(line); old[r['tag']].append(r)
    values = unit_values(); rows = []; nados = 0
    out.mkdir(exist_ok=False)
    with (out/'rockets.jsonl').open('x') as stream:
        for i, item in enumerate(manifest):
            raw = (ROOT/item['path']).read_bytes()
            if hashlib.sha256(raw).hexdigest() != item['sha256']:
                raise ValueError('Native source changed')
            rec = json.loads(raw)
            if str(rec['tag']) != item['tag'] or not rec.get('record_native'):
                raise ValueError('Native identity/schema mismatch')
            found, n = mine(rec, old[item['tag']], values)
            nados += n; rows.extend(found)
            for r in found:
                stream.write(json.dumps(r, separators=(',', ':'))+'\n')
            if (i+1) % 500 == 0:
                print('MINED', i+1, 'ROCKETS', len(rows), flush=True)
            time.sleep(pace_ms/1000)
    groups = dict(all=rows, non_tower=[r for r in rows if not r['tower_candidate']], tower=[r for r in rows if r['tower_candidate']])
    report = dict(status='MEASURED_PUBLIC_CANDIDATES_AND_ORDER_TIMING_NOT_DAMAGE_ATTRIBUTION',
        replays=count, accepted_rockets=len(rows), accepted_tornados=nados,
        source_hashes=hashes, groups={k:summarize(v) for k, v in groups.items()},
        confirmed_defensive_rocket_rate=None, elixir_value_hit=None,
        bootstrap=dict(seed=20261003, repeats=2000, unit='eligible replay tag'),
        limitations=[
            'Non-tower means outside the earlier crown candidate envelope; it is not automatically defensive.',
            'Enemy bodies within2 tiles of aim are candidates, not verified hits; public position changes and simultaneous damage confound attribution.',
            'Nominal body value divides public base-card elixir by base count. Summons, evolutions and partial HP make this a proxy, never actual elixir spent or hit.',
            'Projectile disappearance intervals are not validated impact times. Exact in-flight observations only establish simultaneous presence.',
            '2.5s/0.11 is an audited historical cast-window prior; its radius is in normalized anisotropic board coordinates, not tiles.',
            'Both cast orders and nearby windows/radii are reported separately; one Rocket may contribute to both orders.',
            'No classifier, loss weight, policy rule or deployment is selected; outcome labels never enter model inputs.'])
    if any(hashlib.sha256((ROOT/p).read_bytes()).hexdigest() != h for p, h in hashes.items()):
        raise ValueError('Audit source changed')
    (out/'manifest.json').write_text(json.dumps(manifest, indent=1)+'\n')
    (out/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print('ROCKET_TORNADO_CENSUS_COMPLETE', count, len(rows), nados, flush=True)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--out', required=True, type=Path)
    ap.add_argument('--pace-ms', type=float, default=50); a = ap.parse_args()
    run(a.out, a.pace_ms)
