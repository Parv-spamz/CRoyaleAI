from shared import *
def main():
    assert not (HERE/'evaluated.json').exists();check();t=read(HERE/'trained.json');assert t['complete'] and t['updates']==32
    c.setup();ids,sub,meta,rows=c.load_part('development','cuda');cv=meta['card_vocab']
    from pipeline.eval_gen import load_model
    model,state=load_model(ROOT/t['checkpoint'],'cuda');model.eval();assert state['card_vocab']==cv
    ms,target=masks(ids);met=metric_module();allow=met['allowed'](sub,cv);n=len(ids)
    p=dict(allowed=allow,gate=np.empty(n,np.float32),gate_logit=np.empty(n,np.float32),chosen_card=np.empty(n,np.int32),card_logits=np.empty((n,4),np.float32),expert_cell=np.empty(n,np.int32),log_cell=np.empty(n,np.int32))
    with torch.inference_mode():
        for lo in range(0,n,128):
            ix=np.arange(lo,min(lo+128,n));b=rows.batch(ix);enc=model.encode_gen(b);h=model.heads_gen(enc,b)
            p['gate'][ix]=h['gate'].sigmoid().cpu().numpy();p['gate_logit'][ix]=h['gate'].cpu().numpy();p['card_logits'][ix]=h['card'].cpu().numpy()
            slot=h['card'].masked_fill(~torch.as_tensor(allow[ix],device='cuda'),-torch.inf).argmax(-1).cpu().numpy();p['chosen_card'][ix]=sub['hand_card'][ix,slot]
            p['expert_cell'][ix]=model.cell_logits_gen(enc,b['card'],b['form']).argmax(-1).cpu().numpy()
            p['log_cell'][ix]=model.cell_logits_gen(enc,torch.full_like(b['card'],cv.index('the-log')),torch.zeros_like(b['card'])).argmax(-1).cpu().numpy()
    assert np.isfinite(p['gate']).all() and not np.isnan(p['card_logits']).any()
    counts=met['summarize'](sub,p,cv,ms,target);np.savez_compressed(OUT/'predictions.npz',ids=ids,**p)
    write(HERE/'evaluated.json',dict(complete=True,rows=n,counts=counts,checkpoint_sha256=t['checkpoint_sha256'],cache_sha256=sha(OUT/'predictions.npz'),deployment_accepted=False))
    check();print('OUTCOME_RL_EVALUATED')
if __name__=='__main__':main()
