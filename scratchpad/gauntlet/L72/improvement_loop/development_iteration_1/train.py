"""One fixed final-step arm. Reads training indices only; never evaluates."""
import argparse
import time
import numpy as np
import torch
from common import *


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--arm',choices=('ordinary_v5','ordinary_v6'),required=True)
    a=ap.parse_args();setup();check_prepared();manifest=check_frozen()
    if not torch.cuda.is_available():raise RuntimeError('CUDA required for registered full run')
    dest=OUT/a.arm;dest.mkdir(exist_ok=False)
    ids,sub,meta,rows=load_part('train','cuda')
    version=5 if a.arm=='ordinary_v5' else 6
    state=torch.load(INIT,map_location='cpu');torch.manual_seed(SEED)
    model=initialize(state,version,meta).to('cuda');opt=optimizer(model)
    with np.load(OUT/'draws.npz') as z:draws,mirrors=z['rows'],z['mirror']
    positions=np.searchsorted(ids,draws)
    assert np.array_equal(ids[positions],draws) and draws.shape==(1000,128)
    config=dict(arm=a.arm,feature_version=version,prelaunch_sha256=sha(HERE/'prelaunch.json'),
        prepared_sha256=sha(HERE/'prepared.json'),draws_sha256=sha(OUT/'draws.npz'),
        device='cuda',torch=torch.__version__,cuda=torch.version.cuda,gpu=torch.cuda.get_device_name(),
        steps=1000,batch=128,seed=SEED,loss='unchanged train_gen.losses; shared v6-safe augmentation',
        deployment_accepted=False,development_only=True,simulator_used=False)
    write(dest/'run.json',config);torch.manual_seed(SEED);start=time.time()
    with (dest/'train.jsonl').open('x') as stream:
        for step,chosen in enumerate(positions,1):
            b=augment(rows.batch(chosen),bool(mirrors[step-1]))
            loss,parts=train_step(model,b,opt,False,meta['grid'])
            record=dict(step=step,loss=loss,parts=parts,seconds=time.time()-start)
            stream.write(json.dumps(record,allow_nan=False)+'\n')
            if step%100==0:stream.flush();print(json.dumps(record),flush=True)
    check_frozen()
    # Do not copy stale parent validation metadata into a successor result.
    checkpoint={k:v for k,v in state.items() if k not in ('model','val','eval','optimizer')}
    checkpoint.update(model=model.cpu().state_dict(),args=dict(state['args'],feature_version=version),development_iteration_1=config)
    torch.save(checkpoint,dest/'candidate.pt')
    write(dest/'result.json',dict(complete=True,finite_updates=1000,checkpoint_sha256=sha(dest/'candidate.pt'),
        training_rows=len(ids),prediction_rows=0,development_only=True,deployment_accepted=False))
    print('DEVELOPMENT_1_FULL_ARM_COMPLETE',flush=True)


if __name__=='__main__':main()
