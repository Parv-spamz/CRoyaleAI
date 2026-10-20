"""Describe already-verified past context; never change labels or training inputs."""
from collections import defaultdict
import numpy as np
from experiment import c,DOUT,PHASES

def make_extra(ids,s,cv):
    phase=np.searchsorted([2400,3600,4800],s['tick'],side='right')
    result={}
    for i,name in enumerate(PHASES):
        result['phase_'+name]=phase==i
        result['rocket_'+name]=(phase==i)&(s['y_gate']==1)&(s['y_card']==cv.index('rocket'))
    by_id={int(row):i for i,row in enumerate(ids)};groups=defaultdict(list);seen=set()
    for line in (DOUT/'rows_v2.jsonl').open():
        r=c.json.loads(line)
        if r['part']!='development':continue
        i=by_id[r['id']];assert i not in seen;seen.add(i)
        assert r['tick']==int(s['tick'][i]) and r['rep']==int(s['rep'][i])
        state=r['state'];margin=state['margin'] if state else None
        sign='unknown' if margin is None else 'ahead' if margin>0 else 'behind' if margin<0 else 'equal'
        eq=str(state['crowns'][0]==state['crowns'][1]).lower() if state else 'unknown'
        high='unknown' if state is None or state['enemy_princess_min'] is None else str(state['enemy_princess_min']>1500).lower()
        keys=[f"ctx_margin/{r['phase']}/{eq}/{sign}",f"ctx_bow/{r['phase']}/{r['bow']['status']}",
            'ctx_prior/'+str(min(2,r['bow']['count'])),'ctx_high/'+high,'ctx_grade/'+str(r['grade_crowns_match']).lower()]
        keys += ['ctx_revealed/'+name for name in ('goblin-barrel','witch','night-witch','furnace') if name in r['revealed']]
        for key in keys:groups[key].append(i)
    assert len(seen)==len(ids)
    for key,ix in groups.items():
        value=np.zeros(len(ids),bool);value[ix]=True;result[key]=value
    return result

def independently_verify_extra(ids,s,cv,actual):
    expected={};parts=(s['tick']>=2400).astype(int)+(s['tick']>=3600).astype(int)+(s['tick']>=4800).astype(int)
    for i,name in enumerate(PHASES):
        expected['phase_'+name]=set(ids[parts==i].tolist())
        expected['rocket_'+name]=set(ids[(parts==i)&(s['y_gate']==1)&(s['y_card']==cv.index('rocket'))].tolist())
    lookup=set(ids.tolist());seen=set()
    for line in (DOUT/'rows_v2.jsonl').open():
        r=c.json.loads(line)
        if r['id'] not in lookup:continue
        assert r['part']=='development' and r['id'] not in seen;seen.add(r['id'])
        t=r['state'];m=None if t is None else t['margin']
        sign='unknown' if m is None else ('ahead' if m>0 else ('behind' if m<0 else 'equal'))
        eq='unknown' if t is None else ('true' if t['crowns'][0]==t['crowns'][1] else 'false')
        h='unknown' if t is None or t['enemy_princess_min'] is None else ('true' if t['enemy_princess_min']>1500 else 'false')
        keys=['ctx_margin/'+r['phase']+'/'+eq+'/'+sign,'ctx_bow/'+r['phase']+'/'+r['bow']['status'],
            'ctx_prior/'+str(2 if r['bow']['count']>=2 else r['bow']['count']),'ctx_high/'+h,
            'ctx_grade/'+str(r['grade_crowns_match']).lower()]
        for card in ('goblin-barrel','witch','night-witch','furnace'):
            if card in set(r['revealed']):keys.append('ctx_revealed/'+card)
        for key in keys:expected.setdefault(key,set()).add(r['id'])
    assert seen==lookup and set(actual)==set(expected)
    for key,values in expected.items():assert set(ids[actual[key]].tolist())==values,key
    return len(expected)
