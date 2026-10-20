"""Additional ordinary IL, final-only; no evaluation or old validation path."""
import os
import time
from shared import *
from model import load_dropout,validate_disabled


def main():
    cutoff(); p=check(); assert not (HERE/'training_started.json').exists()
    write(HERE/'training_started.json',dict(pid=os.getpid(),prepared_sha256=sha(HERE/'prepared.json')))
    c.setup(); assert torch.cuda.is_available()
    # Explicit training-only access, without any default train/evaluation CLI.
    ids,sub,meta,rows=c.load_part('train','cuda'); schedule=arrays(OUT/'schedule.npz')
    pos=validate_schedule(schedule['rows'],schedule['mirror'],ids)
    from pipeline.model_gen import load_model
    model,state=load_dropout(INIT,'cuda',initial=True); assert state['card_vocab']==meta['card_vocab']
    assert state['args']['feature_version']==5
    opt=torch.optim.AdamW(model.parameters(),lr=1e-5,weight_decay=.01)
    assert len(opt.state)==0
    config=dict(training_dropout_disabled=True,dropout_settings=validate_disabled(model),arm=ARM,steps=STEPS,batch=128,seed=SEED,optimizer='fresh AdamW',lr=1e-5,weight_decay=.01,
        clip_norm=1,initial_sha256=sha(INIT),schedule_sha256=p['schedule_sha256'],prepared_sha256=sha(HERE/'prepared.json'),
        torch=str(torch.__version__),cuda=torch.version.cuda,training_rows=len(ids),selection='final8000only',feature_version=5)
    write(OUT/'run.json',config); torch.manual_seed(SEED); started=time.time()
    with (OUT/'train.jsonl').open('x',encoding='utf-8') as log:
        for step,chosen in enumerate(pos,1):
            cutoff(); validate_disabled(model); batch=c.augment(rows.batch(chosen),bool(schedule['mirror'][step-1]))
            loss,parts=c.train_step(model,batch,opt,False,meta['grid'])
            rec=dict(dropout_disabled=True,step=step,loss=loss,parts=parts,mirror=bool(schedule['mirror'][step-1]),
                draw_sha256=hashlib.sha256(schedule['rows'][step-1].tobytes()).hexdigest(),seconds=time.time()-started)
            log.write(json.dumps(rec,allow_nan=False)+'\n')
            if step%100==0:
                log.flush(); write(HERE/'progress.json',rec); print(json.dumps(rec),flush=True)
    check()
    checkpoint={k:v for k,v in state.items() if k not in ('model','optimizer','val','eval')}
    checkpoint.update(model=model.cpu().state_dict(),development_iteration_10=config)
    torch.save(checkpoint,OUT/'candidate.pt'); torch.save(opt.state_dict(),OUT/'optimizer.pt')
    portable=torch.load(OUT/'candidate.pt',map_location='cpu',weights_only=True)
    assert portable['development_iteration_10']==config
    assert all(torch.isfinite(v).all() for v in portable['model'].values())
    write(HERE/'trained.json',dict(complete=True,finite_updates=STEPS,checkpoint_sha256=sha(OUT/'candidate.pt'),
        optimizer_sha256=sha(OUT/'optimizer.pt'),log_sha256=sha(OUT/'train.jsonl'),run_sha256=sha(OUT/'run.json'),
        prepared_sha256=sha(HERE/'prepared.json'),training_rows=len(ids),prediction_rows=0,accepted=False,deployed=False))
    print('ORDINARY_NO_DROPOUT_TRAINED')


if __name__=='__main__': main()
