"""Only generic spatial cell-loss weighting changes; ordinary expert exposure."""
import time
import numpy as np
import torch
from experiment import *
from region_loss import train_step

def main():
    c.setup();check_active();assert torch.cuda.is_available()
    dest=OUT/ARM;dest.mkdir(exist_ok=False);ids,sub,meta,rows=c.load_part('train','cuda')
    state=torch.load(c.INIT,map_location='cpu',weights_only=True);torch.manual_seed(c.SEED)
    model=c.initialize(state,6,meta).to('cuda');opt=c.optimizer(model)
    with np.load(SCHEDULE) as z:draws=z['rows'];mirror=z['mirror']
    with np.load(OUT/'weights.npz') as z:
        assert np.array_equal(ids,z['ids']);row_weights=torch.as_tensor(z['weights'],device='cuda')
    positions=np.searchsorted(ids,draws);assert np.array_equal(ids[positions],draws) and draws.shape==(1000,128)
    config=dict(arm=ARM,feature_version=6,prelaunch_sha256=c.sha(HERE/'prelaunch.json'),schedule_sha256=c.sha(SCHEDULE),
        device='cuda',torch=str(torch.__version__),cuda=torch.version.cuda,gpu=torch.cuda.get_device_name(),
        steps=1000,batch=128,seed=c.SEED,loss='fixed all-card spatial-frequency cell CE; other terms unchanged',weights_sha256=c.sha(OUT/'weights.npz'),
        development_only=True,deployment_accepted=False,simulator_used=False)
    c.write(dest/'run.json',config);torch.manual_seed(c.SEED);start=time.time()
    with (dest/'train.jsonl').open('x') as stream:
        for step,selected in enumerate(positions,1):
            b=c.augment(rows.batch(selected),bool(mirror[step-1]))
            loss,parts=train_step(model,b,opt,meta['grid'],row_weights[selected])
            record=dict(step=step,loss=loss,parts=parts,seconds=time.time()-start)
            stream.write(c.json.dumps(record,allow_nan=False)+'\n')
            if step%100==0:stream.flush();print(c.json.dumps(record),flush=True)
    check_active();torch.save(checkpoint(state,model,config),dest/'candidate.pt')
    loaded=torch.load(dest/'candidate.pt',map_location='cpu',weights_only=True)
    assert all(torch.equal(t,loaded['model'][k]) for k,t in model.state_dict().items())
    c.write(dest/'result.json',dict(complete=True,finite_updates=1000,checkpoint_sha256=c.sha(dest/'candidate.pt'),
        training_rows=len(ids),prediction_rows=0,development_only=True,deployment_accepted=False))
    print('SPATIAL_FULL_ARM_COMPLETE',flush=True)

if __name__=='__main__':main()
