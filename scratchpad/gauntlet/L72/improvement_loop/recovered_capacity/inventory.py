"""Join independently qualified source reconstructions, with no model calls."""
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
LOOP = HERE.parent
DEAL = LOOP / 'deal_recovery'
CHECKS = ROOT / 'scratchpad/gauntlet/L71/integration/checks'
ICEBOW = {'ice-wizard', 'knight', 'rocket', 'skeletons', 'tesla', 'the-log', 'tornado', 'x-bow'}


def read(p): return json.loads(Path(p).read_bytes())
def base(s): return s.split('-ev')[0].removesuffix('-hero')
def sha(p):
    with Path(p).open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()


def main():
    output = HERE / 'inventory.json'
    assert not output.exists()
    sources = {}
    def bind(p):
        sources[str(p.relative_to(ROOT))] = sha(p)
        return read(p)
    def receipt(name):
        p = CHECKS / (name + '.json'); r = bind(p)
        assert r['exit_code'] == 0 and r['matched']
        assert hashlib.sha256(p.with_suffix('.out').read_text().encode()).hexdigest() == r['output_sha256']

    old = bind(LOOP / 'confirmation_capacity.json')
    audit = bind(DEAL / 'audit.json')
    assert old['complete'] and audit['complete']
    for p, h in old['sources'].items(): assert sha(ROOT / p) == h
    for p, h in audit['sources'].items(): assert sha(ROOT / p) == h
    original = {r['tag']: r for r in audit['records']}
    assert len(original) == audit['record_count'] == len(audit['records'])
    selected = {}
    for r in old['qualified']:
        a = original[r['tag']]
        assert a['usable'] and a['split'] == r['split']
        assert a['job']['signature'] == r['signature'] and a['job']['decks'] == r['decks']
        assert a['recording_sha256'] == r['sha256']
        selected[r['tag']] = dict(r, origin='original')
    assert len(selected) == sum(old['qualified_by_split'].values())
    recovery_counts = Counter()
    for complete_name, proof_name, receipt_name in (
        ('complete_v3.json', 'verified_v4.json', 'l72-deal-recovery-independent-v4'),
        ('reserved_complete.json', 'reserved_verified.json', 'l72-deal-recovery-reserved-independent'),
    ):
        result = bind(DEAL / complete_name); proof = bind(DEAL / proof_name)
        receipt(receipt_name)
        assert result['complete'] and proof['complete']
        assert proof['complete_sha256'] == sha(DEAL / complete_name)
        assert result['model_predictions'] == 0
        for row in result['rows']:
            a = original[row['tag']]
            assert a['split'] == row['split']
            if row['role'] == 'unchanged_control':
                assert row['tag'] in selected and row['usable']; continue
            assert not a['usable']
            if not row['usable']: continue
            assert row['repeated_equal'] and len(row['attempts']) == 2
            assert all(x['status'] == 'captured' and x['usable'] and not x['reasons'] for x in row['attempts'])
            assert row['tag'] not in selected
            first = row['attempts'][0]
            selected[row['tag']] = dict(tag=row['tag'], split=a['split'], signature=a['job']['signature'],
                decks=a['job']['decks'], path=first['path'], sha256=first['sha256'], origin=complete_name)
            recovery_counts[a['split']] += 1
    assert len({r['signature'] for r in selected.values()}) == len(selected)
    qualified = sorted(selected.values(), key=lambda r: r['tag'])
    sides = []; exact = Counter(); splits = Counter(); own = Counter(); opponent = Counter()
    for r in qualified:
        p = ROOT / r['path']; assert sha(p) == r['sha256']
        splits[r['split']] += 1
        eligible = [i for i, d in enumerate(r['decks']) if {base(c) for c in d} == ICEBOW]
        if not eligible: continue
        exact[r['split']] += 1
        rec = read(p); crawl = ROOT / original[r['tag']]['job']['crawl']
        command_path = crawl / 'plays_ext.csv'
        with command_path.open(encoding='utf-8', newline='') as f: commands = list(csv.DictReader(f))
        for i in eligible:
            side = 1 - i
            raw = {s: Counter(base(c['attr_card']) for c in commands if c['attr_ability'] == '0'
                and {'red': 0, 'blue': 1}[c['attr_s']] == s) for s in (0, 1)}
            actual = {s: Counter(base(c['card']) for c in rec['log'] if c.get('accepted')
                and not c.get('ability') and c['side'] == s) for s in (0, 1)}
            assert actual == raw, 'Native accepted commands differ from original CSV'
            item = dict(tag=r['tag'], split=r['split'], side=side, csv_sha256=sha(command_path),
                own_commands=dict(actual[side]), opponent_commands=dict(actual[1-side]))
            sides.append(item)
            if r['split'] == 'confirmation':
                own.update(actual[side]); opponent.update(actual[1-side])
    report = dict(complete=True, trainable=False, model_predictions=0, N2_complete=False,
        sources=sources, script_sha256=sha(__file__), plan_sha256=sha(HERE / 'PLAN.md'),
        distinct_selected_groups=len(original), qualified_by_split=dict(splits),
        newly_recovered_by_split=dict(recovery_counts), exact_icebow_qualified_replays=dict(exact),
        qualified=qualified, exact_sides=sides, confirmation_exact_own_commands=dict(own),
        confirmation_exact_opponent_commands=dict(opponent),
        component_replay_counts={k: len({r['tag'] for r in sides if r['split'] == 'confirmation'
            and r['opponent_commands'].get(k, 0)}) for k in ('goblin-barrel', 'witch', 'night-witch', 'furnace')},
        limits=['Source casts are not tactical opportunity labels or independent observations.',
                'Original failed attempts remain excluded; distinct successful attempts are separately qualified.',
                'No confirmation model prediction, training activation or acceptance-design waiver.'])
    output.write_text(json.dumps(report, indent=2))
    print(json.dumps({k: report[k] for k in ('qualified_by_split', 'newly_recovered_by_split',
        'exact_icebow_qualified_replays', 'component_replay_counts', 'confirmation_exact_opponent_commands')}))
    print('RECOVERED_CAPACITY_INVENTORY_COMPLETE')


if __name__ == '__main__': main()
