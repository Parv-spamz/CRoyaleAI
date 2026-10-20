"""New aim trainability checks; original training rows only, no saved model."""
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
    for name,p in model.named_parameters():
        if p.requires_grad:assert p.grad is not None and torch.isfinite(p.grad).all(),name
    for prefix in ('query.','cell_key.weight','cell_emb','cell_bias','projectile_target_in.','projectile_target_spread.'):
        assert any(p.grad is not None and torch.count_nonzero(p.grad)>0 for n,p in model.named_parameters() if n.startswith(prefix)),prefix
    with torch.no_grad():
        updated=model(b,card=b['card'],form=b['form'])
        for k in ('gate','card','value','wait'):assert torch.equal(updated[k],original[k]),k
        no_target_changes={}
        for mode in ('padding','unknown'):
            q=dict(b);q['projectiles']=b['projectiles'].clone()
            if mode=='padding':q['projectiles'].zero_()
            else:q['projectiles'][...,4:6]=-1
            assert torch.count_nonzero(model.target_patches(q))==0
            before=base(q,card=q['card'],form=q['form']);after=model(q,card=q['card'],form=q['form'])
            for k in ('gate','card','value','wait'):assert torch.equal(before[k],after[k]),(mode,k)
            assert not torch.equal(before['cell'],after['cell']);no_target_changes[mode]=int(torch.count_nonzero(before['cell']!=after['cell']))
    stream=io.BytesIO();torch.save(checkpoint(state,model,dict(torch=str(torch.__version__),smoke_only=True)),stream);stream.seek(0)
    loaded,restored=load_model(stream,'cpu');assert_base(state,loaded)
    assert all(torch.equal(v,loaded.state_dict()[k]) for k,v in model.state_dict().items())
    with torch.no_grad():
        saved=loaded.gate_head.bias.clone();loaded.gate_head.bias.add_(1)
        try:assert_base(state,loaded)
        except AssertionError:pass
        else:raise AssertionError('Frozen-head corruption accepted')
        loaded.gate_head.bias.copy_(saved);assert_base(state,loaded)
    with np.load(MASKS) as z:assert np.array_equal(dev,z['ids'])
    assert frozen==sources()
    c.write(HERE/'prelaunch.json',dict(complete=True,optimizer_allowed=True,sources=frozen,masks_sha256=c.sha(MASKS),schedule_sha256=c.sha(SCHEDULE),
        initial_checkpoint_sha256=c.sha(INIT),denominators=c.read(FOURTH/'prelaunch.json')['denominators'],
        frozen_decision_path_exact=True,all_initial_outputs_exact=True,heads_after_learning_exact=True,no_target_aim_can_change=no_target_changes,
        portable_roundtrip=True,frozen_head_corruption_rejected=True,
        smoke=dict(losses=[v1,v2],updates=2,counts_as_training=False,checkpoint_saved=False),base_training_mode='eval',trainable_parameters=[n for n,p in model.named_parameters() if p.requires_grad],
        development_policy_predictions=0,full_training_updates=0,deployment_accepted=False))
    print(c.json.dumps(dict(losses=[v1,v2],no_target_aim_can_change=no_target_changes)));print('AIM_HEADS_PREFLIGHT_COMPLETE')
if __name__=='__main__':main()
