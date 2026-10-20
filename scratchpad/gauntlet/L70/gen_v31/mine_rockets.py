"""Stream all accepted replay Rockets and preserve evidence/attribution gaps.

Outputs public pre-cast context plus outcome labels for analysis ONLY. Geometric
targets and compatible HP drops are explicitly candidates, not causal hit truth.
No opponent private state is extracted. No learned model consumes this file.
"""
import argparse
from bisect import bisect_right
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import statistics
import time

ROOT = Path(__file__).resolve().parents[4]
DEFAULT = [f'scratchpad/gauntlet/ext/corpus_gen_pilot/s{i}' for i in range(4)]+[
    'scratchpad/gauntlet/ext/corpus_v6/icebow','scratchpad/gauntlet/ext/corpus_v6/hogeq']


def describe(values):
    v=sorted(float(x) for x in values if x is not None)
    return dict(n=len(v),min=v[0] if v else None,max=v[-1] if v else None,
                median=statistics.median(v) if v else None,
                p10=v[int(.1*(len(v)-1))] if v else None,p90=v[int(.9*(len(v)-1))] if v else None)


def identity(tower):
    return tuple(tower[:3])


def tiebreak(rec):
    final=rec.get('final',{})
    explicit=final.get('tiebreaker')
    if isinstance(explicit,bool): return explicit, 'explicit'
    if 'tiebreak' in str(final.get('termination_reason','')).lower(): return True, 'explicit_reason'
    if final.get('terminated') and final.get('tick',6000)<6000: return False, 'ended_before_five_minutes'
    return None, 'no_explicit_tiebreak_label'


def mine(rec):
    frames=sorted(rec.get('frames',[]),key=lambda f:int(f['tick']))
    ticks=[int(f['tick']) for f in frames]
    play_frames={f['play_index']:f for f in rec.get('play_frames',[])}
    events=sorted([p for p in rec.get('log',[]) if p.get('accepted') and not p.get('ability')],
                  key=lambda p:(int(p.get('engine_tick') or p['tick']),p.get('play_index',0)))
    rockets=[p for p in events if str(p.get('card','')).lower()=='rocket']
    previous=defaultdict(list);out=[]
    tb,tb_source=tiebreak(rec)
    final_towers=rec.get('final',{}).get('towers',[])
    for p in rockets:
        tick=int(p.get('engine_tick') or p['tick']); side=int(p['side'])
        pf=play_frames.get(p.get('play_index'))
        # A delayed accepted play must not use the older pre-attempt play frame.
        i=bisect_right(ticks,tick)-1
        f=pf if pf is not None and int(pf['tick'])==tick else (frames[i] if i>=0 else None)
        row=dict(tag=str(rec['tag']),play_index=p.get('play_index'),tick=tick,side=side,x=p['x'],y=p['y'],
                 context_tick=int(f['tick']) if f else None,elapsed_s=tick*.05,
                 phase='overtime' if tick>=3600 else ('double' if tick>=2400 else 'single'),
                 phase_seconds_left=max(0,(6000-tick if tick>=3600 else 3600-tick)*.05),
                 match_limit_seconds_left=max(0,(6000-tick)*.05),
                 own_elixir_before=(f.get('elixir',[None,None])[side] if f else None),
                 tiebreaker=tb,tiebreaker_evidence=tb_source,
                 crown_tower_hit=None,hit_status='UNATTRIBUTED',targets=[])
        if f:
            towers=f.get('towers',[])
            row['crowns_before']=[3 if any(t[0]==1-s and t[1]=='king' and t[5]<=0 for t in towers)
                                  else sum(t[0]==1-s and t[1]=='princess' and t[5]<=0 for t in towers)
                                  for s in (side,1-side)]
            row['total_tower_hp_margin_before']=sum(t[5]*(1 if t[0]==side else -1) for t in towers)
            distances=[(math.hypot(p['x']-t[3],p['y']-t[4])/1000,t) for t in towers if t[0]!=side and t[5]>0]
            row['nearest_enemy_tower_distance_tiles']=min((d for d,t in distances),default=None)
            for distance,t in distances:
                if distance>3.5: continue
                key=(side,identity(t)); prior=previous[key]
                target=dict(tower=list(identity(t)),hp_before=t[5],distance_tiles=distance,
                    geometric_band='center_within_2_tiles' if distance<=2 else 'edge_2_to_3_5_tiles_unvalidated',
                    prior_rocket_candidates=len(prior),gap_s=(tick-prior[-1])*.05 if prior else None,
                    one_rocket_hp_context=0<t[5]<=497,flight_seen=False,flight_last_tick=None,
                    post_flight_tick=None,hp_drop_around_flight=None)
                # Match observable projectile aim to this accepted cast, bounded before
                # the next same-side Rocket, never use a future frame in pre-cast context.
                next_tick=next((int(q.get('engine_tick') or q['tick']) for q in rockets
                                if q['side']==side and int(q.get('engine_tick') or q['tick'])>tick),tick+300)
                seen=[];after=None
                for ff in frames[max(i,0):]:
                    ft=int(ff['tick'])
                    if ft<tick: continue
                    if ft>min(next_tick,tick+300): break
                    qs=[q for q in ff.get('projectiles',[]) if not isinstance(q,dict) and len(q)>=6 and
                        q[0]==side and str(q[5]).lower()=='rocket' and abs(q[3]-p['x'])<=1 and abs(q[4]-p['y'])<=1]
                    if qs: seen.append(ff)
                    elif seen: after=ff;break
                if seen:
                    target.update(flight_seen=True,flight_last_tick=seen[-1]['tick'])
                if after is not None:
                    before_t=next((x for x in seen[-1].get('towers',[]) if identity(x)==identity(t)),None)
                    after_t=next((x for x in after.get('towers',[]) if identity(x)==identity(t)),None)
                    if before_t is not None and after_t is not None:
                        target.update(post_flight_tick=after['tick'],hp_drop_around_flight=before_t[5]-after_t[5])
                row['targets'].append(target);prior.append(tick)
        row['final_tower_hp_margin']=sum(t['hp']*(1 if t['side']==side else -1) for t in final_towers) if final_towers else None
        out.append(row)
    return out,dict(accepted_plays=len(events),accepted_rockets=len(rockets),frames=len(frames),
                   full=rec.get('record_full',False),native=rec.get('record_native',False))


def run(corpora,out,pace_ms=0):
    if not math.isfinite(pace_ms) or pace_ms<0:raise ValueError('Invalid audit pacing')
    corpora=[p.resolve() for p in corpora]
    out.mkdir(parents=True,exist_ok=False)
    files=[];seen={};counts=Counter();per_corpus={};rows=[];duplicates=[]
    with (out/'rockets.jsonl').open('w',encoding='utf-8') as stream:
        for corpus in corpora:
            stat=Counter()
            for path in sorted(corpus.glob('replay_*.json')):
                raw=path.read_bytes(); rec=json.loads(raw);tag=str(rec['tag'])
                sha=hashlib.sha256(raw).hexdigest()
                if tag in seen:
                    duplicates.append(dict(tag=tag,path=str(path),same_bytes=seen[tag]==sha));continue
                seen[tag]=sha
                found,info=mine(rec)
                files.append(dict(path=str(path.relative_to(ROOT)),sha256=sha,tag=tag))
                stat.update(dict(replays=1,**info))
                for row in found:
                    stream.write(json.dumps(row,separators=(',',':'))+'\n')
                rows.extend(found)
                if pace_ms:time.sleep(pace_ms/1000)
                if len(files)%100==0: time.sleep(.1)
                if len(files)%500==0: print('MINED',len(files),'ROCKETS',len(rows),flush=True)
            per_corpus[str(corpus.relative_to(ROOT))]=dict(stat);counts.update(stat)
    target_rows=[r for r in rows if r['targets']];targets=[t for r in target_rows for t in r['targets']]
    sequences=Counter((r['tag'],r['side'],tuple(t['tower'])) for r in rows for t in r['targets'])
    groups={}
    for key,predicate in [('all',lambda r:True),('tower_candidates',lambda r:bool(r['targets'])),
                          ('tiebreak_confirmed',lambda r:r['tiebreaker'] is True),
                          ('tiebreak_unknown',lambda r:r['tiebreaker'] is None)]:
        rr=[r for r in rows if predicate(r)]
        groups[key]=dict(rockets=len(rr),own_elixir=describe(r['own_elixir_before'] for r in rr),
                        seconds_left=describe(r['match_limit_seconds_left'] for r in rr),
                        phases=dict(Counter(r['phase'] for r in rr)))
    report=dict(status='MEASURED_CANDIDATE_AUDIT_NOT_HIT_TRUTH',counts=dict(counts),corpora=per_corpus,
        rocket_share=counts['accepted_rockets']/counts['accepted_plays'] if counts['accepted_plays'] else None,
        groups=groups,tower_candidates=dict(rockets=len(target_rows),targets=len(targets),
            hp_before=describe(t['hp_before'] for t in targets),gaps_s=describe(t['gap_s'] for t in targets),
            sequence_lengths=dict(sorted(Counter(sequences.values()).items())),
            multi_rocket_tower_sequences=sum(n>=2 for n in sequences.values()),
            flight_seen=sum(t['flight_seen'] for t in targets),
            hp_drop_observed=sum(t['hp_drop_around_flight'] is not None for t in targets)),
        confirmed_hits=None,duplicates=duplicates,
        limitations=['All accepted Rockets enumerated; 3.5-tile candidate radius is an audit envelope, not verified hitbox.',
            '2-tile center band uses cards_stats Rocket radius; corner/collision and level effects unvalidated.',
            'Projectile disappearance plus tower HP loss is not causal damage attribution.',
            'native_logic_clock_stopped at/after five minutes does not prove tiebreak; unknown stays null.',
            'Outcome fields are offline labels, never model inputs. No inference about player intent.',
            'This is an explicitly selected source set; receipt/manifest identifies legacy versus native recordings.',
            'Duplicate replay tags use the first corpus occurrence, matching dataset_gen; excluded variants are listed.'])
    (out/'manifest.json').write_text(json.dumps(files,indent=1)+'\n')
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2),flush=True)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--corpus',nargs='+',type=Path)
    ap.add_argument('--out',type=Path,required=True);ap.add_argument('--pace-ms',type=float,default=0)
    a=ap.parse_args()
    from audit_runtime import lower_own_priority
    lower_own_priority()
    run(a.corpus or [ROOT/p for p in DEFAULT],a.out,a.pace_ms)
