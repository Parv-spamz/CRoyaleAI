"""Fixed CPU auxiliary effect predictors; cannot issue game actions."""
import hashlib, sys
import numpy as np
import torch
from common import *

def tensor_sha(model):
    h=hashlib.sha256()
    for k,v in model.state_dict().items():h.update(k.encode());h.update(v.detach().cpu().numpy().tobytes())
    return h.hexdigest()

def main():
    cutoff();assert not (HERE/'trained.json').exists();torch.set_num_threads(1);torch.use_deterministic_algorithms(True)
    verified=read(HERE/'data_verified.json');report=read(HERE/'collected.json')
    assert verified['complete'] and verified['report_sha256']==sha(HERE/'collected.json') and verified['data_sha256']==report['data_sha256']
    assert sha(ROOT/report['data_path'])==report['data_sha256']
    frozen=sources();assert frozen==report['sources']
    data=read(ROOT/report['data_path']);rows=data['rows'];ix=np.array([i for i,r in enumerate(rows) if r['split']=='training'],dtype=np.int64)
    x=np.asarray([r['features'] for r in rows],dtype=np.float32);y=np.asarray([r['label'] for r in rows],dtype=np.float32)
    assert x.shape==(13824,28) and len(ix)==9216 and np.isfinite(x).all() and set(y)=={0,1}
    train_y=torch.from_numpy(y[ix]);weight=torch.tensor(float((train_y==0).sum()/(train_y==1).sum()))
    results=[];initials={}
    write(HERE/'training_started.json',dict(sources=frozen,data_sha256=report['data_sha256'],device='cpu',torch=str(torch.__version__),training_rows=len(ix),positive_weight=float(weight)))
    for seed in (2026101200,2026101201,2026101202):
        rng=np.random.default_rng(seed+1);draws=np.stack([rng.integers(0,len(ix),size=256,dtype=np.int64) for _ in range(1000)])
        global_draws=ix[draws];drawpath=OUT/f'draws_{seed}.npy';np.save(drawpath,global_draws,allow_pickle=False)
        for arm in ('static_public','motion_public'):
            cutoff();torch.manual_seed(seed)
            net=torch.nn.Sequential(torch.nn.Linear(28,64),torch.nn.ReLU(),torch.nn.Linear(64,64),torch.nn.ReLU(),torch.nn.Linear(64,1))
            initial=tensor_sha(net)
            if seed in initials:assert initial==initials[seed]
            else:initials[seed]=initial
            xx=x.copy()
            if arm=='static_public':xx[:,VELOCITY]=0
            train_x=torch.from_numpy(xx[ix]);opt=torch.optim.Adam(net.parameters(),lr=.001)
            trace=[]
            for update,selected in enumerate(draws,1):
                cutoff();net.train();opt.zero_grad(set_to_none=True)
                logits=net(train_x[selected]).squeeze(-1)
                loss=torch.nn.functional.binary_cross_entropy_with_logits(logits,train_y[selected],pos_weight=weight)
                assert torch.isfinite(loss);loss.backward();norm=torch.nn.utils.clip_grad_norm_(net.parameters(),1.)
                assert torch.isfinite(norm) and all(p.grad is None or torch.isfinite(p.grad).all() for p in net.parameters())
                opt.step();assert all(torch.isfinite(p).all() for p in net.parameters())
                trace.append(dict(update=update,loss=float(loss.detach()),gradient_norm=float(norm)))
                if update%100==0:
                    write(HERE/'progress.json',dict(stage='training',arm=arm,seed=seed,update=update,total_updates=1000))
                    print('TRAIN',arm,seed,update,trace[-1]['loss'],flush=True)
            net.eval()
            with torch.no_grad():prob=torch.sigmoid(net(torch.from_numpy(xx)).squeeze(-1)).double().numpy()
            assert np.isfinite(prob).all() and np.all((prob>=0)&(prob<=1))
            name=f'{arm}_{seed}';checkpoint=OUT/(name+'.pt');torch.save(dict(state_dict=net.state_dict(),architecture=[28,64,64,1],arm=arm,seed=seed,updates=1000,torch=str(torch.__version__),policy=False),checkpoint)
            pp=OUT/(name+'_probabilities.json');write(pp,prob.tolist());tp=OUT/(name+'_trace.json');write(tp,trace)
            per_root={rid:float(np.mean((prob[[i for i,r in enumerate(rows) if r['root_id']==rid]]-y[[i for i,r in enumerate(rows) if r['root_id']==rid]])**2)) for rid in sorted({r['root_id'] for r in rows})}
            result=dict(arm=arm,seed=seed,updates=1000,initial_tensor_sha256=initial,final_tensor_sha256=tensor_sha(net),checkpoint_path=str(checkpoint.relative_to(ROOT)),checkpoint_sha256=sha(checkpoint),probability_path=str(pp.relative_to(ROOT)),probability_sha256=sha(pp),trace_path=str(tp.relative_to(ROOT)),trace_sha256=sha(tp),draw_path=str(drawpath.relative_to(ROOT)),draw_sha256=sha(drawpath),metrics=metrics(prob,y,rows),per_root_brier=per_root)
            results.append(result);write(HERE/'training_progress_results.json',results)
    assert sources()==frozen
    verdict=filters(results)
    write(HERE/'trained.json',dict(complete=True,sources=frozen,data_sha256=report['data_sha256'],data_verifier_sha256=sha(HERE/'data_verified.json'),results=results,filters=verdict,continuation_pass=all(verdict.values()),policy_acceptance=False,deployed=False,training_updates=6000))
    print('IMPACT_LEARNING_TRAINED')

if __name__=='__main__':main()
