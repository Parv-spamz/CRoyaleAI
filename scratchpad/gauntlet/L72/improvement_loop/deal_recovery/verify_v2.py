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
    assert len(rec['play_frames'])==rec['grade']['plays_driven']
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
    for frame,event in zip(rec['play_frames'],[r for r in rec['log'] if r.get('result_code') is not None]):
        assert frame['play_index']==event['play_index'] and frame['tick']==event['engine_tick']
        player=next(p for p in frame['players'] if p['side']==event['side'])
        assert player['hand']==event.get('hand_before',player['hand'])

def main():
    out=HERE/'verified_v2.json';assert not out.exists()
    result=read(HERE/'complete_v2.json');started=read(HERE/'started_v2.json');audit=read(HERE/'audit.json')
    assert result['complete'] and result['started_sha256']==sha(HERE/'started_v2.json')
    assert result['source_audit_sha256']==sha(HERE/'audit.json')
    for p,h in started['sources'].items():assert sha(ROOT/p)==h,p
    assert [r['tag'] for r in result['rows']]==[r['tag'] for r in audit['training_trials']]==started['selected']
    counts=dict(trials=0,repeats=0,usable_recovered=0,unchanged_controls=0,source_commands=0,accepted_commands=0)
    for item,row in zip(audit['training_trials'],result['rows']):
        assert item['split']==row['split']=='training' and item['role']==row['role']
        folder=ROOT/item['job']['crawl']
        for n,h in item['csv_hashes'].items():assert sha(folder/n)==h
        commands=csv_rows(folder/'plays_ext.csv');battle=csv_rows(folder/'battles.csv')[0]
        assert sha(ROOT/item['recording'])==item['recording_sha256']
        captured=[]
        for a in row['attempts']:
            path=ROOT/a['path'];assert sha(path)==a['sha256'];rec=read(path);captured.append(rec)
            if a['status']=='unresolved_opening':
                assert 0<len(rec['reset_history'])<=rec['budget']==64 and row['usable'] is False
                assert len({json.dumps(h['orders'],sort_keys=True) for h in rec['reset_history']})==len(rec['reset_history'])
                continue
            assert rec['seed']==item['seed'] and rec['level']==item['level']
            assert rec['tick_after_reset']==10
            grade,reasons=recount(rec,commands,battle)
            assert grade==a['grade'] and reasons==a['reasons'] and a['usable']==(not reasons)
            assert not inspect(rec)['errors'];opening(rec,commands,item['job'])
            assert rec.get('deal_recovery',{}).get('resets',0)<=64
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
    assert counts['unchanged_controls']==3
    assert counts['usable_recovered']==result['usable_recovered']
    report=dict(complete=True,counts=counts,complete_sha256=sha(HERE/'complete_v2.json'),
        verifier_sha256=sha(__file__),training_only=True,confirmation_replayed=False,model_predictions=0,N2_complete=False)
    out.write_text(json.dumps(report,indent=2));print(json.dumps(counts));print('DEAL_RECOVERY_TRAINING_INDEPENDENT_PASS')

if __name__=='__main__':main()
