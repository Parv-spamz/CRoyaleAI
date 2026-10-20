"""Read completed owner logs; public projectile-to-new-goblin geometry only."""
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import statistics

ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
BARREL=28000004


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def own_xy(x,y,side):
    return ((18000-x)/18000,y/32000) if side==1 else (x/18000,(32000-y)/32000)


def lane(x):return 'left' if x<0.5 else 'right' if x>0.5 else 'middle'


def main():
    sources={};rows=[];counts=Counter();checkpoints=Counter()
    for path in sorted((ROOT/'scratchpad/gauntlet/L68/live_reader').glob('live_play_20261005_*.jsonl')):
        stamp=path.stem.rsplit('_',1)[-1]
        if not '064500'<=stamp<'074600':continue
        events=[json.loads(line) for line in path.open()]
        if not any(e['event']=='end' for e in events):continue
        sources[str(path.relative_to(ROOT))]=sha(path)
        start=next(e for e in events if e['event']=='start')
        checkpoints[start['ckpt_sha256']]+=1
        frames=[e for e in events if e['event']=='decision' and e.get('public')]
        new_by_frame=[];ever=set()
        for f in frames:
            new=[]
            for body in f['public']['raw_bodies']:
                ident=(body.get('address'),body.get('category'))
                if ident not in ever and body.get('card_id')==BARREL and body.get('hp',0)>0:
                    new.append(body)
                ever.add(ident)
            new_by_frame.append(new)
        logs=[];pending=[]
        for event in events:
            if event['event']=='play' and event.get('name')=='Log':
                row=dict(tick=event['tick'],xy=event['xy'],confirmed=None)
                logs.append(row);pending.append(row)
            elif event['event'] in ('confirmed','unconfirmed') and event.get('name')=='Log' and pending:
                row=pending.pop(0);row['confirmed']=event['event']=='confirmed';row['receipt_tick']=event['tick']
        segment=None
        for index,frame in enumerate(frames):
            public=frame['public'];side=public['observer_side']
            barrels=[p for p in public['raw_projectiles'] if p.get('card_id')==BARREL and p['side']!=side]
            if len(barrels)==1:
                p=barrels[0];key=(p['side'],p.get('target_x'),p.get('target_y'))
                if segment is not None and segment['key']!=key:
                    segment['unmatched_reason']='target_changed_or_overlapping_flights'
                    rows.append(segment);segment=None
                if segment is None:
                    segment=dict(file=path.name,exploratory=path.name=='live_play_20261005_064842.jsonl',
                        key=key,observer_side=side,first_tick=frame['tick'],last_tick=frame['tick'],
                        first_frame=index,last_frame=index,observations=0)
                segment['last_tick']=frame['tick'];segment['last_frame']=index;segment['observations']+=1
            elif segment is not None:
                row=segment;segment=None
                row['first_absent_tick']=frame['tick']
                row['matched']=False
                goblins=[b for b in new_by_frame[index] if b['side']==row['key'][0]]
                row['new_goblins']=goblins
                if barrels:row['unmatched_reason']='simultaneous_barrels'
                elif frame['tick']-row['last_tick']>40:row['unmatched_reason']='observation_gap'
                elif len(goblins)!=3:row['unmatched_reason']='not_exactly_three_new_goblins'
                elif any(v is None for v in row['key'][1:]):row['unmatched_reason']='unknown_target'
                else:
                    row['matched']=True
                    x=sum(g['x'] for g in goblins)/3;y=sum(g['y'] for g in goblins)/3
                    tx,ty=row['key'][1:]
                    row['centroid_raw']=[x,y]
                    row['error_tiles']=math.hypot(x-tx,y-ty)/1000
                    row['all_spawning_kind14']=all(g['kind']==14 for g in goblins)
                    row['target_own_xy']=own_xy(tx,ty,row['observer_side'])
                    row['centroid_own_xy']=own_xy(x,y,row['observer_side'])
                    row['lane_equal']=lane(row['target_own_xy'][0])==lane(row['centroid_own_xy'][0])
                rows.append(row)
            elif len(barrels)>1:counts['ambiguous_multi_projectile_frames']+=1
        if segment is not None:
            segment['unmatched_reason']='recording_ends_during_flight';rows.append(segment)
        for row in rows:
            if row['file']!=path.name:continue
            row['preemptive_log_attempts']=[dict(log,target_lane=lane(own_xy(row['key'][1],row['key'][2],row['observer_side'])[0]),
                log_lane=lane(log['xy'][0]),correct_lane=lane(log['xy'][0])==lane(own_xy(row['key'][1],row['key'][2],row['observer_side'])[0]))
                for log in logs if row['first_tick']<=log['tick']<=row['last_tick'] and None not in row['key'][1:]]
    matched=[r for r in rows if r.get('matched')]
    counts.update(log_files=len(sources),flight_segments=len(rows),matched_spawns=len(matched),
        matched_lanes=sum(r['lane_equal'] for r in matched),spawning_triplets=sum(r['all_spawning_kind14'] for r in matched))
    for r in rows:
        if not r.get('matched'):counts['unmatched:'+r['unmatched_reason']]+=1
        for log in r['preemptive_log_attempts']:
            status='confirmed' if log['confirmed'] is True else 'unconfirmed' if log['confirmed'] is False else 'unresolved'
            counts['preemptive_log:'+status+(':'+'correct_lane' if log['correct_lane'] else ':wrong_lane')]+=1
    errors=[r['error_tiles'] for r in matched]
    report=dict(source_sha256=sources,checkpoints=dict(checkpoints),counts=dict(counts),
        centroid_error_tiles=dict(n=len(errors),median=statistics.median(errors) if errors else None,
                                  maximum=max(errors) if errors else None),flights=rows,
        script_sha256=sha(__file__),plan_sha256=sha(HERE/'LIVE_BARREL_PLAN.md'),
        limitations=['First-observed goblin centroid is a temporal public landing proxy, not exact impact or damage attribution.',
                    'The 06:48 example was exploratory; no candidate acceptance is established.',
                    'Missing, rapidly killed or ambiguous spawns remain unmatched, not successful predictions.'])
    (HERE/'live_barrel_landings.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(dict(counts=dict(counts),error=report['centroid_error_tiles'])))
    print('PUBLIC_LIVE_BARREL_LANDING_AUDIT_COMPLETE')


if __name__=='__main__':main()
