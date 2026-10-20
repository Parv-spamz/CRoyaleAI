"""CPU-only, read-only corpus mining. Run from anywhere; outputs beside this script.

No project/engine imports. Two streaming passes, bounded parquet batches, one thread.
Card attribution is evidence-based inference, never a claim of observed unit life.
"""
from __future__ import annotations

import argparse
import bisect
from collections import Counter, defaultdict
import gzip
import hashlib
import json
import math
from pathlib import Path
import re
import time
import sys
from functools import lru_cache

import pyarrow as pa
import pyarrow.parquet as pq
try:
    import ujson
    parse_json = ujson.loads
except ImportError:
    parse_json = json.loads

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
DATA = ROOT / 'scratchpad/gauntlet/L67/hf/replays'
# Reuse the installed third-party parser if available; do not install anything.
try:
    import orjson
except ImportError:
    sys.path.append(str(ROOT/'icebow/.venv/Lib/site-packages'))
    try:
        import orjson
    except ImportError:
        orjson = None
if orjson:
    parse_json = orjson.loads


def compact_json(value):
    return orjson.dumps(value).decode('utf-8') if orjson else json.dumps(value, separators=(',', ':'))
CHAMPIONS = {'archer-queen', 'golden-knight', 'skeleton-king', 'mighty-miner',
             'monk', 'little-prince', 'goblinstein', 'boss-bandit'}
PHASES = ['0-60', '60-120', '120-180', 'OT']
pa.set_cpu_count(1)
pa.set_io_thread_count(1)


@lru_cache(maxsize=2048)
def base(card):
    return re.sub(r'-(?:hero|ev\d+)$', '', card or '')


@lru_cache(maxsize=2048)
def is_ability(card):
    return bool(card and ('-hero' in card or base(card) in CHAMPIONS))


def quantiles(values):
    a = sorted(values)
    def q(p):
        k = (len(a) - 1) * p
        lo, hi = math.floor(k), math.ceil(k)
        return round(a[lo] + (a[hi] - a[lo]) * (k - lo), 4)
    return {'n': len(a), **{name: q(p) if a else None for name, p in
            [('min', 0), ('p10', .1), ('p25', .25), ('p50', .5), ('p75', .75), ('p90', .9), ('p95', .95), ('max', 1)]}}


def shares(counts, keys=None):
    keys = list(counts) if keys is None else keys
    n = sum(counts.values())
    return {'n': n, 'counts': {k: counts.get(k, 0) for k in keys},
            'percent': {k: round(100 * counts.get(k, 0) / n, 4) if n else None for k in keys}}


def phase(t):
    return PHASES[min(3, int(t // 60))] if t is not None and t >= 0 else 'unknown'


def event_time(e):
    tick = e.get('replay_tick_20hz')
    return float(tick) / 20 if tick is not None else e.get('time_seconds')


def position(e):
    co = e.get('coordinates') or {}
    native = co.get('native_world_units') or {}
    x, y = native.get('x'), native.get('y')
    if x is None or y is None or not (0 <= x <= 18000 and 0 <= y <= 32000):
        return None
    side = e.get('side')
    # Schema's native frame: blue/team at bottom, x in [0,18000], y in [0,32000].
    lane = 'left' if x < 9000 else 'right' if x > 9000 else 'center'
    half = 'midline' if y == 16000 else 'own' if ((y < 16000) == (side == 'team')) else 'enemy'
    return {'x': x, 'y': y, 'lane_from_blue': lane, 'half': half}


def deploy_card(e, decks):
    """Keep form suffixes; resolve base events to a unique matching deck slot only."""
    return match_deck(e.get('card_key') or '', tuple(decks.get(e.get('side'), [])),
                      tuple(e.get('deck_card_key_candidates') or []))


@lru_cache(maxsize=100000)
def match_deck(key, deck, hints):
    if is_ability(key) and key in deck:
        return key
    options = [c for c in deck if base(c) == base(key)]
    hinted = [c for c in hints if c in options]
    if hinted:
        options = hinted
    return options[0] if len(options) == 1 and is_ability(options[0]) else None


def prepare(d):
    decks = {s: [c['card_key'] for p in d['battle'][s].get('players', []) for c in p.get('deck', [])]
             for s in ('team', 'opponent')}
    events = []
    for i, e in enumerate(d.get('events', [])):
        t = event_time(e)
        events.append((float('inf') if t is None else t, i, e))
    events.sort(key=lambda x: (x[0], x[1]))
    return decks, events


def resolve(candidates, latest, t, windows, scale=1):
    ages = {c: round(t - latest[c]['time'], 6) for c in candidates if c in latest and t is not None}
    eligible = [c for c, age in ages.items() if 0 <= age <= windows.get(c, 45) * scale]
    if len(candidates) == 1:
        return candidates[0], 'single_candidate', ages, eligible
    if len(eligible) == 1:
        return eligible[0], 'resolved_multiple', ages, eligible
    return None, 'multiple_plausible' if eligible else 'no_plausible_candidate', ages, eligible


def rows(files, label):
    if label == 'mine':
        last = None
        fi = 0
        with gzip.open(OUT/'compact_replays.jsonl.gz', 'rt', encoding='utf-8') as f:
            for line in f:
                filename, ri, tag, d = parse_json(line)
                if last is not None and filename != last:
                    fi += 1
                    print(f'mine {fi}/{len(files)} {last}; elapsed {time.monotonic()-START:.1f}s', flush=True)
                last = filename
                yield DATA/filename, ri, tag, 'unique', d
        print(f'mine {len(files)}/{len(files)} {last}; elapsed {time.monotonic()-START:.1f}s', flush=True)
        return
    seen = {}
    for fi, path in enumerate(files, 1):
        pf = pq.ParquetFile(path)
        ri = 0
        for batch in pf.iter_batches(batch_size=128, columns=['payload_json'], use_threads=False):
            for raw in batch.column(0).to_pylist():
                d = parse_json(raw)
                tag = (d.get('source') or {}).get('replay_tag') or f'{path.name}:{ri}'
                digest = hashlib.sha256(raw.encode()).hexdigest()
                status = 'unique' if tag not in seen else 'duplicate' if seen[tag] == digest else 'conflicting_duplicate'
                seen.setdefault(tag, digest)
                yield path, ri, tag, status, d
                ri += 1
        print(f'{label} {fi}/{len(files)} {path.name}: {ri:,} rows; elapsed {time.monotonic()-START:.1f}s', flush=True)


def calibrate(files):
    delays = defaultdict(list)
    inv = {k: Counter() for k in ['row_status', 'schema', 'event_kinds', 'event_fields', 'candidate_count',
                                'authoritative', 'deck_abilities', 'candidate_abilities', 'battle_type',
                                'coordinate_keys', 'press_nonnull_fields', 'validation_warnings']}
    file_rows = Counter()
    audit = Counter()
    compact = gzip.open(OUT/'compact_replays.jsonl.gz', 'wt', encoding='utf-8', compresslevel=1)
    for path, ri, tag, status, d in rows(files, 'inventory'):
        file_rows[path.name] += 1
        inv['row_status'][status] += 1
        if status != 'unique':
            continue
        inv['schema'][d.get('schema_version')] += 1
        inv['battle_type'][d['battle'].get('battle_type', 'unknown')] += 1
        decks, events = prepare(d)
        minimal = {'battle': {s: {'crowns': d['battle'][s].get('crowns'),
                    'players': [{'deck': [{'card_key': c} for c in decks[s]]}]} for s in decks}, 'events': []}
        for e in d.get('events', []):
            small = {k: e[k] for k in ('kind','side','card_key','replay_tick_20hz','source_index') if k in e}
            if e.get('kind') == 'activate_ability':
                small.update(ability_source_candidates=e.get('ability_source_candidates'),
                             ability_source_authoritative=e.get('ability_source_authoritative'))
            elif deploy_card(e,decks):
                small['deck_card_key_candidates'] = e.get('deck_card_key_candidates')
            if e.get('replay_tick_20hz') is None:
                small['time_seconds'] = e.get('time_seconds')
            if e.get('kind') == 'activate_ability' or (e.get('kind') == 'play_card' and deploy_card(e,decks)):
                small['coordinates'] = {'native_world_units': (e.get('coordinates') or {}).get('native_world_units')}
            minimal['events'].append(small)
        compact.write(compact_json([path.name,ri,tag,minimal])+'\n')
        for deck in decks.values():
            inv['deck_abilities'].update(c for c in deck if is_ability(c))
        latest = defaultdict(dict)
        for t, ei, e in events:
            kind, side = e.get('kind'), e.get('side')
            inv['event_kinds'][kind] += 1
            inv['event_fields'].update(e.keys())
            if not math.isfinite(t):
                audit['events_missing_time'] += 1
                continue
            if e.get('time_seconds') is not None and abs(e['time_seconds'] - t) > .051:
                audit['tick_time_disagreements'] += 1
            if kind == 'play_card':
                card = deploy_card(e, decks)
                if card:
                    latest[side][card] = t
                    audit['ability_deployments'] += 1
                    audit['deployment_form_inferred_from_deck'] += int(e.get('card_key') != card)
                continue
            if kind != 'activate_ability':
                continue
            cand = list(dict.fromkeys(e.get('ability_source_candidates') or []))
            inv['candidate_abilities'].update(cand)
            inv['candidate_count'][str(len(cand))] += 1
            inv['authoritative'][str(e.get('ability_source_authoritative'))] += 1
            inv['press_nonnull_fields'].update(k for k, v in e.items() if v is not None and v != [])
            inv['coordinate_keys'].update((e.get('coordinates') or {}).keys())
            audit['press_coordinates_nonnull'] += int(e.get('coordinates') is not None)
            audit['press_coordinates_valid'] += int(position(e) is not None)
            if len(cand) == 1 and cand[0] in latest[side]:
                delays[cand[0]].append(t - latest[side][cand[0]])
    compact.close()
    all_delays = [x for a in delays.values() for x in a]
    global_p95 = quantiles(all_delays)['p95'] or 45
    cards = sorted(set(inv['deck_abilities']) | set(inv['candidate_abilities']))
    calibration = {}
    for c in cards:
        qs = quantiles(delays[c])
        raw = qs['p95'] if qs['n'] >= 30 else global_p95
        calibration[c] = {'window_seconds': round(max(10, min(90, raw)), 4),
                          'basis': 'card_single_candidate_p95' if qs['n'] >= 30 else 'pooled_p95_fewer_than_30_samples',
                          'single_candidate_delay_seconds': qs}
    return {'counts': inv, 'audit': audit, 'file_rows': file_rows, 'calibration': calibration}


def new_stats():
    return {'presses': 0, 'battles': set(), 'deck_battles': set(), 'deployment_battles': set(),
            'attribution': Counter(), 'unresolved_candidate_mentions': 0,
            'unresolved_plausible_mentions': 0, 'deployments': 0, 'deployment_press_counts': Counter(),
            'linked_presses': 0, 'unlinked_presses': 0, 'linked_outside_window': 0,
            'delay': [], 'first_delay': [], 'gaps': [], 'phase': Counter(), 'crown': Counter(),
            'combo': 0, 'combo_same_tick': 0, 'combo_cards': Counter(),
            'press_position': Counter(), 'deployment_position': Counter(), 'linked_deployment_position': Counter(),
            'position_pairs': Counter(), 'delay_by_deployment_position': defaultdict(list),
            'deployment_censored_by_unresolved': 0}


def pos_key(p):
    return f"{p['lane_from_blue']}/{p['half']}" if p else 'unknown'


def analyse(files, inventory):
    windows = {c: v['window_seconds'] for c, v in inventory['calibration'].items()}
    stats = {c: new_stats() for c in windows}
    total = Counter()
    sensitivity = {str(s): {'outcomes': Counter(), 'resolved_per_card': Counter(), 'changed_from_primary': 0}
                   for s in (.75, 1., 1.25)}
    with gzip.open(OUT / 'presses.jsonl.gz', 'wt', encoding='utf-8') as audit_file:
        for path, row, tag, status, d in rows(files, 'mine'):
            if status != 'unique':
                continue
            decks, events = prepare(d)
            for deck in decks.values():
                for c in set(deck) & stats.keys():
                    stats[c]['deck_battles'].add(tag)
            latest = defaultdict(dict)
            deployments = []
            plays = defaultdict(list)
            for t, ei, e in events:
                if e.get('kind') == 'play_card' and math.isfinite(t):
                    plays[e.get('side')].append((t, ei, e.get('card_key')))
            play_keys = {s: [(t, i) for t, i, c in arr] for s, arr in plays.items()}
            final = [d['battle'][s].get('crowns') for s in ('team', 'opponent')]
            for t, ei, e in events:
                side = e.get('side')
                if e.get('kind') == 'play_card' and math.isfinite(t):
                    c = deploy_card(e, decks)
                    if c:
                        dep = {'card': c, 'time': t, 'index': ei, 'position': position(e), 'press_times': [], 'uncertain': False}
                        latest[side][c] = dep
                        deployments.append(dep)
                        stats[c]['deployments'] += 1
                        stats[c]['deployment_battles'].add(tag)
                        stats[c]['deployment_position'][pos_key(dep['position'])] += 1
                    continue
                if e.get('kind') != 'activate_ability':
                    continue
                total['presses'] += 1
                cand = list(dict.fromkeys(e.get('ability_source_candidates') or []))
                t = t if math.isfinite(t) else None
                c, method, ages, eligible = resolve(cand, latest[side], t, windows)
                if not cand:
                    method = 'no_candidates'
                if len(cand) > 1:
                    for scale, ss in sensitivity.items():
                        chosen, why, _, _ = resolve(cand, latest[side], t, windows, float(scale))
                        ss['outcomes'][why] += 1
                        if chosen:
                            ss['resolved_per_card'][chosen] += 1
                        ss['changed_from_primary'] += int(chosen != c)
                total[method] += 1
                record = {'file': path.name, 'row': row, 'replay_tag': tag, 'event_index': ei,
                          'source_index': e.get('source_index'), 'side': side, 'time_seconds': t,
                          'tick': e.get('replay_tick_20hz'), 'candidates': cand, 'candidate_age_seconds': ages,
                          'plausible_candidates': eligible, 'card': c, 'attribution': method,
                          'source_authoritative': e.get('ability_source_authoritative'), 'press_position': position(e)}
                if c is None:
                    for candidate in cand:
                        stats[candidate]['unresolved_candidate_mentions'] += 1
                        stats[candidate]['unresolved_plausible_mentions'] += int(candidate in eligible)
                        if candidate in latest[side]:
                            latest[side][candidate]['uncertain'] = True
                    total['unresolved'] += 1
                else:
                    s = stats[c]
                    s['presses'] += 1
                    s['battles'].add(tag)
                    s['attribution'][method] += 1
                    s['phase'][phase(t)] += 1
                    # Crowns are monotonic: final 0-0 proves tied throughout. Any nonzero final score
                    # lacks the tower-destruction time, so do not leak final outcome into press context.
                    crown = 'tied' if final == [0, 0] else 'unknown'
                    s['crown'][crown] += 1
                    record['crowns_at_press'] = crown
                    arr = plays.get(side, [])
                    j = bisect.bisect_right(play_keys.get(side, []), (t, ei)) if t is not None else len(arr)
                    combo = j < len(arr) and arr[j][0] - t <= 1.0000001
                    s['combo'] += int(combo)
                    record['combo_within_1s'] = combo
                    if combo:
                        s['combo_cards'][arr[j][2]] += 1
                        s['combo_same_tick'] += int(arr[j][0] == t)
                        record['combo_next_card'] = arr[j][2]
                    s['press_position'][pos_key(record['press_position'])] += 1
                    dep = latest[side].get(c)
                    if dep is not None and t is not None:
                        delay = round(t - dep['time'], 6)
                        s['linked_presses'] += 1
                        s['linked_outside_window'] += int(delay > windows[c])
                        s['delay'].append(delay)
                        if dep['press_times']:
                            s['gaps'].append(round(t - dep['press_times'][-1], 6))
                        else:
                            s['first_delay'].append(delay)
                        dep['press_times'].append(t)
                        pk = pos_key(dep['position'])
                        s['linked_deployment_position'][pk] += 1
                        s['delay_by_deployment_position'][pk].append(delay)
                        s['position_pairs'][pk + ' -> ' + pos_key(record['press_position'])] += 1
                        record.update(deployment_event_index=dep['index'], deployment_time_seconds=dep['time'],
                                      deployment_position=dep['position'], delay_seconds=delay,
                                      within_attribution_window=delay <= windows[c])
                    else:
                        s['unlinked_presses'] += 1
                audit_file.write(compact_json(record) + '\n')
            for dep in deployments:
                s = stats[dep['card']]
                n = len(dep['press_times'])
                s['deployment_press_counts']['0' if n == 0 else '1' if n == 1 else '2+'] += 1
                s['deployment_censored_by_unresolved'] += int(dep['uncertain'])
    abilities = {}
    for c, s in sorted(stats.items()):
        a = {k: s[k] for k in ['presses', 'deployments', 'linked_presses', 'unlinked_presses', 'linked_outside_window',
                               'attribution', 'unresolved_candidate_mentions', 'unresolved_plausible_mentions',
                               'deployment_censored_by_unresolved']}
        a.update(n_battles=len(s['battles']), n_deck_battles=len(s['deck_battles']),
                 n_deployment_battles=len(s['deployment_battles']),
                 presses_per_deployment=round(s['linked_presses']/s['deployments'], 6) if s['deployments'] else None,
                 deployment_press_distribution=shares(s['deployment_press_counts'], ['0', '1', '2+']),
                 delay_seconds=quantiles(s['delay']), first_press_delay_seconds=quantiles(s['first_delay']),
                 repeat_gap_seconds=quantiles(s['gaps']), phase=shares(s['phase'], PHASES + ['unknown']),
                 crowns_at_press=shares(s['crown'], ['ahead', 'behind', 'tied', 'unknown']),
                 combo_within_1s={'count': s['combo'], 'percent': round(100*s['combo']/s['presses'], 4) if s['presses'] else None,
                                  'same_tick_count': s['combo_same_tick'], 'next_cards': s['combo_cards']},
                 press_coordinates=shares(s['press_position']), deployment_coordinates=shares(s['deployment_position']),
                 linked_deployment_coordinates=shares(s['linked_deployment_position']), deployment_to_press_positions=s['position_pairs'],
                 delay_by_deployment_position={p: quantiles(v) for p, v in s['delay_by_deployment_position'].items()},
                 lifetime_proxy=inventory['calibration'][c])
        if s['presses']:
            dominant = max(PHASES, key=lambda p: s['phase'][p])
            median = a['delay_seconds']['p50']
            timing = f'{median:.1f}s after deployment' if median is not None else 'at an unknown delay from deployment'
            a['note'] = (f"Median press is {timing}; {a['phase']['percent'][dominant]:.1f}% fall in {dominant}. "
                         f"{a['combo_within_1s']['percent']:.1f}% precede a friendly card within 1s; "
                         f"{a['deployment_press_distribution']['percent']['2+'] or 0:.1f}% of deployments have repeat presses.")
        else:
            a['note'] = 'Seen in decks but no attributable presses; this corpus cannot establish when this ability is used.'
        abilities[c] = a
    return total, sensitivity, abilities


def context_evidence():
    refs = [
        ('research/sandbox_tools/replay_drive.py', '"skipped": "ability plays not driven by this version"',
         'drive() logs and skips ability presses; no ability action is sent.'),
        ('pipeline/e1_pool.py', 'if "ability" in str(e["skipped"]):',
         'Pool construction preserves skipped presses as ability commands with no card/entity identity.'),
        ('pipeline/e1_pool.py', 'if c.get("ability"):',
         'The parity merge drops ability commands before execution.'),
    ]
    # Discover base environment through the explicit import in e1_pool; never import it.
    candidates = [ROOT / 'scratchpad/gauntlet/L62/engine_env.py', ROOT / 'pipeline/engine/engine_env.py']
    for p in candidates:
        if p.exists():
            refs.append((p.relative_to(ROOT).as_posix(), 'return [c for c in cmds if not c.get("ability")]', 'The base ghost loader drops ability commands before building its execution schedule (lines 325-327).'))
    out = []
    for file, needle, finding in refs:
        lines = (ROOT / file).read_text(encoding='utf-8').splitlines()
        hits = [i for i, l in enumerate(lines, 1) if needle in l]
        out.append({'file': file, 'lines': hits, 'finding': finding, 'needle': needle,
                    'sha256': hashlib.sha256((ROOT / file).read_bytes()).hexdigest()})
    return out


def enrich_repeat_evidence(abilities):
    """Separate repeated deployments supported by singles from heuristic-dependent ones."""
    grouped = {}
    with gzip.open(OUT/'presses.jsonl.gz','rt',encoding='utf-8') as f:
        for line in f:
            e = parse_json(line)
            if e.get('card') and 'deployment_event_index' in e:
                key = (e['replay_tag'],e['deployment_event_index'],e['card'])
                count, inferred = grouped.get(key,(0,False))
                grouped[key] = (count+1, inferred or e['attribution']=='resolved_multiple')
    counts = defaultdict(Counter)
    for (_,_,card),(count,inferred) in grouped.items():
        if count > 1:
            counts[card]['includes_heuristic_attribution' if inferred else 'all_single_candidate'] += 1
    for c,a in abilities.items():
        a['repeat_deployment_attribution_evidence'] = {
            k:counts[c][k] for k in ['all_single_candidate','includes_heuristic_attribution']}


def measured_concerns(report):
    a = report['abilities']
    g, b = a.get('golden-knight'), a.get('boss-bandit')
    notes = []
    if g and b:
        notes.append(f"Golden Knight repeats on {g['deployment_press_distribution']['counts']['2+']:,}/{g['deployments']:,} "
                     f"deployments ({g['deployment_press_distribution']['percent']['2+']:.4f}%), versus Boss Bandit "
                     f"{b['deployment_press_distribution']['percent']['2+']:.4f}%. The expected frequent Golden Knight repetition "
                     "is not supported by these inferred deployment groups; this is not a claim about its game mechanics.")
    notes.append(f"{sum(x['linked_outside_window'] for x in a.values()):,} single-candidate presses exceed their card's window "
                 "and are retained as instructed; all attributed presses have a preceding matching deployment.")
    return notes


def pct(x):
    return '-' if x is None else f'{x:.1f}'


def render(report):
    total, inv = report['totals'], report['inventory']
    lines = ['# Pro-corpus ability presses (phase 1)', '',
             f"Processed {len(report['inputs'])} files / {sum(x['rows'] for x in report['inputs']):,} rows; "
             f"{inv['counts']['row_status'].get('unique', 0):,} unique replay tags. "
             f"{total['presses']:,} presses: {total.get('single_candidate', 0):,} single-candidate, "
             f"{total.get('resolved_multiple', 0):,} multi-candidate resolved, {total.get('unresolved', 0):,} unresolved/dropped.", '',
             'Distribution = percent of all inferred ability-card deployments with 0 / 1 / 2+ attributed presses. '
             'Phase = percent of attributed presses in [0,60) / [60,120) / [120,180) / [180,+inf) seconds; OT begins at 180s. '
             'Median delay uses linked presses, including repeat presses. Unknowns are retained in JSON.', '',
             '| Ability | n presses | n battles | Deployments: 0 / 1 / 2+ (%) | Median delay (s) | Phase split (%) |',
             '|---|---:|---:|---|---:|---|']
    for c, a in report['abilities'].items():
        dist = ' / '.join(pct(a['deployment_press_distribution']['percent'][k]) for k in ['0', '1', '2+'])
        phases = ' / '.join(pct(a['phase']['percent'][k]) for k in PHASES)
        lines.append(f"| {c} | {a['presses']:,} | {a['n_battles']:,} | {dist} | {pct(a['delay_seconds']['p50'])} | {phases} |")
    lines += ['', 'Percentages are rounded to one decimal; 0.0% can represent a rare nonzero count. Exact counts are in JSON.',
              '', '## Attribution and denominators', '',
              'Single candidates are attributed exactly as requested, even outside the heuristic lifetime window. '
              'Multiple candidates resolve only when exactly one has a preceding deployment by that side within its window; '
              'ties remain ambiguous (no arbitrary newest-card winner). Windows use each card\'s single-candidate deployment-to-press p95, '
              'bounded to 10-90s; fewer than 30 samples use the pooled p95. These are activity-window proxies, not measured unit lifetimes. '
              'The most recent same-card deployment ends the previous inferred instance; death/despawn is not observed.', '',
              'Event base keys are joined to a unique deck-card slot, preserving -hero/-ev1 forms. '
              'Unknown form_at_play does not establish which hero/evolution form spawned on that cycle. '
              'The denominator therefore means deployments from the hero/champion deck slot, not engine-verified ability-eligible spawns. '
              'No one-press restriction is imposed. Unresolved presses do not enter usage metrics; zero-press shares are upper bounds '
              'under attribution loss and repeat grouping is inferred. Single candidates without a deployment remain in press counts but not delay/repeat metrics.', '',
              '| Ability | Single | Multi resolved | Unresolved candidate mentions | Plausible unresolved | Window (s) | Deployments | Unlinked presses |',
              '|---|---:|---:|---:|---:|---:|---:|---:|']
    for c, a in report['abilities'].items():
        lines.append(f"| {c} | {a['attribution'].get('single_candidate',0):,} | {a['attribution'].get('resolved_multiple',0):,} | "
                     f"{a['unresolved_candidate_mentions']:,} | {a['unresolved_plausible_mentions']:,} | {a['lifetime_proxy']['window_seconds']:.2f} | "
                     f"{a['deployments']:,} | {a['unlinked_presses']:,} |")
    lines += ['', 'Unresolved candidate mentions overlap across cards and must not be summed as unique presses.', '',
              'Sensitivity (multi-candidate only):', '']
    for scale, s in report['sensitivity'].items():
        lines.append(f"- {scale}x windows: {s['outcomes'].get('resolved_multiple',0):,} resolved; "
                     f"{s['changed_from_primary']:,} assignments differ from primary (including resolved/unresolved changes).")
    lines += ['', '## When each ability is pressed', '']
    for c, a in report['abilities'].items():
        lines.append(f"- **{c}:** {a['note']}")
    lines += ['', '## Timing, combos and repeat presses', '',
              '| Ability | Delay p10 / p50 / p90 (s) | First-press median (s) | Combo within 1s | Repeat gaps n; p10 / p50 / p90 (s) |',
              '|---|---|---:|---:|---|']
    for c, a in report['abilities'].items():
        delay = ' / '.join(pct(a['delay_seconds'][k]) for k in ['p10', 'p50', 'p90'])
        gap = ' / '.join(pct(a['repeat_gap_seconds'][k]) for k in ['p10', 'p50', 'p90'])
        lines.append(f"| {c} | {delay} | {pct(a['first_press_delay_seconds']['p50'])} | {pct(a['combo_within_1s']['percent'])}% | {a['repeat_gap_seconds']['n']:,}; {gap} |")
    lines += ['', 'Combo is the next chronological card play by the same side, within an inclusive 1s after the press; '
              'same-tick later events count, and their count is separate in JSON. It measures proximity, not tactical intent. '
              'Repeat gaps use consecutive presses linked to the same deployment, never across redeployments.', '',
              '## Coordinates and crown context', '',
              f"Press coordinates: {inv['audit'].get('press_coordinates_nonnull',0):,} non-null / "
              f"{inv['audit'].get('press_coordinates_valid',0):,} valid native coordinates across {total['presses']:,} presses. "
              'Deployment coordinates and deployment-to-press delay by location are summarized below and fully in JSON. '
              'A deployment location is not the unit position at the press. Lane is left/right relative to the blue/native frame '
              '(x<9000/x>9000; center at x=9000); own half is y<16000 for team and y>16000 for opponent.', '',
              '| Ability | Linked presses with deployment coordinates | Own-half deployment share | Left / center / right | Median delay by deployment lane/half (s) | Crowns tied known / unknown |',
              '|---|---:|---:|---|---|---|']
    for c, a in report['abilities'].items():
        pos = a['linked_deployment_coordinates']['counts']
        known = sum(v for k,v in pos.items() if k != 'unknown')
        own = sum(v for k,v in pos.items() if k.endswith('/own'))
        lanes = [sum(v for k,v in pos.items() if k.startswith(l+'/')) for l in ['left','center','right']]
        # Per-lane medians are in JSON. Do not take a median of medians here.
        details = '; '.join(f"{p}: {pct(q['p50'])}" for p,q in sorted(a['delay_by_deployment_position'].items()))
        crown = a['crowns_at_press']['counts']
        lines.append(f"| {c} | {known:,} | {100*own/known if known else 0:.1f}% | "
                     f"{' / '.join(str(v) for v in lanes)} | {details} | {crown['tied']:,} / {crown['unknown']:,} |")
    lines += ['', 'Final crown totals do not reveal when towers fell. Only final 0-0 proves tied at every press '
              '(crowns are monotonic); all other presses have unknown crown lead. No final-score backfill is used.', '',
              '## Missing context and phase-2 replay path', '',
              'The observed action events provide no living unit/entity roster, enemy proximity or targeting, '
              'unit HP/shield, current unit position, death/despawn time, damage, projectile state, exact elixir at the press, '
              'ability cooldown/charges/readiness, ability acceptance/effect, or timed tower damage/destruction. '
              'Final tower HP, final crowns, deck average elixir and total leaked elixir are end-of-battle aggregates, '
              'not per-press state. Hand/cycle and elixir can only be modeled under assumptions; they are not observed here. '
              'Phase 2 needs preserved ability commands, source/entity attribution, and state captured immediately before each press. '
              'Simulation will reconstruct context subject to simulator parity; it will not make missing historical state authoritative.', '']
    for ref in report['code_evidence']:
        lines.append(f"- `{ref['file']}:{','.join(map(str,ref['lines']))}`: {ref['finding']}")
    lines += ['', '## Repeat attribution evidence', '',
              'Rare repeat groups can be created by mistaken multi-source attribution. The counts below separate '
              'groups where every press had a single candidate from groups requiring at least one heuristic assignment. '
              'Even the former lack an authoritative unit ID.', '',
              '| Ability | Repeat deployments: all single-candidate | Repeat deployments: includes heuristic |',
              '|---|---:|---:|']
    for c,a in report['abilities'].items():
        evidence = a.get('repeat_deployment_attribution_evidence',{})
        lines.append(f"| {c} | {evidence.get('all_single_candidate',0):,} | {evidence.get('includes_heuristic_attribution',0):,} |")
    lines += ['', '## Concerns and reproducibility', ''] + [f'- {s}' for s in report['concerns'] + measured_concerns(report)]
    lines += ['', 'Run `python -B scratchpad/gauntlet/L70/abilities/mine_abilities.py`; '
              'verify with the same command plus `--verify`. Only this directory is written. '
              '`abilities.json` contains all counts, denominators, quantiles, coordinate breakdowns, calibration and input metadata. '
              '`presses.jsonl.gz` preserves one auditable record per unique-replay ability event, including dropped ambiguities. '
              'No engine or project module is imported.']
    return '\n'.join(lines) + '\n'


def self_test():
    latest = {'a': {'time': 10}, 'b': {'time': 0}}
    assert resolve(['a','b'], latest, 15, {'a':10,'b':10})[:2] == ('a','resolved_multiple')
    assert resolve(['a','b'], latest, 15, {'a':20,'b':20})[0] is None
    assert resolve(['a','b'], latest, 100, {'a':10,'b':10})[0] is None
    assert resolve(['b'], latest, 100, {'b':10})[0] == 'b'
    assert [phase(t) for t in [0,59.95,60,120,180,300]] == ['0-60','0-60','60-120','120-180','OT','OT']
    assert deploy_card({'card_key':'knight','side':'team'}, {'team':['knight-hero']}) == 'knight-hero'
    assert deploy_card({'card_key':'knight','side':'team'}, {'team':['knight-hero','knight-ev1']}) is None
    assert position({'side':'opponent','coordinates':{'native_world_units':{'x':3500,'y':30000}}})['half'] == 'own'
    assert quantiles([1,2,3,4])['p50'] == 2.5


def verify():
    self_test()
    r = json.loads((OUT/'abilities.json').read_text(encoding='utf-8'))
    assert len(r['inputs']) == len(list(DATA.glob('*.parquet')))
    for f in r['inputs']:
        p = DATA/f['name']
        assert p.stat().st_size == f['size_bytes'] and p.stat().st_mtime_ns == f['mtime_ns']
        assert pq.ParquetFile(p).metadata.num_rows == f['rows']
    assert sum(f['rows'] for f in r['inputs']) == sum(r['inventory']['counts']['row_status'].values())
    counts, methods = Counter(), Counter()
    dep = defaultdict(list)
    with gzip.open(OUT/'presses.jsonl.gz','rt',encoding='utf-8') as f:
        for line in f:
            e = json.loads(line)
            methods[e['attribution']] += 1
            if e['card']:
                counts[e['card']] += 1
                if 'deployment_event_index' in e:
                    assert e['delay_seconds'] >= 0
                    dep[(e['replay_tag'], e['deployment_event_index'],e['card'])].append(e['time_seconds'])
            if e['attribution'] == 'resolved_multiple':
                assert e['plausible_candidates'] == [e['card']]
    assert sum(methods.values()) == r['totals']['presses'] == r['inventory']['counts']['event_kinds']['activate_ability']
    assert sum(counts.values()) + r['totals']['unresolved'] == r['totals']['presses']
    assert set(r['inventory']['counts']['deck_abilities']) <= set(r['abilities'])
    repeat = Counter()
    gaps = defaultdict(list)
    for (_,_,c), ts in dep.items():
        repeat[c] += int(len(ts)>1)
        gaps[c].extend(round(b-a,6) for a,b in zip(ts,ts[1:]))
    for c,a in r['abilities'].items():
        assert a['presses'] == counts[c] == a['phase']['n'] == a['crowns_at_press']['n']
        assert a['deployments'] == a['deployment_press_distribution']['n']
        assert a['presses'] == a['linked_presses'] + a['unlinked_presses']
        assert a['delay_seconds']['n'] == a['linked_presses']
        assert a['deployment_press_distribution']['counts']['2+'] == repeat[c]
        assert a['repeat_gap_seconds'] == quantiles(gaps[c])
        assert sum(a['repeat_deployment_attribution_evidence'].values()) == repeat[c]
        assert a['combo_within_1s']['count'] <= a['presses']
    for ref in r['code_evidence']:
        assert ref['lines'], ref
        p = ROOT/ref['file']
        assert hashlib.sha256(p.read_bytes()).hexdigest() == ref['sha256']
    assert (OUT/'abilities.md').read_text(encoding='utf-8') == render(r)
    print('ABILITY_VERIFICATION_PASSED', flush=True)


def main():
    self_test()
    files = sorted(DATA.glob('*.parquet'))
    assert files, DATA
    inputs = [{'name':p.name,'size_bytes':p.stat().st_size,'mtime_ns':p.stat().st_mtime_ns,
               'rows':pq.ParquetFile(p).metadata.num_rows} for p in files]
    if args.reuse_inventory:
        cached = json.loads((OUT/'inventory.json').read_text(encoding='utf-8'))
        assert cached['inputs'] == inputs, 'Inputs changed since inventory'
        inv = cached['inventory']
    else:
        inv = calibrate(files)
        (OUT/'inventory.json').write_text(json.dumps({'inputs':inputs,'inventory':inv},indent=2),encoding='utf-8')
    total, sensitivity, abilities = analyse(files, inv)
    enrich_repeat_evidence(abilities)
    concerns = [
        'Candidate sources are inferred, not authoritative; multi-source resolution depends on empirical activity windows. See sensitivity.',
        'No measured death/entity identity or form-at-play; deployment linkage and repeat counts are estimates. Windows are not biological lifetimes.',
        'Anonymized corpus membership does not independently prove every participant is a professional. Both sides and all battle types are included without filtering.',
        'Unresolved presses are dropped from usage statistics, not silently assigned; per-card ambiguous mentions overlap.',
        'Raw replay tags deduplicate identical payloads; conflicting same-tag payloads use the first occurrence and are counted explicitly.',
        'Phase shares are counts of observed presses, not exposure-adjusted press rates; OT duration and ability deck popularity affect them.',
        'Observed repetitions are reported for every card, without enforcing the proposed once-only expectation.',
        'Inputs are read only; file size/mtime are checked after mining, not cryptographic proof of immutable source bytes.',
    ]
    report = {'schema':'ability-mining.v1','inputs':inputs,'inventory':inv,'totals':total,
              'sensitivity':sensitivity,'abilities':abilities,'code_evidence':context_evidence(),'concerns':concerns}
    (OUT/'abilities.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    (OUT/'abilities.md').write_text(render(report),encoding='utf-8')
    verify()
    print(f'DONE_WITH_CONCERNS: {total["presses"]:,} presses; {len(abilities)} abilities; {time.monotonic()-START:.1f}s',flush=True)


if __name__ == '__main__':
    START = time.monotonic()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true')
    parser.add_argument('--reuse-inventory', action='store_true', help='Reuse completed compact extraction only if input metadata matches')
    args = parser.parse_args()
    verify() if args.verify else main()
