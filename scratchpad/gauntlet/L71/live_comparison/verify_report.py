"""Independent report oracle: recompute attribution, counts and outcomes from prefixes."""
import collections
import copy
import hashlib
import json
import math
from pathlib import Path

import compare as c


def verify(report):
    source_rows = {}
    for entry in report['source_manifest']:
        path = c.ROOT / entry['path']
        with path.open('rb') as f: raw = f.read(entry['bytes'])
        assert len(raw) == entry['bytes']
        assert hashlib.sha256(raw).hexdigest() == entry['sha256'], entry['path']
        prefix = raw[:raw.rfind(b'\n') + 1]
        assert len(raw) - len(prefix) == entry['incomplete_tail_bytes']
        source_rows[path.name] = [json.loads(s) for s in prefix.splitlines() if s.strip()]
    expected_selected = set()
    for name, rows in source_rows.items():
        if not name.startswith('live_play_'): continue
        starts = [r for r in rows if r.get('event') == 'start']
        if len(starts) == 1 and starts[0].get('dry_run') is False:
            stem = starts[0].get('ckpt', '').replace('\\', '/').split('/')[-1]
            if stem in c.MODELS: expected_selected.add(name)
    assert {m['file'] for m in report['matches']} == expected_selected
    assert len(report['matches']) == len(expected_selected)
    grouped = collections.defaultdict(list)
    nav_used = set()
    for m in report['matches']:
        rows = source_rows[m['file']]
        start = next(r for r in rows if r.get('event') == 'start')
        key = c.MODELS[start['ckpt'].replace('\\', '/').split('/')[-1]]
        assert m['model'] == key
        assert m['checkpoint'] == start['ckpt'].replace('\\', '/')
        assert m['start'] == start
        attempts = collections.Counter(r['name'] for r in rows if r.get('event') == 'play')
        confirms = collections.Counter(r['name'] for r in rows if r.get('event') == 'confirmed')
        assert m['attempts'] == attempts and m['confirmed'] == confirms
        end = next((r for r in rows if r.get('event') == 'end'), None)
        assert m['end'] == end
        assert m['frame_count'] == sum(r.get('event') == 'frame' for r in rows)
        assert m['projectile_frames'] == sum(r.get('event') == 'frame' and 'projectiles' in r for r in rows)
        assert m['ability'] == collections.Counter(r['event'] for r in rows if r.get('event') in ('ability', 'ability_confirmed', 'ability_unconfirmed'))
        plays = [i for i, r in enumerate(rows) if r.get('event') == 'play']
        expected_xbow = []
        for j, i in enumerate(plays):
            r = rows[i]
            if r['name'] != 'Xbow': continue
            stop = plays[j + 1] if j + 1 < len(plays) else len(rows)
            receipts = [v for v in rows[i + 1:stop] if v.get('event') in ('confirmed', 'unconfirmed')]
            assert len(receipts) <= 1
            expected = {'name': r['name'], 'tick': r['tick'], 'xy': r.get('xy'), 'receipt': 'missing'}
            if receipts:
                assert receipts[0]['name'] == r['name']
                expected.update(receipt=receipts[0]['event'], receipt_tick=receipts[0]['tick'])
            expected_xbow.append(expected)
        assert m['xbow_placements'] == expected_xbow
        outcome = 'unknown'
        if end:
            t = c.start_time(m['file']) + end['seconds']
            boundary = min((c.start_time(n) for n in source_rows if n.startswith('live_play_') and n > m['file']), default=math.inf)
            eligible = []
            for name, nr in source_rows.items():
                if not name.startswith('ladder_nav_'): continue
                ns = [r for r in nr if r.get('event') == 'nav_start']
                if len(ns) == 1 and t - 1 <= ns[0]['t'] <= t + 30 and ns[0]['t'] < boundary:
                    eligible.append((name, ns[0], [r for r in nr if r.get('event') == 'outcome']))
            if len(eligible) == 1:
                name, ns, outcomes = eligible[0]
                assert m['nav_file'] == name and name not in nav_used
                nav_used.add(name)
                if ns.get('dry_run') is False and len(outcomes) == 1:
                    result = outcomes[0].get('won')
                    outcome = 'win' if result is True else 'loss' if result is False else 'unread_or_draw'
            else: assert m['nav_file'] is None
        assert m['outcome'] == outcome
        grouped[key].append(m)
    for model, g in report['groups'].items():
        ms = grouped[model]
        ended = [m for m in ms if m['end']]
        outcomes = collections.Counter(m['outcome'] for m in ended)
        assert g['logs'] == len(ms) and g['ended_logs'] == len(ended)
        assert g['incomplete_logs'] == len(ms) - len(ended)
        assert (g['wins'], g['losses'], g['unknown_outcomes'], g['unread_or_draw']) == tuple(outcomes[k] for k in ('win', 'loss', 'unknown', 'unread_or_draw'))
        total = sum(sum(m['confirmed'].values()) for m in ended)
        rockets = sum(m['confirmed'].get('Rocket', 0) for m in ended)
        assert g['confirmed'] == total
        assert g['rocket_confirmed_share'] == (rockets / total if total else None)
        n, w = outcomes['win'] + outcomes['loss'], outcomes['win']
        assert g['resolved_matches'] == n
        assert g['win_rate_excluding_unknown_draw'] == (w / n if n else None)
        if n:
            z2 = 1.959963984540054 ** 2
            rad = math.sqrt(z2 * (w * (n - w) / n + z2 / 4))
            independent = [(w + z2 / 2 - rad) / (n + z2), (w + z2 / 2 + rad) / (n + z2)]
            assert all(abs(a - b) < 1e-12 for a, b in zip(independent, g['win_rate_wilson95']))
        assert g['preemptive_log_rate'] is None and g['trophies_over_time'] is None
    for path, digest in report['protected_sha256'].items():
        assert hashlib.sha256((c.ROOT / path).read_bytes()).hexdigest() == digest, path
    assert report['groups'] == c.aggregate(report['matches'])


if __name__ == '__main__':
    import sys
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else c.OUT / 'report.json'
    report = json.loads(path.read_text(encoding='utf-8'))
    verify(report)
    bad = copy.deepcopy(report)
    bad['groups']['r1e_u0155']['wins'] += 1
    try: verify(bad)
    except AssertionError: pass
    else: raise AssertionError('corrupted report accepted')
    print('LIVE_COMPARISON_VERIFIED (source prefixes, independent counts/joins/intervals; corruption rejected)')
