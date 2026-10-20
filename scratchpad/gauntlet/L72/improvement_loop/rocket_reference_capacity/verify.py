"""Independent native-frame recount; imports neither producer nor labeler."""
from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent


def read(p): return json.loads(Path(p).read_bytes())
def sha(p):
    with Path(p).open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
def key(s): return s.split('@')[0].lower().replace(' ', '-')
def dist(a, b): return math.hypot(a[0] - b[0], a[1] - b[1])


def reconstruct(rec, own, rocket_ids, radius, speed):
    by_tick = {int(f['tick']): f for f in rec['frames'] + rec.get('play_frames', [])}
    ticks = sorted(by_tick)
    plays = sorted([dict(p, engine=int(p.get('engine_tick', p['tick']))) for p in rec['log']
                    if p.get('accepted') is True and not p.get('skipped') and
                    not p.get('ability') and p.get('card')], key=lambda p: p['engine'])
    rockets = [p for p in plays if key(p['card']) == 'rocket']
    nados = [p for p in plays if key(p['card']) == 'tornado']
    previous = defaultdict(list)
    out = []
    for p in rockets:
        side, cast, aim = int(p['side']), p['engine'], (p['x'], p['y'])
        if side not in own: continue
        end = min([q['engine'] for q in rockets if int(q['side']) == side and q['engine'] > cast] + [cast + 300])
        flight, areas = [], []
        for tick in ticks[bisect_left(ticks, cast):bisect_left(ticks, end)]:
            frame = by_tick[tick]
            assert 'public_objects' in frame
            for obj in frame['public_objects'].get('projectiles', []) or []:
                if not isinstance(obj, dict) or obj.get('card_id') not in rocket_ids or int(obj['side']) != side: continue
                if obj.get('target_x') is None: continue
                if dist((obj['target_x'], obj['target_y']), aim) < 1000:
                    flight.append((tick, obj))
            for obj in frame['public_objects'].get('area_effects', []) or []:
                if not isinstance(obj, dict) or obj.get('card_id') not in rocket_ids or int(obj['side']) != side: continue
                start = tick - round(obj['source_elapsed_ms'] / 50) if obj.get('source_elapsed_ms') is not None else tick
                if start >= cast and dist((obj['x'], obj['y']), aim) <= radius:
                    areas.append((start, obj))
        landing, point, source = None, None, 'unobserved'
        if areas:
            landing, obj = areas[0]
            point, source = (obj['x'], obj['y']), 'area_start'
        elif flight:
            last, obj = flight[-1]
            landing = last + math.ceil(dist((obj['x'], obj['y']), (obj['target_x'], obj['target_y'])) / speed)
            point, source = (obj['target_x'], obj['target_y']), 'public_aim_catalog_speed'
        row = dict(tag=str(rec['tag']), side=side, tick=cast, card='rocket', x=aim[0], y=aim[1],
                   landing_tick=landing, landing_source=source, landing_point=list(point) if point else None,
                   hp_window_known=None, hp_confirmation_within_two_ticks=None, tower_hits=[],
                   rocket_then_tornado=None, tornado_then_rocket=None)
        if landing is not None:
            low_i, high_i = bisect_right(ticks, landing - 1) - 1, bisect_left(ticks, landing)
            known = low_i >= 0 and high_i < len(ticks) and ticks[high_i] - ticks[low_i] <= 10
            row['hp_window_known'] = known
            row['hp_confirmation_within_two_ticks'] = known and landing - ticks[low_i] <= 2 and ticks[high_i] - landing <= 2
            if known:
                low, high = by_tick[ticks[low_i]], by_tick[ticks[high_i]]
                after = {(int(t[0]), t[1], t[3], t[4]): t[5] for t in high['towers']}
                for t in low['towers']:
                    identity = (int(t[0]), t[1], t[3], t[4])
                    if identity[0] == side or t[5] <= 0 or dist((t[3], t[4]), point) > radius or identity not in after: continue
                    prior = previous[(side, identity)]
                    hp_after = after[identity]
                    row['tower_hits'].append(dict(tower=list(identity), hp_before=t[5], hp_drop=t[5] - hp_after,
                        hp_confirmed=hp_after < t[5], finish=hp_after <= 0, prior_rockets=len(prior),
                        gap_s=(cast - prior[-1]) * .05 if prior else None))
                    prior.append(cast)
            nearby = [q for q in nados if int(q['side']) == side and dist((q['x'], q['y']), point) <= 5500]
            row['rocket_then_tornado'] = any(cast < q['engine'] <= landing + 2 for q in nearby)
            row['tornado_then_rocket'] = any(q['engine'] < cast and 0 <= landing - q['engine'] <= 50 for q in nearby)
        out.append(row)
    return out


def counts(rows):
    tags, casts, sources = defaultdict(set), Counter(), Counter()
    names = ('all_casts', 'landing_unobserved', 'hp_window_known', 'hp_confirmation_within_two_ticks',
             'princess_geometric_reference', 'princess_observed_hp_drop', 'princess_observed_finish',
             'princess_repeat_reference', 'rocket_then_tornado', 'tornado_then_rocket')
    for r in rows:
        princess = [h for h in r['tower_hits'] if h['tower'][1] == 'princess']
        values = (True, r['landing_tick'] is None, r['hp_window_known'] is True,
                  r['hp_confirmation_within_two_ticks'] is True, bool(princess),
                  any(h['hp_confirmed'] for h in princess), any(h['finish'] for h in princess),
                  any(h['prior_rockets'] > 0 for h in princess), r['rocket_then_tornado'] is True,
                  r['tornado_then_rocket'] is True)
        for name, value in zip(names, values):
            if value: casts[name] += 1; tags[name].add(r['tag'])
        sources[r['landing_source']] += 1
    return dict(metrics={k: dict(casts=casts[k], replay_clusters=len(tags[k])) for k in names},
                landing_sources=dict(sources))


def compare(actual, expected, report):
    assert actual == expected, 'Raw reference mismatch'
    result = counts(expected)
    for k in result: assert report[k] == result[k], k
    assert report['policy_predictions'] == report['optimizer_updates'] == 0
    assert report['trainable'] is False and report['N2_complete'] is False


def controls(expected, report):
    compare(expected, expected, report)
    cases = []
    for field, value in [('tick', -1), ('landing_source', 'invented'), ('landing_tick', -1),
                         ('rocket_then_tornado', 'invented'), ('hp_window_known', 'invented')]:
        rows = deepcopy(expected); rows[0][field] = value
        cases.append((field, rows, report))
    rows = deepcopy(expected); rows.pop(); cases.append(('membership', rows, report))
    changed = deepcopy(report); changed['metrics']['all_casts']['casts'] += 1
    cases.append(('cast_count', expected, changed))
    changed = deepcopy(report); changed['metrics']['all_casts']['replay_clusters'] += 1
    cases.append(('cluster_count', expected, changed))
    changed = deepcopy(report); changed['N2_complete'] = True
    cases.append(('acceptance_claim', expected, changed))
    for name, rows, result in cases:
        try: compare(rows, expected, result)
        except AssertionError: pass
        else: raise AssertionError('Corruption accepted: ' + name)
    return dict(positive=1, negative=len(cases))


def main():
    assert not (HERE / 'verified.json').exists()
    started, report, actual = (read(HERE / p) for p in ('started.json', 'report.json', 'references.json'))
    assert sha(HERE / 'started.json') == report['started_sha256']
    assert sha(HERE / 'references.json') == report['references_sha256']
    for p, h in started['sources'].items(): assert sha(ROOT / p) == h, p
    inventory = read(HERE.parent / 'void_capacity/inventory.json')
    exact = inventory['exact_sides']
    assert started['exact_sides'] == exact
    expected_tags = sorted({s['tag'] for s in exact})
    assert [r['tag'] for r in started['members']] == expected_tags
    qualified = {r['tag']: r for r in inventory['qualified']}
    assert started['members'] == [qualified[t] for t in expected_tags]
    cat = read(ROOT / 'research/ext/cr-native-sandbox/native_core/data/live_card_catalog.json')
    rocket_ids = {int(c[k]) for c in cat['cards'] if key(c['display_name']) == 'rocket'
                  for k in ('card_id', 'evolution_form_id', 'hero_form_id') if c.get(k) is not None}
    derived = read(ROOT / 'research/ext/Royale/RoyaleSim/data/derived/cards.json')
    rocket = next(c for c in derived['cards'] if c['name'] == 'Rocket')
    radius, speed = rocket['area_damage_radius_milli'], rocket['projectile']['speed']
    expected = []
    for i, m in enumerate(started['members'], 1):
        assert m['split'] == 'confirmation' and sha(ROOT / m['path']) == m['sha256']
        sides = [s for s in exact if s['tag'] == m['tag']]
        own = {s['side'] for s in sides}
        for side in own:
            assert {c.split('-ev')[0].removesuffix('-hero') for c in m['decks'][1-side]} == {
                'rocket', 'tornado', 'knight', 'ice-wizard', 'tesla', 'x-bow', 'skeletons', 'the-log'}
        rows = reconstruct(read(ROOT / m['path']), own, rocket_ids, radius, speed)
        assert len(rows) == sum(s['own_commands'].get('rocket', 0) for s in sides)
        expected.extend(rows)
        print(f'{i}/{len(started["members"])} raw references verified', flush=True)
    assert report['selected_replays'] == len(expected_tags) and report['selected_sides'] == len(exact)
    compare(actual, expected, report)
    control_result = controls(expected, report)
    result = dict(complete=True, report_sha256=sha(HERE / 'report.json'),
                  script_sha256=sha(__file__), references_sha256=sha(HERE / 'references.json'),
                  controls=control_result, **counts(expected))
    (HERE / 'verified.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))
    print('ROCKET_REFERENCE_CAPACITY_INDEPENDENT_PASS')


if __name__ == '__main__': main()
