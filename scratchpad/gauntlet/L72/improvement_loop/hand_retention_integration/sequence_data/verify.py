"""Independent scalar FIFO and original-log window recount; no model imports."""
from collections import Counter,defaultdict
from itertools import groupby
from zipfile import ZipFile
from shared import *
from pipeline.dataset_gen import card_key
from pipeline.train_rocket_curriculum import take

def reference(plays,tick,side,gid):
    selected=sorted([e for e in plays if e['side']!=side and e['tick']<tick and
                     e.get('accepted',True) and not e.get('ability')],key=lambda e:e['tick'])
    known=set();last={};count=0;issue=False;invalid=False;previous=None;mirrors=0;seen={}
    def outside():return {c for c,(end,size) in last.items() if count-end+size-1<4} if not invalid else set()
    for t,g in groupby(selected,key=lambda e:e['tick']):
        batch=[]
        for e in g:
            eid=e.get('event_id')
            if eid is not None:
                sig=(e['tick'],e.get('card'))
                if eid in seen:
                    if seen[eid]!=sig:raise ValueError('event ID conflict')
                    continue
                seen[eid]=sig
            batch.append(e)
        if not batch:continue
        if len(batch)>1 or any(e.get('gap_before') or e.get('identity_unknown') for e in batch):previous=None
        normalized=[];newprevious=None;gap=any(e.get('gap_before') for e in batch)
        for e in batch:
            raw=card_key(e.get('card') or '');name=raw;unknown=e.get('identity_unknown',False)
            if len(batch)==1 and previous is not None and raw is not None and raw==previous[0]:
                if previous[1]!='mirror' and not(len(known)==8 and 'mirror' not in known) and 'mirror' not in outside():
                    name='mirror';mirrors+=1
                else:unknown=True;gap=True
            normalized.append(None if unknown else name)
            if len(batch)==1 and not unknown:newprevious=(raw,name)
        previous=newprevious
        if gap:last={};count=0;issue=True
        cards=[c for c in normalized if c]
        known.update(cards)
        if len(known)>8:invalid=True;last={};count=0;issue=True;continue
        if None in normalized or len(set(cards))!=len(cards):last={};count=0;issue=True;continue
        for card in cards:
            if card in last:
                end,size=last[card]
                if count-end+size-1+len(cards)-1<4:last={};count=0;issue=True;break
        count+=len(cards)
        for card in cards:last[card]=(count,len(cards))
    inside=set();out=set();bounds={}
    if not invalid:
        for card,(end,size) in last.items():
            recent=count-end;oldest=recent+size-1
            bounds[card]=[max(0,4-oldest),max(0,4-recent)]
            if recent>=4:inside.add(card)
            elif oldest<4:out.add(card)
        if len(known)==8 and len(out)==4:
            inside=known-out
            for card in inside:bounds[card]=[0,0]
    if len(inside)>4 or len(out)>4 or inside&out:inside=set();out=set();bounds={};issue=True
    tok=np.zeros((8,6),np.float32)
    for i,card in enumerate(sorted(known)[:8]):
        cid=gid.get(card,0)
        if cid:
            low,high=bounds.get(card,(0,4));tok[i]=[cid,card in inside,card in out,
                card not in inside|out,low*.25,high*.25]
    q=np.array([min(8,len(known))*.125,not invalid and len(inside)==4,issue or invalid,mirrors>0,1],np.float32)
    return tok,q,known

def window(log,tick,side,hand,end,gid,known):
    # Construct directly from original accepted commands, never collected descriptors.
    events=sorted([(int(e.get('engine_tick',e['tick'])),int(e['side']),card_key(e['card']))
                   for e in log if e.get('accepted') and not e.get('ability') and e.get('card')])
    out=[0,0,0,-1,-1,0,0,0,int(end<tick+500)]
    enemies=[x for x in events if x[1]!=side and 0<x[0]-tick<=400]
    if not enemies:return np.array(out,np.int32)
    et=enemies[0][0];out[3]=et
    if sum(x[0]==et for x in enemies)>1:out[0]=2;return np.array(out,np.int32)
    enemy=enemies[0][2];out[1]=gid.get(enemy,0);out[7]=int(enemy in known)
    responses=[x for x in events if x[1]==side and 0<x[0]-et<=100]
    if not responses:out[0]=1;return np.array(out,np.int32)
    rt=responses[0][0];out[4]=rt
    if sum(x[0]==rt for x in responses)>1:out[0]=2;return np.array(out,np.int32)
    response=responses[0][2];out[2]=gid.get(response,0)
    before=[x for x in events if x[1]==side and tick<=x[0]<et]
    out[5]=len(before);out[6]=sum(x[2]==response for x in before)
    out[0]=3 if not any(int(c)==out[2] for c in hand) else 5 if out[6]>0 else 4
    return np.array(out,np.int32)

def controls():
    from pipeline.opponent_hand_v2 import belief_tokens
    gid={c:i+1 for i,c in enumerate(['a','b','c','d','e','f','g','h','mirror'])}
    fixtures=[]
    for cards in (['a','a','b','c','d'],['a','a','a'],['a','b','c','d','e','f','g','h','a'],['a','b','a']):
        fixtures.append([dict(tick=i+1,side=1,card=c) for i,c in enumerate(cards)])
    fixtures.append([dict(tick=1,side=1,card='a'),dict(tick=1,side=1,card='b'),dict(tick=2,side=1,card='c',gap_before=True)])
    for events in fixtures:
        for tick in range(1,12):
            a,b,_=reference(events,tick,0,gid);actual=belief_tokens(events,tick,0,gid)
            np.testing.assert_array_equal(a,actual['opp_hand']);np.testing.assert_array_equal(b,actual['opp_hand_quality'])
    logs=[dict(tick=10,side=0,card='a',accepted=True),dict(tick=20,side=1,card='b',accepted=True),
          dict(tick=25,side=0,card='a',accepted=True)]
    events=[{k:e[k] for k in ('tick','side','card')} for e in logs]
    for tick in (9,11,21):
        np.testing.assert_array_equal(window(logs,tick,0,[1,3,4,5],1000,gid,{'b'}),
            descriptor(events,tick,0,[1,3,4,5],1000,gid,{'b'}))
    a,b,_=reference(fixtures[0],8,0,gid)
    caught=0
    for col in range(6):
        bad=a.copy();bad[0,col]+=1
        try:np.testing.assert_array_equal(a,bad)
        except AssertionError:caught+=1
    for col in (1,2,4):
        bad=b.copy();bad[col]=1-bad[col]
        try:np.testing.assert_array_equal(b,bad)
        except AssertionError:caught+=1
    expected=window(logs,9,0,[1,3,4,5],1000,gid,{'b'})
    for col in range(9):
        bad=expected.copy();bad[col]+=1
        try:np.testing.assert_array_equal(expected,bad)
        except AssertionError:caught+=1
    assert caught==18
    return dict(positive_prefixes=55,positive_windows=3,corruptions=caught)

def main():
    assert not (HERE/'verified.json').exists()
    started=read(HERE/'started.json');collected=read(HERE/'collected.json')
    assert collected['complete'] and started['sources']==sources()
    assert collected['started_sha256']==sha(HERE/'started.json')
    for n,h in collected['outputs'].items():assert sha(OUT/n)==h
    control=controls();rows=arrays(ROWFILE);f=arrays(OUT/'features.npz');a=arrays(OUT/'audit.npz');binding=read(BINDING)
    np.testing.assert_array_equal(rows['ids'],f['ids']);np.testing.assert_array_equal(rows['ids'],a['ids'])
    assert set(f)=={'ids','opp_hand','opp_hand_quality'}
    # Reconfirm untouched action labels against BOTH archived data versions.
    labels=['rep','side','tick','split','y_gate','y_card','y_xy','y_wait_card','y_wait_dt','y_crowns','y_cell','y_hand_pos']
    for source in (DATA,ORIGINAL):
        with ZipFile(source) as z:
            for k in labels:np.testing.assert_array_equal(rows[k],take(z,k,rows['ids']))
            np.testing.assert_array_equal(a['hand_card'],take(z,'hand_card',rows['ids']))
    streams={v['rep']:v for v in map(json.loads,(OUT/'public_events.jsonl').read_text().splitlines())}
    assert set(streams)==set(map(int,rows['rep']))
    gid={c:i for i,c in enumerate(binding['card_vocab'])};details=read(OUT/'by_replay.json');per_rep={d['rep']:d for d in details}
    totals={p:dict(rows=0,status=[0]*6,truncated=0,full_hand=0,issues=0,mirror_inferred=0,pairs=Counter()) for p in (0,1)}
    for ri,rep in enumerate(sorted(streams)):
        tag=binding['tags'][rep];s=binding['sources'][tag];assert streams[rep]['tag']==tag
        assert sha(ROOT/s['path'])==s['sha256'];rec=read(ROOT/s['path']);end=max(x['tick'] for x in rec['frames'])
        ix=np.flatnonzero(rows['rep']==rep);local=dict(rows=0,status=[0]*6,full_hand=0,issues=0,mirror_inferred=0,truncated=0)
        memo={}
        for i in ix:
            t=int(rows['tick'][i]);side=int(rows['side'][i]);p=int(rows['part'][i])
            if (side,t) not in memo:memo[(side,t)]=reference(streams[rep]['plays'][side],t,side,gid)
            token,q,known=memo[(side,t)];w=window(rec['log'],t,side,a['hand_card'][i],end,gid,known)
            np.testing.assert_array_equal(token,f['opp_hand'][i]);np.testing.assert_array_equal(q,f['opp_hand_quality'][i])
            np.testing.assert_array_equal(w,a['descriptors'][i])
            for target in (local,totals[p]):
                target['rows']+=1;target['status'][int(w[0])]+=1;target['truncated']+=int(w[8])
                for key,j in [('full_hand',1),('issues',2),('mirror_inferred',3)]:target[key]+=int(q[j])
            if w[0] in (4,5):totals[p]['pairs']['/'.join(map(str,w[:3]))]+=1
        for key,value in local.items():assert per_rep[rep][key]==value,(rep,key)
        if (ri+1)%50==0:print('VERIFIED_REPLAYS',ri+1,flush=True)
    assert {str(p):{**v,'pairs':dict(v['pairs'])} for p,v in totals.items()}==collected['summary']
    assert sources()==started['sources']
    write(HERE/'verified.json',dict(complete=True,rows=268718,replays=len(streams),controls=control,
        collected_sha256=sha(HERE/'collected.json'),features_sha256=sha(OUT/'features.npz'),audit_sha256=sha(OUT/'audit.npz'),
        original_labels_exact=True,all_features_exact=True,all_windows_exact=True,all_replays_exact=True))
    print('HAND_SEQUENCE_VERIFIED')
if __name__=='__main__':main()
