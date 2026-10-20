"""Descriptive native-state joins and cached development predictions; no inference."""
from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict
import math
from io_utils import *

PHASES=('single_clock','double_regulation_clock','early_overtime_clock','late_overtime_clock')

def phase(t):return PHASES[bisect_right((2400,3600,4800),t)]

def tower_state(frame, side):
    found={}
    for t in frame.get('towers',[]):
        if len(t)<7 or t[0] not in (0,1) or t[1] not in ('king','princess'):return None
        s,kind,_,x,_,hp,mhp=t[:7]
        if not all(isinstance(v,(int,float)) and math.isfinite(v) for v in (x,hp,mhp)) or hp<0 or mhp<=0:return None
        lane='king' if kind=='king' else ('left' if x<9000 else 'right')
        key=(s,lane)
        if key in found:return None
        found[key]=(hp,mhp)
    keys=[(s,l) for s in (side,1-side) for l in ('king','left','right')]
    if set(found)!=set(keys):return None
    hp=[found[k][0] for k in keys];mx=[found[k][1] for k in keys]
    mins=[min((h for h in hp[3*s:3*s+3] if h>0),default=None) for s in (0,1)]
    pmins=[min((h for h in hp[3*s+1:3*s+3] if h>0),default=None) for s in (0,1)]
    fractions=[min((hp[i]/mx[i] for i in range(3*s,3*s+3) if hp[i]>0),default=None) for s in (0,1)]
    crowns=[3 if hp[3*enemy]<=0 else sum(h==0 for h in hp[3*enemy+1:3*enemy+3]) for enemy in (1,0)]
    return dict(hp=hp,max_hp=mx,crowns=crowns,margin=None if None in mins else mins[0]-mins[1],
        princess_margin=None if None in pmins else pmins[0]-pmins[1],
        fraction_margin=None if None in fractions else fractions[0]-fractions[1],
        enemy_princess_min=pmins[1])

def norm_xy(x,y,side):
    return (1-x/18000,y/32000) if side else (x/18000,1-y/32000)

def join_frame(rec,row,cv):
    if row['y_gate']==0:
        found=[(i,f) for i,f in enumerate(rec['frames']) if f['tick']==row['tick']]
        assert len(found)==1,('WAIT frame',row['tick'],len(found))
        return found[0][1],dict(kind='frames',index=found[0][0])
    events=[p for p in rec['log'] if p.get('accepted') and not p.get('ability') and p.get('side')==row['side']
            and p['tick']==row['tick'] and p['card']==cv[row['y_card']]
            and np.allclose(norm_xy(p['x'],p['y'],row['side']),row['y_xy'],rtol=0,atol=1e-6)]
    assert len(events)==1,('PLAY join',row['tick'],len(events))
    found=[(i,f) for i,f in enumerate(rec['play_frames']) if f['play_index']==events[0]['play_index']]
    assert len(found)==1
    return found[0][1],dict(kind='play_frames',index=found[0][0],play_index=events[0]['play_index'])

def lifetimes(frames):
    active={};lives=[]
    for frame in frames:
        now={}
        for e in frame.get('entities',[]):
            if len(e)<9 or e[3]!='Xbow':continue
            identity=(e[0],e[8]);assert identity not in now
            life=active.get(identity)
            if life is None:
                life=dict(side=e[0],entity=e[8],generation=len(lives),x=e[1],y=e[2],birth=frame['tick'],last=frame['tick'],end=None,continuous=True)
                lives.append(life)
            else:
                life['continuous'] &= frame['tick']-life['last']<=10
                life['last']=frame['tick']
            now[identity]=life
        for identity,life in active.items():
            if identity not in now:
                life['end']=frame['tick'];life['continuous'] &= frame['tick']-life['last']<=10
        active=now
    return lives

def before_frame(frames,ticks,t):
    i=bisect_right(ticks,t)-1
    return frames[i] if i>=0 and t-ticks[i]<=10 else None

def bow_history(commands,labels,lives,frames,ticks,side,tick):
    prior=[p for p in commands if p.get('side')==side and p['card']=='x-bow' and p['tick']<tick
           and labels.get((side,p['tick']),{}).get('offensive_xbow') is True]
    if not prior:return dict(count=0,status='none',cast_tick=None,lock='unknown')
    p=prior[-1];found=[l for l in lives if l['side']==side and l['x']==p['x'] and l['y']==p['y'] and 0<l['birth']-p['tick']<=10]
    result=dict(count=len(prior),status='unknown',cast_tick=p['tick'],lock='unknown')
    if len(found)!=1:return result
    life=found[0]
    # A later disappearance/drop cannot enter an earlier context.
    if life['birth']>=tick:return result
    if life['end'] is None or life['end']>=tick:
        current=before_frame(frames,ticks,tick)
        if current and any(len(e)>=9 and e[0]==side and e[8]==life['entity'] and e[3]=='Xbow' for e in current['entities']):
            result['status']='ongoing'
        return result
    if not life['continuous']:return result
    a=before_frame(frames,ticks,p['tick']);b=before_frame(frames,ticks,life['end'])
    if a is None or b is None:return result
    x,y=tower_state(a,side),tower_state(b,side)
    if x is None or y is None:return result
    drop=sum(max(0,x['hp'][i]-y['hp'][i]) for i in (4,5))
    result.update(status='ended_enemy_princess_hp_drop' if drop else 'ended_no_enemy_princess_hp_drop',
                  end_tick=life['end'],enemy_hp_drop=drop)
    return result

def outcomes(rec,frame,state,side,tick,frames,ticks,accepted):
    out={}
    for sec in (10,30,60):
        end=tick+sec*20;after=before_frame(frames,ticks,end)
        selected=[x for x in ticks if tick<x<=end]
        coverage=(after is not None and ticks[-1]>=end and
                  all(b-a<=10 for a,b in zip([tick]+selected,selected)))
        s=tower_state(after,side) if coverage else None
        if state is None or s is None:
            out[str(sec)]={'covered':False};continue
        charged=[p for p in accepted if tick<=p['tick']<=end]
        known=all(isinstance(p.get('cost'),(int,float)) and math.isfinite(p['cost']) for p in charged)
        spent=[sum(p['cost'] for p in charged if p['side']==j) for j in (side,1-side)] if known else None
        out[str(sec)]=dict(covered=True,spending=spent,own_elixir=after.get('elixir',[None,None])[side],
            princess_hp_drop=[max(0,state['hp'][i]-s['hp'][i]) for i in (1,2,4,5)],
            margin_after=s['margin'],margin_change=None if state['margin'] is None or s['margin'] is None else s['margin']-state['margin'],
            crowns_after=s['crowns'])
    return out

def cache_flags(row,p,cv):
    active=bool(p['gate']>.35 and any(p['allowed']));play=bool(row['y_gate']==1)
    right=bool(p['chosen_card']==row['y_card'] and any(p['allowed']))
    pred=np.array([int(p['expert_cell'])%36/36,int(p['expert_cell'])//36/64])
    d=float(np.linalg.norm((pred-np.array(row['y_xy'],np.float64))*[18,32]))
    return dict(called=int(active),rocket_called=int(active and p['chosen_card']==cv.index('rocket')),
        card=int(play and right),aim1=int(play and d<=1),action=int((play and active and right and d<=1) or (not play and not active)))

def groups(row):
    s=row['state'];sign='unknown' if s is None or s['margin'] is None else ('ahead' if s['margin']>0 else 'behind' if s['margin']<0 else 'equal')
    eq='unknown' if s is None else str(s['crowns'][0]==s['crowns'][1]).lower()
    high='unknown' if s is None or s['enemy_princess_min'] is None else str(s['enemy_princess_min']>1500).lower()
    phase=row['phase'];bow=row['bow']
    result=['all','phase/'+phase,'phase_margin/'+phase+'/'+eq+'/'+sign,'phase_bow/'+phase+'/'+bow['status'],
            'prior_bows/'+str(min(2,bow['count'])),'high_princess/'+high,'grade_match/'+str(row['grade_crowns_match']).lower(),
            'phase_expert/'+phase+'/'+('wait' if not row['play'] else row['expert_card'])]
    for card in ('goblin-barrel','witch','night-witch','furnace'):
        if card in row['revealed']:result.append('revealed/'+card)
    return result

def add_summary(summary,row):
    for group in groups(row):
        key=row['part']+'/'+group;entry=summary.setdefault(key,{'totals':Counter(),'by_replay':{}})
        counters=[entry['totals'],entry['by_replay'].setdefault(row['tag'],Counter())]
        for c in counters:
            c['rows']+=1;c['play']+=row['play'];c['wait']+=1-row['play'];c['expert_rocket']+=row['play'] and row['expert_card']=='rocket'
            c['expert_xbow']+=row['play'] and row['expert_card']=='x-bow'
            for arm,flags in row['predictions'].items():
                for k,v in flags.items():c[arm+'/'+k]+=v
                if row['play'] and row['expert_card']=='rocket':
                    c[arm+'/rocket_action']+=flags['action'];c[arm+'/rocket_aim1']+=flags['aim1']
            for seconds,outcome in row['outcomes'].items():
                prefix=seconds+'s/';c[prefix+'covered']+=outcome['covered']
                if not outcome['covered']:continue
                if outcome['spending'] is not None:
                    c[prefix+'cost_known']+=1;c[prefix+'own_spent']+=outcome['spending'][0];c[prefix+'opp_spent']+=outcome['spending'][1]
                if outcome['margin_change'] is not None:
                    c[prefix+'margin_known']+=1;c[prefix+'margin_change']+=outcome['margin_change']
                for lane,value in zip(('own_left','own_right','enemy_left','enemy_right'),outcome['princess_hp_drop']):c[prefix+lane+'_drop']+=value
                if outcome['own_elixir'] is not None:c[prefix+'elixir_known']+=1;c[prefix+'own_elixir']+=outcome['own_elixir']

def main():
    if (HERE/'report.json').exists() or (OUT/'rows.jsonl').exists():raise ValueError('Fresh audit output required')
    binding=check_binding();a=load_rows();cv=binding['card_vocab'];tags=binding['tags']
    labels=defaultdict(dict)
    for line in LABELS.open():
        x=json.loads(line)
        if x['tag'] in binding['sources'] and x['card']=='x-bow':labels[x['tag']][(x['side'],x['tick'])]=x
    caches={}
    for arm,path in binding['caches'].items():
        with np.load(ROOT/path) as z:caches[arm]={k:z[k] for k in z.files}
    devpos={int(i):j for j,i in enumerate(caches['r1e_corrected']['ids'])}
    summary={};cap=Counter();source_reports=[];count=0
    with (OUT/'rows.jsonl').open('x') as stream:
        for rep in sorted(set(a['rep'].tolist())):
            tag=tags[rep];src=binding['sources'][tag];path=ROOT/src['path'];assert sha(path)==src['sha256']
            rec=read(path);frames=rec['frames'];ticks=[f['tick'] for f in frames]
            assert all(x<y for x,y in zip(ticks,ticks[1:]))
            accepted=sorted([p for p in rec['log'] if p.get('accepted') and p.get('side') in (0,1)],key=lambda p:(p['tick'],p.get('play_index',-1)))
            commands=[p for p in accepted if not p.get('ability')]
            lives=lifetimes(frames)
            cap['replays']+=1;cap['native_crowns_mismatch']+=not rec.get('grade',{}).get('crowns_match',False)
            cap['frames']+=len(frames)
            cap['frames_observed_multiplier']+=sum('elixir_rate' in f or 'elixir_multiplier' in f for f in frames)
            cap['frames_causal_hits']+=sum(f.get('public_objects',{}).get('causal_hit_events') is not None for f in frames)
            cap['entity_rows_with_target_column']+=sum(len(e)>9 for f in frames for e in f.get('entities',[]))
            for j in np.flatnonzero(a['rep']==rep):
                base={k:a[k][j].tolist() for k in FIELDS};side,t=base['side'],base['tick']
                frame,join=join_frame(rec,base,cv);state=tower_state(frame,side)
                if state is not None:
                    order=[0,2,1,3,5,4] if side else list(range(6))
                    expected=np.array([state['hp'][i]/state['max_hp'][i] for i in order]);sc=base['sc']
                    known=np.array(sc[58:64])>.5
                    assert np.allclose(expected[known],np.array(sc[52:58])[known],rtol=0,atol=1e-6),(tag,t,'tower join')
                row=dict(id=int(a['ids'][j]),tag=tag,rep=rep,side=side,tick=t,part='development' if a['part'][j] else 'training',
                    play=int(base['y_gate']),expert_card=cv[base['y_card']],join=join,state=state,phase=phase(t),observed_multiplier=None,
                    revealed=sorted({p['card'] for p in commands if p['side']!=side and p['tick']<t}),
                    bow=bow_history(commands,labels[tag],lives,frames,ticks,side,t),
                    outcomes=outcomes(rec,frame,state,side,t,frames,ticks,accepted),
                    grade_crowns_match=rec.get('grade',{}).get('crowns_match'),
                    native_winner=rec.get('final',{}).get('winner'),native_terminal_tick=rec.get('final',{}).get('tick'),
                    tiebreak_cause='unknown',predictions={})
                if a['part'][j]:
                    k=devpos[row['id']]
                    for arm,p in caches.items():row['predictions'][arm]=cache_flags(base,{key:v[k] for key,v in p.items() if key!='ids'},cv)
                add_summary(summary,row);stream.write(json.dumps(row,allow_nan=False)+'\n');count+=1
            source_reports.append(dict(tag=tag,sha256=src['sha256'],frames=len(frames),last_tick=ticks[-1],grade=rec['grade']))
            if len(source_reports)%100==0:
                stream.flush();write(HERE/'progress.json',dict(replays=len(source_reports),rows=count));print('AUDITED',len(source_reports),count,flush=True)
    assert count==268718
    write(OUT/'by_replay.json',{k:v['by_replay'] for k,v in summary.items()})
    report=dict(complete=True,rows=count,prepared_sha256=sha(HERE/'prepared.json'),rows_sha256=sha(OUT/'rows.jsonl'),
        replay_sha256=sha(OUT/'by_replay.json'),capabilities=dict(cap),sources=source_reports,
        summaries={k:dict(v['totals'],replays=len(v['by_replay'])) for k,v in summary.items()},
        scripts={p.name:sha(p) for p in (HERE/'audit.py',HERE/'io_utils.py',HERE/'METRICS.md')},
        new_predictions=False,optimizer_updates=0,causal_or_gameplay_claim=False)
    write(HERE/'report.json',report);check_binding();print('MATCH_ADAPTATION_AUDIT_COMPLETE')

if __name__=='__main__':main()
