"""Fixed training-state backward diagnostics. No optimizer or checkpoint writes."""
import datetime,os
from common import *
import torch
def main():
    assert not OUT.exists() and not (HERE/'started.json').exists();sh=original();prepared=sh.check()
    assert read(BASE/'rl_failure_audit/verified.json')['complete'];runtime,RL=sh.initialize_runtime();assert runtime==prepared['runtime']
    trained=read(BASE/'development_rl_1/trained.json');assert sha(TRAIN/'train.jsonl')==trained['train_log_sha256']
    logs=[json.loads(s) for s in (TRAIN/'train.jsonl').read_text().splitlines()];assert [l['update'] for l in logs]==list(range(1,33))
    source=sources();OUT.mkdir();write(HERE/'started.json',dict(pid=os.getpid(),utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),sources=source,runtime=runtime,optimizer_updates=0))
    from pipeline.eval_gen import load_model
    ref,_=load_model(sh.INIT,'cuda');ref.eval()
    for p in ref.parameters():p.requires_grad_(False)
    orig_load=np.load
    def limited(path,*args,**kw):
        assert (TRAIN/'rollouts').resolve() in Path(path).resolve().parents,'Only saved original training trajectories/contracts allowed'
        return orig_load(path,*args,**kw)
    np.load=limited
    results=[]
    for u in range(5,32):
        if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime(2026,10,6,4,tzinfo=datetime.timezone.utc):raise RuntimeError('Tuesday cutoff before next gradient sample')
        rawpath=TRAIN/'rollouts'/f'u{u:03d}.json';contract=TRAIN/'rollouts'/f'u{u:03d}_contract.npz';checkpoint=TRAIN/'checkpoints'/f'u{u:03d}.pt'
        assert sha(rawpath)==logs[u]['rollouts_sha256'] and sha(contract)==logs[u]['contract_sha256']
        raw=read(rawpath);inputs={str(p.relative_to(ROOT)):sha(p) for p in (rawpath,contract,checkpoint,sh.INIT)}
        for r in raw:
            p=ROOT/r['trajectory'];assert sha(p)==r['trajectory_sha256'];inputs[str(p.relative_to(ROOT))]=sha(p);r['traj']=arrays(p)
        bn,_=RL.collate(raw,advantage='gae',gamma_tick=.99994,gae_terminal_gap=True);saved=arrays(contract)
        assert np.array_equal(bn['match'],saved['match']) and len(bn['A'])==logs[u]['rows']
        bn['A']=saved['advantage'];bn['ret']=saved['returns'];bn['v_old']=saved['v_old'];B=RL.to_device(bn,'cuda')
        net,state=load_model(checkpoint,'cuda');net.eval();tag=state['development_rl_1']
        assert tag['update']==u and tag['parent_sha256']==sha(sh.INIT) and tag['prepared_sha256']==sha(BASE/'development_rl_1/prepared.json')
        old={k:v.detach().cpu().clone() for k,v in net.state_dict().items()}
        names=[n for n,p in net.named_parameters()];params=list(net.parameters());shapes=[list(p.shape) for p in params]
        n=len(bn['A']);ix=torch.arange(0,n,max(1,n//256),device='cuda')[:256];beta=logs[u-1]['beta_next']
        R=RL.ref_terms(ref,B,.35,.5);kw=dict(tau=.35,T=.5,clip=.2,beta=beta,n_total=n)
        pg,ps=RL.minibatch_loss(net,B,R,ix,**kw);gpg=torch.autograd.grad(pg,params,allow_unused=True)
        vf,vs=RL.minibatch_loss(net,B,R,ix,vf=dict(coef=.5,clip=.2,policy=False,trunk_grad=True),**kw);gv=torch.autograd.grad(vf,params,allow_unused=True)
        det,ds=RL.minibatch_loss(net,B,R,ix,vf=dict(coef=.5,clip=.2,policy=False,trunk_grad=False),**kw);gd=torch.autograd.grad(det,params,allow_unused=True)
        assert vs['ratio_maxdev']<1e-4 and torch.isfinite(pg) and torch.isfinite(vf) and torch.isfinite(det)
        vectors=[]
        for grads in (gpg,gv,gd):
            assert all(g is None or torch.isfinite(g).all() for g in grads)
            vectors.append(np.concatenate([(g.detach().cpu().numpy() if g is not None else np.zeros(tuple(p.shape),np.float32)).reshape(-1) for p,g in zip(params,grads)]))
        reach=[g is not None for g in gv];m=metrics(*vectors,names,shapes,reach)
        assert all(torch.equal(v.detach().cpu(),old[k]) for k,v in net.state_dict().items()) and all(p.grad is None for p in params)
        vectorpath=OUT/f'u{u+1:03d}.npz';np.savez_compressed(vectorpath,pg=vectors[0],vf=vectors[1],detached=vectors[2],indices=ix.cpu().numpy(),reach=np.array(reach))
        result=dict(update=u+1,pre_checkpoint_update=u,cohort_rows=n,sample_rows=len(ix),beta=beta,inputs=inputs,names=names,shapes=shapes,gradient_file=str(vectorpath.relative_to(ROOT)),gradient_sha256=sha(vectorpath),metrics=m,loss_policy=float(pg),loss_critic=float(vf),loss_detached=float(det),ratio_maxdev=vs['ratio_maxdev'],weights_unchanged=True,optimizer_updates=0)
        results.append(result);write(OUT/f'u{u+1:03d}.json',result);write(HERE/'progress.json',dict(completed=len(results),total=27,last_update=u+1))
        print('GRADIENT_UPDATE',u+1,'COMPLETE',flush=True)
        del net,B,R,raw,bn,params,gpg,gv,gd,pg,vf,det,vectors,old
    sh.check();assert sources()==source
    write(HERE/'report.json',dict(complete=True,updates=results,source_binding=source,optimizer_updates=0,new_checkpoint=False,development_predictions=0))
    print('RL_GRADIENT_COLLECTED')
if __name__=='__main__':main()
