"""Final candidate predictions on the same registered development rows."""
import numpy as np
import torch
from experiment import *
from pipeline.model_gen import load_model
from metrics import allowed,summarize

def main():
    c.setup();check_active();dest=OUT/(ARM+'_eval');dest.mkdir(exist_ok=False)
    ids,sub,meta,rows=c.load_part('development','cuda');cv=meta['card_vocab']
    path=OUT/ARM/'candidate.pt';model,state=load_model(path,'cuda')
    assert state['card_vocab']==cv and state['args']['grid']=='lattice';model.eval()
    with np.load(MASKS) as z:
        assert np.array_equal(ids,z['ids']);target=z['target'];masks={k[5:]:z[k] for k in z.files if k.startswith('mask_')}
    n=len(ids);allow=allowed(sub,cv)
    p=dict(allowed=allow,gate=np.empty(n,np.float32),gate_logit=np.empty(n,np.float32),
        chosen_card=np.empty(n,np.int32),card_logits=np.empty((n,4),np.float32),
        expert_cell=np.empty(n,np.int32),log_cell=np.empty(n,np.int32))
    with torch.inference_mode():
        for lo in range(0,n,128):
            ix=np.arange(lo,min(lo+128,n));b=rows.batch(ix);enc=model.encode_gen(b);h=model.heads_gen(enc,b)
            p['gate'][ix]=h['gate'].sigmoid().cpu().numpy();p['gate_logit'][ix]=h['gate'].cpu().numpy()
            p['card_logits'][ix]=h['card'].cpu().numpy()
            slot=h['card'].masked_fill(~torch.as_tensor(allow[ix],device='cuda'),-torch.inf).argmax(-1).cpu().numpy()
            p['chosen_card'][ix]=sub['hand_card'][ix,slot]
            p['expert_cell'][ix]=model.cell_logits_gen(enc,b['card'],b['form']).argmax(-1).cpu().numpy()
            card=torch.full_like(b['card'],cv.index('the-log'))
            p['log_cell'][ix]=model.cell_logits_gen(enc,card,torch.zeros_like(card)).argmax(-1).cpu().numpy()
            if lo%12800==0:print('SPATIAL_PREDICTED',lo,flush=True)
    assert np.isfinite(p['gate']).all() and not np.isnan(p['card_logits']).any()
    report=summarize(sub,p,cv,masks,target)
    np.savez_compressed(dest/'predictions.npz',ids=ids,**p)
    c.write(dest/'report.json',dict(arm=ARM,counts=report,complete=True,rows=n,
        checkpoint_sha256=c.sha(path),prelaunch_sha256=c.sha(HERE/'prelaunch.json'),
        cache_sha256=c.sha(dest/'predictions.npz'),development_only=True,corrected_observations=True,deployment_accepted=False))
    check_active();print('SPATIAL_EVALUATION_COMPLETE',flush=True)

if __name__=='__main__':main()
