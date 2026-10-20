"""Original labels, sample controls and excluded backward; no optimization."""
from shared import *

def main():
    cutoff(); assert not (HERE/'prepared.json').exists(); OUT.mkdir(exist_ok=False)
    c.setup(); c.check_prepared()
    assert read(HERE.parent/'training_fit_audit/reviewed.json')['complete']
    assert read(HERE.parent/'development_iteration_9/reviewed_results.json')['complete']
    assert sha(INIT)==read(c.HERE/'ordinary_v5_portable.json')['portable_sha256']
    raw,meta=raw_labels(); train=c.indices('train'); dev=c.indices('development')
    assert len(train)==213995 and not np.intersect1d(train,dev).size
    assert not np.intersect1d(raw['rep'][train],raw['rep'][dev]).size
    sample=select(train,raw); validate(sample,train,raw)
    with np.load(c.SOURCE,allow_pickle=False) as z:
        for k in ('rep','tick','y_gate','y_card','y_xy','hand_card','split'):
            assert np.array_equal(raw[k][sample],z[k][sample]),k
    negatives=0; bads=[sample[:-1],sample.astype(float),sample[::-1]]
    for value in (int(dev[0]),int(sample[1]),-1):
        b=sample.copy(); b[0]=value; bads.append(b)
    for b in bads:
        try: validate(b,train,raw)
        except (AssertionError,IndexError): negatives+=1
        else: raise AssertionError('Malformed sample accepted')
    assert negatives==6
    draws,mir=schedule(sample); assert draws.shape==(4096,128) and np.isin(draws,sample).all()
    np.savez_compressed(OUT/'schedule.npz',sample=sample,rows=draws,mirror=mir)
    sub,meta=c.load_subset(c.DATA,sample)
    from pipeline.eval_gen import GenRows
    from pipeline.model_gen import load_model
    from pipeline.train_gen import losses
    rows=GenRows(sub,np.arange(1024),'cpu'); b=c.augment(rows.batch(np.searchsorted(sample,draws[0])),bool(mir[0]))
    model,state=load_model(INIT,'cpu'); before={k:v.clone() for k,v in model.state_dict().items()}
    assert state['card_vocab']==meta['card_vocab'] and state['args']['feature_version']==5
    torch.manual_seed(SEED); model.train(); loss,parts=losses(model,b,False,meta['grid']); loss.backward()
    assert torch.isfinite(loss) and all(np.isfinite(v) for v in parts.values())
    assert any(p.grad is not None and torch.count_nonzero(p.grad)>0 for p in model.parameters())
    assert all(p.grad is None or torch.isfinite(p.grad).all() for p in model.parameters())
    assert all(torch.equal(v,model.state_dict()[k]) for k,v in before.items())
    write(HERE/'prepared.json',dict(complete=True,sources=sources(),schedule_sha256=sha(OUT/'schedule.npz'),
        runtime=dict(torch=str(torch.__version__),python=sys.version,cuda=torch.version.cuda),
        controls=dict(positive=2,negative=negatives),probe_loss=float(loss.detach()),probe_weights_unchanged=True,
        optimizer_updates=0,checkpoint_saved=False,development_inference=0,sample_rows=1024,
        replay_groups=int(len(np.unique(raw['rep'][sample]))),draws=int(draws.size),native_draws=int((~mir).sum()*128),
        mirrored_draws=int(mir.sum()*128),initial_sha256=sha(INIT),quarantined=True))
    print('SMALL_SET_FIT_PREPARED')

if __name__=='__main__': main()
