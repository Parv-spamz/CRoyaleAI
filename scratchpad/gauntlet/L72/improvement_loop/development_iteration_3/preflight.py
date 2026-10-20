"""New-loss equivalence/isolation and training-only smoke before activation."""
import io
import numpy as np
import torch
from experiment import *
import aim_loss
from pipeline.train_gen import losses as original_losses
from recount_v2 import independent_masks

def main():
    if (HERE/'prelaunch.json').exists():raise ValueError('Preserve preflight')
    c.setup();prerequisites();OUT.mkdir(exist_ok=False)
    with np.load(c.OUT/'draws.npz') as z:draws=z['rows'];mirrors=z['mirror']
    train=c.indices('train');dev=c.indices('development')
    assert np.isin(draws,train).all() and not np.isin(draws,dev).any()
    ids=np.unique(draws[0]);s,meta=c.load_subset(c.DATA,ids);rows=c.GenRows(s,np.arange(len(ids)),'cpu')
    b=c.augment(rows.batch(np.searchsorted(ids,draws[0])),bool(mirrors[0]));rid=meta['card_vocab'].index('rocket')
    rocket=(b['gate']>.5)&(b['card']==rid)
    assert rocket.any() and (~rocket).any(),'First registered batch must exercise both cases'
    state=torch.load(c.INIT,map_location='cpu',weights_only=True);torch.manual_seed(c.SEED);model=c.initialize(state,6,meta)
    model.train();torch.manual_seed(c.SEED);base,parts=original_losses(model,b,False,meta['grid']);base.backward()
    grads={k:p.grad.clone() for k,p in model.named_parameters() if p.grad is not None}
    model.zero_grad(set_to_none=True);torch.manual_seed(c.SEED);same,sameparts=aim_loss.losses(model,b,meta['grid'],rid,1.)
    assert torch.equal(base,same) and parts==sameparts;same.backward()
    assert all(torch.equal(g,dict(model.named_parameters())[k].grad) for k,g in grads.items())
    # At fixed outputs, extra loss changes only cell gradients on original PLAY Rockets.
    model.zero_grad(set_to_none=True);torch.manual_seed(c.SEED);out=model(b,card=b['card'],form=b['form'])
    p1=aim_loss.components(out,b,meta['grid'],rid,1.);p3=aim_loss.components(out,b,meta['grid'],rid,3.)
    assert all(torch.equal(v,p3[k]) for k,v in p1.items())
    extra=p3['rocket_cell_extra'];assert extra>0
    g=torch.autograd.grad(extra,out['cell'],retain_graph=True)[0]
    assert torch.count_nonzero(g[~rocket])==0 and torch.count_nonzero(g[rocket])>0
    no_rocket=dict(b,card=torch.where(rocket,torch.zeros_like(b['card']),b['card']))
    wait_rocket=dict(b,gate=torch.where(rocket,torch.zeros_like(b['gate']),b['gate']))
    assert 'rocket_cell_extra' not in aim_loss.components(out,no_rocket,meta['grid'],rid,3.)
    assert 'rocket_cell_extra' not in aim_loss.components(out,wait_rocket,meta['grid'],rid,3.)
    torch.manual_seed(c.SEED);loss,smokeparts=aim_loss.train_step(model,b,c.optimizer(model),meta['grid'],rid)
    config=dict(torch=str(torch.__version__),rocket_cell_weight=3.,steps=1000,development_only=True)
    stream=io.BytesIO();torch.save(checkpoint(state,model,config),stream);stream.seek(0)
    recovered=torch.load(stream,map_location='cpu',weights_only=True)
    assert all(torch.equal(t,recovered['model'][k]) for k,t in model.state_dict().items())
    dsub,dmeta=c.load_subset(c.DATA,dev);masks,target,_=independent_masks(dev,dsub,dmeta['card_vocab'])
    with np.load(SECOND_OUT/'schedule.npz') as z:defdev=set(map(int,z['defensive_development']))
    masks['defensive_sequence']=np.array([int(i) in defdev for i in dev])
    masks['defensive_rocket']=masks['defensive_sequence']&(dsub['y_gate']==1)&(dsub['y_card']==rid)
    with np.load(SECOND_OUT/'development_masks.npz') as z:
        assert np.array_equal(dev,z['ids']) and np.array_equal(target,z['target'])
        for key,m in masks.items():assert np.array_equal(m,z['mask_'+key])
    denoms={k:dict(rows=int(m.sum()),replays=len(set(dsub['rep'][m])),plays=int((m&(dsub['y_gate']==1)).sum())) for k,m in masks.items()}
    c.write(HERE/'prelaunch.json',dict(complete=True,optimizer_allowed=True,sources=sources(),denominators=denoms,
        loss1_exact=True,gradients1_exact=True,noncell_terms_unchanged=True,nonrocket_cell_gradient_zero=True,
        rocket_cell_gradient_nonzero=True,no_rocket_and_wait_controls_passed=True,primitive_metadata_roundtrip=True,
        smoke=dict(loss=loss,parts=smokeparts,counts_as_training=False,checkpoint_saved=False,updates=1),
        first_batch_expert_rockets=int(rocket.sum()),development_policy_predictions=0,full_training_updates=0,deployment_accepted=False))
    print(c.json.dumps(dict(smoke_loss=loss,expert_rockets=int(rocket.sum()),denominators=denoms['rocket'])))
    print('ROCKET_AIM_PREFLIGHT_COMPLETE')

if __name__=='__main__':main()
