"""Separate scalar/prefix/oracle verifier. Does not import the reader or producer."""
import copy
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
OUT = ROOT/'icebow/data/bench/opponent_hand_reader_20261006'
sys.path.insert(0,str(ROOT))
from pipeline import vocab


def read(p):
    return json.loads(Path(p).read_text())


def sha(p):
    with Path(p).open('rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest()


def key(n):
    k = vocab.engine_key(n)
    return vocab.base_key(k).replace('_','-') if k else None


def actual_hand(value):
    if not isinstance(value,list) or len(value)!=4:
        return None
    result=[key(x) for x in value]
    return sorted(result) if all(result) and len(set(result))==4 else None


def independent_belief(events, tick, own_side, trusted):
    """Use event prefix groups and intervals, independently of reader state/API."""
    groups=defaultdict(list)
    for e in events:
        if e['tick'] < tick and e['side'] != own_side:
            groups[e['tick']].append(key(e['card']))
    revealed=set(); latest={}; position=0; issues=Counter(); invalid=False
    for t, cards in sorted(groups.items()):
        revealed.update(c for c in cards if c)
        if len(revealed)>8:
            invalid=True; latest={};position=0
            issues['more_than_eight_identities']+=1
            continue
        if None in cards or len(cards)!=len(set(cards)):
            latest={};position=0;issues['unknown_or_duplicate_card_in_batch']+=1
            continue
        if any(c in latest and position-latest[c][0]+latest[c][1]-1+len(cards)-1<4 for c in cards):
            latest={};position=0;issues['impossible_early_replay']+=1
        position+=len(cards)
        latest.update({c:(position,len(cards)) for c in cards})
    inside=set();outside=set();returns={}
    if not invalid:
        for c,(end,size) in latest.items():
            elapsed=position-end
            returns[c]=[max(0,5-elapsed-size),max(0,4-elapsed)]
            if elapsed>=4:inside.add(c)
            if elapsed+size-1<4:outside.add(c)
        if len(revealed)==8 and len(outside)==4:
            inside=revealed-outside
            returns.update({c:[0,0] for c in inside})
    consistent=len(inside)<=4 and len(outside)<=4 and not inside.intersection(outside)
    if not consistent:
        inside=set();outside=set();returns={};issues['inconsistent_hand_size']=1
    if invalid:issues['unsupported_rules_or_deck']=1
    return dict(rules='standard_8_card_fifo_4_hand',revealed=sorted(revealed),
        in_hand=sorted(inside),out_of_hand=sorted(outside),uncertain=sorted(revealed-inside-outside),
        unrevealed_slots=max(0,8-len(revealed)),plays_to_return=returns,
        full_hand=bool(not invalid and consistent and len(inside)==4),
        certified=bool(trusted and not invalid and consistent and not issues),
        conditional_on_complete_events=True,issues=dict(issues))


def measure(p,truth):
    h=set(truth);inside=set(p['in_hand']);outside=set(p['out_of_hand'])
    return dict(queries=1,full_predictions=int(p['full_hand']),
        full_exact=int(p['full_hand'] and inside==h),
        full_errors=int(p['full_hand'] and inside!=h),
        in_claims=len(inside),in_correct=sum(c in h for c in inside),
        out_claims=len(outside),out_correct=sum(c not in h for c in outside),
        unrevealed_slots=p['unrevealed_slots'],issue_queries=int(bool(p['issues'])))


def check_prediction(row,streams,truth):
    assert row['truth']==truth
    for arm in ('ideal','public'):
        ev=streams['ideal'] if arm=='ideal' else streams['public'][1-row['side']]
        expected=independent_belief(ev,row['tick'],1-row['side'],arm=='ideal')
        assert row['predictions'][arm]==expected, (row['tag'],row['log_index'],arm)


def controls(row,streams):
    check_prediction(row,streams,row['truth'])
    future=copy.deepcopy(streams)
    future['public'][1-row['side']].append(dict(tick=row['tick']+1,side=row['side'],card='Rocket'))
    check_prediction(row,future,row['truth'])
    own=copy.deepcopy(streams)
    own['ideal'].append(dict(tick=0,side=1-row['side'],card='Rocket'))
    check_prediction(row,own,row['truth'])
    bad=[]
    x=copy.deepcopy(row);x['truth']=['wrong']*4;bad.append((x,streams))
    x=copy.deepcopy(row);x['predictions']['public']['in_hand']=['wrong'];bad.append((x,streams))
    x=copy.deepcopy(row);x['predictions']['public']['out_of_hand']=['wrong'];bad.append((x,streams))
    x=copy.deepcopy(row);x['predictions']['ideal']['unrevealed_slots']+=1;bad.append((x,streams))
    x=copy.deepcopy(row);x['predictions']['public']['certified']=True;bad.append((x,streams))
    x=copy.deepcopy(row);x['predictions']['ideal']['plays_to_return']['wrong']=[0,0];bad.append((x,streams))
    ev=copy.deepcopy(streams)
    ev['public'][1-row['side']].append(dict(tick=row['tick']-1,side=row['side'],card='Mirror'))
    bad.append((row,ev))
    for x,ev in bad:
        try:check_prediction(x,ev,row['truth'])
        except AssertionError:pass
        else:raise AssertionError('Corruption accepted')
    return dict(positive=3,negative=len(bad))


def main():
    assert not (HERE/'verified.json').exists(),'Fresh verification only'
    start=read(HERE/'started.json');result=read(HERE/'collected.json')
    assert result['started_sha256']==sha(HERE/'started.json')
    for p,h in start['bindings'].items():assert sha(ROOT/p)==h,p
    for p,h in result['outputs'].items():assert sha(OUT/p)==h,p
    assignments=read(HERE.parent/'development_iteration_1/prepared.json')['assignment']
    expected=[(part,tag) for part,n in [('training',32),('development',128)]
              for tag in sorted(t for t,p in assignments.items() if p==part)[:n]]
    assert [(s['part'],s['tag']) for s in start['sources']]==expected
    evs={r['tag']:r for r in map(json.loads,(OUT/'events.jsonl').read_text().splitlines())}
    rows=defaultdict(list)
    for row in map(json.loads,(OUT/'predictions.jsonl').read_text().splitlines()):
        rows[row['tag']].append(row)
    total=defaultdict(Counter);accounting=Counter();details=[]
    for source in start['sources']:
        assert sha(ROOT/source['path'])==source['sha256']
        rec=read(ROOT/source['path']);tag=source['tag'];streams=evs[tag]
        ideal=[]
        for i,e in enumerate(rec['log']):
            if e.get('accepted') and not e.get('ability') and e.get('card'):
                ideal.append(dict(tick=int(e.get('engine_tick',e['tick'])),side=int(e['side']),
                                  card=e['card'],event_id=str(i)))
        assert streams['ideal']==ideal
        frame_ticks={f['tick'] for f in rec['frames']}
        for observer_side, events in enumerate(streams['public']):
            assert all(e['side']==1-observer_side and e['tick'] in frame_ticks for e in events)
            assert [e['tick'] for e in events]==sorted(e['tick'] for e in events)
        indexed={r['log_index']:r for r in rows[tag]}
        assert len(indexed)==len(rows[tag])
        pf={int(f['play_index']):f for f in rec.get('play_frames',[])}
        local=defaultdict(Counter);first={};expected_indices=[]
        for li,e in enumerate(rec['log']):
            accounting['log_entries']+=1
            truth=actual_hand(e.get('hand_before'))
            if truth is None:
                accounting['missing_or_non_four_card_hand']+=1;continue
            side=int(e['side']);tick=int(e.get('engine_tick',e['tick']))
            other=None
            for p in pf.get(int(e['play_index']),{}).get('players',[]):
                if int(p['side'])==side:other=actual_hand(p.get('hand'))
            if other is None:accounting['missing_play_frame_hand']+=1
            elif truth!=other:
                accounting['conflicting_play_frame_hand']+=1;continue
            else:accounting['matching_play_frame_hand']+=1
            expected_indices.append(li)
            row=indexed[li]
            assert (row['part'],row['side'],row['tick'],row['play_index'])==(source['part'],side,tick,e['play_index'])
            assert row['corroborated']==(other is not None)
            cohort='same_tick_ambiguous' if any(x['side']==side and x['tick']==tick and int(x['event_id'])<li for x in ideal) else 'primary'
            assert row['cohort']==cohort
            accounting[cohort]+=1
            check_prediction(row,streams,truth)
            for arm,pred in row['predictions'].items():
                metrics=measure(pred,truth)
                total[source['part']+'/'+cohort+'/'+arm].update(metrics)
                local[cohort+'/'+arm].update(metrics)
                if pred['full_hand']:first.setdefault(str(side)+'/'+arm,tick)
        assert sorted(indexed)==expected_indices
        details.append(dict(tag=tag,part=source['part'],queries=dict(local),first_full_ticks=first,
            accepted_plays=len(ideal),detected_plays=sum(map(len,streams['public'])),
            frames=len(rec['frames']),final_tick=int(rec['frames'][-1]['tick'])))
    assert dict(total)==result['summary']
    assert dict(accounting)==result['accounting']
    assert details==read(OUT/'by_replay.json')
    sample=next(r for rs in rows.values() for r in rs if r['predictions']['ideal']['full_hand'])
    tested=controls(sample,evs[sample['tag']])
    corrupt=copy.deepcopy(result['summary']);next(iter(corrupt.values()))['queries']+=1
    assert dict(total)!=corrupt
    tested['negative']+=1
    evidence=dict(complete=True,replays=len(details),queries=sum(len(v) for v in rows.values()),
        controls=tested,collected_sha256=sha(HERE/'collected.json'),
        all_raw_hands_and_prefix_predictions_reconciled=True,
        all_scalar_and_per_replay_counts_reconciled=True,no_model_calls=True)
    (HERE/'verified.json').write_text(json.dumps(evidence,indent=2))
    print(json.dumps(evidence));print('OPPONENT_HAND_VERIFIED')


if __name__=='__main__':main()
