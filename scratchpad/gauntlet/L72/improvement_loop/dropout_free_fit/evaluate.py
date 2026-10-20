"""Once-only final assay inference, both orientations, no development rows."""
from shared import *

def main():
    cutoff(); check(); assert not (HERE/'evaluation_started.json').exists()
    t=read(HERE/'trained.json'); v=read(HERE/'training_verified.json')
    assert v['complete'] and v['trained_sha256']==sha(HERE/'trained.json')
    assert v['checkpoint_sha256']==sha(OUT/'candidate.pt')==t['checkpoint_sha256']
    write(HERE/'evaluation_started.json',dict(checkpoint_sha256=t['checkpoint_sha256']))
    c.setup(); ids=arrays(OUT/'schedule.npz')['sample']; sub,meta=c.load_subset(c.DATA,ids)
    rows=c.GenRows(sub,np.arange(len(ids)),'cuda'); cv=meta['card_vocab']; n=len(ids)
    from model import load_dropout
    met=scoring(); allow=met['allowed'](sub,cv); counts={}; artifacts={}; checkpoints={}
    for name,path in dict(dropout_free_final=OUT/'candidate.pt').items():
        model,state=load_dropout(path,'cuda'); model.eval(); checkpoints[name]=sha(path)
        assert state['card_vocab']==cv
        assert state['args']['feature_version']==(4 if name=='r1e_corrected' else 5)
        before={k:v.clone() for k,v in model.state_dict().items()}
        for mirrored in (False,True):
            key=name+('/mirrored' if mirrored else '/native'); lab=labels(ids,sub,mirrored)
            p=dict(allowed=allow,gate=np.empty(n,np.float32),gate_logit=np.empty(n,np.float32),
                chosen_card=np.empty(n,np.int32),card_logits=np.empty((n,4),np.float32),expert_cell=np.empty(n,np.int32))
            with torch.inference_mode():
                for lo in range(0,n,128):
                    cutoff(); ix=np.arange(lo,min(lo+128,n)); b=c.augment(rows.batch(ix),mirrored)
                    enc=model.encode_gen(b); h=model.heads_gen(enc,b)
                    p['gate'][ix]=h['gate'].sigmoid().cpu().numpy(); p['gate_logit'][ix]=h['gate'].cpu().numpy()
                    p['card_logits'][ix]=h['card'].cpu().numpy()
                    slot=h['card'].masked_fill(~torch.as_tensor(allow[ix],device='cuda'),-torch.inf).argmax(-1).cpu().numpy()
                    p['chosen_card'][ix]=sub['hand_card'][ix,slot]
                    p['expert_cell'][ix]=model.cell_logits_gen(enc,b['card'],b['form']).argmax(-1).cpu().numpy()
            counts[key]=met['summarize'](lab,p,np.ones(n,np.int64),cv)
            filename=key.replace('/','_')+'.npz'
            np.savez_compressed(OUT/filename,**lab,**p,frequency=np.ones(n,np.int64))
            artifacts[filename]=sha(OUT/filename)
        assert all(torch.equal(val,model.state_dict()[k]) for k,val in before.items())
        del model,before
    # Reuse all prior saved controls exactly; no new control inference.
    previous=read(FIT/'evaluated.json')
    for name in ('r1e_corrected','ordinary_v5','assay_final'):
        checkpoints[name]=previous['checkpoints'][name]
        for mirrored in (False,True):
            key=name+('/mirrored' if mirrored else '/native'); filename=key.replace('/','_')+'.npz'
            assert sha(FOUT/filename)==previous['artifacts'][filename]
            z=arrays(FOUT/filename)
            counts[key]=met['summarize'](z,z,z['frequency'],cv)
            artifacts[filename]=sha(FOUT/filename)
    write(OUT/'counts.json',counts)
    filters={k:criteria(val) for k,val in counts.items()}
    check(); write(HERE/'evaluated.json',dict(complete=True,views_per_model=2048,total_views=2048,reused_control_views=6144,
        sample_rows=1024,card_vocab=cv,artifacts=artifacts,checkpoints=checkpoints,counts_sha256=sha(OUT/'counts.json'),
        training_verified_sha256=sha(HERE/'training_verified.json'),filters=filters,
        diagnostic_fit=all(all(val.values()) for k,val in filters.items() if k.startswith('dropout_free_final/')),
        evaluation_weights_unchanged=True,development_inference=0,quarantined=True,accepted=False,deployed=False))
    print('DROPOUT_FREE_FIT_EVALUATED')

if __name__=='__main__': main()
