"""Training rows only; fixed-weight CPU ablation, no optimizer or checkpoint output."""
import hashlib,json,os,sys
from pathlib import Path
from zipfile import ZipFile
os.environ['CUDA_VISIBLE_DEVICES']='-1'
os.environ['OMP_NUM_THREADS']='1'
os.environ['MKL_NUM_THREADS']='1'
ROOT=Path(__file__).resolve().parents[5]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
import numpy as np
import torch
from pipeline.expert_context import load_contexts
from pipeline.eval_gen import GenRows
from pipeline.model_gen import load_model
from pipeline.opp_elixir_count import card_cost
from pipeline.rocket_teaching import sha
from pipeline.train_rocket_curriculum import take,load_subset

SOURCE=ROOT/'icebow/data/pipeline/gen_dataset_v31_public.npz'
DATA=ROOT/'icebow/data/bench/spawner_identity_20261005/gen_dataset_v5_public.npz'
CONTEXTS=ROOT/'icebow/data/bench/context_teaching_20261005'
CORRECTION=DATA.parent/'manifest.json'
CACHE=ROOT/'icebow/data/bench/train_barrel_residual_20261005/predictions.npz'
ARMS=('v5_rocket_barrel','v6_rocket_barrel','v6_rocket_both')


def summary(p,ids,selection,sub,target,cv):
    play=sub['y_gate']==1;called=(p['gate']>.35)&p['allowed'].any(1)
    card_ok=p['chosen']==sub['y_card']
    xy=np.c_[p['expert_logits'].argmax(-1)%36/36,p['expert_logits'].argmax(-1)//36/64]
    dist=np.linalg.norm((xy-sub['y_xy'])*[18,32],axis=1)
    aim=dist<=1
    action=np.where(play,called&card_ok&aim,~called)
    same=(p['log_logits'].argmax(-1)%36/36<.5)==(target[:,0]<.5)
    fired=called&(p['chosen']==cv.index('the-log'))
    values={'action':action,'card':card_ok&play,'aim':aim&play,'log_fired':fired}
    out={}
    for name,rows in selection.items():
        m=np.isin(ids,rows)
        out[name]=dict(rows=int(m.sum()),plays=int((play&m).sum()),
            **{k:int((v&m).sum()) for k,v in values.items()})
        if name in ('single_pro_log','single_other_play','single_wait'):
            out[name].update(forced_log_same_lane=int((same&m).sum()),
                gated_correct_lane=int((fired&same&m).sum()),gated_wrong_lane=int((fired&~same&m).sum()))
    return out


def main():
    assert not (HERE/'report.json').exists() and not (HERE/'selection.json').exists() and not CACHE.exists()
    torch.set_num_threads(1)
    c,manifest,meta,binding=load_contexts(CONTEXTS,DATA,SOURCE,CORRECTION)
    cv=meta['card_vocab'];log=cv.index('the-log');barrel=cv.index('goblin-barrel')
    with np.load(SOURCE) as z:
        split,rep,tags,gate,card,xy=[z[k] for k in ('split','rep','tags','y_gate','y_card','y_xy')]
        pool=np.flatnonzero(c['pool']&(split==0))
    with ZipFile(SOURCE) as z:
        obj=take(z,'projectiles',pool);hand=take(z,'hand_card',pool);sc=take(z,'sc',pool)
    valid=(obj[:,:,0]>0)&np.isfinite(obj[:,:,4:6]).all(-1)&(obj[:,:,4:6]>=0).all(-1)&(obj[:,:,4:6]<=1).all(-1)
    enemy=(obj[:,:,0]==barrel)&(obj[:,:,1]==1);target=obj[np.arange(len(pool)),enemy.argmax(1),4:6]
    single=(enemy.sum(1)==1)&np.isfinite(target).all(-1)&(target[:,0]>=0)&(target[:,0]<=1)&(target[:,1]>=.5)&(target[:,1]<=1)&((target[:,0]<.4)|(target[:,0]>.6))
    costs=np.array([card_cost(s.replace('-','_')) or 0 for s in cv])
    allowed=(hand>0)&(costs[hand]<=np.floor(sc[:,3]*10+1e-3)[:,None])
    playable=single&((hand==log)&allowed).any(1)
    pro=playable&(gate[pool]==1)&(card[pool]==log)&((xy[pool,0]<.5)==(target[:,0]<.5))
    masks=dict(single_pro_log=pro,single_other_play=playable&(gate[pool]==1)&(card[pool]!=log),
        single_wait=playable&(gate[pool]==0),multiple_barrel=enemy.sum(1)>1,
        ambiguous_barrel=enemy.any(1)&~single,other_projectile=~enemy.any(1)&valid.any(1),
        no_valid_target=~valid.any(1))
    rng=np.random.default_rng(20261005);selection={};sizes={}
    for name,m in masks.items():
        rows=pool[m];replays=np.unique(rep[rows]);chosen=rng.permutation(replays)[:200]
        selected=np.sort(np.array([rng.choice(rows[rep[rows]==r]) for r in chosen],np.int64))
        selection[name]=selected.tolist();sizes[name]=dict(full_rows=len(rows),full_replays=len(replays),selected=len(selected))
    ids=np.unique(np.concatenate([np.array(v,np.int64) for v in selection.values()]))
    assert len(ids) and np.all(split[ids]==0)
    assert not set(rep[ids])&set(rep[c['pool']&(split!=0)])
    sources={str(p.relative_to(ROOT)):sha(p) for p in (SOURCE,DATA,CORRECTION,CONTEXTS/'cohorts.npz',CONTEXTS/'manifest.json',HERE/'PLAN.md',Path(__file__),ROOT/'pipeline/model_gen.py',ROOT/'pipeline/eval_gen.py',ROOT/'pipeline/train_rocket_curriculum.py')}
    paths={arm:ROOT/f'icebow/data/bench/expert_context_20261005/{arm}/candidate.pt' for arm in ARMS}
    hashes={arm:sha(p) for arm,p in paths.items()}
    selected_report=dict(split='training_only',seed=20261005,ids=ids.tolist(),selection=selection,sizes=sizes,sources=sources,checkpoints=hashes,
        replays=[str(tags[r]) for r in sorted(set(rep[ids]))],new_model=False,optimizer_updates=0)
    (HERE/'selection.json').write_text(json.dumps(selected_report,indent=2))
    print('TRAIN_RESIDUAL_SELECTION_BOUND',len(ids),json.dumps(sizes),flush=True)
    sub,meta=load_subset(DATA,ids);rows=GenRows(sub,np.arange(len(ids)),'cpu')
    assert np.array_equal(sub['y_gate'],gate[ids]) and np.array_equal(sub['y_card'],card[ids]) and np.array_equal(sub['y_xy'],xy[ids]) and np.all(sub['split']==0)
    target=sub['projectiles'][np.arange(len(ids)),((sub['projectiles'][:,:,0]==barrel)&(sub['projectiles'][:,:,1]==1)).argmax(1),4:6]
    allow=(sub['hand_card']>0)&(costs[sub['hand_card']]<=np.floor(sub['sc'][:,3]*10+1e-3)[:,None])
    cache=dict(ids=ids,allowed=allow,expert_gate=sub['y_gate'],expert_card=sub['y_card'],expert_xy=sub['y_xy'],target=target)
    summaries={};invariants={}
    for arm,path in paths.items():
        model,state=load_model(path,'cpu');model.eval();version=model.feature_version
        assert state['card_vocab']==cv and state['args']['grid']=='lattice' and version==(6 if arm.startswith('v6') else 5)
        # No checkpoint tensors are assigned or optimized. The property toggle only skips the final p residual.
        modes=('full','residual_off') if version==6 else ('full',)
        accum={mode:{k:[] for k in ('gate','chosen','expert_logits','log_logits','residual_max')} for mode in modes}
        with torch.inference_mode():
            for lo in range(0,len(ids),64):
                ix=np.arange(lo,min(lo+64,len(ids)));b=rows.batch(ix);enc=model.encode_gen(b)
                base_enc=None
                if version==6:
                    try:
                        model.feature_version=5;base_enc=model.encode_gen(b)
                    finally:model.feature_version=version
                    assert torch.equal(enc['g'],base_enc['g'])
                for mode in modes:
                    e=enc if mode=='full' else base_enc;h=model.heads_gen(e,b)
                    slot=h['card'].masked_fill(~torch.as_tensor(allow[ix]),-torch.inf).argmax(-1).numpy()
                    log_card=torch.full_like(b['card'],log)
                    vals=dict(gate=h['gate'].sigmoid().numpy(),chosen=sub['hand_card'][ix,slot],
                        expert_logits=model.cell_logits_gen(e,b['card'],b['form']).numpy(),
                        log_logits=model.cell_logits_gen(e,log_card,torch.zeros_like(log_card)).numpy(),
                        residual_max=(enc['p']-base_enc['p']).abs().flatten(1).max(1).values.numpy() if version==6 else np.zeros(len(ix)))
                    for k,v in vals.items():accum[mode][k].append(v.copy())
        ps={mode:{k:np.concatenate(v) for k,v in a.items()} for mode,a in accum.items()}
        if version==6:
            a,b=ps['full'],ps['residual_off']
            assert np.array_equal(a['gate'],b['gate']) and np.array_equal(a['chosen'],b['chosen'])
            mask=np.isin(ids,selection['no_valid_target'])
            assert np.all(a['residual_max'][mask]==0)
            assert np.array_equal(a['log_logits'][mask],b['log_logits'][mask]) and np.array_equal(a['expert_logits'][mask],b['expert_logits'][mask])
            invariants[arm]=dict(gate_unchanged=True,card_unchanged=True,zero_target_rows=int(mask.sum()),zero_target_logits_unchanged=True,max_residual=float(a['residual_max'].max()))
        for mode,p in ps.items():
            name=arm+'__'+mode
            for k,v in p.items():
                assert np.isfinite(v).all();cache[name+'__'+k]=v
            summaries[name]=summary(dict(p,allowed=allow),ids,selection,sub,target,cv)
            print(name,json.dumps(summaries[name]['single_pro_log']),flush=True)
        assert sha(path)==hashes[arm]
    CACHE.parent.mkdir(parents=True,exist_ok=True);np.savez_compressed(CACHE,**cache)
    for p,h in sources.items():assert sha(ROOT/p)==h
    report=dict(complete=True,selection_sha256=sha(HERE/'selection.json'),cache=str(CACHE.relative_to(ROOT)),cache_sha256=sha(CACHE),
        conditions=list(summaries),summaries=summaries,invariants=invariants,optimizer_updates=0,new_checkpoint=False,live_changed=False,
        limits=['Training-only fixed-weight diagnosis; not unseen performance or acceptance.','Expert/target geometry is not damage or verified historical landing.','Between-checkpoint changes include weight and exposure effects.'])
    (HERE/'report.json').write_text(json.dumps(report,indent=2));print('TRAIN_BARREL_RESIDUAL_COMPLETE')


if __name__=='__main__':main()
