"""Independent NumPy recount of the frozen training aim component cache."""
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent


def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def validate(p,c,b,f,split,membership):
    assert p.ndim==c.ndim==f.ndim==2 and p.shape==c.shape==f.shape
    assert b.shape==(f.shape[1],) and split.shape==(f.shape[0],)
    assert membership.shape==split.shape and membership.dtype==bool and membership.any()
    assert np.all(split==0)
    assert all(np.isfinite(v).all() for v in [p,c,b,f])
    np.testing.assert_allclose(p+c+b,f,rtol=1e-5,atol=1e-5)


def controls():
    p=np.array([[0.,1.],[1.,0.]]);c=np.array([[1.,0.],[0.,1.]]);b=np.array([.25,-.25])
    good=[p,c,b,p+c+b,np.zeros(2,dtype=int),np.ones(2,dtype=bool)]
    validate(*good)
    bad=[]
    a=copy.deepcopy(good);a[3][0,0]+=1;bad.append(a)
    a=copy.deepcopy(good);a[1]=a[1][:1];bad.append(a)
    a=copy.deepcopy(good);a[0][0,0]=np.nan;bad.append(a)
    a=copy.deepcopy(good);a[4][0]=1;bad.append(a)
    a=copy.deepcopy(good);a[5][:]=False;bad.append(a)
    for a in bad:
        try:validate(*a)
        except AssertionError:pass
        else:raise AssertionError('Corruption accepted')
    # Stored float32 labels must be promoted BEFORE scale multiplication.
    edge=np.array([.19444445,.203125],dtype=np.float32).astype(np.float64)
    assert np.hypot(1.5-edge[0]*18,6.5-edge[1]*32)>2
    return dict(positive=2,negative=len(bad))


def main():
    output=HERE/'train_aim_decomposition_verified.json'
    assert not output.exists(),'Preserve existing verifier'
    proof=controls()
    report_path=HERE/'train_aim_decomposition.json'
    report=json.loads(report_path.read_text(encoding='utf-8'))
    assert report['complete'] and report['training_only'] and report['optimization_steps']==0 and report['new_models']==0
    for name,digest in report['sources'].items():assert sha(ROOT/name)==digest,name
    file=Path(report['cache_path']);assert sha(file)==report['cache_sha256']
    old=json.loads((HERE/'train_rocket_diagnosis.json').read_text(encoding='utf-8'))
    cache=np.load(file)
    ids=cache['row_ids'];xy=cache['xy'].astype(np.float64);split=cache['split'];tags=cache['tags']
    assert ids.tolist()==old['selected_row_ids'] and len(ids)==report['rows']
    assert hashlib.sha256(ids.tobytes()).hexdigest()==old['selected_ids_sha256']
    assert len(np.unique(ids))==len(ids) and np.all(split==0)
    # Independently join selection and labels back to the original training arrays.
    source=ROOT/'icebow/data/pipeline/gen_dataset_v31_public.npz'
    context=ROOT/'icebow/data/bench/context_teaching_20261005/cohorts.npz'
    assert sha(source)==report['source_sha256'] and sha(context)==report['contexts_sha256']
    with np.load(source) as z,np.load(context) as co:
        meta=json.loads(str(z['meta']));cards=z['y_card'];gates=z['y_gate'];splits=z['split']
        training=co['pool']&(splits==0);r=(gates==1)&(cards==meta['card_vocab'].index('rocket'))
        masks=[training&co['finish']&r,training&co['combo']&r,
               training&co['combo']&(gates==1)&(cards==meta['card_vocab'].index('tornado')),
               training&r&~co['finish']&~co['combo']]
        rng=np.random.default_rng(20261005)
        selected=[]
        for i,m in enumerate(masks):
            candidates=np.where(m)[0]
            selected.append(candidates if i==0 else np.sort(rng.choice(candidates,min(len(candidates),256),replace=False)))
        assert np.array_equal(ids,np.unique(np.concatenate(selected)))
        for key,index in [('finish',0),('combo_rocket',1),('ordinary_rocket',3)]:
            assert np.array_equal(cache['cohort_'+key],np.isin(ids,selected[index]))
        np.testing.assert_array_equal(xy,z['y_xy'][ids])
        np.testing.assert_array_equal(tags,z['tags'][z['rep'][ids]])
        np.testing.assert_array_equal(split,splits[ids])
    checked={}
    for arm,cohorts in report['summaries'].items():
        p,c,b,f=[cache[arm+'_'+k].astype(np.float64) for k in ['patch','position','bias','full']]
        assert f.shape==(len(ids),2304)
        baseline=f.argmax(axis=1)
        old_rows={r['row']:r for r in old['predictions'][arm]}
        np.testing.assert_allclose(np.c_[baseline%36/36,baseline//36/64],
            [old_rows[int(i)]['predicted_xy'] for i in ids],rtol=0,atol=1e-8)
        for cohort,expected in cohorts.items():
            membership=cache['cohort_'+cohort];validate(p,c,b,f,split,membership)
            wanted=np.where(membership)[0]
            assert len(wanted)==expected['rows'] and len(set(tags[wanted]))==expected['replays']
            sums={k:Counter(correct=0,gained=0,lost=0) for k in expected['modes']}
            masses={k:[] for k in sums};margins={k:[] for k in ['patch','position','bias']};dominants=Counter()
            misses=0
            for i in wanted:
                xs=(np.arange(2304)%36)/2;ys=(np.arange(2304)//36)/2
                eligible=np.hypot(xs-xy[i,0]*18,ys-xy[i,1]*32)<=2
                correct=bool(eligible[baseline[i]])
                vectors={'full':f[i],'no_patch':c[i]+b,'no_position':p[i]+b,
                         'no_bias':p[i]+c[i],'patch_only':p[i],'position_only':c[i],'bias_only':b}
                for name,v in vectors.items():
                    hit=bool(eligible[int(v.argmax())])
                    sums[name].update(correct=int(hit),gained=int(hit and not correct),lost=int(correct and not hit))
                    e=np.exp(v-v.max());masses[name].append(float(e[eligible].sum()/e.sum()))
                if not correct:
                    misses+=1;best=int(np.where(eligible,f[i],-np.inf).argmax())
                    changes={k:float(v[baseline[i]]-v[best]) for k,v in [('patch',p[i]),('position',c[i]),('bias',b)]}
                    for k,v in changes.items():margins[k].append(v)
                    dominants[max(changes,key=changes.get)]+=1
            assert misses==expected['full_misses']
            for name,totals in sums.items():
                assert all(totals[k]==expected['modes'][name][k] for k in totals)
                assert abs(np.mean(masses[name])-expected['modes'][name]['mean_expert_region_mass'])<1e-9
            for name,values in margins.items():
                target=expected['miss_margin_contributions'][name]
                assert dominants[name]==target['dominant_rows']
                if values:assert abs(np.mean(values)-target['mean'])<1e-9
                else:assert target['mean'] is None
            checked[arm+':'+cohort]=dict(rows=len(wanted),full_correct=sums['full']['correct'])
    result=dict(complete=True,training_only=True,controls=proof,checked=checked,
        cache_sha256=sha(file),producer_report_sha256=sha(report_path),script_sha256=sha(__file__),
        model_predictions=0,optimization_steps=0,new_models=0,N2_complete=False)
    output.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print('TRAIN_AIM_DECOMPOSITION_INDEPENDENTLY_VERIFIED')


if __name__=='__main__':main()
