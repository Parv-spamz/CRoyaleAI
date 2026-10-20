"""Independent native trial recount; no resolver import, simulation or inference."""
import csv
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[5]
HERE=Path(__file__).resolve().parent
LOOP=HERE.parent
sys.path[:0]=[str(LOOP),str(ROOT)]
from verify_reserved_icebow_corrected import recount
from verify_native_preflight import compare_frames
from research.sandbox_tools.validate_public_capture import inspect

def read(p):return json.loads(Path(p).read_bytes())
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def csv_rows(p):
    with Path(p).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))

def opening(rec,commands,job):
    # Compare public native pre-command hand names to each original timeline card;
    # separately re-enact the four-card FIFO sequence from recorded tick-zero IDs.
    card_log=[r for r in rec['log'] if r.get('result_code') is not None and not r.get('ability')]
    assert len(rec['play_frames'])==len(card_log)
    catalog=read(ROOT/'research/ext/cr-native-sandbox/native_core/data/live_card_catalog.json')
    values=catalog['cards']
    norm=lambda s:''.join(x for x in s.lower() if x.isalnum())
    by_name={norm(v['internal_name']):int(v['card_id']) for v in values}
    display={int(v['card_id']):v['display_name'] for v in values}
    maps={s:{} for s in ('0','1')}
    for s in ('0','1'):
        state=rec['opening_deal_verified'][s]
        ids=state['hand']+state['queue'];positions=state['hand_positions']+state['queue_positions']
        assert len(set(ids))==8 and sorted(positions)==list(range(8))
        names=rec['final_decks'][s]
        for i,pos in zip(ids,positions):maps[s][names[pos].split('@')[0]]=i
        assert [display[i] for i in state['hand']]==rec['opening_hand'][s]
        assert all(by_name[norm(names[pos].split('@')[0])]==i for i,pos in zip(ids,positions))
    aliases={'barbarian-barrel':'BarbLog','elite-barbarians':'AngryBarbarians','the-log':'Log'}
    # Card IDs are independently taken from the original native card catalog,
    # including known slug/internal-name aliases in the unchanged original driver.
    import ast
    source=(ROOT/'research/sandbox_tools/replay_drive.py').read_text()
    tree=ast.parse(source)
    for node in tree.body:
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='SLUG_ALIASES' for t in node.targets):
            aliases=ast.literal_eval(node.value)
    for side in ('0','1'):
        expected=set()
        for slug in job['decks'][1-int(side)]:
            form='base'
            if slug.endswith('-ev1'):slug=slug[:-4];form='evolution'
            elif slug.endswith('-hero'):slug=slug[:-5];form='hero'
            expected.add((by_name[norm(aliases.get(slug,slug))],form))
        actual=set()
        for name in rec['final_decks'][side]:
            parts=name.split('@')
            actual.add((by_name[norm(parts[0])],parts[1] if len(parts)==2 else 'base'))
        assert actual==expected,'Original deck forms changed'
    for side in ('0','1'):
        state=rec['opening_deal_verified'][side];hand=set(state['hand']);queue=list(state['queue'])
        for command in sorted(commands,key=lambda r:(int(r['tick']),int(r['play_index']))):
            if command['attr_ability']=='1' or {'red':'0','blue':'1'}[command['attr_s']]!=side:continue
            card=by_name[norm(aliases.get(command['attr_card'],command['attr_card']))]
            assert card in hand,(side,command['play_index'],'source card not in inferred native hand')
            hand.remove(card);hand.add(queue.pop(0));queue.append(card)
    for frame,event in zip(rec['play_frames'],card_log):
        assert frame['play_index']==event['play_index'] and frame['tick']==event['engine_tick']
        player=next(p for p in frame['players'] if p['side']==event['side'])
        assert player['hand']==event.get('hand_before',player['hand'])

def check_jobs():
    jobs=read(HERE/'reserved_jobs.json');audit=read(HERE/'audit.json')
    assert jobs['audit_sha256']==sha(HERE/'audit.json')
    assert jobs['training_verified_sha256']==sha(HERE/'verified_v4.json')
    assert jobs['plan_sha256']==sha(HERE/'RESERVED_RECOVERY_PLAN.md')
    expected=sorted([r for r in audit['records'] if r['split']!='training' and not r['position_based']],key=lambda r:r['tag'])
    assert len(jobs['jobs'])==len(expected)
    for job,original in zip(jobs['jobs'],expected):
        assert {k:job[k] for k in original}==original
        assert job['role']=='reserved_fallback' and not original['usable']
        for n,h in job['csv_hashes'].items():assert sha(ROOT/job['job']['crawl']/n)==h
        assert sha(ROOT/job['recording'])==job['recording_sha256']
    assert len({r['tag'] for r in jobs['jobs']})==len(jobs['jobs'])
    print('RESERVED_DEAL_JOBS_VERIFIED')
    return jobs

def main():
    out=HERE/'reserved_verified.json';assert not out.exists()
    result=read(HERE/'reserved_complete.json');started=read(HERE/'reserved_started.json');jobs=check_jobs()
    assert result['complete'] and result['started_sha256']==sha(HERE/'reserved_started.json')
    assert result['source_audit_sha256']==sha(HERE/'audit.json')
    for p,h in started['sources'].items():assert sha(ROOT/p)==h,p
    assert [r['tag'] for r in result['rows']]==[r['tag'] for r in jobs['jobs']]==started['selected']
    counts=dict(trials=0,repeats=0,usable_recovered=0,unchanged_controls=0,source_commands=0,accepted_commands=0)
    for item,row in zip(jobs['jobs'],result['rows']):
        assert item['split']==row['split'] and row['split'] in ('development','confirmation') and item['role']==row['role']
        folder=ROOT/item['job']['crawl']
        for n,h in item['csv_hashes'].items():assert sha(folder/n)==h
        commands=csv_rows(folder/'plays_ext.csv');battle=csv_rows(folder/'battles.csv')[0]
        assert sha(ROOT/item['recording'])==item['recording_sha256']
        captured=[]
        for a in row['attempts']:
            path=ROOT/a['path'];assert sha(path)==a['sha256'];rec=read(path);captured.append(rec)
            if a['status']=='unresolved_opening':
                assert 0<len(rec['reset_history'])<=rec['budget']==61 and rec['total_reset_budget']==64 and row['usable'] is False
                assert len({json.dumps(h['orders'],sort_keys=True) for h in rec['reset_history']})==len(rec['reset_history'])
                continue
            assert rec['seed']==item['seed'] and rec['level']==item['level']
            assert rec['tick_after_reset']==10
            grade,reasons=recount(rec,commands,battle)
            assert grade==a['grade'] and reasons==a['reasons'] and a['usable']==(not reasons)
            assert not inspect(rec)['errors'];opening(rec,commands,item['job'])
            assert rec.get('deal_recovery',{}).get('resets',0)+3<=64
        assert len(captured)==2 and row['attempts'][0]['status']==row['attempts'][1]['status']
        a,b=captured
        if row['attempts'][0]['status']=='unresolved_opening':assert a==b
        else:
            for k in ('log','grade','final','opening_deal_verified'):assert a[k]==b[k]
            for k in ('frames','play_frames'):compare_frames(a[k],b[k])
            assert row['usable']==row['attempts'][0]['usable']
            counts['source_commands']+=len(commands);counts['accepted_commands']+=a['grade']['accepted']
            if item['role']=='unchanged_control':
                old=read(ROOT/item['recording'])
                for k in ('log','grade','final'):assert a[k]==old[k]
                for k in ('frames','play_frames'):compare_frames(a[k],old[k])
                assert row['usable'];counts['unchanged_controls']+=1
            else:counts['usable_recovered']+=int(row['usable'])
        counts['trials']+=1;counts['repeats']+=1
    assert counts['unchanged_controls']==0 and counts['trials']==len(jobs['jobs'])
    assert counts['usable_recovered']==result['usable_recovered']
    report=dict(complete=True,counts=counts,complete_sha256=sha(HERE/'reserved_complete.json'),
        verifier_sha256=sha(__file__),training_only=False,confirmation_replayed=True,model_predictions=0,N2_complete=False)
    out.write_text(json.dumps(report,indent=2));print(json.dumps(counts));print('RESERVED_DEAL_RECOVERY_INDEPENDENT_PASS')

if __name__=='__main__':
    import argparse,time
    ap=argparse.ArgumentParser();ap.add_argument('--jobs-only',action='store_true');ap.add_argument('--wait-for-completion',action='store_true')
    args=ap.parse_args()
    if args.jobs_only:check_jobs()
    else:
        start=time.monotonic()
        while args.wait_for_completion and not (HERE/'reserved_complete.json').exists():
            receipt=ROOT/'scratchpad/gauntlet/L71/integration/checks/l72-deal-recovery-reserved.json'
            if receipt.exists():
                r=read(receipt)
                assert r['exit_code']==0 and r['matched'],'Reserved capture failed'
            assert time.monotonic()-start<3600,'Reserved capture wait exceeded one hour'
            time.sleep(20)
        main()
