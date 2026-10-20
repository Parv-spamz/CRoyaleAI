"""Read-only independent CSV/native recount for the verified Void delta."""
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
LOOP = HERE.parent
VOID = LOOP / 'void_identity'
CHECKS = ROOT / 'scratchpad/gauntlet/L71/integration/checks'
ICEBOW = {'ice-wizard', 'knight', 'rocket', 'skeletons', 'tesla', 'the-log', 'tornado', 'x-bow'}
COMPONENTS = ('goblin-barrel', 'witch', 'night-witch', 'furnace')


def read(p): return json.loads(Path(p).read_bytes())
def base(s): return s.split('-ev')[0].removesuffix('-hero')
def sha(p):
    with Path(p).open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()


def main():
    output = HERE / 'inventory.json'
    assert not output.exists()
    sources = {}
    def bind(p):
        p = Path(p)
        sources[str(p.relative_to(ROOT))] = sha(p)
        return read(p)
    def receipt(name):
        p = CHECKS / (name + '.json'); r = bind(p)
        assert r['exit_code'] == 0 and r['matched']
        assert hashlib.sha256(p.with_suffix('.out').read_text().encode()).hexdigest() == r['output_sha256']

    old = bind(LOOP / 'recovered_capacity/inventory.json')
    old_proof = bind(LOOP / 'recovered_capacity/verified.json')
    receipt('l72-recovered-capacity-independent')
    assert old['complete'] and old_proof['complete']
    assert old_proof['inventory_sha256'] == sha(LOOP / 'recovered_capacity/inventory.json')
    result = bind(VOID / 'collection_complete.json')
    proof = bind(VOID / 'collection_verified.json')
    prepared = bind(VOID / 'prepared.json')
    started = bind(VOID / 'collection_started.json')
    receipt('l72-void-reconstruction-capture')
    receipt('l72-void-reconstruction-independent')
    assert result['complete'] and proof['complete'] and prepared['complete']
    assert proof['complete_sha256'] == sha(VOID / 'collection_complete.json')
    assert proof['script_sha256'] == sha(VOID / 'reconstruct_verify.py')
    assert result['started_sha256'] == sha(VOID / 'collection_started.json')
    for p, h in started['sources'].items(): assert sha(ROOT / p) == h, p
    for p, h in prepared['csv_hashes'].items(): assert sha(ROOT / p) == h, p
    jobs = bind(Path(prepared['jobs_path']))
    assert sha(prepared['jobs_path']) == prepared['jobs_sha256']
    assert [r['tag'] for r in result['rows']] == [j['tag'] for j in jobs]
    old_audit = bind(LOOP / 'deal_recovery/audit.json')
    old_tags = {r['tag'] for r in old_audit['records']}
    assert len(old_tags) == old['distinct_selected_groups']
    assert not old_tags.intersection(j['tag'] for j in jobs)
    selected = {r['tag']: r for r in old['qualified']}
    assert len(selected) == len(old['qualified'])
    expected = {r['tag']: r for r in proof['qualified']}
    sides = list(old['exact_sides'])
    own_delta = Counter(); opp_delta = Counter(); replay_delta = Counter()
    accounting = Counter(); excluded = Counter()
    for job, row in zip(jobs, result['rows']):
        assert row['split'] == job['split'] == 'confirmation'
        assert len(row['attempts']) == 2 and row['repeat_equal']
        first = row['attempts'][0]
        accounting['selections'] += 1
        if first['status'] == 'unresolved_opening':
            assert not row['usable']; accounting['unresolved'] += 1; continue
        assert sha(ROOT / first['path']) == first['sha256']
        grade = first['grade']
        accounting.update(source=grade['plays_total'], driven=grade['plays_driven'],
                          accepted=grade['accepted'], explicitly_skipped=len(grade['skipped']))
        if not row['usable']:
            excluded.update(first['reasons']); accounting['excluded'] += 1; continue
        assert first['usable'] and not first['reasons'] and job['tag'] in expected
        q = expected[job['tag']]
        for k in ('split', 'signature', 'decks'): assert q[k] == job[k]
        for k in ('path', 'sha256'): assert q[k] == first[k]
        assert grade['plays_total'] == grade['plays_driven'] == grade['accepted']
        assert not grade['skipped'] and not grade['elixir_delays']['n'] and grade['crowns_match']
        rec = read(ROOT / first['path'])
        cp = ROOT / job['crawl'] / 'plays_ext.csv'
        with cp.open(encoding='utf-8', newline='') as f: commands = list(csv.DictReader(f))
        assert len(commands) == grade['plays_total']
        raw = {s: Counter(base(c['attr_card']) for c in commands if c['attr_ability'] == '0'
               and {'red': 0, 'blue': 1}[c['attr_s']] == s) for s in (0, 1)}
        actual = {s: Counter(base(c['card']) for c in rec['log'] if c.get('accepted')
                  and not c.get('ability') and c['side'] == s) for s in (0, 1)}
        assert raw == actual
        eligible = [i for i, d in enumerate(job['decks']) if {base(c) for c in d} == ICEBOW]
        assert eligible
        for i in eligible:
            side = 1 - i
            sides.append(dict(tag=job['tag'], split=job['split'], side=side, csv_sha256=sha(cp),
                         own_commands=dict(raw[side]), opponent_commands=dict(raw[1-side])))
            own_delta.update(raw[side]); opp_delta.update(raw[1-side])
            replay_delta.update({k: int(raw[1-side][k] > 0) for k in COMPONENTS})
        selected[job['tag']] = dict(tag=job['tag'], split=job['split'], signature=job['signature'],
            decks=job['decks'], path=first['path'], sha256=first['sha256'], origin='verified_void')
        accounting['usable'] += 1
    assert accounting['usable'] == len(expected) == proof['counts']['usable']
    assert {k: opp_delta[k] for k in COMPONENTS} == proof['component_casts']
    assert {k: replay_delta[k] for k in COMPONENTS} == proof['component_replays']
    assert len({r['signature'] for r in selected.values()}) == len(selected)
    splits = Counter(r['split'] for r in selected.values())
    own = Counter(); opponent = Counter()
    for s in sides:
        if s['split'] == 'confirmation':
            own.update(s['own_commands']); opponent.update(s['opponent_commands'])
    assert own == Counter(old['confirmation_exact_own_commands']) + own_delta
    assert opponent == Counter(old['confirmation_exact_opponent_commands']) + opp_delta
    report = dict(complete=True, trainable=False, N2_complete=False, model_predictions=0,
        sources=sources, script_sha256=sha(__file__), plan_sha256=sha(HERE / 'PLAN.md'),
        distinct_selected_groups=len(old_tags) + len(jobs), qualified_by_split=dict(splits),
        exact_icebow_qualified_replays={s: len({r['tag'] for r in sides if r['split'] == s})
            for s in ('training', 'development', 'confirmation')},
        qualified=sorted(selected.values(), key=lambda r: r['tag']), exact_sides=sides,
        confirmation_exact_own_commands=dict(own), confirmation_exact_opponent_commands=dict(opponent),
        component_replay_counts={k: len({r['tag'] for r in sides if r['split'] == 'confirmation'
            and r['opponent_commands'].get(k, 0)}) for k in COMPONENTS},
        delta_accounting=dict(accounting), delta_exclusions=dict(excluded),
        delta_own_commands=dict(own_delta), delta_opponent_commands=dict(opp_delta),
        limits=['Source casts/replays are not qualified tactical opportunities or sufficient power.',
                'Original failures remain immutable; no missing early-terminal suffix is waived.',
                'No new model, training activation or confirmation policy predictions.'])
    output.write_text(json.dumps(report, indent=2))
    print(json.dumps({k: report[k] for k in ('distinct_selected_groups', 'qualified_by_split',
        'exact_icebow_qualified_replays', 'component_replay_counts', 'delta_accounting', 'delta_exclusions')}))
    print('VOID_CAPACITY_INDEPENDENT_PASS')


if __name__ == '__main__': main()
