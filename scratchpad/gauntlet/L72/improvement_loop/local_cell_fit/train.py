"""Small-set training, quarantined final-only; no development access."""
import os
import time
from shared import *


def main():
    cutoff(); p=check(); assert not (HERE/'training_started.json').exists()
    write(HERE/'training_started.json',dict(pid=os.getpid(),prepared_sha256=sha(HERE/'prepared.json')))
    c.setup(); assert torch.cuda.is_available()
    # Explicit training-only access, without any default train/evaluation CLI.
    schedule=arrays(OUT/'schedule.npz'); ids=schedule['sample']
    sub,meta=c.load_subset(c.DATA,ids)
    rows=c.GenRows(sub,np.arange(len(ids)),'cuda')
    pos=np.searchsorted(ids,schedule['rows']); assert np.array_equal(ids[pos],schedule['rows'])
    from model import load_local
    model,state=load_local(INIT,'cuda',initial=True); assert state['card_vocab']==meta['card_vocab']
    assert state['args']['feature_version']==5
    opt=torch.optim.AdamW(model.parameters(),lr=1e-5,weight_decay=.01)
    assert len(opt.state)==0
    config=dict(arm=ARM,architecture='generic local patch and query cell residual',branch_initialization_seed=2026100612,steps=STEPS,batch=128,seed=SEED,optimizer='fresh AdamW',lr=1e-5,weight_decay=.01,
        clip_norm=1,initial_sha256=sha(INIT),schedule_sha256=p['schedule_sha256'],prepared_sha256=sha(HERE/'prepared.json'),
        torch=str(torch.__version__),cuda=torch.version.cuda,training_rows=len(ids),selection='final4096only',quarantined=True,eligible_policy_parent=False,feature_version=5)
    write(OUT/'run.json',config); torch.manual_seed(SEED); started=time.time()
    with (OUT/'train.jsonl').open('x',encoding='utf-8') as log:
        for step,chosen in enumerate(pos,1):
            cutoff(); batch=c.augment(rows.batch(chosen),bool(schedule['mirror'][step-1]))
            loss,parts=c.train_step(model,batch,opt,False,meta['grid'])
            rec=dict(step=step,loss=loss,parts=parts,mirror=bool(schedule['mirror'][step-1]),
                draw_sha256=hashlib.sha256(schedule['rows'][step-1].tobytes()).hexdigest(),seconds=time.time()-started)
            log.write(json.dumps(rec,allow_nan=False)+'\n')
            if step%100==0:
                log.flush(); write(HERE/'progress.json',rec); print(json.dumps(rec),flush=True)
    check()
    checkpoint={k:v for k,v in state.items() if k not in ('model','optimizer','val','eval')}
    checkpoint.update(model=model.cpu().state_dict(),local_cell_fit=config)
    torch.save(checkpoint,OUT/'candidate.pt'); torch.save(opt.state_dict(),OUT/'optimizer.pt')
    portable=torch.load(OUT/'candidate.pt',map_location='cpu',weights_only=True)
    assert portable['local_cell_fit']==config
    assert all(torch.isfinite(v).all() for v in portable['model'].values())
    write(HERE/'trained.json',dict(complete=True,finite_updates=STEPS,checkpoint_sha256=sha(OUT/'candidate.pt'),
        optimizer_sha256=sha(OUT/'optimizer.pt'),log_sha256=sha(OUT/'train.jsonl'),run_sha256=sha(OUT/'run.json'),
        prepared_sha256=sha(HERE/'prepared.json'),training_rows=len(ids),prediction_rows=0,accepted=False,deployed=False))
    print('LOCAL_CELL_FIT_TRAINED')


if __name__=='__main__': main()
