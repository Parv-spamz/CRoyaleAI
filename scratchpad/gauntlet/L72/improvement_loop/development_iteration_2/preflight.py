"""Check only new curriculum plumbing, masks and serialization, no full training."""
import io
import numpy as np
import torch
from experiment import *
from recount_v2 import independent_masks

def main():
    if (HERE/'prelaunch.json').exists():raise ValueError('Preserve existing prelaunch')
    c.setup();check_prepared()
    with np.load(OUT/'schedule.npz') as z:
        draws=z['rows'];mirror=z['mirror'];defdev=z['defensive_development'];deftrain=z['defensive_training']
    train=c.indices('train');dev=c.indices('development')
    assert np.isin(draws,train).all() and not np.isin(draws,dev).any()
    assert np.isin(deftrain,train).all() and np.isin(defdev,dev).all()
    # Training-only first scheduled batch. No model prediction on development.
    selected=np.unique(draws[0]);sub,meta=c.load_subset(c.DATA,selected)
    rows=c.GenRows(sub,np.arange(len(selected)),'cpu')
    b=c.augment(rows.batch(np.searchsorted(selected,draws[0])),bool(mirror[0]))
    state=torch.load(c.INIT,map_location='cpu',weights_only=True)
    torch.manual_seed(c.SEED);model=c.initialize(state,5,meta)
    torch.manual_seed(c.SEED);loss,parts=c.train_step(model,b,c.optimizer(model),False,meta['grid'])
    assert np.isfinite(loss) and all(np.isfinite(x) for x in parts.values())
    config=dict(torch=str(torch.__version__),steps=1000,development_only=True,deployment_accepted=False)
    stream=io.BytesIO();torch.save(checkpoint(state,model,config),stream);stream.seek(0)
    restored=torch.load(stream,map_location='cpu',weights_only=True)
    assert type(restored['development_iteration_2']['torch']) is str
    assert all(torch.equal(t,restored['model'][k]) for k,t in model.state_dict().items())
    # Original masks are independently rebuilt, only two membership masks added.
    dsub,dmeta=c.load_subset(c.DATA,dev)
    masks,target,_=independent_masks(dev,dsub,dmeta['card_vocab'])
    with np.load(c.OUT/'development_masks.npz') as z:
        assert np.array_equal(dev,z['ids']) and np.array_equal(target,z['target'])
        for key,m in masks.items():assert np.array_equal(m,z['mask_'+key])
    masks['defensive_sequence']=np.isin(dev,defdev)
    masks['defensive_rocket']=masks['defensive_sequence']&(dsub['y_gate']==1)&(dsub['y_card']==dmeta['card_vocab'].index('rocket'))
    denoms={k:dict(rows=int(m.sum()),replays=len(set(dsub['rep'][m])),plays=int((m&(dsub['y_gate']==1)).sum())) for k,m in masks.items()}
    assert denoms['defensive_sequence']['rows']==8183 and denoms['defensive_rocket']['rows']==223
    np.savez_compressed(OUT/'development_masks.npz',ids=dev,target=target,**{'mask_'+k:m for k,m in masks.items()})
    c.write(HERE/'prelaunch.json',dict(complete=True,optimizer_allowed=True,trainable=True,
        activation='only development_iteration_2 defense_sequence_v5 fixed1000 updates',
        sources=sources(),masks_sha256=c.sha(OUT/'development_masks.npz'),denominators=denoms,
        finite_smoke=dict(loss=loss,parts=parts,updates=1,counts_as_training=False,checkpoint_saved=False),
        primitive_metadata_roundtrip=True,weight_bytes_equal=True,development_policy_predictions=0,
        full_training_updates=0,control='verified iteration1 ordinary_v5',deployment_accepted=False))
    print(c.json.dumps(dict(smoke_loss=loss,defensive=denoms['defensive_sequence'],rockets=denoms['defensive_rocket'])))
    print('DEFENCE_DEVELOPMENT_PREFLIGHT_COMPLETE')

if __name__=='__main__':main()
