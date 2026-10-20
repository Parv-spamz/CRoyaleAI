"""Independent source-membership and raw-command capacity recount."""
from collections import Counter
import copy
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
LOOP = HERE.parent
DEAL = LOOP / 'deal_recovery'
ICEBOW = frozenset(('ice-wizard', 'knight', 'rocket', 'skeletons', 'tesla', 'the-log', 'tornado', 'x-bow'))


def read(p): return json.loads(Path(p).read_bytes())
def sha(p):
    with Path(p).open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
def card(s):
    for suffix in ('-ev1', '-ev2', '-hero'):
        if s.endswith(suffix): return s[:-len(suffix)]
    return s


def expected():
    audit = read(DEAL / 'audit.json'); selected = {}
    records = {r['tag']: r for r in audit['records']}
    for r in audit['records']:
        if r['usable']:
            selected[r['tag']] = (r['recording'], r['recording_sha256'], 'original')
    for name in ('complete_v3.json', 'reserved_complete.json'):
        batch = read(DEAL / name)
        for r in batch['rows']:
            if r['role'] == 'unchanged_control':
                assert r['tag'] in selected; continue
            assert not records[r['tag']]['usable']
            if r['usable']:
                assert r['tag'] not in selected
                a = r['attempts'][0]
                selected[r['tag']] = (a['path'], a['sha256'], name)
    members = {}; sides = {}; own = Counter(); opponent = Counter(); by_split = Counter(); added = Counter(); exact = Counter()
    for tag, (path, digest, origin) in selected.items():
        raw = records[tag]; job = raw['job']; split = raw['split']
        assert sha(ROOT / path) == digest
        members[tag] = dict(tag=tag, split=split, signature=job['signature'], decks=job['decks'],
                            path=path, sha256=digest, origin=origin)
        by_split[split] += 1
        if origin != 'original': added[split] += 1
        eligible = [i for i, d in enumerate(job['decks']) if frozenset(map(card, d)) == ICEBOW]
        if eligible: exact[split] += 1
        for i in eligible:
            side = 1 - i; command_path = ROOT / job['crawl'] / 'plays_ext.csv'
            ours = Counter(); theirs = Counter()
            with command_path.open(encoding='utf-8', newline='') as f:
                for command in csv.DictReader(f):
                    if command['attr_ability'] != '0': continue
                    red_side = command['attr_s'] == 'red'
                    target = ours if (side == 0) == red_side else theirs
                    target[card(command['attr_card'])] += 1
            sides[(tag, side)] = dict(tag=tag, side=side, split=split, csv_sha256=sha(command_path),
                own_commands=dict(ours), opponent_commands=dict(theirs))
            if split == 'confirmation': own += ours; opponent += theirs
    components = {c: len({s['tag'] for s in sides.values() if s['split'] == 'confirmation'
        and s['opponent_commands'].get(c, 0)}) for c in ('goblin-barrel', 'witch', 'night-witch', 'furnace')}
    totals = dict(qualified_by_split=dict(by_split), newly_recovered_by_split=dict(added),
        exact_icebow_qualified_replays=dict(exact), confirmation_exact_own_commands=dict(own),
        confirmation_exact_opponent_commands=dict(opponent), component_replay_counts=components)
    return members, sides, totals, len(records)


def compare(report, members, sides, totals, selections):
    assert report['complete'] and report['trainable'] is False and report['N2_complete'] is False
    assert report['model_predictions'] == 0 and report['distinct_selected_groups'] == selections
    assert len(report['qualified']) == len(members)
    assert {r['tag']: r for r in report['qualified']} == members
    assert len({r['signature'] for r in report['qualified']}) == len(members)
    assert len(report['exact_sides']) == len(sides)
    assert {(r['tag'], r['side']): r for r in report['exact_sides']} == sides
    for k, value in totals.items(): assert report[k] == value, k


def main():
    output = HERE / 'verified.json'; assert not output.exists()
    report = read(HERE / 'inventory.json')
    assert report['script_sha256'] == sha(HERE / 'inventory.py')
    assert report['plan_sha256'] == sha(HERE / 'PLAN.md')
    for p, h in report['sources'].items(): assert sha(ROOT / p) == h
    truth = expected(); compare(report, *truth)
    passed = []
    def reject(name, mutation):
        bad = copy.deepcopy(report); mutation(bad)
        try: compare(bad, *truth)
        except AssertionError: passed.append(name)
        else: raise AssertionError('Corruption accepted: ' + name)
    reject('omitted_member', lambda r: r['qualified'].pop())
    reject('duplicate_member', lambda r: r['qualified'].append(r['qualified'][0]))
    reject('changed_split', lambda r: r['qualified'][0].update(split='changed'))
    reject('changed_form', lambda r: r['qualified'][0]['decks'][0].__setitem__(0, 'changed-form'))
    reject('changed_command_count', lambda r: r['exact_sides'][0]['own_commands'].update(rocket=99999))
    reject('changed_aggregate', lambda r: r['confirmation_exact_opponent_commands'].update(witch=99999))
    reject('training_activation', lambda r: r.update(trainable=True))
    reject('premature_acceptance', lambda r: r.update(N2_complete=True))
    proof = dict(complete=True, inventory_sha256=sha(HERE / 'inventory.json'), script_sha256=sha(__file__),
        positive_controls=1, rejected_corruptions=passed, independently_counted=truth[2],
        qualified_records=len(truth[0]), exact_icebow_sides=len(truth[1]), model_predictions=0, N2_complete=False)
    output.write_text(json.dumps(proof, indent=2))
    print(json.dumps(proof)); print('RECOVERED_CAPACITY_INDEPENDENT_PASS')


if __name__ == '__main__': main()
