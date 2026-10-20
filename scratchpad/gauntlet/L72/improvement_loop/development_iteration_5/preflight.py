"""New representation checks and training-only smoke; no saved checkpoint."""
import io
import numpy as np
import torch
from experiment import *
from controls import check as public_controls
from tower_model import migrate,load_checkpoint
from pipeline.train_gen import losses
from pipeline.model_gen import load_model as production_load

def main():
    assert not (HERE/'prelaunch.json').exists();c.setup();check_prepared()
    OUT.mkdir(exist_ok=False);frozen=sources()
    with np.load(SCHEDULE) as z:draws=z['rows'];mirror=z['mirror']
    train=c.indices('train');dev=c.indices('development')
    assert draws.shape==(1000,128) and np.isin(draws,train).all() and not np.isin(draws,dev).any()
    selected=np.unique(draws[0]);sub,meta=c.load_subset(c.DATA,selected);rows=c.GenRows(sub,np.arange(len(selected)),'cpu')
    b=c.augment(rows.batch(np.searchsorted(selected,draws[0])),bool(mirror[0]))
    state=torch.load(c.INIT,map_location='cpu',weights_only=True);torch.manual_seed(c.SEED)
    base=c.initialize(state,6,meta);model=migrate(state,base)
    assert torch.count_nonzero(model.tower_spatial_spread.weight)==0
    controls=public_controls(model,b)
    for obj in (base,model):
        obj.train();torch.manual_seed(c.SEED)
        with torch.no_grad():
            value=obj(b,card=b['card'],form=b['form'])
            if obj is base:original={k:v.clone() for k,v in value.items()}
            else:
                for k,v in original.items():assert torch.equal(v,value[k]),k
    # New path cannot directly change gate/card heads even when nonzero.
    model.eval()
    with torch.no_grad():
        before=model(b,card=b['card'],form=b['form'])
        model.tower_spatial_spread.weight[:,:,1,1]=.01
        after=model(b,card=b['card'],form=b['form'])
        for key in ('gate','card'):assert torch.equal(before[key],after[key]),key
        assert torch.count_nonzero(model.tower_patches(b))>0
        model.tower_spatial_spread.weight.zero_()
    base.train();model.train();torch.manual_seed(c.SEED)
    with torch.no_grad():base_loss,base_parts=losses(base,b,False,meta['grid'])
    del base,original,before,after,value
    opt=optimizer(model);torch.manual_seed(c.SEED)
    loss1,parts1=c.train_step(model,b,opt,False,meta['grid'])
    assert loss1==float(base_loss) and parts1==base_parts
    assert torch.count_nonzero(model.tower_spatial_spread.weight)>0
    loss2,parts2=c.train_step(model,b,opt,False,meta['grid'])
    assert any(p.grad is not None and torch.count_nonzero(p.grad)>0 for p in model.tower_spatial_in.parameters())
    assert np.isfinite([loss1,loss2]).all()
    config=dict(torch=str(torch.__version__),smoke_only=True)
    stream=io.BytesIO();torch.save(checkpoint(state,model,config),stream);stream.seek(0)
    loaded,restored=load_checkpoint(stream)
    assert type(restored['development_iteration_5']['torch']) is str
    assert all(torch.equal(t,loaded.state_dict()[k]) for k,t in model.state_dict().items())
    stream.seek(0)
    try:production_load(stream,'cpu')
    except RuntimeError as error:
        assert 'tower_spatial_' in str(error)
    else:raise AssertionError('Production loader silently accepted extension')
    # Read existing verified masks only; no repeated policy predictions or mask tuning.
    with np.load(MASKS) as z:assert np.array_equal(dev,z['ids'])
    denoms=c.read(FOURTH/'prelaunch.json')['denominators']
    assert sources()==frozen
    c.write(HERE/'prelaunch.json',dict(complete=True,optimizer_allowed=True,sources=frozen,
        masks_sha256=c.sha(MASKS),schedule_sha256=c.sha(SCHEDULE),denominators=denoms,
        controls=controls,initial_outputs_loss_dropout_identical=True,base_loss=float(base_loss),
        smoke=dict(losses=[loss1,loss2],updates=2,counts_as_training=False,checkpoint_saved=False),
        upstream_gradient_verified=True,strict_extension_roundtrip=True,production_loader_rejected=True,
        development_policy_predictions=0,full_training_updates=0,control='verified ordinary_v6',deployment_accepted=False))
    print(c.json.dumps(dict(smoke_losses=[loss1,loss2],controls=controls)));print('TOWER_PREFLIGHT_COMPLETE')

if __name__=='__main__':main()
