"""Count source-command capacity, not policy outcomes or labeled opportunities."""
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
CHECKS=ROOT/'scratchpad/gauntlet/L71/integration/checks'
ICEBOW={'ice-wizard','knight','rocket','skeletons','tesla','the-log','tornado','x-bow'}


def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def base(card):return card.split('-ev')[0].removesuffix('-hero')


def main():
    output=HERE/'confirmation_capacity.json';assert not output.exists()
    collections=[('reserved_pilot','reserved_pilot_independent.json','l72-reserved-pilot-independent'),
                 ('reserved_icebow_corrected','reserved_icebow_corrected_independent.json','l72-corrected-icebow-independent')]
    seen=set();signatures=set();qualified=[];sides=[];sources={};totals=Counter();exact=Counter()
    for name,report_name,receipt_name in collections:
        report=HERE/report_name;proof=read(report);assert proof['complete']
        receipt=CHECKS/(receipt_name+'.json');r=read(receipt)
        assert r['exit_code']==0 and r['matched']
        assert hashlib.sha256(receipt.with_suffix('.out').read_text().encode()).hexdigest()==r['output_sha256']
        sources[str(report.relative_to(ROOT))]=sha(report);sources[str(receipt.relative_to(ROOT))]=sha(receipt)
        data=ROOT/'icebow/data/bench/native_confirmation_20261005'/name
        summary=data/'summary.jsonl';assert sha(summary)==proof['summary_sha256']
        rows=[json.loads(s) for s in summary.read_text().splitlines()]
        prepared=read(HERE/(name+'_prepared.json'));jobs=read(prepared['jobs_path'])
        assert sha(prepared['jobs_path'])==prepared['jobs_sha256']
        sources[str((HERE/(name+'_prepared.json')).relative_to(ROOT))]=sha(HERE/(name+'_prepared.json'))
        for job,row in zip(jobs,rows):
            assert job['tag']==row['tag'] and job['split']==row['split']
            assert job['tag'] not in seen and job['signature'] not in signatures
            seen.add(job['tag']);signatures.add(job['signature'])
            if not row['usable']:continue
            path=data/'recordings'/('replay_'+job['tag']+'.json')
            qualified.append(dict(tag=job['tag'],split=job['split'],signature=job['signature'],
                path=str(path.relative_to(ROOT)),sha256=row['recording_sha256'],decks=job['decks']))
            totals[job['split']]+=1
            eligible=[i for i,d in enumerate(job['decks']) if {base(c) for c in d}==ICEBOW]
            if not eligible:continue
            exact[job['split']]+=1
            assert sha(path)==row['recording_sha256'];rec=read(path)
            with (ROOT/job['crawl']/'plays_ext.csv').open(encoding='utf-8',newline='') as f:commands=list(csv.DictReader(f))
            for deck_index in eligible:
                own=1-deck_index
                accepted=[p for p in rec['log'] if p.get('accepted') and not p.get('ability')]
                actual={s:Counter(base(p['card']) for p in accepted if p['side']==s) for s in (own,1-own)}
                expected={s:Counter(base(p['attr_card']) for p in commands if p['attr_ability']=='0'
                                   and {'red':0,'blue':1}[p['attr_s']]==s) for s in (own,1-own)}
                assert actual==expected,'Independent original CSV card-count mismatch'
                sides.append(dict(tag=job['tag'],split=job['split'],side=own,
                    own_commands=dict(actual[own]),opponent_commands=dict(actual[1-own]),
                    opponent_deck=job['decks'][1-deck_index]))
    assert len(qualified)==sum(totals.values())
    conf=[r for r in sides if r['split']=='confirmation']
    opponent=Counter();own=Counter()
    for r in conf:opponent.update(r['opponent_commands']);own.update(r['own_commands'])
    report=dict(complete=True,trainable=False,model_predictions=0,N2_complete=False,
        sources=sources,script_sha256=sha(__file__),plan_sha256=sha(HERE/'CONFIRMATION_CAPACITY_PLAN.md'),
        distinct_selected_groups=len(seen),qualified_by_split=dict(totals),
        exact_icebow_qualified_replays=dict(exact),qualified=qualified,exact_sides=sides,
        confirmation_exact_sides=len(conf),confirmation_exact_own_commands=dict(own),
        confirmation_exact_opponent_commands=dict(opponent),
        component_replay_counts={k:len({r['tag'] for r in conf if r['opponent_commands'].get(k,0)})
                                  for k in ['goblin-barrel','witch','night-witch','furnace']},
        limits=['Source cast counts are upper bounds, not qualified tactical opportunities.',
                'No independence claim for repeated casts or both sides of one replay.',
                'Training/development general decks cannot replace missing exact-Icebow confirmation.'])
    output.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({k:report[k] for k in ['qualified_by_split','exact_icebow_qualified_replays',
        'component_replay_counts','confirmation_exact_opponent_commands']}))
    print('CONFIRMATION_CAPACITY_INDEPENDENT_COMMAND_COUNTS_VERIFIED')


if __name__=='__main__':main()
