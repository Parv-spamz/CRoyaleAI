"""Decompose the real cell head on the previously fixed training-only rows."""
import hashlib
import json
import math
import os
from pathlib import Path
import sys

os.environ['CUDA_VISIBLE_DEVICES']='-1'
os.environ['OMP_NUM_THREADS']='1'
os.environ['MKL_NUM_THREADS']='1'
ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
import numpy as np
import torch
from pipeline.eval_gen import GenRows
from pipeline.model_gen import load_model
from pipeline.train_rocket_curriculum import load_subset
from diagnose_train_rocket import SOURCE,CONTEXTS,CHECKPOINTS


def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def summarize(parts,xy,mask,tags):
    patch,position,bias,full=[np.asarray(parts[k],dtype=np.float64) for k in ('patch','position','bias','full')]
    assert full.shape==patch.shape==position.shape and bias.shape==(full.shape[1],)
    np.testing.assert_allclose(patch+position+bias,full,atol=1e-5,rtol=1e-5)
    cells=np.arange(full.shape[1]);cx=cells%36/36;cy=cells//36/64
    distance=np.hypot((cx[None]-xy[:,0,None])*18,(cy[None]-xy[:,1,None])*32)
    region=distance<=2
    assert np.all(region.any(axis=1))
    modes=dict(full=full,no_patch=position+bias,no_position=patch+bias,
               no_bias=patch+position,patch_only=patch,position_only=position,
               bias_only=np.broadcast_to(bias,full.shape))
    baseline=region[np.arange(len(full)),full.argmax(axis=1)]
    result={}
    for mode,logits in modes.items():
        aim=logits.argmax(axis=1);correct=region[np.arange(len(full)),aim]
        weights=np.exp(logits-logits.max(axis=1,keepdims=True))
        mass=(weights*region).sum(axis=1)/weights.sum(axis=1)
        result[mode]=dict(correct=int(correct[mask].sum()),
            gained=int((~baseline&correct&mask).sum()),lost=int((baseline&~correct&mask).sum()),
            mean_expert_region_mass=float(mass[mask].mean()))
    chosen=full.argmax(axis=1);best=np.where(region,full,-np.inf).argmax(axis=1)
    miss=mask&~baseline;ix=np.flatnonzero(miss)
    contributions={k:p[ix,chosen[ix]]-p[ix,best[ix]] for k,p in
                   [('patch',patch),('position',position),('bias',np.broadcast_to(bias,full.shape))]}
    dominant=np.stack(list(contributions.values()),axis=1).argmax(axis=1) if len(ix) else np.array([],dtype=int)
    margins={k:dict(mean=float(v.mean()) if len(v) else None,dominant_rows=int((dominant==i).sum()))
             for i,(k,v) in enumerate(contributions.items())}
    return dict(rows=int(mask.sum()),replays=len(set(tags[mask].tolist())),modes=result,
                full_misses=int(miss.sum()),miss_margin_contributions=margins)


def main():
    torch.set_num_threads(1)
    output=HERE/'train_aim_decomposition.json'
    out=ROOT/'icebow/data/bench/train_aim_decomposition_20261005'
    assert not output.exists() and not out.exists(),'Fresh outputs required'
    old_path=HERE/'train_rocket_diagnosis.json'
    old=json.loads(old_path.read_text(encoding='utf-8'))
    assert old['split']=='training_only'
    assert sha(SOURCE)==old['source_sha256']
    assert sha(CONTEXTS/'cohorts.npz')==old['contexts_sha256']
    with np.load(SOURCE) as z,np.load(CONTEXTS/'cohorts.npz') as c:
        meta=json.loads(str(z['meta']))
        split,card,gate,rep,tags=[z[k] for k in ('split','y_card','y_gate','rep','tags')]
        train=c['pool']&(split==0);rocket=meta['card_vocab'].index('rocket');tornado=meta['card_vocab'].index('tornado')
        is_rocket=(gate==1)&(card==rocket)
        masks=dict(finish=train&c['finish']&is_rocket,combo_rocket=train&c['combo']&is_rocket,
                   combo_tornado=train&c['combo']&(gate==1)&(card==tornado),
                   ordinary_rocket=train&is_rocket&~c['finish']&~c['combo'])
        rng=np.random.default_rng(20261005)
        selected={k:np.flatnonzero(v) if k=='finish' else
                  np.sort(rng.choice(np.flatnonzero(v),min(int(v.sum()),256),replace=False)) for k,v in masks.items()}
    ids=np.unique(np.concatenate(list(selected.values())))
    assert ids.tolist()==old['selected_row_ids']
    assert hashlib.sha256(ids.tobytes()).hexdigest()==old['selected_ids_sha256']
    assert np.all(split[ids]==0)
    membership={k:np.isin(ids,v) for k,v in selected.items() if k!='combo_tornado'}
    sub,meta=load_subset(SOURCE,ids)
    rows=GenRows(sub,np.arange(len(ids)),'cpu')
    cache=dict(row_ids=ids,xy=sub['y_xy'],split=split[ids],tags=tags[rep[ids]],
               **{'cohort_'+k:v for k,v in membership.items()})
    summaries={};errors={}
    sources={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),old_path,
        HERE/'TRAIN_AIM_DECOMPOSITION_PLAN.md',ROOT/'pipeline/model_gen.py',ROOT/'pipeline/model_v3.py',
        ROOT/'pipeline/eval_gen.py',ROOT/'pipeline/train_rocket_curriculum.py']}
    for arm,relative in CHECKPOINTS.items():
        path=ROOT/relative;assert sha(path)==old['checkpoints'][arm]
        sources[relative]=sha(path)
        model,state=load_model(path,'cpu');model.eval()
        assert model.feature_version==4 and state['args']['grid']=='lattice'
        collected={k:[] for k in ('patch','position','full')}
        with torch.no_grad():
            for lo in range(0,len(ids),64):
                ix=np.arange(lo,min(lo+64,len(ids)));b=rows.batch(ix);enc=model.encode_gen(b)
                query=model.query(torch.cat([enc['g'],model.emb(b['card'],b['form'])],-1))
                spatial=(model.cell_key(enc['p'])*query.unsqueeze(1)).sum(-1)
                patch=spatial[:,model.cell_patch]/math.sqrt(model.d)
                position=(query@model.cell_key(model.cell_emb).t())/math.sqrt(model.d)
                full=model.cell_logits_gen(enc,b['card'],b['form'])
                torch.testing.assert_close(patch+position+model.cell_bias,full,atol=1e-5,rtol=1e-5)
                for key,value in [('patch',patch),('position',position),('full',full)]:
                    collected[key].append(value.numpy())
        parts={k:np.concatenate(v) for k,v in collected.items()}
        parts['bias']=model.cell_bias.detach().numpy().copy()
        prediction=parts['full'].argmax(axis=1)
        xy=np.c_[prediction%36/36,prediction//36/64]
        previous={r['row']:r for r in old['predictions'][arm]}
        assert set(previous)==set(map(int,ids))
        np.testing.assert_allclose(xy,[previous[int(i)]['predicted_xy'] for i in ids],rtol=0,atol=1e-8)
        errors[arm]=float(np.abs(parts['patch']+parts['position']+parts['bias']-parts['full']).max())
        summaries[arm]={k:summarize(parts,sub['y_xy'],mask,cache['tags']) for k,mask in membership.items()}
        for k,value in parts.items():cache[arm+'_'+k]=value
        print(arm,{k:v['modes']['full']['correct'] for k,v in summaries[arm].items()},flush=True)
    assert all(sha(ROOT/p)==h for p,h in sources.items()),'Source changed during diagnosis'
    out.mkdir();file=out/'components.npz';np.savez_compressed(file,**cache)
    report=dict(complete=True,training_only=True,optimization_steps=0,new_models=0,
        source_sha256=old['source_sha256'],contexts_sha256=old['contexts_sha256'],sources=sources,
        selected_ids_sha256=old['selected_ids_sha256'],cache_path=str(file),cache_sha256=sha(file),
        rows=len(ids),max_reconstruction_error=errors,previous_full_aim_matches=True,summaries=summaries,
        limits=['Fixed training diagnosis only; no confirmation predictions or deployment approval.',
                'Teacher-forced distance to expert cast, not Rocket impact or game outcome.',
                'Removing a term changes the decoder; diagnostic ablations are not trained candidates.',
                'Spatial features contain transformed global context, not only local unit information.'])
    output.write_text(json.dumps(report,indent=2,allow_nan=False),encoding='utf-8')
    print('TRAIN_AIM_DECOMPOSITION_COMPLETE')


if __name__=='__main__':main()
