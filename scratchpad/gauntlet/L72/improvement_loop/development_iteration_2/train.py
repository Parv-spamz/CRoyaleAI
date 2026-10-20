"""Fixed final-step v5 arm; only the registered training exposure differs."""
import time
import numpy as np
import torch
from experiment import *

def main():
    c.setup();check_active()
    if not torch.cuda.is_available():raise RuntimeError('CUDA required')
    dest=OUT/ARM;dest.mkdir(exist_ok=False)
    ids,sub,meta,rows=c.load_part('train','cuda')
    state=torch.load(c.INIT,map_location='cpu');torch.manual_seed(c.SEED)
    model=c.initialize(state,5,meta).to('cuda');opt=c.optimizer(model)
    with np.load(OUT/'schedule.npz') as z:draws,mirrors=z['rows'],z['mirror']
    positions=np.searchsorted(ids,draws)
    assert np.array_equal(ids[positions],draws) and draws.shape==(1000,128)
    config=dict(arm=ARM,feature_version=5,prelaunch_sha256=c.sha(HERE/'prelaunch.json'),
        schedule_sha256=c.sha(OUT/'schedule.npz'),device='cuda',torch=str(torch.__version__),
        cuda=torch.version.cuda,gpu=torch.cuda.get_device_name(),steps=1000,batch=128,seed=c.SEED,
        loss='unchanged train_gen.losses; shared v6-safe augmentation',
        deployment_accepted=False,development_only=True,simulator_used=False)
    c.write(dest/'run.json',config);torch.manual_seed(c.SEED);start=time.time()
    with (dest/'train.jsonl').open('x') as stream:
        for step,chosen in enumerate(positions,1):
            b=c.augment(rows.batch(chosen),bool(mirrors[step-1]))
            loss,parts=c.train_step(model,b,opt,False,meta['grid'])
            record=dict(step=step,loss=loss,parts=parts,seconds=time.time()-start)
            stream.write(c.json.dumps(record,allow_nan=False)+'\n')
            if step%100==0:stream.flush();print(c.json.dumps(record),flush=True)
    check_active();torch.save(checkpoint(state,model,config),dest/'candidate.pt')
    # Mandatory standard-loader-compatible serialization at the first save.
    loaded=torch.load(dest/'candidate.pt',map_location='cpu',weights_only=True)
    assert all(torch.equal(t,loaded['model'][k]) for k,t in model.state_dict().items())
    c.write(dest/'result.json',dict(complete=True,finite_updates=1000,checkpoint_sha256=c.sha(dest/'candidate.pt'),
        training_rows=len(ids),prediction_rows=0,development_only=True,deployment_accepted=False))
    print('DEFENCE_DEVELOPMENT_FULL_ARM_COMPLETE',flush=True)

if __name__=='__main__':main()
