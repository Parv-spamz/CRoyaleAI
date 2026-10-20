"""R1-REVISED: isolate tower HP loss during recorded X-Bow lifetimes.

The fitting rows use only clean adjacent observation windows: no other own body,
spell projectile or area within seven tiles of the target in either frame.
Unknown controllers, interrupted observations and censored negatives stay out.
"""
import argparse,hashlib,json,math,sys
from pathlib import Path
from bisect import bisect_left,bisect_right
from collections import Counter
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from pipeline.public_outcomes import normalize,distance,tower_id
from pipeline.dataset_gen import card_key

def inspect(rec):
    if not any(p.get('accepted') is True and not p.get('skipped') and not p.get('ability') and card_key(p.get('card') or '')=='x-bow' for p in rec.get('log',[])):
        return []
    # Labels may use the full pre-play observation; these are never features.
    frames=sorted({int(f['tick']):normalize(f) for f in rec['frames']+rec.get('play_frames',[])}.values(),key=lambda f:f['tick'])
    ticks=[f['tick'] for f in frames];rows=[]
    for play in rec.get('log',[]):
        if play.get('accepted') is not True or play.get('skipped') or play.get('ability') or card_key(play.get('card') or '')!='x-bow':continue
        p=dict(play,tick=int(play.get('engine_tick',play['tick'])))
        tick,side=p['tick'],p['side'];i=bisect_right(ticks,tick)-1
        row=dict(tag=rec['tag'],tick=tick,side=side,x=p['x'],y=p['y'],hit=None)
        if i<0:row['excluded']='no_precast_frame';rows.append(row);continue
        towers=[t for t in frames[i]['towers'] if t['side']!=side and t['hp']>0 and
                (t['kind']=='king' or (t['x']<9000)==(p['x']<9000))]
        if not towers:row['excluded']='no_live_lane_tower';rows.append(row);continue
        target=min(towers,key=lambda t:distance(t,p));tid=tower_id(target)
        birth=None
        for f in frames[bisect_left(ticks,tick):bisect_right(ticks,tick+100)]:
            candidates=[e for e in f['bodies'] if e['side']==side and e['card']=='x-bow' and e['hp']>0 and distance(e,p)<=1000]
            if len(candidates)==1:birth=(f['tick'],candidates[0]);break
        if birth is None:row['excluded']='controller_not_found';rows.append(row);continue
        born,body=birth;uid=body['id'];alive=[]
        for f in frames[bisect_left(ticks,born):bisect_right(ticks,born+800)]:
            bodies=[e for e in f['bodies'] if e['side']==side and e['id']==uid and e['hp']>0]
            if not bodies:break
            alive.append(f)
        row.update(controller_id=uid,distance_milli=distance(body,target),placement_distance_milli=distance(p,target),
                   target=list(tid),born_tick=born,end_tick=alive[-1]['tick'],
                   own_y=1-p['y']/32000 if side==0 else p['y']/32000)
        hit=False;clean=0;confounded=0;gaps=0;deltas=[]
        def clear(f):
            return not (any(e['side']==side and e['hp']>0 and e['id']!=uid and distance(e,target)<=7000 for e in f['bodies']) or
                any(q['side']==side and q['card']!='x-bow' and distance(q,target)<=7000 for q in f['projectiles']+f['areas']))
        # Include the first frame after death for the final interval, but only
        # classify negatives if the recording covers the complete lifetime.
        end_i=bisect_right(ticks,alive[-1]['tick']);censored=end_i==len(frames)
        window=alive+([] if censored else [frames[end_i]])
        for lo,hi in zip(window,window[1:]):
            if hi['tick']-lo['tick']>10:gaps+=1;continue
            old=next((t for t in lo['towers'] if tower_id(t)==tid),None)
            new=next((t for t in hi['towers'] if tower_id(t)==tid),None)
            if old is None or new is None or old['hp']<=0:continue
            if not clear(lo) or not clear(hi):confounded+=1;continue
            clean+=hi['tick']-lo['tick']
            if new['hp']<old['hp']:hit=True;deltas.append(dict(tick=hi['tick'],hp_drop=old['hp']-new['hp']))
        row.update(clean_ticks=clean,confounded_windows=confounded,censored=censored,hp_drops=deltas)
        # An isolated HP drop proves a hit even in an otherwise crowded life.
        # A negative needs the WHOLE lifetime clear; a momentarily empty tower
        # neighbourhood cannot establish that another interval was a miss.
        row['hit']=True if hit else False if clean and not censored and not confounded and not gaps else None
        if row['hit'] is None:row['excluded']='no_clean_window_or_censored'
        rows.append(row)
    return rows

def calibrate(rows):
    eligible=[r for r in rows if r.get('hit') is not None]
    if not eligible or {r['hit'] for r in eligible}!={True,False}:return dict(status='STOP_TELL_LEAD',reason='Need both isolated hit and not-hit examples',rows=rows)
    ds=sorted({r['distance_milli'] for r in eligible})
    thresholds=[ds[0]-1]+ds
    def table(threshold):
        c=Counter(('TP' if r['hit'] else 'FP') if r['distance_milli']<=threshold else ('FN' if r['hit'] else 'TN') for r in eligible)
        return {k:c[k] for k in ('TP','FP','FN','TN')}
    def balanced_error(t):
        c=table(t);return .5*(c['FN']/(c['TP']+c['FN'])+c['FP']/(c['TN']+c['FP']))
    def error(t):
        c=table(t);return (c['FP']+c['FN'])/len(eligible)
    threshold=min(thresholds,key=lambda t:(error(t),t));c=table(threshold)
    modal=Counter(round(r['own_y'],6) for r in rows if 'own_y' in r).most_common(1)[0][0]
    modal_rows=[r for r in eligible if round(r['own_y'],6)==modal]
    modal_distances=[r['distance_milli'] for r in modal_rows]
    modal_ok=bool(modal_distances) and sorted(modal_distances)[len(modal_distances)//2]<=threshold
    overlap=(c['FP']+c['FN'])/len(eligible)
    modal_distance=sorted(modal_distances)[len(modal_distances)//2] if modal_distances else float('inf')
    candidates=[t for t in thresholds if t>=modal_distance]
    alternative=min(candidates,key=lambda t:(error(t),t)) if candidates else None
    # Report both definitions rather than hiding a class-imbalanced overlap.
    passed=overlap<=.15 and modal_ok
    return dict(status='R1_REVISED_CALIBRATION_PASS' if passed else 'STOP_TELL_LEAD',reach_milli=threshold,
        confusion=c,overlap=overlap,balanced_overlap=balanced_error(threshold),eligible=len(eligible),excluded=len(rows)-len(eligible),
        modal_y=modal,modal_offensive=modal_ok,modal_distances=modal_distances,
        best_modal_compatible=(dict(reach_milli=alternative,overlap=error(alternative),confusion=table(alternative)) if alternative is not None else None),
        rule='nearest alive lane tower, isolated clean-window HP drops; minimum classification error, narrower tie',rows=rows)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--corpus',nargs='+',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    rows=[];sources=[];seen=set();cached={}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    code=hashlib.sha256(Path(__file__).read_bytes()+(ROOT/'pipeline/public_outcomes.py').read_bytes()+(ROOT/'pipeline/public_geometry.py').read_bytes()).hexdigest()
    cache=a.out.with_suffix('.rows.jsonl')
    if cache.is_file():
        for line in cache.read_text().splitlines():
            try:item=json.loads(line)
            except json.JSONDecodeError:continue
            if item.get('code_sha256')==code:cached[item['path']]=item
    for corpus in a.corpus:
        for path in sorted([*corpus.glob('replay_*.json'),*corpus.glob('j*/replay_*.json')]):
            raw=path.read_bytes();rec=json.loads(raw)
            if rec['tag'] in seen:continue
            if not rec.get('record_native') or not rec.get('record_full') or not all('public_objects' in f for f in rec['frames']):
                raise ValueError('Not a full public native recording: '+str(path))
            seen.add(rec['tag']);source=dict(path=str(path),tag=rec['tag'],sha256=hashlib.sha256(raw).hexdigest());sources.append(source)
            old=cached.get(str(path))
            if old is not None and old['sha256']==source['sha256']:result=old['rows']
            else:
                result=inspect(rec)
                with cache.open('a') as f:f.write(json.dumps(dict(source,code_sha256=code,rows=result))+'\n')
            rows.extend(result)
            if len(seen)%100==0:print('calibrated recordings',len(seen),flush=True)
    report=calibrate(rows);report['sources']=sources
    if 'reach_milli' in report:
        from public_xbow_validation import boards
        report['review_boards']=boards(ROOT/'scratchpad/gauntlet/L70/gen_v31/proxy_labels_2300/xbow_examples.json',report['reach_milli'])
        report['boards_authorized_for_weighting']=report['status']=='R1_REVISED_CALIBRATION_PASS'
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,indent=2))
    print(json.dumps({k:v for k,v in report.items() if k not in ('rows','sources','modal_distances')}),flush=True)
if __name__=='__main__':main()
