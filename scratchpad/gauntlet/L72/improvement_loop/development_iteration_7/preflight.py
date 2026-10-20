"""New branch-only training invariant checks on original training rows only."""
import io
import numpy as np
import torch
from experiment import *
from pipeline.model_gen import load_model
def equal(a,b):
    assert a.keys()==b.keys()
    for k in a:assert torch.equal(a[k],b[k]),k
def main():
    assert not (HERE/'prelaunch.json').exists();c.setup();prerequisites();OUT.mkdir(exist_ok=False);frozen=sources()
    with np.load(SCHEDULE) as z:draws=z['rows'];mirrors=z['mirror']
    train=c.indices('train');dev=c.indices('development')
    assert draws.shape==(1000,128) and np.isin(draws,train).all() and not np.isin(draws,dev).any()
    ids=np.unique(draws[0]);sub,meta=c.load_subset(c.DATA,ids);rows=c.GenRows(sub,np.arange(len(ids)),'cpu')
    b=c.augment(rows.batch(np.searchsorted(ids,draws[0])),bool(mirrors[0]))
    state=torch.load(INIT,map_location='cpu',weights_only=True);torch.manual_seed(c.SEED)
    base=c.initialize(state,5,meta).eval();model=initialize(state,meta);assert_base(state,model)
    with torch.no_grad():
        original=base(b,card=b['card'],form=b['form']);equal(original,model(b,card=b['card'],form=b['form']))
        old_loss,old_parts=losses(base,b,False,meta['grid'])
    opt=optimizer(model);v1,p1=train_step(model,b,opt,meta['grid']);assert v1==float(old_loss) and p1==old_parts
    assert torch.count_nonzero(model.projectile_target_spread.weight)>0;assert_base(state,model)
    v2,p2=train_step(model,b,opt,meta['grid']);assert_base(state,model)
    assert any(p.grad is not None and torch.count_nonzero(p.grad)>0 for p in model.projectile_target_in.parameters())
    with torch.no_grad():
        updated=model(b,card=b['card'],form=b['form'])
        for k in ('gate','card','value','wait'):assert torch.equal(updated[k],original[k]),k
        for mode in ('padding','unknown'):
            q=dict(b);q['projectiles']=b['projectiles'].clone()
            if mode=='padding':q['projectiles'].zero_()
            else:q['projectiles'][...,4:6]=-1
            assert torch.count_nonzero(model.target_patches(q))==0
            equal(base(q,card=q['card'],form=q['form']),model(q,card=q['card'],form=q['form']))
    stream=io.BytesIO();torch.save(checkpoint(state,model,dict(torch=str(torch.__version__),smoke_only=True)),stream);stream.seek(0)
    loaded,restored=load_model(stream,'cpu');assert_base(state,loaded)
    assert all(torch.equal(v,loaded.state_dict()[k]) for k,v in model.state_dict().items())
    with np.load(MASKS) as z:assert np.array_equal(dev,z['ids'])
    assert frozen==sources()
    c.write(HERE/'prelaunch.json',dict(complete=True,optimizer_allowed=True,sources=frozen,masks_sha256=c.sha(MASKS),schedule_sha256=c.sha(SCHEDULE),
        initial_checkpoint_sha256=c.sha(INIT),denominators=c.read(FOURTH/'prelaunch.json')['denominators'],
        frozen_base_exact=True,all_initial_outputs_exact=True,heads_after_learning_exact=True,no_target_exact=True,portable_roundtrip=True,
        smoke=dict(losses=[v1,v2],updates=2,counts_as_training=False,checkpoint_saved=False),base_training_mode='eval',trainable_parameters=[n for n,p in model.named_parameters() if p.requires_grad],
        development_policy_predictions=0,full_training_updates=0,deployment_accepted=False))
    print(c.json.dumps(dict(losses=[v1,v2],base_exact=True)));print('FROZEN_PROJECTILE_PREFLIGHT_COMPLETE')
if __name__=='__main__':main()
