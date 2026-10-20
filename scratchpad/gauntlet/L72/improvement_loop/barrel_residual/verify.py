"""Independent cached-logit and original-source recount; never invokes a model."""
import copy,hashlib,json,math,sys
from pathlib import Path
from zipfile import ZipFile
import numpy as np
ROOT=Path(__file__).resolve().parents[5]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from pipeline.train_rocket_curriculum import take


def read(p):return json.loads(Path(p).read_bytes())
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def recount(payload,selection,truth,conditions,log_id):
    ids=payload['ids'];assert np.array_equal(ids,truth['ids']) and len(set(map(int,ids)))==len(ids)
    assert np.all(truth['split']==0)
    for cached,source in [('expert_gate','y_gate'),('expert_card','y_card'),('expert_xy','y_xy'),('target','target'),('allowed','allowed')]:
        assert np.array_equal(payload[cached],truth[source]),cached
    positions={int(r):i for i,r in enumerate(ids)}
    for name,chosen in selection.items():
        assert len(set(chosen))==len(chosen) and set(chosen)<=set(positions)
        assert len(set(map(int,truth['rep'][[positions[r] for r in chosen]])))==len(chosen)
    out={};per_row={}
    for condition in conditions:
        pref=condition+'__'
        for field in ('expert_logits','log_logits','gate','chosen','residual_max'):
            assert np.isfinite(payload[pref+field]).all(),field
        ex=np.argmax(payload[pref+'expert_logits'],axis=1)
        lg=np.argmax(payload[pref+'log_logits'],axis=1)
        rows=[]
        for i in range(len(ids)):
            is_play=bool(truth['y_gate'][i]);called=bool(payload[pref+'gate'][i]>.35 and payload['allowed'][i].any())
            card=int(payload[pref+'chosen'][i])
            dx=(int(ex[i])%36/36-float(truth['y_xy'][i,0]))*18
            dy=(int(ex[i])//36/64-float(truth['y_xy'][i,1]))*32
            aim=math.hypot(dx,dy)<=1
            same=(int(lg[i])%36/36<.5)==(float(truth['target'][i,0])<.5)
            fired=called and card==log_id
            rows.append(dict(action=called and card==int(truth['y_card'][i]) and aim if is_play else not called,
                card=is_play and card==int(truth['y_card'][i]),aim=is_play and aim,log_fired=fired,
                forced_log_same_lane=same,gated_correct_lane=fired and same,gated_wrong_lane=fired and not same))
        per_row[condition]=rows;out[condition]={}
        for name,chosen in selection.items():
            ix=[positions[r] for r in chosen]
            counts=dict(rows=len(ix),plays=sum(int(truth['y_gate'][i]) for i in ix))
            for k in ('action','card','aim','log_fired'):counts[k]=sum(int(rows[i][k]) for i in ix)
            if name in ('single_pro_log','single_other_play','single_wait'):
                for k in ('forced_log_same_lane','gated_correct_lane','gated_wrong_lane'):counts[k]=sum(int(rows[i][k]) for i in ix)
            out[condition][name]=counts
    for full in conditions:
        if not full.startswith('v6') or not full.endswith('__full'):continue
        off=full.removesuffix('full')+'residual_off';assert off in conditions
        for key in ('gate','chosen'):
            assert np.array_equal(payload[full+'__'+key],payload[off+'__'+key]),key
        zero=np.flatnonzero(~truth['valid_target'])
        assert np.all(payload[full+'__residual_max'][zero]==0)
        for key in ('expert_logits','log_logits'):
            assert np.array_equal(payload[full+'__'+key][zero],payload[off+'__'+key][zero]),key
    return out,per_row


def check(payload,selection,truth,report,log_id):
    counts,rows=recount(payload,selection,truth,report['conditions'],log_id)
    assert counts==report['summaries'],'reported_counts'
    assert report['optimizer_updates']==0 and not report['new_checkpoint'] and not report['live_changed']
    return rows


def controls():
    ids=np.array([100,101]);xy=np.array([[6/36,50/64],[6/36,50/64]],dtype=np.float32)
    truth=dict(ids=ids,split=np.zeros(2,int),rep=np.array([1,2]),y_gate=np.ones(2,int),y_card=np.ones(2,int),
        y_xy=xy,target=np.array([[.25,.8],[0.,0.]]),allowed=np.ones((2,4),bool),valid_target=np.array([True,False]))
    p=dict(ids=ids,expert_gate=truth['y_gate'].copy(),expert_card=truth['y_card'].copy(),expert_xy=xy.copy(),target=truth['target'].copy(),allowed=truth['allowed'].copy())
    selection={'single_pro_log':[100],'no_valid_target':[101]};names=['v6_fixture__full','v6_fixture__residual_off']
    for name in names:
        ex=np.zeros((2,2304),np.float32);ex[:,50*36+6]=3
        lg=ex.copy()
        if name.endswith('residual_off'):lg[0]=0;lg[0,50*36+30]=3
        for k,v in dict(gate=np.array([.8,.8]),chosen=np.ones(2,int),expert_logits=ex,log_logits=lg,residual_max=np.array([1.,0.])).items():p[name+'__'+k]=v
    summary,_=recount(p,selection,truth,names,1)
    report=dict(conditions=names,summaries=summary,optimizer_updates=0,new_checkpoint=False,live_changed=False)
    check(p,selection,truth,report,1)
    failures=[]
    for name in ('membership','heldout','label','logits','gate_invariance','card_invariance','zero_target','reported_count'):
        a,b,t,r=copy.deepcopy((p,selection,truth,report))
        if name=='membership':b['single_pro_log']=[999]
        elif name=='heldout':t['split'][0]=1
        elif name=='label':a['expert_card'][0]=2
        elif name=='logits':a['v6_fixture__full__log_logits'][0,50*36+30]=5
        elif name=='gate_invariance':a['v6_fixture__residual_off__gate'][0]=.1
        elif name=='card_invariance':a['v6_fixture__residual_off__chosen'][0]=2
        elif name=='zero_target':a['v6_fixture__full__residual_max'][1]=1
        else:r['summaries']['v6_fixture__full']['single_pro_log']['rows']+=1
        try:check(a,b,t,r,1)
        except (AssertionError,KeyError):failures.append(name)
        else:raise AssertionError('Corruption accepted '+name)
    return dict(positive_checks=1,rejected_corruptions=failures)


def main():
    assert not (HERE/'verified.json').exists()
    control=controls()
    report=read(HERE/'report.json');sel=read(HERE/'selection.json')
    assert report['conditions']==['v5_rocket_barrel__full','v6_rocket_barrel__full','v6_rocket_barrel__residual_off','v6_rocket_both__full','v6_rocket_both__residual_off']
    assert sha(HERE/'selection.json')==report['selection_sha256']
    for p,h in sel['sources'].items():assert sha(ROOT/p)==h,p
    for arm,h in sel['checkpoints'].items():assert sha(ROOT/f'icebow/data/bench/expert_context_20261005/{arm}/candidate.pt')==h
    cache=ROOT/report['cache'];assert sha(cache)==report['cache_sha256']
    with np.load(cache) as z:p={k:z[k] for k in z.files}
    source=ROOT/'icebow/data/pipeline/gen_dataset_v31_public.npz'
    with np.load(source) as z:
        meta=json.loads(str(z['meta']));cv=meta['card_vocab'];splits=z['split'];reps=z['rep']
        with np.load(ROOT/'icebow/data/bench/context_teaching_20261005/cohorts.npz') as c:pool=np.flatnonzero(c['pool']&(splits==0))
        full_gate=z['y_gate'];full_card=z['y_card'];full_xy=z['y_xy']
    ids=np.asarray(sel['ids'],np.int64);assert np.array_equal(ids,p['ids']) and np.all(np.isin(ids,pool))
    with ZipFile(source) as z:
        objects=take(z,'projectiles',pool);hand=take(z,'hand_card',pool);sc=take(z,'sc',pool)
    # Icebow Log's established two-elixir cost, used only to verify declared membership.
    barrel=cv.index('goblin-barrel');log=cv.index('the-log')
    enemy=(objects[:,:,0]==barrel)&(objects[:,:,1]==1)
    targets=objects[np.arange(len(pool)),enemy.argmax(1),4:6]
    valid=(objects[:,:,0]>0)&np.isfinite(objects[:,:,4:6]).all(-1)&(objects[:,:,4:6]>=0).all(-1)&(objects[:,:,4:6]<=1).all(-1)
    single=(enemy.sum(1)==1)&np.isfinite(targets).all(-1)&(targets[:,0]>=0)&(targets[:,0]<=1)&(targets[:,1]>=.5)&(targets[:,1]<=1)&((targets[:,0]<.4)|(targets[:,0]>.6))
    available=single&(hand==log).any(1)&(np.floor(sc[:,3]*10+1e-3)>=2)
    masks=[available&(full_gate[pool]==1)&(full_card[pool]==log)&((full_xy[pool,0]<.5)==(targets[:,0]<.5)),
        available&(full_gate[pool]==1)&(full_card[pool]!=log),available&(full_gate[pool]==0),enemy.sum(1)>1,
        enemy.any(1)&~single,~enemy.any(1)&valid.any(1),~valid.any(1)]
    assert list(sel['selection'])==['single_pro_log','single_other_play','single_wait','multiple_barrel','ambiguous_barrel','other_projectile','no_valid_target']
    rng=np.random.default_rng(20261005)
    for (name,chosen),mask in zip(sel['selection'].items(),masks):
        rows=pool[mask];groups=np.unique(reps[rows]);group_sample=rng.permutation(groups)[:200]
        expected=sorted(int(rng.choice(rows[reps[rows]==g])) for g in group_sample)
        assert chosen==expected
        assert sel['sizes'][name]==dict(full_rows=len(rows),full_replays=len(groups),selected=len(chosen))
    ix=np.searchsorted(pool,ids);assert np.array_equal(pool[ix],ids)
    from pipeline.opp_elixir_count import card_cost
    costs=np.array([card_cost(s.replace('-','_')) or 0 for s in cv])
    truth=dict(ids=ids,split=splits[ids],rep=reps[ids],y_gate=full_gate[ids],y_card=full_card[ids],y_xy=full_xy[ids],target=targets[ix],
        allowed=(hand[ix]>0)&(costs[hand[ix]]<=np.floor(sc[ix,3]*10+1e-3)[:,None]),valid_target=valid[ix].any(1))
    rows=check(p,sel['selection'],truth,report,log)
    positions={int(r):i for i,r in enumerate(ids)};pairs={}
    for arm in ('v6_rocket_barrel','v6_rocket_both'):
        full=rows[arm+'__full'];off=rows[arm+'__residual_off'];pairs[arm]={}
        for cohort,chosen in sel['selection'].items():
            ix=[positions[r] for r in chosen];pairs[arm][cohort]={}
            keys=['action','aim']+(['gated_correct_lane','gated_wrong_lane','forced_log_same_lane'] if cohort=='single_pro_log' else [])
            for k in keys:
                pairs[arm][cohort][k]=dict(off_only=sum(int(off[i][k] and not full[i][k]) for i in ix),
                    full_only=sum(int(full[i][k] and not off[i][k]) for i in ix),both=sum(int(full[i][k] and off[i][k]) for i in ix),neither=sum(int(not full[i][k] and not off[i][k]) for i in ix))
    proof=dict(complete=True,report_sha256=sha(HERE/'report.json'),selection_sha256=sha(HERE/'selection.json'),script_sha256=sha(__file__),
        rows=len(ids),strata=sel['sizes'],controls=control,paired_transitions=pairs,zero_target_rows=int((~truth['valid_target']).sum()),optimizer_updates=0,new_checkpoint=False,
        limitations=['Training-only evidence; residual-off is not a qualified candidate.','No physical landing, gameplay or fresh confirmation inference.'])
    (HERE/'verified.json').write_text(json.dumps(proof,indent=2))
    print(json.dumps({arm:pairs[arm]['single_pro_log'] for arm in pairs}));print('TRAIN_BARREL_RESIDUAL_INDEPENDENT_PASS')


if __name__=='__main__':main()
