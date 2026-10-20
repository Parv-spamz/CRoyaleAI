"""Read-only pilot recount from CSVs and native records, independent of its grader."""
from collections import Counter, defaultdict
import argparse
import copy
import csv
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
DATA = ROOT / 'icebow/data/bench/native_confirmation_20261005/reserved_pilot'
CHECKS = ROOT / 'scratchpad/gauntlet/L71/integration/checks'
sys.path.insert(0, str(ROOT))
from research.sandbox_tools.validate_public_capture import inspect
from verify_native_preflight import compare_frames


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def receipt(path, token):
    r = read(path)
    assert r['exit_code'] == 0 and r['matched'] is True
    assert r['expected'] == token
    output = path.with_suffix('.out').read_text(encoding='utf-8')
    assert hashlib.sha256(output.encode()).hexdigest() == r['output_sha256']


def read_csv(path):
    with Path(path).open(encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


def recount(rec, commands, battle):
    """Check log membership, then independently derive every stored grade field."""
    ordered = sorted(commands, key=lambda e: (int(e['tick']), int(e['play_index'])))
    assert len(ordered) == int(battle['plays'])
    assert len({int(e['play_index']) for e in ordered}) == len(ordered)
    log = rec['log']
    assert len(log) <= len(ordered)
    attempted = accepted = invalid = 0
    delayed = []
    rejected = Counter()
    skipped = []
    for src, event in zip(ordered, log):
        assert event['play_index'] == int(src['play_index'])
        assert event['tick'] == int(src['tick'])
        assert event['side'] == {'red': 0, 'blue': 1}[src['attr_s']]
        ability = bool(int(src['attr_ability']))
        if not ability:
            assert event['card'] == src['attr_card']
            if 'skipped' not in event:
                x, y = int(src['x_units']), int(src['y_units'])
                if src['attr_i'] == '1':
                    x, y = 18000 - x, 32000 - y
                assert (event['x'], event['y']) == (x, y)
        else:
            assert event.get('ability') is True
        if 'skipped' in event:
            skipped.append(event)
        if event.get('result_code') is None:
            assert 'skipped' in event
            continue
        attempted += 1
        assert isinstance(event['accepted'], bool)
        assert event['accepted'] == (event['result_code'] == 0)
        accepted += int(event['accepted'])
        if not event['accepted']:
            rejected[event['result_name']] += 1
        invalid += int(event['placement_valid'] is False)
        assert event['delay_ticks'] >= 0
        delayed.append(event['delay_ticks'])
    expected = [int(battle['opponent_crowns']), int(battle['team_crowns'])]
    assert [rec['expected']['crowns_by_side'][str(i)] for i in (0, 1)] == expected
    terminal = rec['final'].get('terminal_tick')
    grade = dict(plays_total=len(ordered), plays_driven=attempted, accepted=accepted,
                 rejected_by_reason=dict(rejected), invalid_placement=invalid,
                 elixir_delays=dict(n=sum(d > 0 for d in delayed),
                                   max_ticks=max(delayed, default=0), sum_ticks=sum(delayed)),
                 skipped=skipped, crowns_match=rec['final']['crowns'] == expected,
                 terminal_vs_last_play_ticks=terminal-int(ordered[-1]['tick']) if terminal else None)
    assert grade == rec['grade'], 'Raw command recount disagrees with saved grade'
    reasons = []
    if attempted != len(ordered): reasons.append('undriven_commands')
    if accepted != attempted or rejected: reasons.append('rejected_commands')
    if skipped: reasons.append('skipped_commands')
    if invalid: reasons.append('invalid_placement')
    if any(delayed): reasons.append('elixir_delay')
    if rec['final']['crowns'] != expected: reasons.append('crown_mismatch')
    if rec['final']['terminated'] is not True: reasons.append('nonterminal')
    return grade, reasons


def verify_record(job, row):
    assert all(row[k] == job[k] for k in ('index', 'tag', 'split', 'strata'))
    folder = ROOT / job['crawl']
    commands = read_csv(folder / 'plays_ext.csv')
    battles = read_csv(folder / 'battles.csv')
    assert len(battles) == 1
    assert all(e['replay_tag'] == job['tag'] for e in commands + battles)
    p = DATA / 'recordings' / ('replay_' + job['tag'] + '.json')
    if 'recording_sha256' not in row:
        assert row['usable'] is False and row['reasons'] == ['unreconstructable_source']
        assert any(s in row['error'] for s in ('no (hand, queue) assignment reproduces the play sequence',
                                              'plays cards outside its deck'))
        assert not p.exists()
        return dict(source_commands=len(commands), source_excluded=True)
    assert sha(p) == row['recording_sha256'] and p.stat().st_size == row['bytes']
    rec = read(p)
    assert rec['tag'] == job['tag'] and rec['seed'] == 424242 and rec['level'] == 11
    assert rec['record_every'] == 10 and rec['record_full'] is True
    grade, reasons = recount(rec, commands, battles[0])
    assert grade == row['grade'] and reasons == row['reasons']
    assert row['usable'] is (len(reasons) == 0)
    if row['usable']:
        assert all(e['engine_tick'] == e['tick'] for e in rec['log']), 'Qualified command was delivered late'
    fields = inspect(rec)
    assert fields == row['fields'] and not fields['errors']
    if job['repeat']:
        p2 = DATA / 'repeats' / p.name
        assert sha(p2) == row['repeat_sha256']
        rec2 = read(p2)
        for key in ('final', 'log', 'grade'):
            assert rec[key] == rec2[key]
        compare_frames(rec['frames'], rec2['frames'])
        compare_frames(rec['play_frames'], rec2['play_frames'])
        assert all(row['repeat_equal'].values())
    else:
        assert 'repeat_sha256' not in row
    return dict(source_commands=len(commands), driven_commands=grade['plays_driven'],
                accepted_commands=grade['accepted'], skipped_commands=len(grade['skipped']),
                repeat=int(job['repeat']), coverage=fields['coverage'])


def verify_sources():
    prepared = read(HERE / 'reserved_pilot_prepared.json')
    prov = read(HERE / 'reserved_collection_provenance.json')
    assert sha(HERE / 'reserved_pilot_prepared.json') == prov['prepared_sha256']
    for name, digest in prov['sources'].items():
        assert sha(ROOT / name) == digest, name
    assert sha(HERE / 'RESERVED_PILOT_PLAN.md') == prepared['plan_sha256']
    assert sha(prepared['jobs_path']) == prepared['jobs_sha256'] == prov['jobs_sha256']
    assert sha(prepared['csv_hashes_path']) == prepared['csv_hashes_sha256']
    for name,digest in prepared['raw_parts'].items():
        assert sha(ROOT/'scratchpad/gauntlet/L67/hf/replays'/name)==digest, name
    for name, digest in read(prepared['csv_hashes_path']).items():
        assert sha(ROOT / name) == digest, name
    for stem in ('receipt', 'report'):
        path = CHECKS / 'l72-native-capture-v2.json' if stem == 'receipt' else HERE / 'native_capture_v2_verified.json'
        assert sha(path) == prov['preflight_' + stem + '_sha256']
    receipt(CHECKS / 'l72-native-capture-v2.json', 'NATIVE_CAPTURE_V2_PREFLIGHT_PASS')
    compat = read(HERE / 'native_compatibility.json')
    reserve = read(HERE / 'replay_reservation.json')
    assert sha(compat['compatible_file']) == prepared['compatible_sha256']
    assert sha(reserve['reservation_file']) == prepared['reservation_sha256']
    compatible = [json.loads(s) for s in Path(compat['compatible_file']).read_text().splitlines()]
    reserved = {r['tag']: r for s in Path(reserve['reservation_file']).read_text().splitlines()
                if (r := json.loads(s))}
    ordered = sorted(compatible, key=lambda r: hashlib.sha256((prepared['salt'] + r['signature']).encode()).hexdigest())
    selected = {r['tag'] for r in ordered if 'exact_icebow' in r['strata']}
    strata = ('rocket_deck','rocket_tornado_deck','xbow_deck','log_vs_barrel',
              'versus_witch','versus_night-witch','versus_furnace')
    for split in ('training', 'development', 'confirmation'):
        pool = [r for r in ordered if r['split'] == split]
        for stratum in ('ordinary', *strata):
            cohort = [r for r in pool if stratum == 'ordinary' or stratum in r['strata']]
            selected.update(r['tag'] for r in cohort[:32])
    jobs = read(prepared['jobs_path'])
    compatible_by_tag = {r['tag']:r for r in compatible}
    assert len(jobs) == 645 == len({j['tag'] for j in jobs})
    assert [r['tag'] for r in ordered if r['tag'] in selected] == [j['tag'] for j in jobs]
    for i, job in enumerate(jobs):
        assert job['index'] == i and job['repeat'] == (i % 25 == 0)
        bound = reserved[job['tag']]
        for key in ('split', 'signature'):
            assert job[key] == bound[key], (job['tag'], key)
        for key in ('split', 'signature', 'decks', 'strata'):
            assert job[key] == compatible_by_tag[job['tag']][key], (job['tag'], key)
    assert len({j['signature'] for j in jobs}) == len(jobs)
    return jobs


def self_test():
    src = dict(tick='20', play_index='0', attr_s='red', attr_ability='0',
               attr_card='knight', x_units='1000', y_units='2000', attr_i='1')
    event = dict(tick=20, play_index=0, side=0, card='knight', x=17000, y=30000,
                 accepted=True, result_code=0, placement_valid=True, delay_ticks=0, result_name='accepted')
    battle = dict(plays='1', opponent_crowns='1', team_crowns='0')
    rec = dict(log=[event], expected=dict(crowns_by_side={'0':1,'1':0}),
               final=dict(crowns=[1,0],terminated=True,terminal_tick=30),
               grade=dict(plays_total=1,plays_driven=1,accepted=1,rejected_by_reason={},
                          invalid_placement=0,elixir_delays=dict(n=0,max_ticks=0,sum_ticks=0),
                          skipped=[],crowns_match=True,terminal_vs_last_play_ticks=10))
    assert recount(rec,[src],battle)[1] == []
    mutations = [lambda r:r['log'][0].update(play_index=1), lambda r:r['log'][0].update(tick=21),
                 lambda r:r['log'][0].update(side=1), lambda r:r['log'][0].update(x=1000),
                 lambda r:r['log'][0].update(card='tesla'), lambda r:r['log'][0].update(accepted=False),
                 lambda r:r['log'][0].update(delay_ticks=1), lambda r:r['final'].update(crowns=[0,1]),
                 lambda r:r['grade'].update(accepted=2), lambda r:r['log'].append(copy.deepcopy(event))]
    for mutate in mutations:
        bad = copy.deepcopy(rec); mutate(bad)
        try: recount(bad,[src],battle)
        except AssertionError: pass
        else: raise AssertionError('Corrupted evidence accepted')
    fixture = dict(tick=1, public_objects=dict(projectiles=[dict(id='a',card_id=1,generation_key=1,x=5)],area_effects=[]))
    a=[copy.deepcopy(fixture),copy.deepcopy(fixture)]; a[1]['tick']=2
    b=copy.deepcopy(a)
    for frame in b: frame['public_objects']['projectiles'][0]['id']='b'
    compare_frames(a,b)
    b[1]['public_objects']['projectiles'][0]['id']='c'
    try: compare_frames(a,b)
    except AssertionError: pass
    else: raise AssertionError('Split object lifetime accepted')
    print('RESERVED_PILOT_RECOUNT_CONTROLS_PASS: 2 positives, 11 corruptions rejected')


def main(args):
    if args.self_test:
        return self_test()
    own_sources = {str(p.relative_to(ROOT)):sha(p) for p in (
        Path(__file__), HERE/'verify_native_preflight.py', HERE/'PILOT_RECONCILIATION_PLAN.md',
        ROOT/'research/sandbox_tools/validate_public_capture.py')}
    final_receipt = CHECKS / 'l72-reserved-pilot-collection.json'
    if args.wait_for_completion:
        deadline = time.monotonic() + 7200
        while not final_receipt.exists():
            if time.monotonic() > deadline: raise TimeoutError('Existing collection did not finish within two hours')
            print('WAITING_FOR_EXISTING_COLLECTION', flush=True); time.sleep(30)
    for name,digest in own_sources.items():
        assert sha(ROOT/name)==digest, name
    if not args.training_smoke:
        receipt(final_receipt, 'RESERVED_PILOT_COLLECTION_COMPLETE')
    jobs = verify_sources()
    rows = [json.loads(s) for s in (DATA / 'summary.jsonl').read_text().splitlines()]
    if args.training_smoke:
        selected = [(jobs[r['index']],r) for r in rows if r['split']=='training'][:10]
        assert len(selected)==10
        for job,row in selected: verify_record(job,row)
        print('RESERVED_PILOT_TRAINING_SMOKE_PASS: 10 completed training records')
        return
    assert len(rows)==len(jobs)
    complete=read(HERE/'reserved_collection_complete.json')
    assert complete['complete'] and not complete['new_model_trained'] and not complete['N2_complete']
    assert sha(DATA/'summary.jsonl') == complete['summary_sha256']
    assert sha(HERE/'reserved_collection_provenance.json') == complete['provenance_sha256']
    totals=Counter(); by_split=defaultdict(Counter); by_stratum=defaultdict(Counter)
    commands=Counter(); coverage=Counter(); decks=defaultdict(Counter); usable=defaultdict(list)
    repeats=[]; unavailable_repeats=[]; exact=[]
    for job,row in zip(jobs,rows):
        counts=verify_record(job,row)
        commands.update({k:v for k,v in counts.items() if k!='coverage'})
        coverage.update(counts.get('coverage',{}))
        status='usable' if row['usable'] else 'excluded'
        totals[status]+=1; by_split[job['split']][status]+=1
        for s in job['strata']: by_stratum[job['split']+':'+s][status]+=1
        for reason in row['reasons']: totals['reason:'+reason]+=1
        if row['usable']: usable[job['split']].append(job['tag'])
        for deck in job['decks']: decks[job['split']][','.join(sorted(deck))]+=int(row['usable'])
        if job['repeat']:
            (unavailable_repeats if counts.get('source_excluded') else repeats).append(job['tag'])
        if 'exact_icebow' in job['strata']:
            exact.append(dict(tag=job['tag'],split=job['split'],usable=row['usable'],reasons=row['reasons']))
    split={k:dict(v) for k,v in by_split.items()}; strata={k:dict(v) for k,v in by_stratum.items()}
    assert dict(totals)==complete['totals'] and split==complete['by_split'] and strata==complete['by_stratum']
    assert {s:usable[s] for s in ('training','development','confirmation')}==complete['qualified_tags']
    assert len(repeats)+len(unavailable_repeats)==26
    assert len(exact)==11 and all(e['split']=='confirmation' for e in exact)
    for name,digest in own_sources.items():
        assert sha(ROOT/name)==digest, name
    report=dict(complete=True,replays=len(rows),totals=dict(totals),by_split=split,by_stratum=strata,
                commands=dict(commands),coverage=dict(coverage),exact_icebow=exact,
                repeats_verified=repeats,source_excluded_scheduled_repeats=unavailable_repeats,
                usable_original_deck_counts={k:{d:n for d,n in v.items() if n} for k,v in decks.items()},
                summary_sha256=sha(DATA/'summary.jsonl'),collection_receipt_sha256=sha(final_receipt),
                producer_report_sha256=sha(HERE/'reserved_collection_complete.json'),
                script_sha256=sha(__file__),repeat_oracle_sha256=sha(HERE/'verify_native_preflight.py'),
                verification_sources=own_sources,
                model_predictions=0,N2_complete=False,
                limitations=['Reconstruction counts are not tactical opportunity denominators or statistical power.',
                             'General-deck examples do not replace missing exact-Icebow component evidence.',
                             'Public timings/recorded outcomes retain preflight semantic limits.'])
    output=HERE/'reserved_pilot_independent.json'
    assert not output.exists(), 'Preserve original verification report'
    output.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('replays','totals','by_split','commands')}))
    print('RESERVED_PILOT_INDEPENDENTLY_VERIFIED')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    group=parser.add_mutually_exclusive_group()
    group.add_argument('--self-test',action='store_true')
    group.add_argument('--training-smoke',action='store_true')
    group.add_argument('--wait-for-completion',action='store_true')
    main(parser.parse_args())
