"""Conservative pro Log/Barrel evidence, never an exact landing-time claim.

The lower bound counts only same-tick observed Goblin Barrel flight at a Log
cast, uniquely linked to a driven barrel command. The upper bound includes any
opponent Log after the driven barrel cast. Missing landing/Skeleton evidence
therefore cannot become a false zero. Nothing here supplies policy inputs.
"""
import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import re
import time

import numpy as np

ROOT=Path(__file__).resolve().parents[4]
BARRELS={'goblinbarrel','skeletonbarrel'}


def key(name):
    return re.sub('[^a-z0-9]','',str(name).split('@')[0].lower())


def cast_tick(play):
    return int(play.get('engine_tick') if play.get('engine_tick') is not None else play['tick'])


def mine(rec):
    accepted=[p for p in rec.get('log',[]) if p.get('accepted') and not p.get('ability')]
    barrels=[p for p in accepted if key(p.get('card')) in BARRELS]
    logs=[p for p in accepted if key(p.get('card')) in ('log','thelog')]
    by_tick={};duplicate_equivalent=0
    for f in rec.get('frames',[]):
        tick=int(f['tick'])
        # Only the public projectile observation participates in this audit.
        # Same-tick ability costs can change elixir without changing that input.
        public=dict(tick=tick)
        if 'projectiles' in f:public['projectiles']=f['projectiles']
        if tick in by_tick:
            if public!=by_tick[tick]:
                raise ValueError(f'Conflicting duplicate frame tick {tick} in replay {rec.get("tag")}')
            duplicate_equivalent+=1
        else:by_tick[tick]=public
    frames=[by_tick[t] for t in sorted(by_tick)]
    casts=defaultdict(list)
    for i,p in enumerate(barrels):
        if key(p['card'])=='goblinbarrel':
            casts[(int(p['side']),float(p['x']),float(p['y']))].append((cast_tick(p),i))
    active={};last_absent={};evidence=defaultdict(list);ambiguous=0
    log_at=defaultdict(list)
    for p in logs:
        log_at[cast_tick(p)].append(p)
    for f in frames:
        tick=int(f['tick']);groups=defaultdict(list)
        if 'projectiles' not in f:
            active.clear();last_absent.clear()
            continue
        for q in f['projectiles']:
            if isinstance(q,list) and len(q)==6 and key(q[5])=='goblinbarrel':
                groups[(int(q[0]),float(q[3]),float(q[4]))].append(q)
        for identity in casts:
            objects=groups.get(identity,[])
            if not objects:
                active.pop(identity,None);last_absent[identity]=tick
                continue
            if len(objects)!=1:
                active[identity]=None;ambiguous+=1
                continue
            if identity not in active:
                # Require a prior observed absence. A recording opening with a
                # projectile already present cannot establish which cast made it.
                start=last_absent.get(identity)
                candidates=[i for t,i in casts[identity] if start is not None and start<=t<=tick]
                active[identity]=candidates[0] if len(candidates)==1 else None
            barrel=active[identity]
            if barrel is not None and any(cast_tick(barrels[barrel])<t<=tick for t,_ in casts[identity]):
                # Without object IDs, continuous same-target presence could now
                # refer to a replacement flight. Never credit the earlier cast.
                active[identity]=barrel=None
            if barrel is None:
                continue
            for log in log_at.get(tick,[]):
                if int(log['side'])!=identity[0]:
                    evidence[barrel].append(dict(log_play_index=log.get('play_index'),tick=tick,
                                                 frame_tick=tick,barrel_target=list(identity[1:])))
    rows=[]
    for i,p in enumerate(barrels):
        later=[q for q in logs if int(q['side'])!=int(p['side']) and cast_tick(q)>=cast_tick(p)]
        certain=bool(evidence[i]);possible=bool(later)
        assert not certain or possible
        rows.append(dict(tag=str(rec['tag']),play_index=p.get('play_index'),tick=cast_tick(p),
                         side=int(p['side']),card=key(p['card']),certain_in_flight=certain,
                         possible_full_metric=possible,same_tick_evidence=evidence[i]))
    log_ticks={cast_tick(p) for p in logs}
    return dict(tag=str(rec['tag']),barrels=rows,counts=dict(driven_barrels=len(rows),
        goblin_barrels=sum(r['card']=='goblinbarrel' for r in rows),
        skeleton_barrels=sum(r['card']=='skeletonbarrel' for r in rows),
        certain_in_flight=sum(r['certain_in_flight'] for r in rows),
        possible_full_metric=sum(r['possible_full_metric'] for r in rows),
        accepted_logs=len(logs),log_ticks_with_exact_frame=len(log_ticks&{int(f['tick']) for f in frames}),
        ambiguous_projectile_frames=ambiguous,duplicate_equivalent_projectile_frames=duplicate_equivalent))


def aggregate(replays):
    fields=('driven_barrels','goblin_barrels','skeleton_barrels','certain_in_flight',
            'possible_full_metric','accepted_logs','log_ticks_with_exact_frame','ambiguous_projectile_frames',
            'duplicate_equivalent_projectile_frames')
    total={field:sum(r['counts'][field] for r in replays) for field in fields}
    n=total['driven_barrels']
    bounds=[total['certain_in_flight']/n,total['possible_full_metric']/n] if n else None
    # Bootstrap replay clusters; undefined no-barrel resamples are explicit.
    a=np.asarray([[r['counts'][f] for f in ('certain_in_flight','possible_full_metric','driven_barrels')]
                  for r in replays],dtype=float)
    draws=[];undefined=0
    if len(a)>1 and n:
        rng=np.random.default_rng(20261003)
        for _ in range(100):
            ix=rng.integers(len(a),size=(100,len(a)))
            sums=a[ix].sum(axis=1);valid=sums[:,2]>0;undefined+=int((~valid).sum())
            draws.extend((sums[valid,:2]/sums[valid,2,None]).tolist())
    ci=np.quantile(draws,[.025,.975],axis=0).T.tolist() if draws else None
    return dict(counts=total,full_metric_value=None,status='PARTIAL_INTERVAL_EVIDENCE_NOT_EXACT_METRIC',
        descriptive_bounds=bounds,bound_endpoint_ci95=ci,bootstrap=dict(unit='replay',repeats=10000,
        seed=20261003,undefined_resamples=undefined,insufficient_clusters=len(a)<2),limitations=[
            'Denominator is accepted replay-engine barrel commands, not every original human barrel.',
            'Lower endpoint requires an exact-tick Log and visible uniquely linked Goblin Barrel projectile.',
            'No landing label is inferred from disappearance. Post-landing half-second cases remain unresolved.',
            'Skeleton Barrel body/death recognition is unvalidated; those opportunities remain unresolved.',
            'Mirror commands are not resolved into a copied card; mirrored barrel coverage is not established.',
            'Upper endpoint includes any enemy Log at or after cast, even much later; it is deliberately loose.',
            'Same-card/target overlaps, absent projectile exports and missing exact frames cannot prove absence.',
            'Equivalent same-tick public projectile observations count once; conflicting projectile duplicates fail.',
            'Intervals describe sampling of these replay clusters; selection/source bias remains.'])


def run(corpora,out,recordings=(),pace_ms=0):
    if not math.isfinite(pace_ms) or pace_ms<0:raise ValueError('Invalid audit pacing')
    out.mkdir(parents=True,exist_ok=False)
    seen=set();manifest=[];results=[];duplicates=[]
    groups=[sorted(corpus.glob('replay_*.json')) for corpus in corpora]+[list(recordings)]
    for paths in groups:
        for path in paths:
            raw=path.read_bytes();rec=json.loads(raw);tag=str(rec['tag'])
            if tag in seen:
                duplicates.append(str(path));continue
            seen.add(tag)
            results.append(mine(rec))
            manifest.append(dict(path=str(path.resolve().relative_to(ROOT)),tag=tag,
                                 sha256=hashlib.sha256(raw).hexdigest()))
            if pace_ms:time.sleep(pace_ms/1000)
            if len(results)%100==0:time.sleep(.1)
    result=aggregate(results);result['selected_replays']=len(results);result['duplicate_paths']=duplicates
    for name,contents in (('report.json',result),('manifest.json',manifest)):
        (out/name).write_text(json.dumps(contents,indent=2)+'\n')
    with (out/'barrels.jsonl').open('w') as stream:
        for replay in results:
            for row in replay['barrels']:stream.write(json.dumps(row)+'\n')
    print(json.dumps(dict(status=result['status'],replays=len(results),counts=result['counts'],
                         descriptive_bounds=result['descriptive_bounds']),indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--corpus',type=Path,nargs='+')
    group.add_argument('--recording',type=Path,nargs='+')
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--pace-ms',type=float,default=0)
    args=parser.parse_args()
    from audit_runtime import lower_own_priority
    lower_own_priority()
    run(args.corpus or [],args.out,args.recording or [],args.pace_ms)
