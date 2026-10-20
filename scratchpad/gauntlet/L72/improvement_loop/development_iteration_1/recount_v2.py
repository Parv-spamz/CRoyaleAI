"""Independent raw-label/cache recount. Does not import metrics or evaluator."""
from zipfile import ZipFile
from recovery_common import check_recovery
import numpy as np
import common as c
from pipeline import vocab
from pipeline.opp_elixir_count import card_cost
from pipeline.train_rocket_curriculum import take


def independent_masks(ids,s,cv):
    with np.load(c.SOURCE) as z,ZipFile(c.SOURCE) as archive:
        off=z['off'];positions=np.concatenate([np.arange(off[i],off[i+1]) for i in ids])
        tokens=take(archive,'tok',positions)
    masks={}
    for family in ('witch','night_witch','furnace'):
        original=[];corrected=[];cls=vocab.unit_id(family)
        for a,b in zip(s['off'][:-1],s['off'][1:]):
            t=tokens[a:b];u=s['tok'][a:b]
            original.append(bool(np.any((t[:,0]==cls)&(t[:,2]>.5))))
            corrected.append(bool(np.any((u[:,0]==cls)&(u[:,2]>.5))))
        masks[family]=np.asarray(original)
        masks[family+'_parent']=masks[family]&np.asarray(corrected)
        masks[family+'_child_only']=masks[family]&~np.asarray(corrected)
    costs=np.asarray([card_cost(name.replace('-','_')) or 0 for name in cv])
    available=(s['hand_card']>0)&(costs[s['hand_card']]<=np.floor(s['sc'][:,3]*10+.001)[:,None])
    enemy=(s['projectiles'][:,:,0]==cv.index('goblin-barrel'))&(s['projectiles'][:,:,1]==1)
    target=s['projectiles'][np.arange(len(ids)),np.argmax(enemy,axis=1),4:6]
    x,y=target[:,0],target[:,1]
    valid=(enemy.sum(1)==1)&np.isfinite(target).all(1)&(x>=0)&(x<=1)&(y>=.5)&(y<=1)&((x<.4)|(x>.6))
    ready=valid&np.any((s['hand_card']==cv.index('the-log'))&available,axis=1)
    play=s['y_gate']==1
    pro=ready&play&(s['y_card']==cv.index('the-log'))&((s['y_xy'][:,0]<.5)==(x<.5))
    masks.update(barrel_pro=pro,barrel_other_play=ready&play&~pro,barrel_wait=ready&~play,
        barrel_multiple=enemy.sum(1)>1,barrel_ambiguous=enemy.any(1)&~valid,barrel_absent=~enemy.any(1),
        rocket=play&(s['y_card']==cv.index('rocket')),all=np.ones(len(ids),bool))
    with np.load(c.ROOT/'icebow/data/bench/context_teaching_20261005/cohorts.npz') as z:
        for key in ('finish','combo','xbow','xbow_no_lifetime_target'):masks[key]=z[key][ids]
    return masks,target,available


def independently_count(s,p,cv,masks,target):
    chosen=np.argmax(np.where(p['allowed'],p['card_logits'],-np.inf),axis=1)
    assert np.array_equal(s['hand_card'][np.arange(len(chosen)),chosen],p['chosen_card'])
    expected_gate=1/(1+np.exp(-p['gate_logit'].astype(np.float64)))
    assert np.allclose(expected_gate,p['gate'],rtol=0,atol=1e-7)
    play=s['y_gate']==1
    active=(p['gate']>.35)&p['allowed'].any(1)
    right=(p['chosen_card']==s['y_card'])&p['allowed'].any(1)
    pred=np.stack(((p['expert_cell']%36)/36,(p['expert_cell']//36)/64),axis=1)
    distance=np.sqrt(np.sum(((pred-s['y_xy'])*np.array([18,32]))**2,axis=1))
    lane=(p['log_cell']%36<18)==(target[:,0]<.5)
    log=active&(p['chosen_card']==cv.index('the-log'))
    flags=dict(play=play,card=play&right,action=(play&active&right&(distance<=1))|(~play&~active),
        called=active,aim1=play&(distance<=1),aim2=play&(distance<=2),
        rocket_called=active&(p['chosen_card']==cv.index('rocket')),
        log_correct=log&lane,log_wrong=log&~lane,log_not_fired=~log,forced_log_same=lane)
    out={}
    for key,mask in masks.items():
        reps=sorted(set(s['rep'][mask].tolist()));parts={}
        for rep in reps:
            ix=np.flatnonzero(mask&(s['rep']==rep))
            parts[str(rep)]={'rows':len(ix),**{f:int(np.count_nonzero(v[ix])) for f,v in flags.items()}}
        out[key]={'rows':int(np.count_nonzero(mask)),'replays':len(reps),
            **{f:int(np.count_nonzero(v[mask])) for f,v in flags.items()},'by_replay':parts}
    return out


def controls():
    # Known two-row PLAY/WAIT example, then corrupt the declared cache outputs.
    cv=['pad','the-log','rocket'];s=dict(hand_card=np.array([[1,2,0,0],[1,2,0,0]]),
        y_gate=np.array([1,0]),y_card=np.array([1,0]),y_xy=np.array([[.25,.75],[0.,0.]]),rep=np.array([7,8]))
    p=dict(allowed=np.array([[True,True,False,False]]*2),card_logits=np.array([[2.,1.,-np.inf,-np.inf]]*2),
        chosen_card=np.array([1,1]),gate_logit=np.array([2.,-2.]),gate=1/(1+np.exp(-np.array([2.,-2.]))),
        expert_cell=np.array([48*36+9,0]),log_cell=np.array([48*36+9,48*36+27]))
    masks={'all':np.array([True,True])};target=np.array([[.25,.75],[.25,.75]])
    report=independently_count(s,p,cv,masks,target)
    assert report['all']['action']==2 and report['all']['card']==1 and report['all']['log_correct']==1
    negatives=0
    for key in ('chosen_card','gate'):
        bad={k:v.copy() for k,v in p.items()};bad[key][0]=0
        try:independently_count(s,bad,cv,masks,target)
        except AssertionError:negatives+=1
        else:raise AssertionError('Bad cache accepted')
    for key,field in [('expert_cell','action'),('log_cell','log_correct')]:
        bad={k:v.copy() for k,v in p.items()};bad[key][0]=48*36+27
        assert independently_count(s,bad,cv,masks,target)['all'][field]!=report['all'][field]
        negatives+=1
    return dict(positive=1,negative=negatives)


def main():
    dest=c.HERE/'results_verified_v2.json'
    if dest.exists():raise ValueError('Preserve existing recount')
    c.check_prepared();c.check_frozen();check_recovery();fixtures=controls()
    ids=c.indices('development');s,meta=c.load_subset(c.DATA,ids);cv=meta['card_vocab']
    masks,target,available=independent_masks(ids,s,cv)
    with np.load(c.OUT/'development_masks.npz') as z:
        assert np.array_equal(z['ids'],ids) and np.array_equal(z['target'],target)
        for key,value in masks.items():assert np.array_equal(z['mask_'+key],value),key
    reports={};hashes={}
    for arm in ('r1e_corrected','ordinary_v5','ordinary_v6'):
        folder=c.OUT/(arm+('_eval' if arm=='r1e_corrected' else '_eval_v2'));report=c.read(folder/'report.json');cache=folder/'predictions.npz'
        assert report['cache_sha256']==c.sha(cache)
        with np.load(cache) as z:
            p={k:z[k] for k in z.files if k!='ids'};assert np.array_equal(z['ids'],ids)
        assert np.array_equal(p['allowed'],available)
        result=independently_count(s,p,cv,masks,target)
        assert result==report['counts'],arm
        reports[arm]=result;hashes[arm]=dict(report=c.sha(folder/'report.json'),cache=c.sha(cache))
    with np.load(c.OUT/'draws.npz') as z:draws,mirrors=z['rows'],z['mirror']
    train=c.indices('train');rng=np.random.default_rng(c.SEED)
    for i in range(1000):
        assert np.array_equal(draws[i],train[rng.choice(len(train),128)])
        assert bool(mirrors[i])==bool(rng.random()<.5)
    for arm in ('ordinary_v5','ordinary_v6'):
        folder=c.OUT/arm;result=c.read(folder/'result.json');config=c.read(folder/'run.json')
        logs=[c.json.loads(line) for line in (folder/'train.jsonl').read_text().splitlines()]
        assert [x['step'] for x in logs]==list(range(1,1001))
        assert all(np.isfinite(x['loss']) and all(np.isfinite(v) for v in x['parts'].values()) for x in logs)
        assert result['finite_updates']==1000 and result['checkpoint_sha256']==c.sha(folder/'candidate.pt')
        assert config['draws_sha256']==c.sha(c.OUT/'draws.npz')
        hashes[arm]['checkpoint']=result['checkpoint_sha256']
        proof=c.read(c.HERE/(arm+'_portable.json'))
        assert proof['source_sha256']==result['checkpoint_sha256']
        assert proof['portable_sha256']==c.sha(folder/'candidate_portable.pt')
        er=c.read(c.OUT/(arm+'_eval_v2')/'report.json')
        assert er['checkpoint_sha256']==proof['portable_sha256']
        hashes[arm]['portable_checkpoint']=proof['portable_sha256']
    a,b=reports['ordinary_v5'],reports['ordinary_v6']
    enough=a['barrel_pro']['rows']>0 and all(a[f]['rows']>0 for f in ('witch','night_witch','furnace'))
    card_delta=b['all']['card']/b['all']['play']-a['all']['card']/a['all']['play']
    filters=dict(denominators_present=enough,barrel_correct=b['barrel_pro']['log_correct']>a['barrel_pro']['log_correct'],
        barrel_wrong=b['barrel_pro']['log_wrong']<=a['barrel_pro']['log_wrong'],card_noninferior=card_delta>=-.005,
        **{f+'_nonregression':b[f]['action']>=a[f]['action'] for f in ('witch','night_witch','furnace')})
    summary={arm:{key:{k:v for k,v in counts.items() if k!='by_replay'} for key,counts in report.items()} for arm,report in reports.items()}
    c.write(dest,dict(complete=True,controls=fixtures,rows=len(ids),hashes=hashes,counts=summary,
        v6_continuation_filters=filters,v6_continuation_point_filter_passed=all(filters.values()),
        developmental_only=True,untouched_generalization=False,deployment_accepted=False))
    c.check_frozen();check_recovery();print(c.json.dumps(filters));print('DEVELOPMENT_1_INDEPENDENT_RECOUNT_COMPLETE')


if __name__=='__main__':main()
