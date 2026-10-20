"""One final-checkpoint development inference, after independent training checks."""
from shared import *
from model import load_dropout


def main():
    cutoff(); check(); assert not (HERE/'evaluation_started.json').exists()
    t=read(HERE/'trained.json'); v=read(HERE/'training_verified.json')
    assert v['complete'] and v['trained_sha256']==sha(HERE/'trained.json')
    assert v['checkpoint_sha256']==sha(OUT/'candidate.pt')==t['checkpoint_sha256']
    write(HERE/'evaluation_started.json',dict(checkpoint_sha256=t['checkpoint_sha256']))
    c.setup(); ids,sub,meta,rows=c.load_part('development','cuda'); cv=meta['card_vocab']
    from pipeline.model_gen import load_model
    model,state=load_dropout(OUT/'candidate.pt','cuda'); model.eval()
    assert state['card_vocab']==cv and state['args']['feature_version']==5
    ms,target=masks(ids); met=scoring(); allow=met['allowed'](sub,cv); n=len(ids)
    p=dict(allowed=allow,gate=np.empty(n,np.float32),gate_logit=np.empty(n,np.float32),
        chosen_card=np.empty(n,np.int32),card_logits=np.empty((n,4),np.float32),
        expert_cell=np.empty(n,np.int32),log_cell=np.empty(n,np.int32))
    with torch.inference_mode():
        for lo in range(0,n,128):
            cutoff(); ix=np.arange(lo,min(lo+128,n)); b=rows.batch(ix)
            enc=model.encode_gen(b); h=model.heads_gen(enc,b)
            p['gate'][ix]=h['gate'].sigmoid().cpu().numpy(); p['gate_logit'][ix]=h['gate'].cpu().numpy()
            p['card_logits'][ix]=h['card'].cpu().numpy()
            slot=h['card'].masked_fill(~torch.as_tensor(allow[ix],device='cuda'),-torch.inf).argmax(-1).cpu().numpy()
            p['chosen_card'][ix]=sub['hand_card'][ix,slot]
            p['expert_cell'][ix]=model.cell_logits_gen(enc,b['card'],b['form']).argmax(-1).cpu().numpy()
            p['log_cell'][ix]=model.cell_logits_gen(enc,torch.full_like(b['card'],cv.index('the-log')),torch.zeros_like(b['card'])).argmax(-1).cpu().numpy()
    assert np.isfinite(p['gate']).all() and np.isfinite(p['gate_logit']).all() and not np.isnan(p['card_logits']).any()
    counts=met['summarize'](sub,p,cv,ms,target)
    np.savez_compressed(OUT/'predictions.npz',ids=ids,**p)
    write(HERE/'evaluated.json',dict(complete=True,rows=n,counts=counts,checkpoint_sha256=t['checkpoint_sha256'],
        cache_sha256=sha(OUT/'predictions.npz'),training_verified_sha256=sha(HERE/'training_verified.json'),accepted=False,deployed=False))
    check(); print('ORDINARY_NO_DROPOUT_EVALUATED')


if __name__=='__main__': main()
