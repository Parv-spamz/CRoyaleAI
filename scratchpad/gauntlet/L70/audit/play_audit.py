"""Offline, single-process audit. Reads existing artifacts; writes only beside this script.

Run from any directory with Python + numpy (numpy is used only for the small S1 file).
No project modules are imported, so importing this file cannot start a bot or engine.
"""
from __future__ import annotations

import bisect
import collections
import datetime as dt
import fnmatch
import hashlib
import json
import math
import statistics as st
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
LOGS = ROOT / 'scratchpad/gauntlet/L68/live_reader'
CARD_TABLE = ROOT / 'icebow/config/cards_stats.json'
NAMES = ['IceWizard', 'Knight', 'Log', 'Rocket', 'Skeletons', 'Tesla', 'Tornado', 'Xbow']
MAX_GAP = 0.5  # seconds between samples supporting a continuous opportunity
MIN_PERIOD = 2.0
GRACE = 5.0
TARGET_RADIUS = 3.5  # tiles, operational proximity, not a verified game hitbox
NORMAL_STOPS = {'battle_over_hands_visible', 'battle_over', 'inactive'}
MANIFEST = OUT / 'input_manifest.json'
FROZEN = {r['path']: r for r in json.loads(MANIFEST.read_text(encoding='utf-8'))['files']} if MANIFEST.exists() else {}


def rel(p):
    return p.relative_to(ROOT).as_posix()


def read_jsonl(p):
    with p.open('rb') as f:
        raw = f.read(FROZEN[rel(p)]['bytes']) if FROZEN else f.read()
    if FROZEN:
        assert hashlib.sha256(raw).hexdigest() == FROZEN[rel(p)]['sha256'], f'Source prefix changed: {p}'
    rows, errors = [], []
    for i, line in enumerate(raw.splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except (ValueError, UnicodeDecodeError) as e:
            errors.append({'line': i, 'error': str(e)})
            continue
        row['_line'] = i
        rows.append(row)
    return rows, {'path': rel(p), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(),
                  'parse_errors': errors}


def inputs(pattern):
    if FROZEN:
        return sorted(ROOT / p for p in FROZEN if fnmatch.fnmatch(Path(p).name, pattern))
    return sorted(LOGS.glob(pattern))


def hist(values):
    return dict(sorted(collections.Counter(values).items()))


def describe(values):
    vals = list(values)
    return {'n': len(vals), 'mean': st.mean(vals) if vals else None,
            'median': st.median(vals) if vals else None,
            'min': min(vals) if vals else None, 'max': max(vals) if vals else None}


def frac(k, n):
    return {'count': k, 'n': n, 'fraction': k / n if n else None}


def pct(k, n):
    return f'{k}/{n} ({100*k/n:.1f}%)' if n else f'{k}/{n} (undefined)'


def xy(e, side):
    # Exact equivalent of live_play.py:158-160, without importing that module.
    x, y = (18000-e[1], 32000-e[2]) if side == 1 else (e[1], e[2])
    return [x / 18000, 1 - y / 32000]


def distance(a, b):
    return math.hypot((a[0]-b[0])*18, (a[1]-b[1])*32)


def unix_start(p):
    # Filenames are local time; these dates are EDT. Explicit offset avoids host TZ dependence.
    return dt.datetime.strptime(p.stem.removeprefix('live_play_'), '%Y%m%d_%H%M%S').replace(
        tzinfo=dt.timezone(dt.timedelta(hours=-4))).timestamp()


def load_matches():
    selected, excluded, manifest = [], [], []
    files = sorted(set(inputs('live_play_20261002_2*.jsonl')) |
                   set(inputs('live_play_20261003_*.jsonl')))
    for p in files:
        rows, provenance = read_jsonl(p)
        start = next((r for r in rows if r['event'] == 'start'), {})
        if 'league1c' not in str(start.get('ckpt', '')):
            excluded.append({'file': p.name, 'reason': 'start.ckpt does not contain league1c'})
            continue
        manifest.append(provenance)
        plays = [r for r in rows if r['event'] == 'play']
        frames = [r for r in rows if r['event'] == 'frame']
        end = next((r for r in rows if r['event'] == 'end'), None)
        stop = next((r for r in reversed(rows) if r['event'] == 'stop'), {})
        m = {'file': p.name, 'start': start, 'start_unix': unix_start(p), 'end': end,
             'stop': stop, 'plays': plays, 'frames': frames,
             'outcome': 'unknown', 'nav_pair': None,
             'counts': {c: sum(q['name'] == c for q in plays) for c in NAMES}}
        # Link decisions to their one pending receipt, never infer confirmations from totals.
        pending = None
        for r in rows:
            if r['event'] == 'play':
                pending = r
                r['receipt'] = 'missing'
            elif r['event'] in ('confirmed', 'unconfirmed') and pending is not None:
                assert pending['name'] == r['name'], (p, pending, r)
                pending['receipt'] = r['event']
                pending['receipt_tick'] = r['tick']
                pending['spawn'] = r.get('spawn')
                pending = None
        if end:
            assert end['played'] == len(plays), p
            m['estimated_end_unix'] = m['start_unix'] + end['seconds']
        selected.append(m)
    return selected, excluded, manifest


def pair_nav(selected, manifest):
    navs = []
    for p in inputs('ladder_nav_2026100[23]_*.jsonl'):
        rows, prov = read_jsonl(p)
        manifest.append(prov)
        start = next((r for r in rows if r['event'] == 'nav_start'), None)
        if start:
            navs.append({'file': p.name, 't': start['t'],
                         'outcomes': [r for r in rows if r['event'] == 'outcome']})
    navs.sort(key=lambda n: n['t'])
    used = set()
    for i, m in enumerate(selected):
        if not m['end']:
            continue
        t = m['estimated_end_unix']
        next_start = selected[i+1]['start_unix'] if i+1 < len(selected) else math.inf
        candidates = [n for n in navs if t-1 <= n['t'] <= t+30 and n['t'] < next_start]
        if len(candidates) != 1:
            m['pair_failure'] = f'{len(candidates)} nav starts in eligible interval'
            continue
        n = candidates[0]
        assert n['file'] not in used
        used.add(n['file'])
        m['nav_pair'] = {'file': n['file'], 'gap_seconds': n['t']-t,
                         'outcome_events': n['outcomes']}
        if len(n['outcomes']) == 1:
            won = n['outcomes'][0].get('won')
            m['outcome'] = 'win' if won is True else 'loss' if won is False else 'null'
    return len(navs)


def towers_for(m):
    fs = m['frames']
    if not fs:
        return
    assert len({f['my_side'] for f in fs}) == 1, m['file']
    assert all(b['tick'] >= a['tick'] and b['t_dev'] >= a['t_dev'] for a, b in zip(fs, fs[1:]))
    me = fs[0]['my_side']
    towers = []
    for side in [0, 1]:
        for lane, x, y in [('left_native', 3500, 6500 if side == 0 else 25500),
                            ('right_native', 14500, 6500 if side == 0 else 25500),
                            ('king', 9000, 3000 if side == 0 else 29000)]:
            cand = [e for e in fs[0]['ents'] if e[0] == side and abs(e[1]-x) < 500
                    and abs(e[2]-y) < 500 and e[5] >= 3000]
            assert cand, (m['file'], side, lane, 'no initial tower')
            e = max(cand, key=lambda a: a[5])
            assert e[3] == -1  # data verification, not solely a guessed kind value
            coord = xy(e, me)
            key = ('our' if side == me else 'enemy') + '_' + (
                'king' if lane == 'king' else 'left' if coord[0] < .5 else 'right')
            t = {'key': key, 'side': side, 'native_xy': [e[1], e[2]], 'xy': coord,
                 'max_hp': e[5], 'initial_hp': e[4], 'address': e[7], 'card_id': e[3],
                 'hp': [], 'kinds': set(), 'death_index': None, 'death_evidence': None,
                 'missing_transient_samples': 0, 'hp_increases': 0, 'address_reuse_samples': 0}
            for f in fs:
                at_address = [a for a in f['ents'] if a[7] == t['address']]
                found = [a for a in at_address if a[0] == side and a[3] == -1
                         and a[1:3] == t['native_xy'] and a[5] == t['max_hp']]
                t['address_reuse_samples'] += bool(at_address and not found)
                if found:
                    a = found[0]
                    assert a[1:3] == t['native_xy'] and a[5] == t['max_hp'], (m['file'], key)
                    t['hp'].append(max(0, a[4]))
                    t['kinds'].add(a[6])
                else:
                    t['hp'].append(None)
            # Persistent disappearance is a separate explicit death inference. Do not fill
            # isolated missing samples or absence at the recording boundary with zero.
            for i, hp in enumerate(t['hp']):
                if hp == 0:
                    t['death_index'], t['death_evidence'] = i, 'explicit_zero_hp'
                    break
                if hp is None:
                    j = i
                    while j < len(fs) and t['hp'][j] is None:
                        j += 1
                    if j == len(fs) and j-i >= 3 and fs[j-1]['t_dev']-fs[i]['t_dev'] >= .19:
                        t['death_index'], t['death_evidence'] = i, 'persistent_disappearance'
                        break
                    t['missing_transient_samples'] += 1
            if t['death_index'] is not None:
                for i in range(t['death_index'], len(fs)):
                    t['hp'][i] = 0
            t['hp_increases'] = sum(b > a for a, b in zip(t['hp'], t['hp'][1:])
                                    if a is not None and b is not None)
            t['final_hp'] = t['hp'][-1]
            t['kinds'] = sorted(t['kinds'])
            towers.append(t)
    m['towers'] = {t['key']: t for t in towers}
    m['frame_ticks'] = [f['tick'] for f in fs]
    # Match-end claims need a normal stop near the last frame, not merely an end record.
    last_tick = fs[-1]['tick']
    m['end_covered'] = bool(m['end'] and m['stop'].get('why') in NORMAL_STOPS
                            and 0 <= m['stop'].get('tick', math.inf)-last_tick <= 20)
    m['frame_coverage'] = {'n': len(fs), 'first_tick': fs[0]['tick'], 'last_tick': last_tick,
                           'stop_tick': m['stop'].get('tick'), 'end_covered': m['end_covered'],
                           'gaps_over_half_second': sum(b['t_dev']-a['t_dev'] > MAX_GAP
                                                       for a, b in zip(fs, fs[1:]))}


def rocket_damage(recorded):
    candidates = []
    for m in recorded:
        for p in m['plays']:
            if p['name'] != 'Rocket' or p['receipt'] != 'confirmed':
                continue
            for k in ('enemy_left', 'enemy_right'):
                t = m['towers'][k]
                if distance(p['xy'], t['xy']) > TARGET_RADIUS:
                    continue
                for i in range(1, len(m['frames'])):
                    f, prev = m['frames'][i], m['frames'][i-1]
                    lag = f['t_dev']-p['t_dev']
                    a, b = t['hp'][i-1:i+1]
                    if (3 <= lag <= 6 and a is not None and b is not None and b > 0
                            and 300 <= a-b <= 700 and f['t_dev']-prev['t_dev'] <= MAX_GAP):
                        candidates.append({'file': m['file'], 'play_tick': p['tick'], 'lane': k,
                                           'before_tick': prev['tick'], 'after_tick': f['tick'],
                                           'before_line': prev['_line'], 'after_line': f['_line'],
                                           'before_hp': a, 'after_hp': b, 'drop': a-b,
                                           'lag_seconds': lag, 'distance_tiles': distance(p['xy'], t['xy'])})
    counts = collections.Counter(c['drop'] for c in candidates)
    assert counts, 'No measured Rocket damage; must investigate before choosing a threshold'
    ranked = counts.most_common()
    assert ranked[0][1] >= 2 and (len(ranked) == 1 or ranked[0][1] > ranked[1][1])
    table = json.loads(CARD_TABLE.read_text())
    return {'used_hp': ranked[0][0], 'method': 'mode of repeated post-Rocket, nonlethal tower HP steps',
            'supporting_steps_n': ranked[0][1], 'candidate_steps_n': len(candidates),
            'candidate_drop_distribution': dict(counts), 'evidence': candidates,
            'table_source': rel(CARD_TABLE), 'table_level': table['meta']['level'],
            'table_crown_damage': table['cards']['rocket']['crown_tower_damage'],
            'level_of_our_rocket': 'not logged; measured live damage used, no level scaling assumed'}


def periods(fs, hp, threshold):
    """Conservative sampled continuous intervals; gaps/unknowns break intervals."""
    result, first, last = [], None, None
    for i, f in enumerate(fs):
        good = hp[i] is not None and 0 < hp[i] <= threshold and f['elixir'] >= 6
        connected = last is not None and f['t_dev']-fs[last]['t_dev'] <= MAX_GAP
        if first is not None and (not good or not connected):
            if fs[last]['t_dev']-fs[first]['t_dev'] >= MIN_PERIOD:
                result.append((first, last))
            first = None
        if good:
            if first is None:
                first = i
            last = i
    if first is not None and fs[last]['t_dev']-fs[first]['t_dev'] >= MIN_PERIOD:
        result.append((first, last))
    return result


def frame_index(m, tick):
    i = bisect.bisect_right(m['frame_ticks'], tick)-1
    return i if i >= 0 and tick-m['frame_ticks'][i] <= 10 else None


def recorded_metrics(m, threshold):
    fs, towers = m['frames'], m['towers']
    opportunities, placements, rocket_plays = [], [], []
    for key in ['enemy_left', 'enemy_right']:
        t = towers[key]
        for a, b in periods(fs, t['hp'], threshold):
            start, end = fs[a]['t_dev'], fs[b]['t_dev']
            shots = [p for p in m['plays'] if p['name'] == 'Rocket' and
                     start <= p['t_dev'] <= end+GRACE and distance(p['xy'], t['xy']) <= TARGET_RADIUS]
            confirmed = [p for p in shots if p['receipt'] == 'confirmed']
            death = t['death_index']
            # Distinguish a response from attribution: a confirmed cast is not a proven kill.
            prior_shots = [p for p in m['plays'] if p['name'] == 'Rocket' and p['receipt'] == 'confirmed'
                           and distance(p['xy'], t['xy']) <= TARGET_RADIUS and death is not None
                           and 0 <= fs[death]['t_dev']-p['t_dev'] <= 7]
            kingdeath = towers['enemy_king']['death_index']
            king_collapse = death is not None and kingdeath is not None and abs(fs[death]['tick']-fs[kingdeath]['tick']) <= 4
            if confirmed:
                status = 'converted_rocket_cast'
            elif death is not None and not prior_shots and not king_collapse:
                status = 'died_other'
            elif death is not None:
                status = 'death_cause_ambiguous'
            elif m['end_covered'] and t['final_hp'] is not None and t['final_hp'] > 0:
                status = 'expired_survived_end'
            else:
                status = 'censored'
            opportunities.append({'file': m['file'], 'lane': key, 'start_tick': fs[a]['tick'],
                                  'end_tick': fs[b]['tick'], 'start_line': fs[a]['_line'], 'end_line': fs[b]['_line'],
                                  'duration_seconds': end-start, 'start_hp': t['hp'][a],
                                  'minimum_hp': min(t['hp'][a:b+1]),
                                  'minimum_elixir': min(f['elixir'] for f in fs[a:b+1]),
                                  'status': status, 'targeted_attempt_ticks': [p['tick'] for p in shots],
                                  'targeted_confirmed_ticks': [p['tick'] for p in confirmed],
                                  'any_rocket_attempt_ticks': [p['tick'] for p in m['plays'] if p['name'] == 'Rocket' and start <= p['t_dev'] <= end+GRACE],
                                  'death_tick': fs[death]['tick'] if death is not None else None,
                                  'death_within_grace': death is not None and fs[death]['t_dev'] <= end+GRACE,
                                  'final_hp': t['final_hp'], 'outcome': m['outcome']})
    for p in m['plays']:
        if p['name'] != 'Rocket':
            continue
        i = frame_index(m, p['tick'])
        target = min([towers[k] for k in ['enemy_left', 'enemy_right']], key=lambda t: distance(p['xy'], t['xy']))
        di = target['death_index']
        rocket_plays.append({'tick': p['tick'], 'xy': p['xy'], 'receipt': p['receipt'],
                            'nearest_tower': target['key'], 'distance_tiles': distance(p['xy'], target['xy']),
                            'hp_at_play': target['hp'][i] if i is not None else None,
                            'death_delay_seconds': fs[di]['t_dev']-p['t_dev'] if di is not None else None})
    for p in m['plays']:
        if p['name'] != 'Xbow':
            continue
        i = frame_index(m, p['tick'])
        lane = 'left' if p['xy'][0] < .5 else 'right'
        defensive = p['xy'][1] > .58
        hp = towers['enemy_'+lane]['hp'][i] if i is not None else None
        hp4 = [towers[k]['hp'][i] for k in ['enemy_left', 'enemy_right', 'our_left', 'our_right']] if i is not None else []
        kings_alive = i is not None and all((towers[k]['hp'][i] or 0) > 0 for k in ['our_king', 'enemy_king'])
        score = [sum(h == 0 for h in hp4[:2]), sum(h == 0 for h in hp4[2:])] if hp4 and None not in hp4 and kings_alive else None
        spawn = p.get('spawn')
        placements.append({'file': m['file'], 'tick': p['tick'], 'line': p['_line'], 'xy': p['xy'],
                           'defensive': defensive, 'lane': lane, 'enemy_lane_hp': hp,
                           'lane_state': 'unknown' if hp is None else 'dead' if hp == 0 else 'alive',
                           'crowns_ours_enemy': score, 'at_one_one': score == [1, 1],
                           'remaining_princess_target': score == [1, 1] and hp is not None and hp > 0,
                           'receipt': p['receipt'], 'spawn': spawn,
                           'spawn_defensive': bool(spawn[0][1] > .58) if spawn else None})
    left, right = towers['enemy_left'], towers['enemy_right']
    final = [left['final_hp'], right['final_hp']]
    damage = [t['max_hp']-t['final_hp'] if t['final_hp'] is not None else None for t in [left, right]]
    total = sum(damage) if None not in damage else None
    concentration = max(damage)/total if total else None
    both = all(h is not None and 0 < h < t['max_hp']/2 for h, t in zip(final, [left, right]))
    m['B'] = {'opportunities': opportunities, 'xbow': placements, 'rocket_plays': rocket_plays,
              'damage': {'left': damage[0], 'right': damage[1], 'total': total,
                         'concentration': concentration, 'end_covered': m['end_covered'],
                         'both_below_half_neither_destroyed_observed': both,
                         'both_below_half_neither_destroyed_end': both and m['end_covered']}}


def pro_metrics():
    result = {}
    p = ROOT / 'icebow/data/pipeline/gen_dataset_v2.json'
    d = json.loads(p.read_text())
    total = sum(v['plays'] for v in d['card_counts'].values())
    assert total == d['stats']['play_rows']
    result['generalist_metadata'] = {'source': rel(p), 'replays_n': d['replays'],
                                    'rocket_share': frac(d['card_counts']['rocket']['plays'], total),
                                    'elixir': None, 'caveat': 'Mixed decks; not deck-matched; metadata has no elixir-at-play.'}
    try:
        import numpy as np
    except ImportError:
        result['s1'] = {'available': False, 'needed': 'numpy to read existing s1_dataset.npz; no engine rerun needed'}
        return result
    p = ROOT / 'icebow/data/pipeline/s1_dataset.npz'
    with np.load(p, allow_pickle=False) as z:
        meta = json.loads(str(z['meta']))
        gate, slot, sc, rep, side = z['y_gate'], z['y_slot'], z['sc'], z['rep'], z['side']
        play = gate == 1
        rs = meta['cards'].index('rocket')
        rocket = play & (slot == rs)
        assert int(play.sum()) == meta['stats']['play_rows']
        card_stats = {}
        for i, card in enumerate(meta['cards']):
            mask = play & (slot == i)
            card_stats[card] = {'share': frac(int(mask.sum()), int(play.sum())),
                                'elixir_at_play': describe((sc[mask, 3].astype(float)*10).tolist())}
        result['s1'] = {'available': True, 'source': rel(p), 'meta': meta,
                         'play_rows_n': int(play.sum()), 'rocket_rows_n': int(rocket.sum()),
                         'replays_with_plays_n': int(len(set(rep[play].tolist()))),
                         'replay_sides_with_plays_n': len(set(zip(rep[play].tolist(), side[play].tolist()))),
                         'rocket_share': frac(int(rocket.sum()), int(play.sum())), 'cards': card_stats,
                         'elixir_source': 'sc[:,3] * 10; pipeline/obs_contract.py:569,614-615',
                         'row_source': 'pipeline/dataset.py:1-19,134-150; accepted plays, gate==1 only',
                         'caveat': 'Existing replay-engine states for the Icebow corpus; original live elixir and player pro status are not independently verified. Not a causal or skill ranking.'}
    return result


def aggregate(matches, recorded):
    plays = [p for m in matches for p in m['plays']]
    card = {c: {'plays_n': sum(m['counts'][c] for m in matches),
                'per_match': describe(m['counts'][c] for m in matches),
                'per_match_distribution': hist(m['counts'][c] for m in matches),
                'elixir_at_play': describe(p['elixir'] for p in plays if p['name'] == c),
                'share': frac(sum(p['name'] == c for p in plays), len(plays)),
                'receipts': dict(collections.Counter(p['receipt'] for p in plays if p['name'] == c))}
            for c in NAMES}
    wins = {}
    for name, has in [('rocket_ge_1', True), ('rocket_0', False)]:
        group = [m for m in matches if (m['counts']['Rocket'] > 0) == has]
        c = collections.Counter(m['outcome'] for m in group)
        wins[name] = {'matches_n': len(group), 'outcomes': dict(c), 'win_rate_known': frac(c['win'], c['win']+c['loss'])}
    opp = [x for m in recorded for x in m['B']['opportunities']]
    xb = [x for m in recorded for x in m['B']['xbow']]
    off = [x for x in xb if not x['defensive']]
    one = [x for x in xb if x['at_one_one']]
    end = [m for m in recorded if m['end_covered']]
    b = {'recorded_matches_n': len(recorded), 'end_covered_matches_n': len(end),
         'opportunities': {'periods_n': len(opp), 'matches_n': len({x['file'] for x in opp}),
                           'towers_n': len({(x['file'], x['lane']) for x in opp}),
                           'any_rocket_response_periods_n': sum(bool(x['any_rocket_attempt_ticks']) for x in opp),
                           'died_other_unique_towers_n': len({(x['file'], x['lane']) for x in opp if x['status'] == 'died_other'}),
                           'died_other_within_grace_periods_n': sum(x['status'] == 'died_other' and x['death_within_grace'] for x in opp),
                           'statuses': dict(collections.Counter(x['status'] for x in opp)), 'periods': opp},
         'concentration_end_covered': describe(m['B']['damage']['concentration'] for m in end if m['B']['damage']['concentration'] is not None),
         'concentration_all_observed': describe(m['B']['damage']['concentration'] for m in recorded if m['B']['damage']['concentration'] is not None),
         'both_low_end_matches': [{'file': m['file'], 'outcome': m['outcome'],
                                   'left_hp': m['towers']['enemy_left']['final_hp'],
                                   'right_hp': m['towers']['enemy_right']['final_hp']}
                                  for m in end if m['B']['damage']['both_below_half_neither_destroyed_end']],
         'xbow': {'placements_n': len(xb), 'matches_n': len({x['file'] for x in xb}),
                  'defensive': frac(sum(x['defensive'] for x in xb), len(xb)),
                  'offensive_n': len(off), 'offensive_lane_state': dict(collections.Counter(x['lane_state'] for x in off)),
                  'offensive_dead_lane': frac(sum(x['lane_state'] == 'dead' for x in off), sum(x['lane_state'] != 'unknown' for x in off)),
                  'all_lane_state': dict(collections.Counter(x['lane_state'] for x in xb)),   # lead 10-03: every X-Bow
                  'all_lane_state_by_crowns': {str(k): v for k, v in collections.Counter(
                      (x['lane_state'], tuple(x['crowns_ours_enemy']) if x.get('crowns_ours_enemy') else None) for x in xb).items()},
                  'one_one_n': len(one), 'one_one_matches_n': len({x['file'] for x in one}),
                  'one_one_destinations': dict(collections.Counter(('defensive_' if x['defensive'] else 'offensive_') + x['lane_state'] for x in one)),
                  'one_one_placements': one,
                  'receipt_counts': dict(collections.Counter(x['receipt'] for x in xb)),
                  'confirmed_spawn_n': sum(x['spawn_defensive'] is not None for x in xb),
                  'confirmed_spawn_defensive_n': sum(x['spawn_defensive'] is True for x in xb)}}
    b['tower_validation'] = {
        'towers_n': len(recorded)*6,
        'princess_max_hp_distribution': hist(t['max_hp'] for m in recorded for k,t in m['towers'].items() if not k.endswith('king')),
        'king_max_hp_distribution': hist(t['max_hp'] for m in recorded for k,t in m['towers'].items() if k.endswith('king')),
        'kinds_observed': sorted({v for m in recorded for t in m['towers'].values() for v in t['kinds']}),
        'address_reused_towers_n': sum(t['address_reuse_samples'] > 0 for m in recorded for t in m['towers'].values()),
        'hp_increase_steps_n': sum(t['hp_increases'] for m in recorded for t in m['towers'].values()),
        'transient_missing_samples_n': sum(t['missing_transient_samples'] for m in recorded for t in m['towers'].values()),
        'death_evidence': dict(collections.Counter(t['death_evidence'] or 'alive_at_endpoint' for m in recorded for t in m['towers'].values()))}
    return {'matches_n': len(matches), 'plays_n': len(plays), 'cards': card, 'win_split_descriptive_only': wins,
            'rocket_zero_matches': frac(sum(m['counts']['Rocket'] == 0 for m in matches), len(matches)),
            'xbow_defensive_all': frac(sum(p['xy'][1] > .58 for p in plays if p['name'] == 'Xbow'), sum(p['name'] == 'Xbow' for p in plays))}, b


def check_logic():
    # Small positive/negative controls for the most consequential audit definitions.
    assert xy([0, 3500, 6500], 0) == [3500/18000, 1-6500/32000]
    assert xy([0, 3500, 6500], 1) == [14500/18000, 6500/32000]
    fs = [{'t_dev': i/10, 'elixir': 6} for i in range(22)]
    assert periods(fs, [497]*22, 497) == [(0, 21)]
    assert not periods(fs, [498]*22, 497)
    assert not periods(fs[:20], [497]*20, 497)
    assert not periods(fs, [0]*22, 497)
    fs[10]['elixir'] = 5.99
    assert not periods(fs, [497]*22, 497)


def main():
    check_logic()
    selected, excluded, manifest = load_matches()
    nav_n = pair_nav(selected, manifest)
    matches = [m for m in selected if m['plays'] or m['frames']]
    no_battle = [m['file'] for m in selected if not m['plays'] and not m['frames']]
    recorded = [m for m in matches if m['frames']]
    for m in recorded:
        towers_for(m)
    damage = rocket_damage(recorded)
    for m in recorded:
        recorded_metrics(m, damage['used_hp'])
    a, b = aggregate(matches, recorded)
    pro = pro_metrics()
    pairs = [m for m in matches if m['nav_pair']]
    concerns = [
        'Source logs grew during inspection. input_manifest.json freezes the first successful audit file list and byte prefixes; reruns verify SHA-256 and ignore later appends/new logs.',
        'Play events are decisions/tap attempts; receipt counts are reported separately. A confirmed cast is not proof of a Rocket kill.',
        'Frame logs are a recording-selected subset, not a random sample. No hand contents are logged: HP/elixir opportunities do not establish Rocket availability.',
        'Rocket damage is measured from repeated HP steps; exact card level and exclusive damage attribution are not recorded.',
        'Tower destruction is inferred from persistent disappearance when zero HP is absent; final-frame damage can include king-collapse and tiebreak effects.',
        'Opportunity periods use sampled device time, split on gaps over 0.5 s; counts are period-level and can revisit the same tower.',
        'Rocket-on-tower uses a declared 3.5-tile centre-distance proxy; confirmed-target casts and causal kills are distinct.',
        'All logged X-Bows are defensive under the requested y>0.58 rule; there is no offensive sample for a dead-lane rate.',
        'S1 comparison uses accepted replay-engine plays and simulated elixir; mixed-deck generalist share is contextual only, and original player pro status is unverified.',
    ]
    incomplete = [m['file'] for m in matches if not m['end']]
    censored = [m['file'] for m in recorded if not m['end_covered']]
    unknown = [m['file'] for m in matches if m['outcome'] not in ['win', 'loss']]
    if incomplete:
        concerns.insert(0, f'{len(incomplete)} begun match log(s) lack an end event; included in observed-play counts and excluded from end-state claims: '+', '.join(incomplete))
    if censored:
        concerns.insert(1, f'{len(censored)}/{len(recorded)} recordings lack covered normal match ends: '+', '.join(censored))
    if unknown:
        concerns.insert(2, f'{len(unknown)}/{len(matches)} matches lack a binary paired outcome: '+', '.join(unknown))
    # Sensitivity is recomputed from the same snapshots, never by re-driving anything.
    sensitivity = {}
    for threshold in sorted({damage['table_crown_damage'], damage['used_hp']}):
        sensitivity[str(threshold)] = sum(len(periods(m['frames'], m['towers'][k]['hp'], threshold))
                                          for m in recorded for k in ['enemy_left', 'enemy_right'])
    data = {'scope': {'selected_logs_n': len(selected), 'begun_matches_n': len(matches),
                      'empty_sessions': no_battle, 'excluded_by_ckpt': excluded, 'no_end_matches': incomplete,
                      'nav_logs_n': nav_n, 'pairings_succeeded_n': len(pairs),
                      'pairing_gap_seconds': describe(m['nav_pair']['gap_seconds'] for m in pairs),
                      'binary_outcomes_n': len(matches)-len(unknown), 'recorded_matches_n': len(recorded)},
            'rocket_damage': damage, 'A': a, 'B': b, 'C': pro, 'concerns': concerns,
            'threshold_sensitivity_period_counts': sensitivity, 'source_manifest': manifest,
            'matches': []}
    data['artifact_sources'] = []
    for p in [CARD_TABLE, ROOT/'icebow/data/pipeline/gen_dataset_v2.json', ROOT/'icebow/data/pipeline/s1_dataset.npz',
              ROOT/'pipeline/dataset.py', ROOT/'pipeline/obs_contract.py', LOGS/'live_play.py']:
        raw = p.read_bytes()
        data['artifact_sources'].append({'path': rel(p), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})
    for m in matches:
        item = {k: v for k, v in m.items() if k not in ['frames', 'towers', 'frame_ticks']}
        if 'towers' in m:
            item['towers'] = {k: {a: v for a, v in t.items() if a != 'hp'} for k, t in m['towers'].items()}
        data['matches'].append(item)
    assert sum(c['plays_n'] for c in a['cards'].values()) == a['plays_n']
    assert sum(b['opportunities']['statuses'].values()) == b['opportunities']['periods_n']
    assert all(not p['parse_errors'] for p in manifest), 'Malformed source JSONL; inspect manifest'
    data['xbow_y_values'] = dict(collections.Counter(str(p['xy'][1]) for m in matches for p in m['plays'] if p['name'] == 'Xbow'))   # was an assert (all 0.6094); lead 10-03
    if not FROZEN:
        MANIFEST.write_text(json.dumps({'note': 'Frozen read-only input file list and byte prefixes; future appends are excluded.', 'files': manifest}, indent=2)+'\n', encoding='utf-8')
    summary, md = render(data)
    data['summary_lines'] = summary
    (OUT / 'audit.json').write_text(json.dumps(data, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    (OUT / 'audit.md').write_text(md, encoding='utf-8')
    # Verify serialized deliverables, not merely in-memory objects.
    saved = json.loads((OUT / 'audit.json').read_text(encoding='utf-8'))
    assert saved['summary_lines'] == (OUT / 'audit.md').read_text(encoding='utf-8').splitlines()[:len(summary)]
    print('\n'.join(summary))
    print('AUDIT_OK')


def render(d):
    a, b, c, scope = d['A'], d['B'], d['C'], d['scope']
    n, nr = a['matches_n'], b['recorded_matches_n']
    rc = a['cards']['Rocket']; zero = a['rocket_zero_matches']; o = b['opportunities']; x = b['xbow']
    states = o['statuses']; known = scope['binary_outcomes_n']; endn = b['end_covered_matches_n']
    conc = b['concentration_end_covered']; both = b['both_low_end_matches']
    summary = [
        f"Audited {n} begun matches ({scope['selected_logs_n']} selected logs; {len(scope['empty_sessions'])} empty session excluded), with {nr} recordings and {a['plays_n']} play attempts.",
        f"Paired {scope['pairings_succeeded_n']}/{n} matches to navigation runs; {known}/{n} have win/loss outcomes.",
        f"Rocket: {rc['plays_n']}/{a['plays_n']} plays ({100*rc['plays_n']/a['plays_n']:.2f}%); zero in {pct(zero['count'], zero['n'])} matches; median play elixir {rc['elixir_at_play']['median']:.2f} (n={rc['plays_n']} plays).",
        'Win rates with/without Rocket: '+ '; '.join(f"{label} {pct(a['win_split_descriptive_only'][key]['win_rate_known']['count'], a['win_split_descriptive_only'][key]['win_rate_known']['n'])}" for key, label in [('rocket_ge_1','with'),('rocket_0','without')])+'; descriptive only.',
        f"At measured {d['rocket_damage']['used_hp']}-HP Rocket damage (n={d['rocket_damage']['supporting_steps_n']} drops), {o['periods_n']} finish-off periods across {o['matches_n']}/{nr} recordings: {states.get('converted_rocket_cast',0)} Rocket conversions, {states.get('died_other',0)} other deaths, {states.get('expired_survived_end',0)} survived to end, {states.get('censored',0)+states.get('death_cause_ambiguous',0)} unresolved (n={o['periods_n']} periods).",
        f"Median damage concentration: {100*conc['median']:.1f}% (n={conc['n']} end-covered matches); both enemy princess towers below half, neither destroyed: {len(both)}/{endn} end-covered matches.",
        f"Recorded X-Bows: {pct(x['defensive']['count'], x['defensive']['n'])} defensive; {pct(x['offensive_dead_lane']['count'], x['offensive_dead_lane']['n'])} offensive placements in a dead lane.",
        f"At 1-1: {x['one_one_n']} X-Bows across {x['one_one_matches_n']} recordings; {sum(not p['remaining_princess_target'] for p in x['one_one_placements'])} in the destroyed-princess lane, {sum(p['remaining_princess_target'] for p in x['one_one_placements'])} in the remaining-princess lane (n={x['one_one_n']} placements).",
    ]
    if c['s1']['available']:
        s = c['s1']; r = s['cards']['rocket']['elixir_at_play']
        summary.append(f"S1 Icebow replay proxy: Rocket {pct(s['rocket_rows_n'],s['play_rows_n'])} of plays; median simulated elixir {r['median']:.2f} (n={r['n']} Rocket plays; {s['replays_with_plays_n']} replays).")
    summary.append(f"Limits: {len(scope['no_end_matches'])}/{n} begun logs lack an end; {nr-endn}/{nr} recordings lack covered normal ends; hand availability and causal Rocket kills are unverified.")
    assert len(summary) <= 10
    lines = summary + ['', '## Scope and methods', '',
        'This is a descriptive audit of existing files, with no bot changes or play-quality verdict. '
        'A includes every selected log with a play or frame; empty sessions are excluded. Partial matches contribute only observed plays. '
        'All card and placement counts use `play` decisions, with confirmation receipts retained in JSON.', '',
        'Inputs: `scratchpad/gauntlet/L68/live_reader/live_play_20261002_2*.jsonl` and `live_play_20261003_*.jsonl`, '
        'filtered by `start.ckpt` containing `league1c`; navigation glob `ladder_nav_2026100[23]_*.jsonl`. '
        'Every input snapshot has a byte count and SHA-256 in `audit.json.source_manifest`. '
        '`input_manifest.json` freezes the first successful audit file list and exact byte prefixes because source logs were growing. '
        'Later runs read only those prefixes and reject hash mismatches; new logs and appended bytes are excluded. '
        'Card/dataset/source-code artifact hashes are in `artifact_sources`.', '',
        'Outcome pairing: filename local EDT start + `end.seconds` estimates the log end. Require exactly one nav start in [-1, +30] seconds, '
        'before the next selected live log starts, and enforce one-to-one use. The filename has one-second resolution; setup before the elapsed-time timer can add a few seconds. '
        'Missing/null outcomes are excluded from binary win-rate denominators, not counted as losses.', '',
        f"Pairing gaps: median {scope['pairing_gap_seconds']['median']:.2f} s, range {scope['pairing_gap_seconds']['min']:.2f}–{scope['pairing_gap_seconds']['max']:.2f} s (n={scope['pairing_gap_seconds']['n']} pairs). "
        f"Empty sessions (n={len(scope['empty_sessions'])}): {', '.join(scope['empty_sessions']) or 'none'}.", '',
        'Tower identification: choose the largest-max-HP entity within 500 native units of each expected static location in the first frame; '
        'verify card_id=-1 and match address, side, position and max HP together. Freed addresses can be reused by troops; those are not towers. Native princess centres are (3500,6500)/(14500,6500) for side 0 and '
        '(3500,25500)/(14500,25500) for side 1; kings are (9000,3000)/(9000,29000). Kind alone is not used, because it changes. '
        'Our coordinates exactly follow `live_play.py:158-160`: side 0=(x/18000,1-y/32000), side 1=(1-x/18000,y/32000). '
        'Our-frame x<0.5 is left; enemy princess y=0.203125. Tower HP/max HP and observed kinds appear per match in JSON.', '',
        'A tower is dead after explicit zero HP or disappearance lasting at least three samples and 0.19 seconds through the recording end, '
        'backdated to first absence. Short missing runs remain unknown. The last observed state counts as match-end-covered only with a normal battle-over stop '
        'within 20 ticks (1 game second). Tick-stalled and missing-end recordings are censored. Final observed state is still reported for all recordings.', '',
        'Finish-off periods: maximal continuous sampled runs with 0<enemy princess HP<=497 and our elixir>=6, duration>=2 seconds on `t_dev`; '
        'gaps>0.5 seconds or failed/unknown conditions break a run. Dead towers are excluded. A response is a confirmed Rocket cast aimed within 3.5 tiles '
        'of that tower centre, during the run or through +5 seconds. This is an operational targeting proxy, not verified hitbox geometry or proof of a kill. '
        'If no response, classify a later tower death as other only if no nearby confirmed Rocket was cast in its preceding 7 seconds and no simultaneous king collapse; '
        'otherwise mark ambiguous. A surviving tower requires a covered end; all other cases are censored. Each period is counted, so repeated periods can share one eventual death.', '',
        'Damage concentration = max(maxHP-left_finalHP, maxHP-right_finalHP) / summed enemy princess HP loss. '
        'Unknown HP or zero total damage makes the ratio undefined. Missing destroyed towers are zero as above. '
        'These are HP-loss totals, not attacker-attributed damage; king-collapse and tiebreak HP changes are included. '
        'The both-below-half test is strictly 0<HP<0.5*maxHP for both towers.', '',
        'X-Bow classification uses intended play xy and the last frame at or before the play (maximum age 10 ticks). '
        'Defensive means y>0.58; every other placement is offensive. Dead-lane means the enemy princess in that x lane is dead. '
        'A 1-1 score requires one destroyed princess on each side and both kings alive; unknown states remain unclassified. '
        'The per-placement JSON also retains receipt and observed spawn coordinates.', '',
        '## Rocket damage evidence', '',
        f"`{d['rocket_damage']['table_source']}` says level {d['rocket_damage']['table_level']} crown damage {d['rocket_damage']['table_crown_damage']} HP. "
        f"The bot's Rocket level is not logged. Use the repeated measured {d['rocket_damage']['used_hp']}-HP drop instead "
        f"(n={d['rocket_damage']['supporting_steps_n']} supporting steps / {d['rocket_damage']['candidate_steps_n']} candidate steps). "
        'Candidates are positive, nonlethal 300–700 HP steps within 3–6 seconds of a confirmed nearby Rocket, with adjacent frames no more than 0.5 seconds apart.', '',
        '| Match | Rocket tick | HP-step ticks | HP before → after | Drop | Delay (s) |',
        '|---|---:|---|---|---:|---:|']
    for e in d['rocket_damage']['evidence']:
        lines.append(f"| {e['file']} | {e['play_tick']} | {e['before_tick']}→{e['after_tick']} | {e['before_hp']}→{e['after_hp']} | {e['drop']} | {e['lag_seconds']:.3f} |")
    shots = [(m['file'], p) for m in d['matches'] if 'B' in m for p in m['B']['rocket_plays']]
    lines += ['', f'Recorded Rocket attempts (n={len(shots)} plays in {nr} recordings); nearest-princess HP at play and later disappearance timing:', '',
              '| Match | Play tick | Receipt | Nearest tower | Distance (tiles) | HP at play | Later death delay (s) |',
              '|---|---:|---|---|---:|---:|---:|']
    for file, p in shots:
        lag = f"{p['death_delay_seconds']:.3f}" if p['death_delay_seconds'] is not None else 'not observed'
        lines.append(f"| {file} | {p['tick']} | {p['receipt']} | {p['nearest_tower']} | {p['distance_tiles']:.3f} | {p['hp_at_play']} | {lag} |")
    lines += ['', f"Threshold sensitivity (same n={nr} recordings): "+', '.join(f'{k} HP: {v} periods' for k,v in d['threshold_sensitivity_period_counts'].items())+'.', '',
              '## A. All begun matches', '', f'All per-match distributions include zeros (n={n} matches). Elixir denominators are play attempts.', '',
              '| Card | Plays / all plays | Mean/match | Median/match | Counts per match: matches | Median elixir (n plays) | Receipts |',
              '|---|---|---:|---:|---|---|---|']
    for card, v in a['cards'].items():
        lines.append(f"| {card} | {pct(v['plays_n'],a['plays_n'])} | {v['per_match']['mean']:.3f} | {v['per_match']['median']} | {json.dumps(v['per_match_distribution'])} | {v['elixir_at_play']['median']:.4f} (n={v['elixir_at_play']['n']}) | {json.dumps(v['receipts'])} |")
    lines += ['', '| Rocket group | Matches | W / L / null / unknown | Win rate (known binary outcomes) |', '|---|---:|---|---|']
    for name, v in a['win_split_descriptive_only'].items():
        oc = v['outcomes']; wr = v['win_rate_known']
        lines.append(f"| {name} | {v['matches_n']} | {' / '.join(str(oc.get(k,0)) for k in ['win','loss','null','unknown'])} | {pct(wr['count'],wr['n'])} |")
    lines += ['', 'Descriptive only: match duration, deck/opponent, match state, and selection can affect both Rocket use and outcome; this split does not estimate an effect of playing Rocket.', '',
              f"All-log X-Bow defensive placement share: {pct(a['xbow_defensive_all']['count'],a['xbow_defensive_all']['n'])}.", '',
              '## B. Recorded matches', '',
              f"Frame sample n={nr}; covered normal ends n={endn}; opportunities n={o['periods_n']} periods on {o['towers_n']} towers in {o['matches_n']} matches. "
              f"Status counts (denominator {o['periods_n']} periods): {json.dumps(states, sort_keys=True)}.", '',
              f"Any Rocket attempted anywhere during period/+5 s: {o['any_rocket_response_periods_n']}/{o['periods_n']} periods; thus the zero-conversion finding does not depend on target-radius choice. "
              f"Other-death periods refer to {o['died_other_unique_towers_n']} unique towers; {o['died_other_within_grace_periods_n']}/{states.get('died_other',0)} such period outcomes died within +5 s, with the rest dying later in the recording.", '',
              '| Match | Lane | Start–end tick | Duration (s) | Start/min HP | Status | Rocket attempt ticks | Death tick | Outcome |',
              '|---|---|---|---:|---|---|---|---|---|']
    for p in o['periods']:
        lines.append(f"| {p['file']} | {p['lane']} | {p['start_tick']}–{p['end_tick']} | {p['duration_seconds']:.2f} | {p['start_hp']}/{p['minimum_hp']} | {p['status']} | {p['targeted_attempt_ticks']} | {p['death_tick']} | {p['outcome']} |")
    tv = b['tower_validation']
    lines += ['', f"Tower validation (n={tv['towers_n']} towers): princess max-HP distribution (n={nr*4}) {json.dumps(tv['princess_max_hp_distribution'])}; "
              f"king max-HP distribution (n={nr*2}) {json.dumps(tv['king_max_hp_distribution'])}. "
              f"Address reuse after removal affects {tv['address_reused_towers_n']}/{tv['towers_n']} towers and is ignored. "
              f"Death/endpoint classifications (n={tv['towers_n']}): {json.dumps(tv['death_evidence'])}. "
              f"HP increases: {tv['hp_increase_steps_n']}; transient missing samples: {tv['transient_missing_samples_n']} (over all {tv['towers_n']} tower tracks)."]
    lines += ['', f"Damage concentration at covered ends: median {conc['median']:.4f}, mean {conc['mean']:.4f} (n={conc['n']}). "
              f"All observed recording endpoints, including censored: median {b['concentration_all_observed']['median']:.4f} (n={b['concentration_all_observed']['n']}).", '',
              '| Match | End covered | Enemy left HP/max | Enemy right HP/max | Left/right damage | Concentration | Both low at end | Outcome |',
              '|---|---|---|---|---|---:|---|---|']
    for m in d['matches']:
        if 'B' not in m:
            continue
        dm=m['B']['damage']; l=m['towers']['enemy_left']; r=m['towers']['enemy_right']
        value = f"{dm['concentration']:.4f}" if dm['concentration'] is not None else 'undefined'
        lines.append(f"| {m['file']} | {dm['end_covered']} | {l['final_hp']}/{l['max_hp']} | {r['final_hp']}/{r['max_hp']} | {dm['left']}/{dm['right']} | {value} | {dm['both_below_half_neither_destroyed_end']} | {m['outcome']} |")
    lines += ['', f"Both low, neither destroyed at covered end: {len(both)}/{endn} matches; outcomes (n={len(both)}): {json.dumps(dict(collections.Counter(q['outcome'] for q in both)))}. The qualifying matches are marked above.", '',
              f"Intended X-Bow y distribution, all logs (n={a['cards']['Xbow']['plays_n']} placements): " + json.dumps(d['xbow_y_values']) + '.', '',
              f"Recorded X-Bow placements n={x['placements_n']} in {x['matches_n']}/{nr} matches. Defensive {pct(x['defensive']['count'],x['defensive']['n'])}; "
              f"offensive n={x['offensive_n']}, lane states {json.dumps(x['offensive_lane_state'])}. "
              f"Receipts (n={x['placements_n']}): {json.dumps(x['receipt_counts'])}. "
              f"Observed-spawn defensive share: {pct(x['confirmed_spawn_defensive_n'],x['confirmed_spawn_n'])} (only receipts with spawn coordinates).", '',
              f"1-1 placements: n={x['one_one_n']} in {x['one_one_matches_n']} matches. Each row is one placement; all placements are also in JSON.", '',
              '| Match | Tick | Intended xy | Defensive | Lane | Enemy lane HP | Remaining princess lane | Receipt |',
              '|---|---:|---|---|---|---:|---|---|']
    for p in x['one_one_placements']:
        lines.append(f"| {p['file']} | {p['tick']} | {p['xy']} | {p['defensive']} | {p['lane']} | {p['enemy_lane_hp']} | {p['remaining_princess_target']} | {p['receipt']} |")
    lines += ['', '## C. Existing replay comparison', '']
    g=c['generalist_metadata']; gs=g['rocket_share']
    lines.append(f"Generalist metadata `{g['source']}`: Rocket {pct(gs['count'],gs['n'])} across {g['replays_n']} source replays. {g['caveat']}")
    if c['s1']['available']:
        s=c['s1']
        lines += ['', f"S1 `{s['source']}`: {s['play_rows_n']} accepted PLAY rows, {s['replays_with_plays_n']} replays, {s['replay_sides_with_plays_n']} replay sides. "
                  f"Use `y_gate==1`, card slot from embedded `meta.cards`, and {s['elixir_source']}. "
                  'WAIT rows are excluded; dataset is the unaugmented, unshifted S1 file. '
                  f"{s['caveat']}", '', '| Card | Share of S1 plays | Median simulated elixir (n plays) |', '|---|---|---|']
        for card,v in s['cards'].items():
            lines.append(f"| {card} | {pct(v['share']['count'],v['share']['n'])} | {v['elixir_at_play']['median']:.4f} (n={v['elixir_at_play']['n']}) |")
    lines += ['', 'For a verified live-pro elixir comparison, the needed data are player/provenance labels plus original time-aligned card-play and pre-play elixir observations for matching Icebow decks. Existing S1 engine-derived states cannot verify those facts.', '',
              '## Concerns', ''] + ['- '+v for v in d['concerns']]
    lines += ['', '## Reproduction', '', '`python scratchpad/gauntlet/L70/audit/play_audit.py`', '',
              'Single process; standard library plus numpy for selective S1 arrays. No device connections, project imports, engine execution, GPU work, or writes outside this audit directory.', '']
    return summary, '\n'.join(lines)


if __name__ == '__main__':
    main()
