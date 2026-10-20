"""New schedule boundaries and excluded finite backward probe, no optimizer."""
from shared import *


def main():
    cutoff(); assert not (HERE/'prepared.json').exists(); OUT.mkdir(exist_ok=False)
    c.setup(); c.check_prepared()
    assert read(HERE.parent/'training_fit_audit/reviewed.json')['complete']
    assert sha(INIT)==read(c.HERE/'ordinary_v5_portable.json')['portable_sha256']
    ref=read(HERE.parent/'development_rl_3/results_verified.json')
    for name,path in CONTROLS.items(): assert sha(path)==ref['hashes'][name]['cache']
    assert sha(MASKS)==read(HERE.parent/'development_iteration_4/prelaunch.json')['masks_sha256']
    train=c.indices('train'); dev=c.indices('development')
    assert len(train)==213995 and len(dev)==54723 and not np.intersect1d(train,dev).size
    rng=np.random.default_rng(SEED); draws=[]; mirrors=[]
    for _ in range(STEPS):
        draws.append(train[rng.choice(len(train),128)]); mirrors.append(rng.random()<.5)
    draws=np.asarray(draws); mirrors=np.asarray(mirrors)
    validate_schedule(draws,mirrors,train); negatives=0
    bads=[(draws[:-1],mirrors),(draws.astype(float),mirrors),(draws,mirrors[:-1]),(draws,mirrors.astype(int))]
    for value in (int(dev[0]),int(train[-1]+1)):
        bad=draws.copy(); bad[0,0]=value; bads.append((bad,mirrors))
    for x,y in bads:
        try: validate_schedule(x,y,train)
        except (AssertionError,IndexError): negatives+=1
        else: raise AssertionError('Corrupt schedule accepted')
    assert negatives==6
    ids=np.unique(draws[0]); sub,meta=c.load_subset(c.DATA,ids)
    from pipeline.eval_gen import GenRows
    from pipeline.model_gen import load_model
    from pipeline.train_gen import losses
    rows=GenRows(sub,np.arange(len(ids)),'cpu'); batch=c.augment(rows.batch(np.searchsorted(ids,draws[0])),bool(mirrors[0]))
    model,state=load_model(INIT,'cpu'); before={k:v.clone() for k,v in model.state_dict().items()}
    assert state['card_vocab']==meta['card_vocab'] and state['args']['feature_version']==5
    torch.manual_seed(SEED); model.train(); loss,parts=losses(model,batch,False,meta['grid']); loss.backward()
    assert torch.isfinite(loss) and all(np.isfinite(v) for v in parts.values())
    assert any(p.grad is not None and torch.count_nonzero(p.grad)>0 for p in model.parameters())
    assert all(p.grad is None or torch.isfinite(p.grad).all() for p in model.parameters())
    assert all(torch.equal(v,model.state_dict()[k]) for k,v in before.items())
    ms,target=masks(dev)
    assert ms['rocket'].sum()==955 and ms['rocket_late_overtime_clock'].sum()==320
    assert ms['defensive_sequence'].sum()==8183 and ms['barrel_pro'].sum()==63
    np.savez_compressed(OUT/'schedule.npz',rows=draws,mirror=mirrors)
    write(HERE/'prepared.json',dict(complete=True,sources=sources(),schedule_sha256=sha(OUT/'schedule.npz'),
        runtime=dict(torch=str(torch.__version__),python=sys.version,cuda=torch.version.cuda),
        controls=dict(positive=2,negative=negatives),probe_loss=float(loss.detach()),probe_parts=parts,
        probe_weights_unchanged=True,optimizer_updates=0,checkpoint_saved=False,development_inference=0,
        draws=int(draws.size),unique_rows=int(np.unique(draws).size),steps=STEPS,seed=SEED,
        native_draws=int((~mirrors).sum()*128),mirrored_draws=int(mirrors.sum()*128),initial_sha256=sha(INIT)))
    print('ORDINARY_EXTENDED_PREPARED')


if __name__=='__main__': main()
