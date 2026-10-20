"""Loss-only isolation/gradient checks and fixed first-training-batch smoke."""
import io
import numpy as np
import torch
from experiment import *
import region_loss
from pipeline.train_gen import losses as original_losses
from pipeline.model_gen import load_model

def main():
    assert not (HERE/'prelaunch.json').exists();c.setup();prerequisites()
    prepared=c.read(HERE/'prepared.json');verified=c.read(HERE/'verified.json')
    assert verified['complete'] and verified['prepared_sha256']==c.sha(HERE/'prepared.json')
    assert prepared['weights_sha256']==c.sha(OUT/'weights.npz');frozen=sources()
    with np.load(SCHEDULE) as z:draws=z['rows'];mirrors=z['mirror']
    train=c.indices('train');dev=c.indices('development')
    assert np.isin(draws,train).all() and not np.isin(draws,dev).any()
    with np.load(OUT/'weights.npz') as z:
        assert np.array_equal(train,z['ids']);weights=torch.as_tensor(z['weights'][np.searchsorted(train,draws[0])])
    ids=np.unique(draws[0]);s,meta=c.load_subset(c.DATA,ids);rows=c.GenRows(s,np.arange(len(ids)),'cpu')
    raw=rows.batch(np.searchsorted(ids,draws[0]));raw['cell_region_weight']=weights
    b=c.augment(raw,bool(mirrors[0]));assert torch.equal(b['cell_region_weight'],weights)
    assert torch.equal(c.augment(raw,True)['cell_region_weight'],weights)
    state=torch.load(c.INIT,map_location='cpu',weights_only=True);torch.manual_seed(c.SEED)
    model=c.initialize(state,6,meta);model.train();ones=torch.ones_like(weights)
    torch.manual_seed(c.SEED);base,parts=original_losses(model,b,False,meta['grid']);base.backward()
    grads={k:p.grad.clone() for k,p in model.named_parameters() if p.grad is not None}
    model.zero_grad(set_to_none=True);torch.manual_seed(c.SEED)
    same,sameparts=region_loss.losses(model,b,meta['grid'],ones)
    assert torch.equal(base,same) and parts==sameparts;same.backward()
    assert all(torch.equal(g,dict(model.named_parameters())[k].grad) for k,g in grads.items())
    model.zero_grad(set_to_none=True);torch.manual_seed(c.SEED);out=model(b,card=b['card'],form=b['form'])
    unit=region_loss.components(out,b,meta['grid'],ones);weighted=region_loss.components(out,b,meta['grid'],weights)
    assert set(unit)==set(weighted)
    for key in unit:
        if key!='cell':assert torch.equal(unit[key],weighted[key]),key
    delta=weighted['cell']-unit['cell'];assert delta!=0
    g=torch.autograd.grad(delta,out['cell'],retain_graph=True)[0];play=b['gate']>.5
    assert torch.count_nonzero(g[~play])==0 and torch.count_nonzero(g[play])>0
    ignored=weights.clone();ignored[~play]=float('nan')
    p=region_loss.components(out,b,meta['grid'],ignored)
    assert all(torch.equal(v,p[k]) for k,v in weighted.items())
    allwait=dict(b,gate=torch.zeros_like(b['gate']))
    assert 'cell' not in region_loss.components(out,allwait,meta['grid'],weights)
    rejected=0
    for bad in (0.,-1.,float('nan')):
        wrong=weights.clone();wrong[torch.nonzero(play)[0,0]]=bad
        try:region_loss.components(out,b,meta['grid'],wrong)
        except AssertionError:rejected+=1
        else:raise AssertionError('Invalid PLAY weight accepted')
    # Scale invariance of a normalized weighted mean is checked within floating precision.
    doubled=region_loss.components(out,b,meta['grid'],weights*2)
    assert torch.allclose(doubled['cell'],weighted['cell'],rtol=0,atol=1e-6)
    del out,g,base,same,grads,unit,weighted,p,doubled,delta
    torch.manual_seed(c.SEED);loss,smoke=region_loss.train_step(model,b,c.optimizer(model),meta['grid'],weights)
    stream=io.BytesIO();torch.save(checkpoint(state,model,dict(torch=str(torch.__version__))),stream);stream.seek(0)
    loaded,recovered=load_model(stream,'cpu')
    assert type(recovered['development_iteration_6']['torch']) is str
    assert all(torch.equal(t,loaded.state_dict()[k]) for k,t in model.state_dict().items())
    with np.load(MASKS) as z:assert np.array_equal(dev,z['ids'])
    assert sources()==frozen
    c.write(HERE/'prelaunch.json',dict(complete=True,optimizer_allowed=True,sources=frozen,
        masks_sha256=c.sha(MASKS),schedule_sha256=c.sha(SCHEDULE),weights_sha256=c.sha(OUT/'weights.npz'),
        denominators=c.read(FOURTH/'prelaunch.json')['denominators'],unit_loss_gradient_exact=True,
        other_terms_exact=True,play_only_cell_gradient=True,wait_weight_ignored=True,mirror_weight_identity=True,
        normalized_weight_scale_invariance=True,invalid_play_weights_rejected=rejected,standard_roundtrip=True,
        smoke=dict(loss=loss,parts=smoke,updates=1,counts_as_training=False,checkpoint_saved=False),
        full_training_updates=0,development_policy_predictions=0,deployment_accepted=False))
    print(c.json.dumps(dict(smoke_loss=loss,weight_range=[float(weights.min()),float(weights.max())])));print('SPATIAL_PREFLIGHT_COMPLETE')

if __name__=='__main__':main()
