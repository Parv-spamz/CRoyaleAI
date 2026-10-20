"""R1 source-shot/HP validation on corrected recordings and 12 retained boards."""
import argparse, json, sys
from pathlib import Path
from collections import defaultdict,Counter
from bisect import bisect_left,bisect_right
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from pipeline.public_outcomes import normalize,label_recording,distance,tower_id
from pipeline.public_geometry import constants,defensive_xbow,in_xbow_range

def inspect(rec):
    frames=[normalize(f) for f in rec['frames']];frames=list({f['tick']:f for f in frames}.values());frames.sort(key=lambda f:f['tick'])
    ticks=[f['tick'] for f in frames];labels=label_recording(dict(rec,frames=frames),normalized=True)['xbows'];result=[]
    for row in labels:
        t,side=row['tick'],row['side'];near=frames[bisect_left(ticks,t):bisect_right(ticks,t+100)]
        births=[(f['tick'],e) for f in near for e in f['bodies'] if e['side']==side and e['card']=='x-bow' and e['hp']>0 and distance(e,row)<=500]
        out=dict(tag=rec['tag'],tick=t,side=side,offensive=row['offensive_xbow'],defensive=row['defensive_xbow'],tower_damage=None,troop_damage=None)
        if not births:out['unknown']='controller_not_found';result.append(out);continue
        born,body=births[0];uid=body['id']
        alive=[f['tick'] for f in frames if f['tick']>=born and any(e['side']==side and e['id']==uid and e['hp']>0 for e in f['bodies'])]
        end=max(alive);tracks=defaultdict(list)
        for f in frames[bisect_left(ticks,born):bisect_right(ticks,end+40)]:
            for q in f['projectiles']:
                if q['side']==side and q['card']=='x-bow':tracks[q['id'],q['generation']].append((f['tick'],q))
        shots=[];towerhit=troophit=False;ambiguous=False
        for track in tracks.values():
            start,q=track[0]
            if start>end or distance(q,body)>2000:continue
            # Refuse attribution when another own X-Bow is equally near the origin.
            f=frames[bisect_left(ticks,start)]
            if any(e['side']==side and e['card']=='x-bow' and e['id']!=uid and distance(e,q)<=distance(body,q) for e in f['bodies']):
                ambiguous=True;continue
            last,q=track[-1];i=bisect_left(ticks,last)
            if i+1>=len(frames):continue
            lo,hi=frames[i],frames[i+1]
            if hi['tick']-last>2:ambiguous=True;continue
            target=dict(x=q['tx'],y=q['ty']) if q['tx'] is not None else q
            after={tower_id(v):v for v in hi['towers']}
            towerhit |= any(v['side']!=side and distance(v,target)<=1500 and tower_id(v) in after and after[tower_id(v)]['hp']<v['hp'] for v in lo['towers'])
            afterb={(v['side'],v['id']):v for v in hi['bodies']}
            troophit |= any(v['side']!=side and distance(v,target)<=1000 and (v['side'],v['id']) in afterb and afterb[v['side'],v['id']]['hp']<v['hp'] for v in lo['bodies'])
            shots.append(last)
        censored=end>=ticks[-1]
        out.update(controller_id=uid,lifetime_end_tick=end,shot_tracks=len(shots),censored=censored,
                   tower_damage=bool(towerhit) if not censored and not ambiguous else True if towerhit else None,
                   troop_damage=bool(troophit) if not censored and not ambiguous else True if troophit else None)
        result.append(out)
    return result

def boards(path,reach=None):
    out=[]
    for r in json.loads(path.read_text()):
        p=r['placement'];x,y=p['xy'];side=p['side']
        world=dict(side=side,x=x*18000 if side==0 else (1-x)*18000,y=(1-y)*32000 if side==0 else y*32000)
        towers=[]
        for lane,nx in [('left',3500/18000),('right',14500/18000)]:
            towers.append(dict(side=1-side,kind='princess',x=nx*18000 if side==0 else (1-nx)*18000,
                               y=25500 if side==0 else 6500,hp=p['tower_hp']['enemy_'+lane]))
        towers.append(dict(side=1-side,kind='king',x=9000,y=29000 if side==0 else 3000,hp=1 if p['crowns_ours_enemy'][0]<3 else 0))
        frame=dict(towers=towers)
        out.append(dict(tag=p['tag'],play_index=p['play_index'],stratum=r['stratum'],defensive=defensive_xbow(world,frame,reach),
            offensive=any(v['hp']>0 and in_xbow_range(world,v,reach) for v in towers)))
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--corpus',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    rows=[]
    for p in sorted(a.corpus.glob('replay_*.json')):rows.extend(inspect(json.loads(p.read_text())))
    groups={}
    for label in ('offensive','defensive'):
        subset=[r for r in rows if r[label]];known=[r for r in subset if r['tower_damage'] is not None]
        troops=[r for r in subset if r['troop_damage'] is not None]
        groups[label]=dict(n=len(subset),tower_known=len(known),tower_hit=sum(r['tower_damage'] for r in known),
            never_hit_share=sum(not r['tower_damage'] for r in known)/len(known) if known else None,
            troop_known=len(troops),troop_hit=sum(r['troop_damage'] for r in troops))
    fail=groups['offensive']['never_hit_share'] is None or groups['offensive']['never_hit_share']>.30
    report=dict(status='STOP_TELL_LEAD' if fail else 'R1_RECORDED_VALIDATION_PASS',groups=groups,constants=constants(),rows=rows,
        boards=boards(ROOT/'scratchpad/gauntlet/L70/gen_v31/proxy_labels_2300/xbow_examples.json'),
        limitation='Source-shot geometry plus HP deltas, not native causal damage. Ambiguous origins and censored lifetimes excluded.')
    a.out.write_text(json.dumps(report,indent=2));print(json.dumps(dict(status=report['status'],groups=groups)),flush=True)
if __name__=='__main__':main()
