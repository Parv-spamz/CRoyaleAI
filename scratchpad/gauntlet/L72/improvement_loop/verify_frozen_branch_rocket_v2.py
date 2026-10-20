"""Independent scalar geometry/aggregation from raw labels and saved caches.

Shares file I/O only. Does not import producer, model, or producer metric code.
"""
import copy,math,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent / "frozen_branch_rocket"))
from data_io import *
CONTROL='ordinary_v5';CAND='frozen_base_projectile_v6'
def location(cell):
    assert isinstance(cell,(int,np.integer)) and 0<=cell<2304
    x,y=int(cell)%36,int(cell)//36
    return x,y,(y//4)*9+x//4
def targets(objects):
    valid=[];support=set();own=enemy=False;identities=set();bad=False
    for j,o in enumerate(objects):
        card,side=int(o[0]),float(o[1]);x,y=map(float,o[4:6])
        good=card>0 and math.isfinite(x) and math.isfinite(y) and 0<=x<=1 and 0<=y<=1
        valid.append(good)
        if not good:
            bad|=card>0;continue
        assert side in (0,1);own|=side==0;enemy|=side==1;identities.add(card)
        cx=min(8,int(np.float32(x)*np.float32(9)));cy=min(15,int(np.float32(y)*np.float32(16)))
        for yy in range(max(0,cy-1),min(15,cy+1)+1):
            for xx in range(max(0,cx-1),min(8,cx+1)+1):support.add(yy*9+xx)
    return valid,support,own,enemy,identities,bad
def row(s,ps,i,support):
    x,y=map(float,s['y_xy'][i]);play=s['y_gate'][i]==1
    cx=min(35,max(0,round(float(np.float32(x)*np.float32(36)))));cy=min(63,max(0,round(float(np.float32(y)*np.float32(64)))))
    expert=cy*36+cx;out={}
    for arm,p in ps.items():
        px,py,patch=location(p['expert_cell'][i]);distance=math.hypot((px/36-x)*18,(py/64-y)*32)
        active=bool(p['gate'][i]>.35 and any(p['allowed'][i]));card=p['chosen_card'][i]==s['y_card'][i]
        out[arm]=dict(aim1=bool(play and distance<=1),action=bool(active and card and distance<=1) if play else not active,
            called=active,correct_card=bool(play and card and any(p['allowed'][i])),distance=distance,
            expert_in_support=location(expert)[2] in support,predicted_in_support=patch in support)
    a,b=out[CONTROL],out[CAND]
    flags=dict(aim_gained=bool(play and not a['aim1'] and b['aim1']),aim_lost=a['aim1'] and not b['aim1'],
        both_right=a['aim1'] and b['aim1'],both_wrong=bool(play and not a['aim1'] and not b['aim1']),
        action_gained=not a['action'] and b['action'],action_lost=a['action'] and not b['action'],
        cell_changed=ps[CONTROL]['expert_cell'][i]!=ps[CAND]['expert_cell'][i],
        patch_changed=location(ps[CONTROL]['expert_cell'][i])[2]!=location(ps[CAND]['expert_cell'][i])[2],
        distance_better=bool(play and b['distance']<a['distance']),distance_worse=bool(play and b['distance']>a['distance']),
        gate_decision_changed=a['called']!=b['called'],card_choice_changed=ps[CONTROL]['chosen_card'][i]!=ps[CAND]['chosen_card'][i],
        log_cell_changed=ps[CONTROL]['log_cell'][i]!=ps[CAND]['log_cell'][i])
    for k in ('expert_in_support','predicted_in_support'):
        flags['control_'+k]=a[k];flags['candidate_'+k]=b[k]
    return expert,out,flags
def membership(ids,expected,split):
    assert np.array_equal(ids,expected) and len(set(ids))==len(ids) and np.all(split==0)
def equal(a,b):assert a==b
def controls():
    p=np.zeros((3,8),np.float32);p[0]=[1,1,.2,.2,0,0,0,0];p[1]=[2,0,0,0,1,1,0,0];p[2]=[3,1,0,0,-1,.5,0,0]
    v,s,own,enemy,cards,bad=targets(p)
    assert v==[True,True,False] and own and enemy and bad and cards=={1,2}
    assert s=={0,1,9,10,133,134,142,143}
    q=np.zeros((1,8),np.float32);q[0]=[5,1,0,0,.51,.51,0,0]
    assert targets(q)[1]=={yy*9+xx for yy in (7,8,9) for xx in (3,4,5)}
    q[0,4]=np.nan;assert not targets(q)[1]
    q[0,4]=0;q[0,0]=0;assert not targets(q)[1]
    assert location(4)==(4,0,1) and math.hypot((4/36-3/36)*18,0)<=1
    ids=np.array([2,7,9]);membership(ids,ids,np.zeros(3))
    rejected=0
    cases=[lambda:membership(ids[::-1],ids,np.zeros(3)),lambda:membership(np.array([2,7,7]),ids,np.zeros(3)),
        lambda:membership(ids,ids,np.array([0,1,0])),lambda:membership(ids+1,ids,np.zeros(3)),
        lambda:location(-1),lambda:location(2304),lambda:location(1.5),
        lambda:equal({'rows':3,'aim_lost':1},{'rows':3,'aim_lost':0}),
        lambda:equal(s,{0,1,9,10}),lambda:equal(v,[True,True,True])]
    for f in cases:
        try:f()
        except AssertionError:rejected+=1
        else:raise AssertionError('Corruption accepted')
    assert rejected==10
    return dict(positive=6,negative=rejected)
def main():
    assert not (HERE/'verified_v2.json').exists()
    failed=ROOT/'scratchpad/gauntlet/L71/integration/checks/l72-frozen-branch-rocket-independent.json'
    failure=read(failed);assert failure['exit_code']!=0 and not failure['matched']
    helper_hash=sha(Path(__file__).resolve());ctl=controls();start=read(HERE/'started.json');assert inputs()==start['inputs']
    report=read(HERE/'report.json');expected=read(OUT/'by_replay.json');rocket_rows=read(OUT/'rocket_rows.json')
    for key,path in [('details_sha256',OUT/'details.npz'),('replays_sha256',OUT/'by_replay.json'),('rocket_rows_sha256',OUT/'rocket_rows.json')]:assert sha(path)==report[key]
    ids,s,cv,masks,ps=load();membership(ids,ids,s['split']);masks=dict(masks)
    contexts={};allflags=[];allvalues=[];rocket_records=[]
    with np.load(OUT/'details.npz') as archive:
        d={k:archive[k] for k in archive.files}
        assert np.array_equal(ids,d['ids'])
        for k in FIELDS:assert np.array_equal(s[k],d[k])
        for i in range(len(ids)):
            valid,support,own,enemy,identities,bad=targets(s['projectiles'][i])
            assert np.array_equal(valid,d['valid'][i]) and support==set(np.flatnonzero(d['support'][i]))
            expert,values,f=row(s,ps,i,support);assert expert==d['target'][i]
            for k,v in f.items():assert bool(v)==bool(d['transition/'+k][i]),(i,k)
            for arm,p in ps.items():
                for key in ('expert_cell','log_cell','chosen_card','gate'):assert p[key][i]==d[arm+'/'+key][i]
            near=False
            for slot,tx in ((4,3.5/18),(5,14.5/18)):
                near|=s['sc'][i,64+slot]>.5 and math.hypot((float(s['y_xy'][i,0])-tx)*18,(float(s['y_xy'][i,1])-6.5/32)*32)<=1
            keys={'none':sum(valid)==0,'one':sum(valid)==1,'multiple':sum(valid)>1,'own_only':own and not enemy,'enemy_only':enemy and not own,'mixed':own and enemy,'invalid_real':bad,'near_princess':near,'other_aim':not near}
            for card in identities:keys['identity/'+cv[card]]=True
            for k,v in keys.items():
                if k not in contexts:contexts[k]=np.zeros(len(ids),bool)
                contexts[k][i]=v
            allflags.append(f);allvalues.append(values)
            if s['y_gate'][i]==1 and s['y_card'][i]==cv.index('rocket'):
                rocket_records.append(dict(row=int(ids[i]),rep=int(s['rep'][i]),side=int(s['side'][i]),tick=int(s['tick'][i]),expert_xy=s['y_xy'][i].tolist(),expert_cell=expert,
                    projectiles=[o.tolist() for o in s['projectiles'][i] if o[0]>0],valid_targets=sum(valid),**{k:bool(v) for k,v in f.items()},
                    models={a:dict(cell=int(ps[a]['expert_cell'][i]),distance=float(v['distance']),aim1=v['aim1'],action=v['action']) for a,v in values.items()}))
    play=s['y_gate']==1
    for k,m in contexts.items():masks['context/'+k]=m;masks['rocket_context/'+k]=m&masks['rocket']
    for card in set(s['y_card'][play]):masks['expert_card/'+cv[int(card)]]=play&(s['y_card']==card)
    masks['play']=play;masks['wait']=~play
    assert set(masks)==set(expected)==set(report['counts'])
    for name,m in masks.items():
        reps={}
        for i in np.flatnonzero(m):
            rep=str(int(s['rep'][i]));r=reps.setdefault(rep,dict(rows=0,**{k:0 for k in allflags[i]},**{a+'/'+k:0 for a in ps for k in ('aim1','action','called','correct_card')}))
            r['rows']+=1
            for k,v in allflags[i].items():r[k]+=int(v)
            for arm,values in allvalues[i].items():
                for k in ('aim1','action','called','correct_card'):r[arm+'/'+k]+=int(values[k])
        assert reps==expected[name],name
        tot={k:sum(r[k] for r in reps.values()) for k in report['counts'][name] if k!='replays'};tot['replays']=len(reps)
        assert tot==report['counts'][name],name
    assert len(rocket_records)==len(rocket_rows)==955
    for a,b in zip(rocket_records,rocket_rows):
        for arm in a['models']:
            assert math.isclose(a['models'][arm]['distance'],b['models'][arm]['distance'],rel_tol=1e-14,abs_tol=1e-14)
            a['models'][arm]['distance']=b['models'][arm]['distance']
        assert a==b,a['row']
    assert inputs()==start['inputs']
    write(HERE/'verified_v2.json',dict(complete=True,helper_sha256=helper_hash,failed_receipt_sha256=sha(failed),rows=len(ids),groups=len(masks),models=len(ps),rocket_rows=len(rocket_rows),controls=ctl,report_sha256=sha(HERE/'report.json'),started_sha256=sha(HERE/'started.json'),predictions=0,optimizer_updates=0))
    assert helper_hash==sha(Path(__file__).resolve())
    print('FROZEN_BRANCH_ROCKET_INDEPENDENT_V2_COMPLETE')
if __name__=='__main__':main()
