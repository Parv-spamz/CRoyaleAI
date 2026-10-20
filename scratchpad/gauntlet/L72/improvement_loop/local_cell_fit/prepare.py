"""Once-only local mechanism qualification; zero optimizer or saved probe model."""
import copy
import io
import shutil
from shared import *
from model import load_local


def mapping(patch,offset):
    assert patch.shape==offset.shape==(2304,)
    assert patch.dtype==offset.dtype==torch.int64
    for cell in range(2304):
        y,x=divmod(cell,36)
        assert int(patch[cell])==(y//4)*9+x//4
        assert int(offset[cell])==(y%4)*4+x%4
    assert len(set(zip(patch.tolist(),offset.tolist())))==2304


def main():
    cutoff(); assert not (HERE/'prepared.json').exists(); OUT.mkdir(exist_ok=False)
    c.setup(); c.check_prepared()
    assert read(FIT/'reviewed_results.json')['complete']
    assert read(HERE.parent/'small_set_aim_audit/reviewed.json')['complete']
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
    base,state=load_model(INIT,'cpu'); model,_=load_local(INIT,'cpu',initial=True)
    base.eval(); model.eval(); before={k:v.clone() for k,v in model.state_dict().items()}
    assert state['card_vocab']==meta['card_vocab'] and state['args']['feature_version']==5
    assert all(torch.equal(v,before[k]) for k,v in base.state_dict().items())
    mapping(model.cell_patch,model.local_cell_offset)
    mapping_negative=0
    for which in ('patch','offset','dtype'):
        p=model.cell_patch.clone(); o=model.local_cell_offset.clone()
        if which=='patch': p[0]=1
        elif which=='offset': o[0]=1
        else: o=o.float()
        try: mapping(p,o)
        except AssertionError: mapping_negative+=1
        else: raise AssertionError('Malformed mapping accepted')
    assert mapping_negative==3
    # In-memory full loader roundtrip, never a saved probe checkpoint.
    payload=dict(state,model=model.state_dict(),local_cell_fit=dict(quarantined=True,eligible_policy_parent=False))
    memory=io.BytesIO(); torch.save(payload,memory); memory.seek(0)
    restored,_=load_local(memory,'cpu'); restored.eval()
    assert all(torch.equal(v,restored.state_dict()[k]) for k,v in before.items())
    with torch.inference_mode():
        for mirrored in (False,True):
            b=c.augment(rows.batch(np.searchsorted(sample,draws[0])),mirrored)
            e0=base.encode_gen(b); e1=model.encode_gen(b); e2=restored.encode_gen(b)
            h0=base.heads_gen(e0,b); h1=model.heads_gen(e1,b); h2=restored.heads_gen(e2,b)
            for k in h0: assert torch.equal(h0[k],h1[k]) and torch.equal(h1[k],h2[k]),k
            a0=base.cell_logits_gen(e0,b['card'],b['form'])
            a1=model.cell_logits_gen(e1,b['card'],b['form'])
            a2=restored.cell_logits_gen(e2,b['card'],b['form'])
            assert torch.equal(a0,a1) and torch.equal(a1,a2)
    # Fixed synthetic temporary weights: local and query sensitivity, no optimizer.
    probe=copy.deepcopy(model)
    with torch.no_grad():
        for param in probe.local_cell.parameters(): param.zero_()
        probe.local_cell[0].weight[0,0]=1
        probe.local_cell[0].weight[0,model.d]=1
        probe.local_cell[2].weight[0,0]=1
        probe.local_cell[2].weight[1,0]=-1
        p=torch.zeros(1,144,model.d); q=torch.zeros(1,model.d)
        s0=probe.local_scores(p,q); p[0,73,0]=1; sp=probe.local_scores(p,q)
        assert torch.equal(sp[:, :73],s0[:, :73]) and torch.equal(sp[:,74:],s0[:,74:])
        assert sp[0,73,0]-sp[0,73,1]>0 and torch.count_nonzero(s0)==0
        p.zero_(); q[0,0]=1; sq=probe.local_scores(p,q)
        assert torch.all(sq[0,:,0]-sq[0,:,1]>0)
        assert torch.equal(sp.mean(-1),torch.zeros(1,144)) and torch.equal(sq.mean(-1),torch.zeros(1,144))
        gathered=sp[:,probe.cell_patch,probe.local_cell_offset]
        scalar=torch.tensor([[float(sp[0,int(probe.cell_patch[i]),int(probe.local_cell_offset[i])]) for i in range(2304)]])
        assert torch.equal(gathered,scalar)
    b=c.augment(rows.batch(np.searchsorted(sample,draws[0])),bool(mir[0]))
    torch.manual_seed(SEED); model.train(); loss,parts=losses(model,b,False,meta['grid']); loss.backward()
    assert torch.isfinite(loss) and all(np.isfinite(v) for v in parts.values())
    assert all(p.grad is None or torch.isfinite(p.grad).all() for p in model.parameters())
    assert model.local_cell[2].weight.grad is not None and torch.count_nonzero(model.local_cell[2].weight.grad)>0
    assert all(torch.equal(v,model.state_dict()[k]) for k,v in before.items())
    write(HERE/'prepared.json',dict(complete=True,sources=sources(),schedule_sha256=sha(OUT/'schedule.npz'),
        runtime=dict(torch=str(torch.__version__),python=sys.version,cuda=torch.version.cuda),
        controls=dict(positive=2,negative=negatives),mapping_controls=dict(cells=2304,positive=1,negative=mapping_negative),
        mechanism=dict(initial_exact=True,roundtrip_exact=True,local_patch_dependence=True,query_dependence=True,zero_mean=True,scalar_gather_exact=True),
        probe_loss=float(loss.detach()),probe_weights_unchanged=True,optimizer_updates=0,checkpoint_saved=False,
        development_inference=0,sample_rows=1024,replay_groups=int(len(np.unique(raw['rep'][sample]))),
        draws=int(draws.size),native_draws=int((~mir).sum()*128),mirrored_draws=int(mir.sum()*128),
        initial_sha256=sha(INIT),quarantined=True))
    print('LOCAL_CELL_FIT_PREPARED')


if __name__=='__main__': main()
