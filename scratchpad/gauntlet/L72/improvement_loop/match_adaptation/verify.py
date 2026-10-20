"""Independent original-label/native/cached-prediction recount. No producer import."""
import argparse
from collections import Counter,defaultdict
import copy
import math
import time
from io_utils import *

def state(f,seat):
    t=f.get('towers',[])
    if len(t)!=6:return None
    table={}
    for x in t:
        if len(x)<7 or x[0] not in [0,1] or x[1] not in ['king','princess']:return None
        if any(not isinstance(v,(float,int)) or not math.isfinite(v) for v in (x[3],x[5],x[6])) or x[5]<0 or x[6]<=0:return None
        key=(x[0],0 if x[1]=='king' else 1 if x[3]<9000 else 2)
        if key in table:return None
        table[key]=(x[5],x[6])
    order=[(s,k) for s in [seat,1-seat] for k in range(3)]
    if set(table)!=set(order):return None
    hp=[table[k][0] for k in order];maximum=[table[k][1] for k in order]
    absolute=[];fraction=[];princess=[]
    for j in [0,3]:
        alive=[i for i in range(j,j+3) if hp[i]>0]
        absolute.append(min([hp[i] for i in alive],default=None))
        fraction.append(min([hp[i]/maximum[i] for i in alive],default=None))
        princess.append(min([hp[i] for i in alive if i%3!=0],default=None))
    diff=lambda values:None if any(x is None for x in values) else values[0]-values[1]
    crown=[]
    for j in [3,0]:crown.append(3 if hp[j]==0 else int(hp[j+1]==0)+int(hp[j+2]==0))
    return dict(hp=hp,max_hp=maximum,crowns=crown,margin=diff(absolute),fraction_margin=diff(fraction),
                princess_margin=diff(princess),enemy_princess_min=princess[1])

def normalize(rec):
    ordered=[]
    for f in rec['frames']:
        if ordered and ordered[-1]['tick']==f['tick']:
            if ordered[-1]!=f:raise ValueError('Inconsistent duplicate')
        else:
            if ordered:assert ordered[-1]['tick']<f['tick']
            ordered.append(f)
    return ordered

def at(frames,t):
    ticks=[f['tick'] for f in frames]
    i=int(np.searchsorted(ticks,t,side='right'))-1
    return None if i<0 or t-ticks[i]>10 else frames[i]

def expected_bow(commands,bowlabels,frames,seat,t):
    plays=[p for p in commands if p['side']==seat and p['card']=='x-bow' and p['tick']<t and
           bowlabels.get((seat,p['tick']),{}).get('offensive_xbow') is True]
    result=dict(count=len(plays),status='unknown' if plays else 'none',cast_tick=plays[-1]['tick'] if plays else None,lock='unknown')
    if not plays:return result
    p=plays[-1];births=[]
    # Independent search for births only in the fixed ten-tick cast window.
    for i,f in enumerate(frames):
        if not p['tick']<f['tick']<=p['tick']+10:continue
        previous=frames[i-1]['entities'] if i else []
        for e in f.get('entities',[]):
            if len(e)<9 or e[0]!=seat or e[3]!='Xbow' or [e[1],e[2]]!=[p['x'],p['y']]:continue
            if not any(len(v)>=9 and v[0]==seat and v[3]=='Xbow' and v[8]==e[8] for v in previous):births.append((i,e[8]))
    if len(births)!=1:return result
    i,eid=births[0]
    if frames[i]['tick']>=t:return result
    visible=lambda f:any(len(e)>=9 and e[0]==seat and e[3]=='Xbow' and e[8]==eid for e in f.get('entities',[]))
    end=i+1
    while end<len(frames) and visible(frames[end]):end+=1
    if end==len(frames) or frames[end]['tick']>=t:
        current=at(frames,t)
        if current and visible(current):result['status']='ongoing'
        return result
    if any(frames[k]['tick']-frames[k-1]['tick']>10 for k in range(i+1,end+1)):return result
    before=at(frames,p['tick']);after=frames[end]
    if before is None:return result
    a,b=state(before,seat),state(after,seat)
    if a is None or b is None:return result
    drop=max(0,a['hp'][4]-b['hp'][4])+max(0,a['hp'][5]-b['hp'][5])
    result.update(status='ended_enemy_princess_hp_drop' if drop else 'ended_no_enemy_princess_hp_drop',end_tick=after['tick'],enemy_hp_drop=drop)
    return result

def reconstruct(base,rec,frames,bowlabels,cv):
    tick,seat=int(base['tick']),int(base['side']);play=int(base['y_gate'])
    accepted=sorted([p for p in rec['log'] if p.get('accepted') and p.get('side') in (0,1)],key=lambda p:(p['tick'],p.get('play_index',-1)))
    cards=[p for p in accepted if not p.get('ability')]
    if play:
        options=[]
        for p in cards:
            if p['side']!=seat or p['tick']!=tick or p['card']!=cv[int(base['y_card'])]:continue
            xy=[p['x']/18000,1-p['y']/32000] if seat==0 else [1-p['x']/18000,p['y']/32000]
            if max(abs(x-y) for x,y in zip(xy,base['y_xy']))<=1e-6:options.append(p)
        assert len(options)==1
        matches=[i for i,f in enumerate(rec['play_frames']) if f['play_index']==options[0]['play_index']]
        assert len(matches)==1
        index=matches[0];fr=rec['play_frames'][index];join=dict(kind='play_frames',index=index,play_index=options[0]['play_index'])
    else:
        matches=[i for i,f in enumerate(rec['frames']) if f['tick']==tick];assert matches
        index=matches[0];fr=rec['frames'][index];assert all(fr==rec['frames'][i] for i in matches)
        join=dict(kind='frames',index=index)
    initial=state(fr,seat);period='single_clock' if tick<2400 else 'double_regulation_clock' if tick<3600 else 'early_overtime_clock' if tick<4800 else 'late_overtime_clock'
    futures={}
    for sec in [10,30,60]:
        end=tick+20*sec;f=at(frames,end)
        observed=[tick]+[q['tick'] for q in frames if tick<q['tick']<=end]
        valid=f is not None and frames[-1]['tick']>=end and max(np.diff(observed),default=0)<=10
        after=state(f,seat) if valid else None
        if initial is None or after is None:futures[str(sec)]={'covered':False};continue
        charged=[p for p in accepted if tick<=p['tick']<=end]
        known=all(isinstance(p.get('cost'),(int,float)) and math.isfinite(p['cost']) for p in charged)
        sums=[sum(p['cost'] for p in charged if p['side']==s) for s in [seat,1-seat]] if known else None
        futures[str(sec)]=dict(covered=True,spending=sums,own_elixir=f.get('elixir',[None,None])[seat],
            princess_hp_drop=[max(0,initial['hp'][k]-after['hp'][k]) for k in [1,2,4,5]],
            margin_after=after['margin'],margin_change=None if initial['margin'] is None or after['margin'] is None else after['margin']-initial['margin'],crowns_after=after['crowns'])
    return dict(join=join,state=initial,phase=period,observed_multiplier=None,
        revealed=sorted(set(p['card'] for p in cards if p['side']==1-seat and p['tick']<tick)),
        bow=expected_bow(cards,bowlabels,frames,seat,tick),outcomes=futures,
        grade_crowns_match=rec.get('grade',{}).get('crowns_match'),native_winner=rec.get('final',{}).get('winner'),
        native_terminal_tick=rec.get('final',{}).get('tick'),tiebreak_cause='unknown')

def predictions(base,cache,cv):
    play=int(base['y_gate'])==1
    active=bool(float(cache['gate'])>.35 and cache['allowed'].any())
    card=bool(cache['chosen_card']==base['y_card'] and cache['allowed'].any())
    cell=int(cache['expert_cell']);x,y=cell%36/36,cell//36/64
    dx=(x-float(base['y_xy'][0]))*18;dy=(y-float(base['y_xy'][1]))*32
    distance=math.sqrt(dx*dx+dy*dy)
    return dict(called=int(active),rocket_called=int(active and cache['chosen_card']==cv.index('rocket')),
                card=int(play and card),aim1=int(play and distance<=1),action=int(play and active and card and distance<=1 or not play and not active))

def group_names(r):
    s=r['state'];m=s['margin'] if s else None
    sign='unknown' if m is None else 'ahead' if m>0 else 'behind' if m<0 else 'equal'
    eq=str(s['crowns'][0]==s['crowns'][1]).lower() if s else 'unknown'
    high='unknown' if s is None or s['enemy_princess_min'] is None else str(s['enemy_princess_min']>1500).lower()
    ph=r['phase'];b=r['bow']
    names=['all',f'phase/{ph}',f'phase_margin/{ph}/{eq}/{sign}',f'phase_bow/{ph}/'+b['status'],
        'prior_bows/'+str(min(2,b['count'])),'high_princess/'+high,'grade_match/'+str(r['grade_crowns_match']).lower(),
        f'phase_expert/{ph}/'+(r['expert_card'] if r['play'] else 'wait')]
    return names+['revealed/'+x for x in ('goblin-barrel','witch','night-witch','furnace') if x in r['revealed']]

def contributions(r):
    c=Counter(rows=1,play=r['play'],wait=1-r['play'],expert_rocket=int(r['play'] and r['expert_card']=='rocket'),expert_xbow=int(r['play'] and r['expert_card']=='x-bow'))
    for arm,p in r['predictions'].items():
        for k,v in p.items():c[arm+'/'+k]=v
        if c['expert_rocket']:c[arm+'/rocket_action']=p['action'];c[arm+'/rocket_aim1']=p['aim1']
    for sec,o in r['outcomes'].items():
        h=sec+'s/';c[h+'covered']=int(o['covered'])
        if not o['covered']:continue
        if o['spending'] is not None:c[h+'cost_known']=1;c[h+'own_spent']=o['spending'][0];c[h+'opp_spent']=o['spending'][1]
        if o['margin_change'] is not None:c[h+'margin_known']=1;c[h+'margin_change']=o['margin_change']
        for lane,v in zip(['own_left','own_right','enemy_left','enemy_right'],o['princess_hp_drop']):c[h+lane+'_drop']=v
        if o['own_elixir'] is not None:c[h+'elixir_known']=1;c[h+'own_elixir']=o['own_elixir']
    return c

def compare(left,right):
    if left!=right:raise AssertionError('Independent raw row mismatch')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--wait',action='store_true');args=ap.parse_args()
    receipt=ROOT/'scratchpad/gauntlet/L71/integration/checks/l72-match-adaptation-audit-v2.json'
    if args.wait:
        while not receipt.exists():time.sleep(5)
    status=read(receipt);assert status['exit_code']==0 and status['matched'], 'Producer must succeed'
    assert not (HERE/'verified_v2.json').exists()
    source_hash=sha(__file__);binding=check_binding();report=read(HERE/'report_v2.json')
    assert report['complete'] and report['prepared_sha256']==sha(HERE/'prepared.json')
    assert report['rows_sha256']==sha(OUT/'rows_v2.jsonl') and report['replay_sha256']==sha(OUT/'by_replay_v2.json')
    for filename,h in report['scripts'].items():assert sha(HERE/filename)==h
    a=load_rows();cv=binding['card_vocab'];lookup={int(row):i for i,row in enumerate(a['ids'])}
    caches={}
    for arm,path in binding['caches'].items():
        with np.load(ROOT/path) as z:caches[arm]={k:z[k] for k in z.files}
    dev={int(row):i for i,row in enumerate(caches['r1e_corrected']['ids'])}
    labels=defaultdict(dict)
    for line in LABELS.open():
        x=json.loads(line)
        if x['tag'] in binding['sources'] and x['card']=='x-bow':labels[x['tag']][(x['side'],x['tick'])]=x
    totals=defaultdict(Counter);per=defaultdict(lambda:defaultdict(Counter));seen=set();tag=None;count=0;fixtures=None
    for line in (OUT/'rows_v2.jsonl').open():
        r=json.loads(line);row_id=r['id'];assert row_id in lookup and row_id not in seen;seen.add(row_id)
        i=lookup[row_id];base={k:a[k][i] for k in FIELDS}
        assert r['rep']==int(base['rep']) and r['side']==int(base['side']) and r['tick']==int(base['tick'])
        assert r['tag']==binding['tags'][int(base['rep'])] and r['part']==('development' if a['part'][i] else 'training')
        assert r['play']==int(base['y_gate']) and r['expert_card']==cv[int(base['y_card'])]
        if tag!=r['tag']:
            tag=r['tag'];src=binding['sources'][tag];assert sha(ROOT/src['path'])==src['sha256'];rec=read(ROOT/src['path']);frames=normalize(rec)
        expected=reconstruct(base,rec,frames,labels[tag],cv)
        actual={k:r[k] for k in expected};compare(expected,actual)
        if fixtures is None:
            corrupt=[]
            for field,value in [('phase','fake'),('observed_multiplier',3),('revealed',['future-secret']),('tiebreak_cause','inferred-from-tick')]:
                b=copy.deepcopy(actual);b[field]=value;corrupt.append(b)
            for field in ('state','bow','join','outcomes'):
                b=copy.deepcopy(actual);b[field]={};corrupt.append(b)
            n=0
            for bad in corrupt:
                try:compare(expected,bad)
                except AssertionError:n+=1
                else:raise AssertionError('Corruption passed')
            fixtures=dict(positive=1,negative=n)
        p={}
        if r['part']=='development':
            for arm,cache in caches.items():p[arm]=predictions(base,{k:v[dev[row_id]] for k,v in cache.items() if k!='ids'},cv)
        compare(p,r['predictions'])
        values=contributions(r)
        for group in group_names(r):
            key=r['part']+'/'+group;totals[key].update(values);per[key][tag].update(values)
        count+=1
        if count%20000==0:write(HERE/'verify_progress.json',dict(rows=count));print('VERIFIED',count,flush=True)
    assert seen==set(lookup) and count==268718
    assert set(totals)==set(report['summaries'])
    for key,c in totals.items():compare(dict(c,replays=len(per[key])),report['summaries'][key])
    compare({k:{t:dict(c) for t,c in v.items()} for k,v in per.items()},read(OUT/'by_replay_v2.json'))
    assert sha(__file__)==source_hash
    write(HERE/'verified_v2.json',dict(complete=True,rows=count,report_sha256=sha(HERE/'report_v2.json'),source_sha256=source_hash,
        raw_sources=len(binding['sources']),fixtures=fixtures,all_raw_rows_matched=True,new_predictions=False,optimizer_updates=0,
        direct_lock_or_causal_damage_verified=False))
    print('MATCH_ADAPTATION_INDEPENDENT_COMPLETE')

if __name__=='__main__':main()
