"""Fail-closed twenty-replay semantic preflight. Stdlib only; remote or local.

Disappearance brackets measure recording/motion compatibility, never causal
impact truth. Owner 2026-10-04 accepts recording-derived outcomes; no hit hook gate.
"""
import argparse
from collections import Counter,defaultdict
from bisect import bisect_right
import hashlib
import json
import math
from pathlib import Path
import statistics

FIELDS={
    'projectiles':{'side','card_id','x','y','id','generation_key','target_x','target_y','past_motion_tti_ms'},
    'area_effects':{'side','card_id','x','y','id','category','source_elapsed_ms','source_life_ms','source_remaining_ms'},
    'causal_hit_events':{'tick','source_projectile_id','source_card_id','source_side','target_entity_id','target_kind','damage'},
}

def finite(value):return isinstance(value,(int,float)) and math.isfinite(value)
def summary(values):
    return dict(n=len(values),mean=statistics.mean(values) if values else None,
                median=statistics.median(values) if values else None,
                max=max(values) if values else None)

def inspect(rec):
    errors=Counter();coverage=Counter();areas=defaultdict(list);flights=defaultdict(list)
    if rec.get('record_native') is not True:errors['native_id_marker_missing']+=1
    if rec.get('drive_abilities') is not True:errors['ability_driving_not_enabled']+=1
    cadence=rec.get('record_every')
    if cadence not in (1,2,3,4,10):errors['unsupported_capture_cadence']+=1
    frames=rec.get('frames',[])
    if not frames:errors['no_frames']+=1
    frame_by_tick={f['tick']:f for f in frames};ticks=sorted(frame_by_tick)
    for event in rec.get('log',[]):
        if not (event.get('ability') and event.get('accepted')):continue
        coverage['accepted_ability_events']+=1
        if any(key not in event for key in ('entity_id','side','engine_tick')):
            errors['accepted_ability_fields_missing']+=1;continue
        at=bisect_right(ticks,event['engine_tick'])-1
        if at<0 or event['engine_tick']-ticks[at]>20:
            errors['accepted_ability_fresh_frame_missing']+=1;continue
        if not any(len(e)==9 and e[-1]==event['entity_id'] and e[0]==event['side'] and e[4]>0 for e in frame_by_tick[ticks[at]]['entities']):
            errors['accepted_ability_controller_missing']+=1
    for f in frames:
        tick=f['tick'];evidence=f.get('public_objects',{})
        for e in f.get('entities',[]):
            if len(e)!=9:errors['entity_native_tail_missing']+=1
        for kind,required in FIELDS.items():
            rows=evidence.get(kind)
            if kind=='causal_hit_events' and rows is None:
                continue  # optional diagnostics, explicitly not a capture gate
            if rows is None:
                errors[kind+'_export_missing']+=1;continue
            if not isinstance(rows,list):errors[kind+'_not_list']+=1;continue
            for r in rows:
                coverage[kind+'_rows']+=1
                if required-set(r):errors[kind+'_required_field_missing']+=1;continue
                if any(k in r for k in ('hand','next','deck','opponent_elixir','owner_slot_a','owner_slot_b')):
                    errors['private_field_in_public_object']+=1
                if kind=='causal_hit_events':
                    if not finite(r['damage']) or r['damage']<=0 or r['tick']>tick:errors['invalid_causal_hit']+=1
                    coverage['causal_'+str(r['target_kind'])+'_hits']+=1
                    continue
                if any(not finite(r[k]) for k in ('x','y')) or r['side'] not in (0,1):errors['invalid_object_geometry']+=1
                if kind=='projectiles':
                    tti=r['past_motion_tti_ms']
                    if tti is not None:
                        if not finite(tti) or tti<0:errors['invalid_tti']+=1
                        else:coverage['past_motion_tti_known']+=1
                    flights[r['id'],r['generation_key']].append((tick,tti))
                else:
                    elapsed,life,left=(r['source_'+k+'_ms'] for k in ('elapsed','life','remaining'))
                    if not all(finite(v) for v in (elapsed,life,left)):errors['invalid_area_timer']+=1;continue
                    if min(elapsed,life,left)<0 or abs(max(0,life-elapsed)-left)>1:errors['area_timer_arithmetic']+=1
                    areas[r['id'],r['category'],r['card_id']].append((tick,elapsed,life,left))
    slope=[];expirations=[]
    last=max([f['tick'] for f in frames],default=0)
    for identity,seq in areas.items():
        by_tick={r[0]:r for r in seq};seq=[by_tick[t] for t in sorted(by_tick)]
        for a,b in zip(seq,seq[1:]):
            if 0 < b[0]-a[0] <= max(1,cadence or 1):
                slope.append((b[1]-a[1])-50*(b[0]-a[0]))
                if b[1]<a[1]:
                    if identity[2]==13000015:coverage['persistent_baby_dragon_aura_refreshes']+=1
                    else:errors['area_elapsed_regressed']+=1
        if seq[-1][0]<last:expirations.append(seq[-1][3])
    bracket=[]
    for seq in flights.values():
        by_tick={t:ms for t,ms in seq};ticks=sorted(by_tick)
        # Only uninterrupted tracks that end before the recording does.
        if ticks[-1]>=last or any(not 0<b-a<=max(1,cadence or 1) for a,b in zip(ticks,ticks[1:])):continue
        for t in ticks:
            ms=by_tick[t]
            if ms is None:continue
            predicted=t+ms/50
            bracket.append(max(ticks[-1]-predicted,0,predicted-(ticks[-1]+cadence))*.05)
    coverage.update(frames=len(frames),area_tracks=len(areas),projectile_tracks=len(flights))
    return dict(tag=rec['tag'],errors=dict(errors),coverage=dict(coverage),
                area_elapsed_step_error_ms=summary(slope),area_last_remaining_before_disappearance_ms=summary(expirations),
                tti_distance_outside_disappearance_bracket_s=summary(bracket))

def validate(directory,expected_tags):
    errors=Counter();coverage=Counter();rows=[];manifest=[]
    paths=sorted(directory.glob('replay_*.json'))
    if len(expected_tags)!=20 or len(set(expected_tags))!=20:errors['expected_tag_contract_not_twenty_unique']+=1
    seen=[]
    for p in paths:
        raw=p.read_bytes();rec=json.loads(raw);seen.append(rec['tag']);result=inspect(rec)
        rows.append(result);errors.update(result['errors']);coverage.update(result['coverage'])
        manifest.append(dict(path=p.name,tag=rec['tag'],bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
    if sorted(seen)!=sorted(expected_tags):errors['replay_tag_set_mismatch']+=1
    for name in ('area_effects_rows','projectiles_rows','past_motion_tti_known','accepted_ability_events'):
        if not coverage[name]:errors[name+'_not_demonstrated']+=1
    return dict(status='PASS' if not errors else 'FAIL_DO_NOT_START_FULL_REDRIVE',errors=dict(errors),
        coverage=dict(coverage),replays=rows,manifest=manifest,
        limitations=['TTI disappearance error is not validated landing error; cancellation and object lifetime also cause disappearance.',
            'Area arithmetic and observed timer progression are necessary but not sufficient for visible expiration semantics.',
            'Rocket outcomes use recorded landing geometry and HP deltas per owner ruling; a native damage hook is not required.'])

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--directory',type=Path,required=True);p.add_argument('--jobs',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    args=p.parse_args();jobs=json.loads(args.jobs.read_text());result=validate(args.directory,[r['tag'] for r in jobs])
    args.out.write_text(json.dumps(result,indent=2)+'\n');print(result['status'],json.dumps(result['errors']))
    raise SystemExit(0 if result['status']=='PASS' else 2)
