"""Q0: bounded, offline live-log comparison. No game, model or network imports.

Run with the icebow interpreter. Source prefixes are fixed before reading; incomplete
matches and unread result screens are never treated as losses. Re-run for a new snapshot.
"""
from __future__ import annotations

import argparse
import collections
import ctypes
import datetime as dt
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
LOGS = ROOT / 'scratchpad/gauntlet/L68/live_reader'
MODELS = {'rseries_r1_u0155.pt': 'old_r1_u0155',
          'rseries_r1e31_u0155.pt': 'r1e_u0155'}
PROTECTED = ['scratchpad/gauntlet/L68/live_reader/live_play.py',
             'scratchpad/gauntlet/L70/live/run_live.sh',
             'scratchpad/gauntlet/L70/live/CKPT_OVERRIDE']


def wilson(wins, n):
    if n == 0:
        return None
    if not 0 <= wins <= n:
        raise ValueError('invalid binomial counts')
    z = 1.959963984540054
    p, den = wins / n, 1 + z * z / n
    center = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return [max(0.0, center - half), min(1.0, center + half)]


def source_prefix(path, size):
    with path.open('rb') as f:
        raw = f.read(size)
    if len(raw) != size:
        raise ValueError(f'source shrank: {path.name}')
    complete = raw[:raw.rfind(b'\n') + 1]
    rows = []
    for line_no, line in enumerate(complete.splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, dict):
            raise ValueError(f'non-object event: {path.name}:{line_no}')
        rows.append(row)
    return rows, {'path': path.relative_to(ROOT).as_posix(), 'bytes': size,
                  'sha256': hashlib.sha256(raw).hexdigest(),
                  'incomplete_tail_bytes': len(raw) - len(complete)}


def start_time(name):
    # Dates in this comparison are EDT. Keep host timezone out of the join.
    return dt.datetime.strptime(Path(name).stem, 'live_play_%Y%m%d_%H%M%S').replace(
        tzinfo=dt.timezone(dt.timedelta(hours=-4))).timestamp()


def match_summary(name, rows):
    starts = [r for r in rows if r.get('event') == 'start']
    if len(starts) != 1:
        return None, 'missing_or_duplicate_start'
    start = starts[0]
    ckpt = start.get('ckpt', '').replace('\\', '/')
    model = MODELS.get(ckpt.rsplit('/', 1)[-1])
    if not model or start.get('dry_run') is not False:
        return None, 'other_checkpoint_or_not_explicitly_live'
    ends = [r for r in rows if r.get('event') == 'end']
    if len(ends) > 1:
        raise ValueError(f'duplicate end: {name}')
    plays, pending, frames = [], None, []
    ability = collections.Counter()
    for r in rows:
        event = r.get('event')
        if event == 'play':
            p = {'name': r['name'], 'tick': r['tick'], 'xy': r.get('xy'),
                 'receipt': 'missing'}
            plays.append(p)
            pending = p
        elif event in ('confirmed', 'unconfirmed'):
            if pending is None or pending['name'] != r.get('name'):
                raise ValueError(f'unmatched card receipt: {name}')
            pending['receipt'] = event
            pending['receipt_tick'] = r['tick']
            pending = None
        elif event == 'frame':
            frames.append(r)
        elif event in ('ability', 'ability_confirmed', 'ability_unconfirmed'):
            ability[event] += 1
    attempts = collections.Counter(p['name'] for p in plays)
    confirmed = collections.Counter(p['name'] for p in plays if p['receipt'] == 'confirmed')
    end = ends[0] if ends else None
    if end and (end['played'] != len(plays) or end['confirmed'] != sum(confirmed.values())):
        raise ValueError(f'end totals disagree with events: {name}')
    xb = [p for p in plays if p['name'] == 'Xbow']
    return {'file': name, 'model': model, 'checkpoint': ckpt, 'start': start,
            'started_unix': start_time(name), 'end': end,
            'estimated_end_unix': start_time(name) + end['seconds'] if end else None,
            'outcome': 'unknown', 'outcome_reason': 'incomplete_match' if not end else 'unpaired',
            'nav_file': None, 'attempts': dict(attempts), 'confirmed': dict(confirmed),
            'missing_receipts': sum(p['receipt'] == 'missing' for p in plays),
            'ability': dict(ability), 'xbow_placements': xb,
            'frame_count': len(frames),
            'projectile_frames': sum('projectiles' in f for f in frames),
            'trophy_observations': [r['trophies'] for r in rows if isinstance(r.get('trophies'), (int, float))]}, None


def join_outcomes(matches, navs, all_match_starts):
    used = set()
    for m in matches:
        if m['end'] is None:
            continue
        t = m['estimated_end_unix']
        next_start = min((s for s in all_match_starts if s > m['started_unix']), default=math.inf)
        eligible = [n for n in navs if t - 1 <= n['t'] <= t + 30 and n['t'] < next_start]
        if len(eligible) != 1:
            m['outcome_reason'] = f'{len(eligible)}_eligible_navs'
            continue
        n = eligible[0]
        if n['file'] in used:
            raise ValueError('a navigation result was assigned twice')
        used.add(n['file'])
        m['nav_file'], m['nav_gap_seconds'] = n['file'], n['t'] - t
        if n['dry_run'] or len(n['outcomes']) != 1:
            m['outcome_reason'] = 'dry_nav_or_not_one_outcome'
            continue
        won = n['outcomes'][0].get('won')
        m['outcome'] = 'win' if won is True else 'loss' if won is False else 'unread_or_draw'
        m['outcome_reason'] = 'paired_navigation'


def aggregate(matches):
    groups = {}
    for model in MODELS.values():
        rows = [m for m in matches if m['model'] == model]
        ended = [m for m in rows if m['end'] is not None]
        counts = collections.Counter(m['outcome'] for m in ended)
        attempts, confirmed, ability, xy = (collections.Counter() for _ in range(4))
        timeline = []
        for m in ended:
            attempts.update(m['attempts']); confirmed.update(m['confirmed']); ability.update(m['ability'])
            for p in m['xbow_placements']:
                if p['receipt'] == 'confirmed' and p['xy'] is not None:
                    xy[','.join(f'{v:.4f}' for v in p['xy'])] += 1
            timeline.append({'file': m['file'], 'started_unix': m['started_unix'], 'outcome': m['outcome']})
        n = counts['win'] + counts['loss']
        total_attempts, total_confirmed = sum(attempts.values()), sum(confirmed.values())
        groups[model] = {'logs': len(rows), 'ended_logs': len(ended), 'incomplete_logs': len(rows) - len(ended),
                         'wins': counts['win'], 'losses': counts['loss'], 'resolved_matches': n,
                         'unread_or_draw': counts['unread_or_draw'], 'unknown_outcomes': counts['unknown'],
                         'win_rate_excluding_unknown_draw': counts['win'] / n if n else None,
                         'win_rate_wilson95': wilson(counts['win'], n),
                         'card_attempts': dict(attempts), 'card_confirmed': dict(confirmed),
                         'attempts': total_attempts, 'confirmed': total_confirmed,
                         'rocket_attempt_share': attempts['Rocket'] / total_attempts if total_attempts else None,
                         'rocket_confirmed_share': confirmed['Rocket'] / total_confirmed if total_confirmed else None,
                         'ability': dict(ability), 'xbow_confirmed_intended_xy': dict(sorted(xy.items())),
                         'matches_with_frames': sum(m['frame_count'] > 0 for m in ended),
                         'frames': sum(m['frame_count'] for m in ended),
                         'frames_with_projectile_field': sum(m['projectile_frames'] for m in ended),
                         'preemptive_log_rate': None,
                         'preemptive_log_status': 'unavailable: saved live frames omit projectile flight and barrel-play denominator',
                         'trophies_over_time': None,
                         'trophies_status': 'unavailable: live/nav event schema has no numeric trophy timeline',
                         'timeline': timeline}
    return groups


def build(since='20261003', until=None):
    if until is None:
        until = dt.datetime.now(dt.timezone(dt.timedelta(hours=-4))).strftime('%Y%m%d')
    created = dt.datetime.now(dt.timezone.utc).isoformat()
    # Freeze size inventory once; never read the growing tail beyond this snapshot.
    paths = sorted(p for p in LOGS.glob('*.jsonl') if p.name.startswith(('live_play_', 'ladder_nav_'))
                   and since <= p.stem.split('_')[-2] <= until)
    inventory = [(p, p.stat().st_size) for p in paths]
    matches, navs, manifest, excluded, all_starts = [], [], [], [], []
    for p, size in inventory:
        rows, source = source_prefix(p, size)
        manifest.append(source)
        if p.name.startswith('live_play_'):
            all_starts.append(start_time(p.name))
            m, reason = match_summary(p.name, rows)
            if m:
                matches.append(m)
            else:
                excluded.append({'file': p.name, 'reason': reason})
        else:
            starts = [r for r in rows if r.get('event') == 'nav_start']
            if len(starts) == 1:
                navs.append({'file': p.name, 't': starts[0]['t'], 'dry_run': starts[0].get('dry_run') is not False,
                             'outcomes': [r for r in rows if r.get('event') == 'outcome']})
    join_outcomes(matches, navs, all_starts)
    return {'schema': 1, 'created_utc': created, 'since': since, 'until': until,
            'source_manifest': manifest, 'matches': matches, 'excluded': excluded,
            'all_match_starts': all_starts, 'groups': aggregate(matches),
            'protected_sha256': {s: hashlib.sha256((ROOT / s).read_bytes()).hexdigest() for s in PROTECTED},
            'limitations': [
                'Observational time-separated cohorts; trophy range, opponents, reader and ability-rule changes are confounders.',
                'Wilson intervals are descriptive binomial intervals, not a causal or sequential significance test.',
                'Behaviour uses ended logs, including unknown outcomes; unfinished matches are excluded from behaviour totals.',
                'X-Bow coordinates are intended placements attached to confirmed plays, not independently measured landings.',
                'Draw/unread is not counted as a loss. Frame logging is a selected subset, typically clip matches.',
                'No trophy values or preemptive-Log rate are inferred from wins, troop spawns, or absence of logged fields.'
            ]}


def markdown(report):
    lines = ['# Q0 live comparison', '', f"Snapshot: {report['created_utc']}", '',
             '| Checkpoint | W / L | Unknown / unread | Win rate (Wilson 95%) | Confirmed Rockets / plays |',
             '|---|---:|---:|---:|---:|']
    for name, g in report['groups'].items():
        ci = g['win_rate_wilson95']
        rate = f"{100*g['win_rate_excluding_unknown_draw']:.1f}% [{100*ci[0]:.1f}, {100*ci[1]:.1f}]" if ci else 'unavailable'
        lines.append(f"| {name} | {g['wins']} / {g['losses']} | {g['unknown_outcomes']} / {g['unread_or_draw']} | {rate} | {g['card_confirmed'].get('Rocket', 0)} / {g['confirmed']} |")
    intervals = [g['win_rate_wilson95'] for g in report['groups'].values()]
    if any(ci is None for ci in intervals):
        comparison = 'At least one checkpoint has no resolved matches yet.'
    elif max(ci[0] for ci in intervals) <= min(ci[1] for ci in intervals):
        comparison = 'The descriptive Wilson intervals overlap; these data do not establish a winner.'
    else:
        comparison = 'The descriptive Wilson intervals do not overlap, but the observational cohorts do not establish a causal checkpoint effect.'
    lines += ['', comparison + ' Sequential ladder runs also differ in opponents and conditions.',
              '', 'Checkpoint identity comes from each match start.ckpt; outcomes come from a unique subsequent navigation event within 30 seconds of the recorded end, before the next match.',
              '', 'Pre-emptive Log and trophy progression are unavailable from these saved event schemas. Missing values are null, not zero.', '']
    for name, g in report['groups'].items():
        lines += [f"## {name}", '', f"Ended logs {g['ended_logs']}; incomplete logs {g['incomplete_logs']}; frames in {g['matches_with_frames']} ended matches.",
                  f"Ability attempts / confirmed: {g['ability'].get('ability', 0)} / {g['ability'].get('ability_confirmed', 0)}.",
                  f"Confirmed X-Bow intended coordinates: `{json.dumps(g['xbow_confirmed_intended_xy'], sort_keys=True)}`.", '']
    lines += ['## Limits', ''] + ['- ' + s for s in report['limitations']]
    lines += ['', 'Reproduce with `icebow/.venv/Scripts/python.exe scratchpad/gauntlet/L71/live_comparison/compare.py`.',
              'Verify this exact snapshot with `icebow/.venv/Scripts/python.exe scratchpad/gauntlet/L71/live_comparison/verify_report.py`.', '']
    return '\n'.join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--since', default='20261003')
    ap.add_argument('--until', default=None, help='last local date YYYYMMDD; default today in EDT')
    ap.add_argument('--out', type=Path, default=OUT / 'report.json')
    a = ap.parse_args()
    try:
        ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x4000)
    except AttributeError:
        pass
    report = build(a.since, a.until)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    a.out.with_suffix('.md').write_text(markdown(report), encoding='utf-8')
    print(json.dumps({k: {f: v[f] for f in ('ended_logs', 'wins', 'losses', 'unknown_outcomes', 'win_rate_wilson95', 'rocket_confirmed_share')}
                      for k, v in report['groups'].items()}, indent=2))


if __name__ == '__main__':
    main()
