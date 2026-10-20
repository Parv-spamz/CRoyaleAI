"""Independent diagnostic arithmetic; never imports audit.py or its functions."""
import copy,collections
from data_io import *
def validate(s,p,ids,expected):
    assert ids.dtype.kind in 'iu' and np.array_equal(ids,expected) and np.all(np.diff(ids)>0)
    n=len(ids);assert all(len(x)==n for x in p.values())
    assert p['allowed'].shape==(n,4) and p['allowed'].dtype==bool and p['card_logits'].shape==(n,4)
    assert np.isfinite(p['gate']).all() and np.all((p['gate']>=0)&(p['gate']<=1))
    assert np.isfinite(p['gate_logit']).all() and np.isfinite(p['card_logits'][p['allowed']]).all()
    assert np.allclose(p['gate'],1/(1+np.exp(-p['gate_logit'].astype(np.float64))),rtol=0,atol=1e-7)
    slot=np.argmax(np.where(p['allowed'],p['card_logits'],-np.inf),axis=1)
    assert np.array_equal(p['chosen_card'],s['hand_card'][np.arange(n),slot])
    assert p['expert_cell'].dtype.kind in 'iu' and np.all((p['expert_cell']>=0)&(p['expert_cell']<2304))
def compute(s,p):
    isplay=s['y_gate']==1;has=np.count_nonzero(p['allowed'],axis=1)>0
    active=(p['gate']>.35)&has;right=np.logical_and(p['chosen_card']==s['y_card'],has)
    pred=np.stack(((p['expert_cell']%36)/36,(p['expert_cell']//36)/64),axis=1)
    dist=np.sqrt(np.sum(((pred-s['y_xy'])*np.array([18,32]))**2,axis=1));aim=dist<=1
    states=np.empty(len(isplay),int)
    states[isplay]=(active.astype(int)*4+right.astype(int)*2+aim.astype(int))[isplay]
    states[~isplay]=8+active[~isplay].astype(int)
    return dict(state=states,distance=dist,fire=active,card=right,aim=aim,action=np.isin(states,[7,8]))
def count(ix,play,vals,ps):
    selected=play[ix];out=dict(rows=len(ix),play=int(np.count_nonzero(selected)),wait=int(np.count_nonzero(~selected)),models={},pairs={})
    for arm,v in vals.items():
        action=v['action'][ix]
        out['models'][arm]=dict(action=int(action.sum()),called=int(v['fire'][ix].sum()),card=int(np.count_nonzero(selected&v['card'][ix])),aim1=int(np.count_nonzero(selected&v['aim'][ix])),play_action=int(np.count_nonzero(selected&action)),wait_action=int(np.count_nonzero(~selected&action)))
    b=vals[ARM]
    for arm in (CONTROL,'r1e_corrected'):
        a=vals[arm];aa=a['action'][ix];ba=b['action'][ix];gain=np.logical_and(~aa,ba);loss=np.logical_and(aa,~ba)
        r=dict(action_gained=int(gain.sum()),action_lost=int(loss.sum()),play_gained=int((gain&selected).sum()),play_lost=int((loss&selected).sum()),wait_gained=int((gain&~selected).sum()),wait_lost=int((loss&~selected).sum()),fire_changed=int(np.count_nonzero(a['fire'][ix]!=b['fire'][ix])),card_changed=int(np.count_nonzero(ps[arm]['chosen_card'][ix]!=ps[ARM]['chosen_card'][ix])),cell_changed=int(np.count_nonzero(ps[arm]['expert_cell'][ix]!=ps[ARM]['expert_cell'][ix])),aim_gained=int(np.count_nonzero(selected&~a['aim'][ix]&b['aim'][ix])),aim_lost=int(np.count_nonzero(selected&a['aim'][ix]&~b['aim'][ix])))
        matrix=[[0]*10 for _ in range(10)]
        for (old,new),n in collections.Counter(zip(a['state'][ix].tolist(),b['state'][ix].tolist())).items():matrix[old][new]=n
        r['states']=matrix;r['hybrid_actions']=[]
        for bits in range(8):
            active=vals[ARM if bits&4 else arm]['fire'][ix]
            right=vals[ARM if bits&2 else arm]['card'][ix]
            aim=vals[ARM if bits&1 else arm]['aim'][ix]
            r['hybrid_actions'].append(int(np.count_nonzero((selected&active&right&aim)|(~selected&~active))))
        assert r['hybrid_actions'][0]==out['models'][arm]['action'] and r['hybrid_actions'][7]==out['models'][ARM]['action']
        assert sum(map(sum,matrix))==len(ix)
        assert out['models'][ARM]['action']-out['models'][arm]['action']==r['play_gained']-r['play_lost']+r['wait_gained']-r['wait_lost']
        out['pairs'][arm]=r
    return out
def same(a,b):assert a==b,'Diagnostic output differs from independent arithmetic'
def controls():
    n=10;ids=np.arange(n);states=np.arange(n);gate=np.array([.9 if i&4 else .1 for i in range(8)]+[.1,.9]);card=np.array([1 if i&2 else 2 for i in range(8)]+[1,1])
    s=dict(y_gate=np.array([1]*8+[0,0]),y_card=np.ones(n,int),y_xy=np.zeros((n,2)),hand_card=np.tile([1,2,0,0],(n,1)))
    p=dict(allowed=np.tile([True,True,False,False],(n,1)),gate=gate,gate_logit=np.log(gate/(1-gate)),card_logits=np.array([[2,1,0,0] if c==1 else [1,2,0,0] for c in card],float),chosen_card=card,expert_cell=np.array([0 if i&1 else 2303 for i in range(8)]+[0,0]))
    validate(s,p,ids,ids);v=compute(s,p);assert np.array_equal(v['state'],states)
    ps={a:p for a in CACHE};vs={a:v for a in CACHE};r=count(ids,s['y_gate']==1,vs,ps)
    assert r['models'][ARM]['action']==2 and r['models'][ARM]['play_action']==1 and r['models'][ARM]['wait_action']==1
    q=copy.deepcopy(p);q['allowed'][0]=False;q['chosen_card'][0]=1;validate(s,q,ids,ids);assert not compute(s,q)['fire'][0]
    rejected=0
    cases=[]
    for key,value in [('chosen_card',0),('gate',.8),('expert_cell',-1)]:
        q=copy.deepcopy(p);q[key][0]=value;cases.append((q,ids))
    cases.append(({k:x[:-1] for k,x in p.items()},ids));bad=ids.copy();bad[1]=0;cases.append((p,bad))
    for q,badids in cases:
        try:validate(s,q,badids,ids)
        except (AssertionError,ValueError,IndexError):rejected+=1
        else:raise AssertionError('Corrupt cache accepted')
    for key in ('action','states','hybrid'):
        bad=copy.deepcopy(r)
        if key=='action':bad['models'][ARM]['action']+=1
        elif key=='states':bad['pairs'][CONTROL]['states'][0][0]+=1
        else:bad['pairs'][CONTROL]['hybrid_actions'][3]+=1
        try:same(bad,r)
        except AssertionError:rejected+=1
        else:raise AssertionError('Corrupt output accepted')
    return dict(positive=2,negative=rejected)
def main():
    assert not (HERE/'verified.json').exists();binding=identities();start=read(HERE/'started.json');assert start['inputs']==binding
    fixture=controls();ids,s,cv,groups,ps=load();play=s['y_gate']==1
    report=read(HERE/'report.json');assert report['complete'] and report['rows']==54723 and report['replays']==405 and report['predictions']==report['optimizer_updates']==0
    assert sha(OUT/'by_replay.json')==report['by_replay_sha256'] and sha(OUT/'rocket_rows.json')==report['rocket_rows_sha256']
    for k in LABELS:assert hashlib.sha256(s[k].tobytes()).hexdigest()==report['label_hashes'][k]
    for a,p in ps.items():
        validate(s,p,ids,ids);assert np.array_equal(p['allowed'],ps[CONTROL]['allowed'])
    vals={a:compute(s,p) for a,p in ps.items()};by=read(OUT/'by_replay.json')
    assert set(report['counts'])==set(groups)==set(by)
    for g,m in groups.items():
        ix=np.flatnonzero(m);same(count(ix,play,vals,ps),report['counts'][g])
        expected={str(int(rep)):count(ix[s['rep'][ix]==rep],play,vals,ps) for rep in np.unique(s['rep'][ix])}
        same(expected,by[g])
    records=read(OUT/'rocket_rows.json');rocket=np.flatnonzero(groups['rocket']);assert len(records)==len(rocket)==955
    for rec,i in zip(records,rocket):
        aa,bb=vals[CONTROL],vals[ARM]
        expected=dict(row=int(ids[i]),rep=int(s['rep'][i]),side=int(s['side'][i]),tick=int(s['tick'][i]),expert_card=int(s['y_card'][i]),expert_xy=s['y_xy'][i].tolist(),hand=s['hand_card'][i].tolist(),allowed=ps[CONTROL]['allowed'][i].tolist(),changes=dict(fire=bool(aa['fire'][i]!=bb['fire'][i]),card=bool(ps[CONTROL]['chosen_card'][i]!=ps[ARM]['chosen_card'][i]),aim=bool(aa['aim'][i]!=bb['aim'][i]),action=int(bb['action'][i])-int(aa['action'][i])),models={a:dict(gate=float(p['gate'][i]),card=int(p['chosen_card'][i]),cell=int(p['expert_cell'][i]),distance=float(vals[a]['distance'][i]),state=int(vals[a]['state'][i])) for a,p in ps.items()})
        same(rec,expected)
    assert identities()==binding
    write(HERE/'verified.json',dict(complete=True,rows=len(ids),replays=405,groups=len(groups),rocket_records=len(records),controls=fixture,report_sha256=sha(HERE/'report.json'),source_sha256=sha(Path(__file__)),inputs=binding,by_replay_sha256=sha(OUT/'by_replay.json'),rocket_rows_sha256=sha(OUT/'rocket_rows.json'),predictions=0,optimizer_updates=0,accepted=False))
    print('RL_FAILURE_AUDIT_VERIFIED')
if __name__=='__main__':main()
