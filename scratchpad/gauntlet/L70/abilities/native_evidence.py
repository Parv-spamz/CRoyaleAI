"""Audit accepted native ability events and public controller-frame coverage.

No policy changes, model fitting, hidden-state features or inferred eligibility.
First observed age is not deployment delay and is not a calibration target.
"""
import argparse
from bisect import bisect_right
from collections import Counter,defaultdict
import hashlib
import json
from pathlib import Path
import sys
import time

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
AUDIT=HERE.parent/'gen_v31'
sys.path.insert(0,str(AUDIT))
from audit_runtime import lower_own_priority
from mine_rockets import describe


def replay_evidence(rec):
    if rec.get('record_native') is not True:raise ValueError('Requires explicit native recording')
    events=[p for p in rec.get('log',[]) if p.get('ability')]
    if not events:return {}
    needed={(int(p['side']),int(p['entity_id'])) for p in events
            if p.get('accepted') is True and p.get('entity_id') is not None}
    by_tick=defaultdict(list);first_seen={}
    for f in rec.get('frames',[]):
        alive={}
        for e in f.get('entities',[]):
            if len(e) not in (8,9):raise ValueError('Unexpected native entity schema')
            if e[4]<=0 or e[-2]<0:continue
            identity=(int(e[0]),int(e[-1]))
            if identity not in needed:continue
            if identity in alive:raise ValueError('Duplicate native entity identity in a frame')
            alive[identity]=int(e[-2])
            first_seen[identity]=min(first_seen.get(identity,int(f['tick'])),int(f['tick']))
        by_tick[int(f['tick'])].append(alive)
    ticks=sorted(by_tick)
    result={}
    for p in events:
        ability=str(p.get('card') or 'unattributed')
        if ability not in result:result[ability]=dict(counts=Counter(),reasons=Counter(),native_ids=Counter(),ages=[])
        out=result[ability];c=out['counts'];c['logged_events']+=1
        if p.get('accepted') is not True:
            key='skipped' if p.get('skipped') else ('rejected' if p.get('accepted') is False else 'unknown_acceptance')
            c[key]+=1;out['reasons'][str(p.get('skipped') or p.get('result_name') or 'unknown')]+=1
            continue
        c['accepted']+=1
        if p.get('entity_id') is None:c['accepted_missing_entity_id']+=1;continue
        c['accepted_with_entity_id']+=1
        tick=int(p['engine_tick'] if p.get('engine_tick') is not None else p['tick'])
        identity=(int(p['side']),int(p['entity_id']))
        i=bisect_right(ticks,tick)-1
        if i<0 or tick-ticks[i]>20:c['accepted_without_fresh_frame']+=1;continue
        observations=by_tick[ticks[i]]
        cids={frame.get(identity) for frame in observations}
        # Every same-tick observation must agree on the same living controller.
        if len(cids)!=1 or None in cids:c['accepted_controller_unconfirmed']+=1;continue
        c['accepted_controller_confirmed']+=1;out['native_ids'][str(next(iter(cids)))]+=1
        age=tick-first_seen[identity]
        if age<0:raise ValueError('Future controller sighting used')
        out['ages'].append(age*.05)
    return result


def run(out,pace_ms):
    if pace_ms<50:raise ValueError('Full audit requires at least50ms pacing')
    out.mkdir(parents=True,exist_ok=False)
    source=AUDIT/'native_mining_1552/manifest.json'
    original=source.read_bytes();manifest=json.loads(original)
    counts=defaultdict(Counter);reasons=defaultdict(Counter);ids=defaultdict(Counter);ages=defaultdict(list)
    for i,item in enumerate(manifest):
        raw=(ROOT/item['path']).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=item['sha256']:raise ValueError('Verified replay changed')
        rec=json.loads(raw)
        if str(rec['tag'])!=str(item['tag']):raise ValueError('Replay identity changed')
        for ability,e in replay_evidence(rec).items():
            counts[ability].update(e['counts']);reasons[ability].update(e['reasons']);ids[ability].update(e['native_ids'])
            ages[ability].extend(e['ages'])
        time.sleep(pace_ms/1000)
        if (i+1)%500==0:print('AUDITED',i+1,flush=True)
    if source.read_bytes()!=original:raise ValueError('Input manifest changed')
    totals=sum(counts.values(),Counter())
    assert totals['logged_events']==sum(totals[k] for k in ('accepted','skipped','rejected','unknown_acceptance'))
    assert totals['accepted']==sum(totals[k] for k in ('accepted_missing_entity_id','accepted_with_entity_id'))
    assert totals['accepted_with_entity_id']==sum(totals[k] for k in (
        'accepted_controller_confirmed','accepted_controller_unconfirmed','accepted_without_fresh_frame'))
    result=dict(status='NATIVE_EVENT_AND_CONTROLLER_EVIDENCE_NOT_CALIBRATION',replays=len(manifest),
        source_manifest=str(source.relative_to(ROOT)),source_manifest_sha256=hashlib.sha256(original).hexdigest(),
        totals=dict(totals),abilities={a:dict(counts=dict(counts[a]),reasons=dict(reasons[a]),
            native_controller_ids=dict(ids[a]),first_observed_age_s=describe(ages[a])) for a in sorted(counts)},
        limitations=[
            'Logged replay-engine activations are not guaranteed faithful to the original human match.',
            'Ability names use the recorder attribution; raw names are not silently mapped to trained model labels.',
            'Controller coverage requires a fresh frame at or before the press, with all same-tick sightings agreeing.',
            'Age from first observed living entity is not exact deployment-to-press delay.',
            'No eligible-lifetime denominator, readiness truth, calibrated policy or runtime wiring is claimed.'])
    (out/'report.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(status=result['status'],replays=result['replays'],totals=result['totals'])),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--pace-ms',type=float,default=50);args=parser.parse_args()
    lower_own_priority();run(args.out,args.pace_ms)
