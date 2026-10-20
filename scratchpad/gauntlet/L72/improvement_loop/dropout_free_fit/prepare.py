"""Once-only dropout mechanism preflight; no optimizer or saved probe."""
import copy,io,shutil
from shared import *
from model import load_dropout,dropout_settings,validate_disabled

def main():
    cutoff(); assert not (HERE/'prepared.json').exists(); OUT.mkdir(exist_ok=False)
    c.setup(); c.check_prepared()
    assert read(FIT/'reviewed_results.json')['complete']
    assert read(HERE.parent/'lattice_label_audit/reviewed.json')['complete']
    assert read(HERE.parent/'local_cell_contribution/reviewed.json')['complete']
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
    prior=arrays(FOUT/'schedule.npz'); draws,mir=schedule(sample)
    assert np.array_equal(sample,prior['sample']) and np.array_equal(draws,prior['rows']) and np.array_equal(mir,prior['mirror'])
    shutil.copyfile(FOUT/'schedule.npz',OUT/'schedule.npz')
    assert sha(OUT/'schedule.npz')==sha(FOUT/'schedule.npz')
    sub,meta=c.load_subset(c.DATA,sample)
    from pipeline.model_gen import load_model
    from pipeline.train_gen import losses
    rows=c.GenRows(sub,np.arange(1024),'cpu')
    base,state=load_model(INIT,'cpu');model,_=load_dropout(INIT,'cpu',initial=True)
    base.eval();model.eval();before={k:v.clone() for k,v in model.state_dict().items()}
    assert state['card_vocab']==meta['card_vocab'] and state['args']['feature_version']==5
    assert state['args']['grid']==meta['grid']=='lattice'
    assert set(base.state_dict())==set(before) and all(torch.equal(v,before[k]) for k,v in base.state_dict().items())
    original=dropout_settings(base);disabled=validate_disabled(model)
    assert original.keys()==disabled.keys() and all(v==.1 for v in original.values())
    payload=dict(state,model=model.state_dict(),dropout_free_fit=dict(quarantined=True,eligible_policy_parent=False,dropout_settings=disabled))
    memory=io.BytesIO();torch.save(payload,memory);memory.seek(0);restored,_=load_dropout(memory,'cpu');restored.eval()
    assert all(torch.equal(v,restored.state_dict()[k]) for k,v in before.items())
    with torch.inference_mode():
        for mirrored in (False,True):
            b=c.augment(rows.batch(np.searchsorted(sample,draws[0])),mirrored)
            a=base(b,card=b['card'],form=b['form']);z=model(b,card=b['card'],form=b['form']);r=restored(b,card=b['card'],form=b['form'])
            assert a.keys()==z.keys()==r.keys()
            for k in a:assert torch.equal(a[k],z[k]) and torch.equal(z[k],r[k]),k
        # A fixed training batch with different dropout seeds: no optimizer.
        b=c.augment(rows.batch(np.searchsorted(sample,draws[0])),bool(mir[0]))
        model.train();base.train();torch.manual_seed(SEED+100)
        no_a=model(b,card=b['card'],form=b['form']);torch.manual_seed(SEED+101)
        no_b=model(b,card=b['card'],form=b['form'])
        for k in no_a:assert torch.equal(no_a[k],no_b[k]),k
        torch.manual_seed(SEED+100);yes_a=base(b,card=b['card'],form=b['form'])['cell']
        torch.manual_seed(SEED+101);yes_b=base(b,card=b['card'],form=b['form'])['cell']
        assert not torch.equal(yes_a,yes_b)
    bad=copy.deepcopy(model)
    next(m for m in bad.modules() if isinstance(m,torch.nn.MultiheadAttention)).dropout=.1
    try:validate_disabled(bad)
    except AssertionError:dropout_negative=1
    else:raise AssertionError('Reenabled dropout accepted')
    b=c.augment(rows.batch(np.searchsorted(sample,draws[0])),bool(mir[0]))
    torch.manual_seed(SEED);model.train();loss,parts=losses(model,b,False,meta['grid']);loss.backward()
    assert torch.isfinite(loss) and all(np.isfinite(v) for v in parts.values())
    assert all(p.grad is None or torch.isfinite(p.grad).all() for p in model.parameters())
    assert any(p.grad is not None and torch.count_nonzero(p.grad)>0 for p in model.parameters())
    assert all(torch.equal(v,model.state_dict()[k]) for k,v in before.items())
    write(HERE/'prepared.json',dict(complete=True,sources=sources(),schedule_sha256=sha(OUT/'schedule.npz'),
        runtime=dict(torch=str(torch.__version__),python=sys.version,cuda=torch.version.cuda),
        controls=dict(positive=2,negative=negatives),dropout_controls=dict(positive=3,negative=dropout_negative),
        original_dropout=original,disabled_dropout=disabled,mechanism=dict(initial_eval_exact=True,roundtrip_exact=True,
            same_parameters=True,training_seed_invariance=True,ordinary_dropout_stochastic=True,reenabled_dropout_rejected=True),
        probe_loss=float(loss.detach()),probe_weights_unchanged=True,optimizer_updates=0,checkpoint_saved=False,
        development_inference=0,sample_rows=1024,replay_groups=int(len(np.unique(raw['rep'][sample]))),
        draws=int(draws.size),native_draws=int((~mir).sum()*128),mirrored_draws=int(mir.sum()*128),
        initial_sha256=sha(INIT),quarantined=True))
    print('DROPOUT_FREE_FIT_PREPARED')
if __name__=='__main__':main()
