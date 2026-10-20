"""Matched training-only spawner decomposition; CPU inference, no optimizer."""
import hashlib
import json
import os
from pathlib import Path
import sys

os.environ['CUDA_VISIBLE_DEVICES']='-1'
os.environ['OMP_NUM_THREADS']='1'
os.environ['MKL_NUM_THREADS']='1'
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
import numpy as np
import torch
from pipeline import vocab
from pipeline.eval_gen import GenRows
from pipeline.expert_context import probabilities
from pipeline.model_gen import load_model
from pipeline.opp_elixir_count import card_cost
from pipeline.rocket_teaching import sha
from pipeline.train_rocket_curriculum import load_subset

HERE=Path(__file__).resolve().parent
SOURCE=ROOT/'icebow/data/pipeline/gen_dataset_v31_public.npz'
CORRECTED=ROOT/'icebow/data/bench/spawner_identity_20261005/gen_dataset_v5_public.npz'
CONTEXTS=ROOT/'icebow/data/bench/context_teaching_20261005/cohorts.npz'
FAMILIES=('witch','night_witch','furnace')
R1E='icebow/data/bench/rl_royale/rseries_r1e31/rseries_r1e31_u0155.pt'
ARMS={
    'r1e_original':(R1E,False),
    'r1e_corrected':(R1E,True),
    **{n:(f'icebow/data/bench/expert_context_20261005/{n}/candidate.pt',n.startswith('v5'))
       for n in ('v4_uniform','v5_uniform','v4_rocket','v5_rocket')},
}


def row_presence(tokens,off,key):
    hit=(tokens[:,0]==vocab.unit_id(key)) & (tokens[:,2]==1)
    prefix=np.r_[0,np.cumsum(hit)]
    return (prefix[off[1:]]-prefix[off[:-1]])>0


def main():
    torch.set_num_threads(1)
    out=HERE/'train_spawner_diagnosis.json'
    cache=HERE/'train_spawner_predictions.npz'
    if out.exists() or cache.exists():raise ValueError('Fresh diagnosis output required')
    with np.load(SOURCE) as z,np.load(CONTEXTS) as c:
        split,gate,rep,tags,off=[z[k] for k in ('split','y_gate','rep','tags','off')]
        cohorts={k:c[k] for k in c.files}
        tok=z['tok']
        masks={k:row_presence(tok,off,k) & cohorts['pool'] & (split==0) for k in FAMILIES}
    del tok
    rng=np.random.default_rng(20261005)
    selected={};strata={}
    for family,mask in masks.items():
        for play in (0,1):
            ix=np.flatnonzero(mask & (gate==play))
            replay_ids=rng.permutation(np.unique(rep[ix]))[:200]
            choices=np.asarray([rng.choice(ix[rep[ix]==r]) for r in replay_ids],dtype=np.int64)
            name=family+('_play' if play else '_wait')
            selected[name]=np.sort(choices)
            strata[name]=dict(full_rows=len(ix),full_replays=len(np.unique(rep[ix])),
                              selected_rows=len(choices))
    ids=np.unique(np.concatenate(list(selected.values())))
    if not len(ids) or np.any(split[ids]!=0):raise ValueError('Training-only selection required')
    print('TRAIN_SPAWNER_ROWS',len(ids),flush=True)
    exposure={arm:{k:float(probabilities(cohorts,split,arm)[m].sum()*128000)
                   for k,m in masks.items()} for arm in ('uniform','rocket')}
    old,meta=load_subset(SOURCE,ids)
    new,new_meta=load_subset(CORRECTED,ids)
    if meta['card_vocab']!=new_meta['card_vocab']:raise ValueError('Vocabulary drift')
    for key in old:
        if key not in ('tok','unit_form') and not np.array_equal(old[key],new[key]):
            raise ValueError('Nonidentity input changed: '+key)
    changed=old['tok'][:,0]!=new['tok'][:,0]
    prefix=np.r_[0,np.cumsum(changed)]
    changed_rows=(prefix[old['off'][1:]]-prefix[old['off'][:-1]])>0
    parents={k:row_presence(new['tok'],new['off'],k) for k in FAMILIES}
    positions={k:np.isin(ids,v) for k,v in selected.items()}
    cv=meta['card_vocab']
    costs=np.array([card_cost(k.replace('-','_')) or 0 for k in cv])
    allowed=(old['hand_card']>0) & (costs[old['hand_card']]<=np.floor(old['sc'][:,3]*10+1e-3)[:,None])
    play=old['y_gate']==1
    summaries={};predictions={};hashes={}
    for name,(relative,corrected) in ARMS.items():
        sub=new if corrected else old
        model,state=load_model(ROOT/relative,'cpu');model.eval()
        if state['args']['grid']!='lattice' or model.feature_version not in (4,5):
            raise ValueError('Unexpected model contract')
        rows=GenRows(sub,np.arange(len(ids)),'cpu')
        gates=[];cards=[];cells=[]
        with torch.no_grad():
            for lo in range(0,len(ids),64):
                ix=np.arange(lo,min(lo+64,len(ids)));b=rows.batch(ix)
                enc=model.encode_gen(b);h=model.heads_gen(enc,b)
                slot=h['card'].masked_fill(~torch.as_tensor(allowed[ix]),-torch.inf).argmax(-1).numpy()
                gates.extend(h['gate'].sigmoid().numpy())
                cards.extend(sub['hand_card'][ix,slot])
                cells.extend(model.cell_logits_gen(enc,b['card'],b['form']).argmax(-1).numpy())
        gates=np.asarray(gates);cards=np.asarray(cards);cells=np.asarray(cells)
        xy=np.c_[cells%36/36,cells//36/64]
        distance=np.linalg.norm((xy-sub['y_xy'])*[18,32],axis=1)
        called=(gates>.35) & allowed.any(1)
        card_ok=(cards==sub['y_card']) & allowed.any(1)
        action=np.where(play,called & card_ok & (distance<=1),~called)
        pred=dict(gate=gates,chosen_card=cards,expert_cell=cells,action=action,
                  card_correct=card_ok,aim_within_one=distance<=1,called=called)
        predictions.update({name+'__'+k:v for k,v in pred.items()})
        summaries[name]={}
        for family in FAMILIES:
            for phase in ('play','wait'):
                mask=positions[family+'_'+phase]
                summaries[name][family+'_'+phase]=dict(rows=int(mask.sum()),
                    replays=len(np.unique(rep[ids[mask]])),changed_rows=int((mask & changed_rows).sum()),
                    corrected_parent_present=int((mask & parents[family]).sum()),
                    called=int(called[mask].sum()),card_correct=int(card_ok[mask & play].sum()),
                    forced_aim_within_one=int((distance[mask & play]<=1).sum()),
                    action_correct=int(action[mask].sum()))
        hashes[name]=sha(ROOT/relative)
        print(name,json.dumps(summaries[name]),flush=True)
    np.savez_compressed(cache,ids=ids,rep=rep[ids],split=split[ids],tags=tags,
        y_gate=old['y_gate'],y_card=old['y_card'],y_xy=old['y_xy'],allowed=allowed,
        changed_rows=changed_rows,**{k+'__mask':m for k,m in positions.items()},
        **{k+'__parent':m for k,m in parents.items()},**predictions)
    pairs={}
    for a,b in [('r1e_corrected','r1e_original'),('v4_uniform','r1e_original'),
                ('v5_uniform','v4_uniform'),('v4_rocket','v4_uniform'),
                ('v5_rocket','v5_uniform'),('v5_rocket','v4_rocket')]:
        aa=predictions[a+'__action'];bb=predictions[b+'__action']
        pairs[a+'_vs_'+b]={k:dict(rows=int(m.sum()),gains=int((m & aa & ~bb).sum()),
            losses=int((m & ~aa & bb).sum())) for k,m in positions.items()}
    report=dict(schema=1,split='training_only',seed=20261005,rows=len(ids),strata=strata,
        selection='one random row per replay per family/gate, capped200 per stratum',
        source_sha256=sha(SOURCE),corrected_sha256=sha(CORRECTED),contexts_sha256=sha(CONTEXTS),
        script_sha256=sha(__file__),checkpoint_hashes=hashes,predictions_sha256=sha(cache),
        expected_exposures_in_128000_draws=exposure,summaries=summaries,paired_action_flips=pairs,
        limitations=['Training diagnosis, not generalization or acceptance.',
            'Original enemy family masks may represent parent or misidentified child.',
            'Strata oversample rare families and split PLAY/WAIT; no pooled population score.',
            'Expert-forced aim is not actual card-conditioned gameplay or impact.',
            'R1e corrected is an explicit zero-adaptation diagnostic, not a deployable checkpoint.'])
    out.write_text(json.dumps(report,indent=2,allow_nan=False))
    print('TRAIN_SPAWNER_DIAGNOSIS_COMPLETE')


if __name__=='__main__':main()
