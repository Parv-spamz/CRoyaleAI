"""Fixed1000 aim-only updates; train membership only, no evaluation."""
import time
import numpy as np
import torch
from experiment import *
def main():
    c.setup();check_active();assert torch.cuda.is_available();dest=OUT/ARM;dest.mkdir(exist_ok=False)
    ids,sub,meta,rows=c.load_part('train','cuda');state=torch.load(INIT,map_location='cpu',weights_only=True);torch.manual_seed(c.SEED)
    model=initialize(state,meta).to('cuda');opt=optimizer(model);assert_base(state,model)
    with np.load(SCHEDULE) as z:draws=z['rows'];mirror=z['mirror']
    pos=np.searchsorted(ids,draws);assert draws.shape==(1000,128) and np.array_equal(ids[pos],draws)
    config=dict(arm=ARM,feature_version=6,prelaunch_sha256=c.sha(HERE/'prelaunch.json'),schedule_sha256=c.sha(SCHEDULE),initial_checkpoint_sha256=c.sha(INIT),
        torch=str(torch.__version__),cuda=torch.version.cuda,gpu=torch.cuda.get_device_name(),device='cuda',steps=1000,batch=128,seed=c.SEED,decision_path_frozen=True,base_mode='eval',
        loss='original expert losses; gradients only through existing aim head and generic projectile target modules',development_only=True,deployment_accepted=False,simulator_used=False)
    c.write(dest/'run.json',config);torch.manual_seed(c.SEED);start=time.time()
    with (dest/'train.jsonl').open('x') as f:
        for step,sel in enumerate(pos,1):
            b=c.augment(rows.batch(sel),bool(mirror[step-1]));loss,parts=train_step(model,b,opt,meta['grid'])
            record=dict(step=step,loss=loss,parts=parts,seconds=time.time()-start);f.write(c.json.dumps(record,allow_nan=False)+'\n')
            if step%100==0:assert_base(state,model);f.flush();print(c.json.dumps(record),flush=True)
    assert_base(state,model);check_active();torch.save(checkpoint(state,model,config),dest/'candidate.pt')
    loaded=torch.load(dest/'candidate.pt',map_location='cpu',weights_only=True)
    assert all(torch.equal(v,loaded['model'][k]) for k,v in state['model'].items() if not aim_parameter(k))
    c.write(dest/'result.json',dict(complete=True,finite_updates=1000,checkpoint_sha256=c.sha(dest/'candidate.pt'),non_aim_weights_exact=True,training_rows=len(ids),prediction_rows=0,deployment_accepted=False))
    print('AIM_HEADS_FULL_ARM_COMPLETE')
if __name__=='__main__':main()
