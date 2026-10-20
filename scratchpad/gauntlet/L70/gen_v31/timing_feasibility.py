"""Offline feasibility of a causal radial-speed estimate; never a model feature.

Only earlier/current public projectile positions form an estimate. Future frames
are used solely to score its prediction against a disappearance interval. A
disappearance is NOT guaranteed impact, so this cannot validate impact timing.
"""
import json
import math
from pathlib import Path
import hashlib
from collections import defaultdict, Counter
import statistics

ROOT=Path(__file__).resolve().parents[4]
CARDS={'Rocket','GoblinBarrel','SkeletonBarrel'}


def estimate(previous,current,dt):
    if dt<=0: return None
    old=math.hypot(previous[1]-previous[3],previous[2]-previous[4])
    now=math.hypot(current[1]-current[3],current[2]-current[4])
    closing=(old-now)/dt
    return now/closing if closing>0 else None


def evaluate(rec):
    active={};done=[]
    for frame in sorted(rec['frames'],key=lambda f:f['tick']):
        tick=frame['tick'];groups=defaultdict(list)
        for q in frame.get('projectiles',[]):
            if len(q)>=6 and q[5] in CARDS:
                groups[(q[0],q[5],q[3],q[4])].append(q)
        for key in list(active):
            if key not in groups or len(groups[key])!=1:
                track=active.pop(key)
                if key not in groups:
                    track['disappearance_interval']=[track['last_tick'],tick]
                else: track['censored']='ambiguous overlapping objects'
                done.append(track)
        for key,group in groups.items():
            if len(group)!=1:continue
            q=group[0]
            if key not in active:
                active[key]=dict(tag=rec['tag'],card=key[1],side=key[0],first_tick=tick,
                                 last_tick=tick,last=q,estimates=[])
            else:
                track=active[key];dt=tick-track['last_tick']
                tti=estimate(track['last'],q,dt)
                if tti is not None:
                    track['estimates'].append(dict(tick=tick,tti_s=tti*.05,predicted_end_tick=tick+tti))
                track.update(last_tick=tick,last=q)
    done.extend(dict(t,censored='recording ends before disappearance') for t in active.values())
    for t in done:
        t.pop('last')
        for e in t['estimates']:
            if 'disappearance_interval' in t:
                lo,hi=t['disappearance_interval'];pred=e['predicted_end_tick']
                e['outside_interval_error_s']=max(lo-pred,pred-hi,0)*.05
    return done


def summary(tracks):
    out={}
    for card in sorted(CARDS):
        ts=[t for t in tracks if t['card']==card]
        estimates=[e for t in ts for e in t['estimates'] if 'outside_interval_error_s' in e]
        errors=[e['outside_interval_error_s'] for e in estimates]
        widths=[(t['disappearance_interval'][1]-t['disappearance_interval'][0])*.05 for t in ts if 'disappearance_interval' in t]
        out[card]=dict(observed_tracks=len(ts),tracks_with_estimate=sum(bool(t['estimates']) for t in ts),
            scored_estimates=len(errors),outside_interval=sum(x>0 for x in errors),
            median_outside_interval_error_s=statistics.median(errors) if errors else None,
            max_outside_interval_error_s=max(errors) if errors else None,
            median_disappearance_interval_width_s=statistics.median(widths) if widths else None)
    return out


if __name__=='__main__':
    paths=[ROOT/'.foreman/codex_autopilot/runs/native_full_sample.json',
           *sorted((ROOT/'.foreman/codex_autopilot/runs/rocket_native_samples_1510').glob('replay_*.json'))]
    tracks=[];inputs={}
    for p in paths:
        raw=p.read_bytes();inputs[str(p.relative_to(ROOT))]=hashlib.sha256(raw).hexdigest()
        tracks.extend(evaluate(json.loads(raw)))
    report=dict(status='EXPLORATORY_NOT_VALIDATED_FOR_MODEL_INPUT',inputs=inputs,summary=summary(tracks),tracks=tracks,
        limitations=['Four selected recordings, not a representative held-out evaluation.',
            'Anonymous same-card/same-target objects can merge; ambiguous overlaps are censored.',
            'Position-only radial speed extrapolates constant speed; native Rocket acceleration may violate it.',
            'Disappearance intervals are not impact labels. Error is only distance outside those intervals.',
            'No new feature/default, recorder, live path or VM configuration was changed. Owner decision remains open.'])
    Path(__file__).with_name('timing_feasibility.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report['summary'],indent=2))
