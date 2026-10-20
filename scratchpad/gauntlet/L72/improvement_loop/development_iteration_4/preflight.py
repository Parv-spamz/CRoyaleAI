"""New schedule plumbing smoke only; no model evaluation on development."""
import io
import numpy as np
import torch
from experiment import *
from recount_v2 import independent_masks
from extra_masks import make_extra,independently_verify_extra

def main():
    assert not (HERE/'prelaunch.json').exists();c.setup();check_prepared()
    with np.load(OUT/'schedule.npz') as z:draws=z['rows'];mirror=z['mirror']
    train=c.indices('train');dev=c.indices('development')
    assert np.isin(draws,train).all() and not np.isin(draws,dev).any()
    chosen=np.unique(draws[0]);sub,meta=c.load_subset(c.DATA,chosen);rows=c.GenRows(sub,np.arange(len(chosen)),'cpu')
    b=c.augment(rows.batch(np.searchsorted(chosen,draws[0])),bool(mirror[0]))
    state=torch.load(c.INIT,map_location='cpu',weights_only=True);torch.manual_seed(c.SEED)
    model=c.initialize(state,6,meta);torch.manual_seed(c.SEED)
    loss,parts=c.train_step(model,b,c.optimizer(model),False,meta['grid'])
    assert np.isfinite(loss) and all(np.isfinite(x) for x in parts.values())
    stream=io.BytesIO();torch.save(checkpoint(state,model,dict(torch=str(torch.__version__))),stream);stream.seek(0)
    restored=torch.load(stream,map_location='cpu',weights_only=True)
    assert type(restored['development_iteration_4']['torch']) is str
    assert all(torch.equal(t,restored['model'][k]) for k,t in model.state_dict().items())
    s,meta=c.load_subset(c.DATA,dev);cv=meta['card_vocab'];masks,target,_=independent_masks(dev,s,cv)
    with np.load(SECOND_OUT/'schedule.npz') as z:defdev=z['defensive_development']
    masks['defensive_sequence']=np.isin(dev,defdev)
    masks['defensive_rocket']=masks['defensive_sequence']&(s['y_gate']==1)&(s['y_card']==cv.index('rocket'))
    with np.load(SECOND_OUT/'development_masks.npz') as z:
        assert np.array_equal(dev,z['ids']) and np.array_equal(target,z['target'])
        for key,value in masks.items():assert np.array_equal(value,z['mask_'+key])
    extra=make_extra(dev,s,cv);count=independently_verify_extra(dev,s,cv,extra);masks.update(extra)
    denoms={key:dict(rows=int(m.sum()),replays=len(set(s['rep'][m])),plays=int((m&(s['y_gate']==1)).sum())) for key,m in masks.items()}
    assert denoms['phase_late_overtime_clock']['rows']==6422 and denoms['rocket_late_overtime_clock']['rows']==320
    np.savez_compressed(OUT/'development_masks.npz',ids=dev,target=target,**{'mask_'+key:m for key,m in masks.items()})
    c.write(HERE/'prelaunch.json',dict(complete=True,optimizer_allowed=True,sources=sources(),
        masks_sha256=c.sha(OUT/'development_masks.npz'),denominators=denoms,extra_masks_independently_matched=count,
        smoke=dict(loss=loss,parts=parts,updates=1,counts_as_training=False,checkpoint_saved=False),
        primitive_metadata_roundtrip=True,development_policy_predictions=0,full_training_updates=0,
        control='verified ordinary_v6',deployment_accepted=False))
    print(c.json.dumps(dict(smoke_loss=loss,extra_masks=count)));print('PHASE_PREFLIGHT_COMPLETE')

if __name__=='__main__':main()
