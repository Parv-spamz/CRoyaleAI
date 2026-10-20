"""Data-access/augmentation/migration controls and checkpoint-free CPU smoke."""
import sys
import numpy as np
import torch
from common import *
from metrics import make_masks
from recount import controls as recount_controls,independent_masks
from pipeline.train_gen import losses


def main():
    if (HERE/'prelaunch.json').exists() or (OUT/'draws.npz').exists():raise ValueError('Fresh prelaunch required')
    setup();prepared=check_prepared();train=indices('train');dev=indices('development')
    validate_indices(train,train);validate_indices(dev,dev)
    rejected=0
    for bad in (np.r_[train,dev[0]],train[:-1],train[::-1],np.r_[train,train[0]]):
        try:validate_indices(bad,train)
        except ValueError:rejected+=1
        else:raise AssertionError('Boundary corruption accepted')
    rng=np.random.default_rng(SEED);draws=[];mirrors=[]
    for _ in range(1000):
        draws.append(train[rng.choice(len(train),128)]);mirrors.append(rng.random()<.5)
    draws=np.asarray(draws);mirrors=np.asarray(mirrors)
    assert not np.isin(draws,dev).any()
    # Fixed first draw only, for a small smoke, not a trained candidate.
    ids=np.unique(draws[0]);sub,meta=load_subset(DATA,ids);rows=GenRows(sub,np.arange(len(ids)),'cpu')
    batch=rows.batch(np.searchsorted(ids,draws[0]))
    state=torch.load(INIT,map_location='cpu')
    torch.manual_seed(SEED);v5=initialize(state,5,meta)
    torch.manual_seed(SEED);v6=initialize(state,6,meta)
    for key,tensor in v5.state_dict().items():assert torch.equal(tensor,v6.state_dict()[key])
    assert torch.count_nonzero(v6.projectile_target_spread.weight)==0
    v5.eval();v6.eval()
    with torch.no_grad():
        a=v5(batch,card=batch['card'],form=batch['form']);b=v6(batch,card=batch['card'],form=batch['form'])
        for key in a:assert torch.equal(a[key],b[key]),key
    mirrored=augment(batch,True)
    twice=augment(mirrored,True)
    for key in batch:
        assert torch.allclose(batch[key],twice[key],rtol=0,atol=1e-6),key
    for model in (v5,v6):
        model.train();torch.manual_seed(SEED)
        out=model(mirrored,card=mirrored['card'],form=mirrored['form'])
        if model is v5:first={k:v.detach().clone() for k,v in out.items()}
        else:
            for key in first:assert torch.equal(first[key],out[key]),key
    # Canonical mirror exactly matches the original v6 loss (including dropout).
    torch.manual_seed(SEED);x,xparts=losses(v6,batch,True,meta['grid'])
    torch.manual_seed(SEED);y,yparts=losses(v6,mirrored,False,meta['grid'])
    assert torch.equal(x,y) and xparts==yparts
    del x,y,out,a,b
    smoke={}
    for name,model in [('ordinary_v5',v5),('ordinary_v6',v6)]:
        torch.manual_seed(SEED)
        loss,parts=train_step(model,mirrored,optimizer(model),False,meta['grid'])
        smoke[name]=dict(finite_loss=loss,parts=parts,checkpoint_saved=False,updates=1,counts_as_training=False)
    assert torch.count_nonzero(v6.projectile_target_spread.weight)>0,'Residual has no learning path'
    # Freeze masks/denominators before any policy predictions on development.
    dsub,dmeta=load_subset(DATA,dev);masks,target=make_masks(dev,dsub,dmeta['card_vocab'])
    independent,itarget,_=independent_masks(dev,dsub,dmeta['card_vocab'])
    assert np.array_equal(itarget,target)
    for key in masks:assert np.array_equal(masks[key],independent[key]),key
    np.savez_compressed(OUT/'draws.npz',rows=draws,mirror=mirrors)
    np.savez_compressed(OUT/'development_masks.npz',ids=dev,target=target,**{'mask_'+k:v for k,v in masks.items()})
    denom={k:dict(rows=int(v.sum()),replays=len(set(dsub['rep'][v])),plays=int((v&(dsub['y_gate']==1)).sum())) for k,v in masks.items()}
    result=dict(complete=True,prepared_sha256=sha(HERE/'prepared.json'),sources=frozen_sources(),
        runtime=dict(torch=torch.__version__,python=sys.version,cuda_build=torch.version.cuda,simulator_used=False),
        draws_sha256=sha(OUT/'draws.npz'),masks_sha256=sha(OUT/'development_masks.npz'),
        split_boundary_corruptions_rejected=rejected,zero_initial_residual_equal=True,
        base_dropout_equal=True,mirror_loss_equal=True,finite_smoke=smoke,
        counter_controls=recount_controls(),denominators=denom,checkpoint_saved=False,
        full_training_updates=0,development_policy_predictions=0,final_acceptance=False)
    write(HERE/'prelaunch.json',result)
    print(json.dumps(dict(denominators=denom,smoke=smoke)))
    print('DEVELOPMENT_1_PRELAUNCH_PASS')


if __name__=='__main__':main()
