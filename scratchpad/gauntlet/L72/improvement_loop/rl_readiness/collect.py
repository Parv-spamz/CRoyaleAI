import copy,datetime,functools,math,os
from unittest.mock import patch
import numpy as np
import torch
from common import *

def forbidden(*args,**kwargs):raise AssertionError('Legacy validation/learner access forbidden in readiness')
def main():
    assert not (HERE/'started.json').exists()
    assert read(HERE.parent/'terminal_wrapper_policy/reviewed_results.json')['complete']
    bound=sources();OUT.mkdir(exist_ok=False)
    torch.set_num_threads(1)
    from pipeline.royale_runtime import activate
    stamp=activate()
    from pipeline import e1_eval as E,rl_royale as RL,search_s0 as S
    from pipeline.royale_env import RoyaleSelfPlayEnv
    spec=importlib.util.spec_from_file_location('ready_terminal',HERE.parent/'terminal_wrapper/adapter.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    # Runtime reads of expert npz datasets are forbidden; checkpoints are separate.
    orig_load=np.load
    def local_np_load(path,*args,**kwargs):
        assert OUT.resolve() in Path(path).resolve().parents,'Expert/confirmation array access forbidden'
        return orig_load(path,*args,**kwargs)
    np.load=local_np_load
    RL.gen_v3val_arrays=forbidden;RL.Learner.__init__=forbidden
    ss=scenarios();models={};infos={}
    for arm in ARMS:models[arm],infos[arm]=E.load_policy(g.CKPTS[arm],'cuda')
    opps={}
    for name,path in [('gen',g.OPP_GEN),('s1',g.OPP_S1)]:
        pol,info=E.load_policy(path,'cuda');opps[name]=(pol,S.live_cfg(.27,info['grid'],'cuda'))
    write(HERE/'started.json',dict(pid=os.getpid(),utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),sources=bound,runtime=stamp,scenarios=ss))
    initial={};records=[];gradients={}
    class RecordedMatch(mod.TerminalAwareMatch):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,stop_decisions_at_fulltime=True,**kwargs)
            self.initial=dict(state_sha256=blobsha(self.env.core.save_state()),forms=self.env.loaded_forms)
        def result(self):
            r=super().result();st=self.env.core.state()
            r['readiness']=dict(initial=self.initial,boundary=int(st.regular_ticks+st.overtime_ticks),native=dict(tick=int(st.tick),winner=int(st.winner),winner_side=int(self.env.episode.get('winner',-1)),crowns=[int(p.crowns) for p in st.players],game_over=bool(st.game_over),terminated=bool(self.env.terminated),state_sha256=blobsha(self.env.core.save_state())),plays=self.learner.plays)
            return r
    from pipeline.e1_eval import ICEBOW_ENGINE_DECK
    for arm in ARMS:
        pol=models[arm];net=pol.model;original={k:v.detach().cpu().clone() for k,v in net.state_dict().items()}
        results=[]
        cfg=S.live_cfg(.35,infos[arm]['grid'],'cuda');cfg.update(policy='sample',T=.5,record=True,record_tick=True,noise_off='all')
        assert cfg['action_delay_ticks']==cfg['extrapolate_ticks']==26 and cfg['noise_off']=='all'
        for i,s in enumerate(ss):
            if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime(2026,10,6,4,tzinfo=datetime.timezone.utc):raise RuntimeError('Tuesday cutoff before next readiness game')
            sp=dict(tag=s['tag'],seed=s['seed'],learner_side=s['side'],learner_deck=list(ICEBOW_ENGINE_DECK),opp_deck=s['opp_deck'],opp=dict(id=s['opp']))
            made=[]
            def factory():
                e=RoyaleSelfPlayEnv(decision_ticks=10,tail_cap=7200,forms_mode='deck',hero_abilities=True,ability_policy='v2');made.append(e);return e
            with patch.object(E,'SelfPlayMatch',RecordedMatch):
                one=[];E.run_selfplay_batch(factory,pol,opps,RL.rollout_jobs([(i,sp,0)],0),cfg,1,on_result=one.append)
            assert len(one)==1;r=one[0];results.append(r)
            assert r['form_fallbacks']==[] and r['readiness']['native']['game_over'] and r['readiness']['native']['terminated']
            initial.setdefault(str(i),r['readiness']['initial']);assert r['readiness']['initial']==initial[str(i)]
            t=r['traj'];assert all(k in t for k in E.gen_row_keys(net))
            assert set(E.gen_row_keys(net))<=set(t) and 'phi_state' not in t
            assert len(t['tick']) and np.all(t['tick']<r['readiness']['boundary'])
            path=OUT/f'{i}_{arm}_trajectory.npz';np.savez_compressed(path,**t)
            record={k:v for k,v in r.items() if k!='traj'}
            rp=OUT/f'{i}_{arm}_result.json';write(rp,RL._py(record))
            records.append(dict(arm=arm,scenario=i,trajectory=str(path.relative_to(ROOT)),trajectory_sha256=sha(path),result=str(rp.relative_to(ROOT)),result_sha256=sha(rp)))
            made[0].close();write(HERE/'progress.json',dict(games=len(records),total=8,last=f'{i}_{arm}'))
            print('COMPLETE',len(records),arm,i,flush=True)
        Bn,counts=RL.collate(results,advantage='gae',gamma_tick=GAMMA,gae_terminal_gap=True)
        B=RL.to_device(Bn,'cuda');n=len(Bn['A']);re={k:[] for k in ('lp_gate','lp_card','lp_cell')}
        with torch.no_grad():
            for lo in range(0,n,128):
                terms=RL.policy_terms(net,B,torch.arange(lo,min(lo+128,n),device='cuda'),.35,.5)
                for k in re:re[k].append(terms[k].cpu().numpy())
        re={k:np.concatenate(v) for k,v in re.items()}
        ratio=np.expm1(sum(re.values())-Bn['lp_old'])
        assert np.all(np.isfinite(ratio)) and np.max(np.abs(ratio))<RATIO_LIMIT
        _,analytic=RL.gae(Bn['r_step'],np.zeros(n),Bn['match'],Bn['gamma_row'],1.)
        cache=OUT/f'{arm}_recomputed.npz'
        np.savez_compressed(cache,**re,match=Bn['match'],r_step=Bn['r_step'],gamma_row=Bn['gamma_row'],analytic=analytic)
        # Backward-only probe on a fixed prefix, with no optimizer construction.
        ac=dict(advantage='gae',gae_gamma_unit='tick',gae_gamma_tick=GAMMA,gae_terminal_gap=True,gae_lambda=1.)
        gst=RL.gae_batch(net,B,ac);ref=RL.ref_terms(net,B,.35,.5)
        idx=torch.arange(min(256,n),device='cuda');net.zero_grad(set_to_none=True)
        loss,_=RL.minibatch_loss(net,B,ref,idx,tau=.35,T=.5,clip=.2,beta=.3,n_total=n)
        loss.backward();groups={}
        for prefix in ('gate_head','card','query','cell_key'):
            gs=[p.grad for name,p in net.named_parameters() if prefix in name and p.grad is not None]
            groups[prefix]=sum(float(x.double().square().sum()) for x in gs)
        assert all(math.isfinite(x) and x>0 for x in groups.values()),groups
        assert all(torch.isfinite(p.grad).all() for p in net.parameters() if p.grad is not None)
        net.zero_grad(set_to_none=True)
        vloss,_=RL.minibatch_loss(net,B,ref,idx,tau=.35,T=.5,clip=.2,beta=.3,n_total=n,vf=dict(coef=.5,clip=.2,policy=False,trunk_grad=False))
        vloss.backward();vg=sum(float(p.grad.double().square().sum()) for name,p in net.named_parameters() if name.startswith('value_head') and p.grad is not None)
        assert math.isfinite(vg) and vg>0
        assert all(torch.equal(original[k],v.detach().cpu()) for k,v in net.state_dict().items())
        gradients[arm]=dict(policy_loss=float(loss.detach()),critic_loss=float(vloss.detach()),policy_gradient_squares=groups,critic_gradient_square=vg,unchanged_parameters=True,optimizer_updates=0,ratio_maxdev=float(np.max(np.abs(ratio))),rows=n,recomputed=str(cache.relative_to(ROOT)),recomputed_sha256=sha(cache),counts=counts,gae=gst,public_keys=list(E.gen_row_keys(net)))
        net.zero_grad(set_to_none=True)
    assert sources()==bound
    write(HERE/'report.json',dict(complete=True,records=records,gradients=gradients,initial=initial,runtime=stamp,sources=bound,optimizer_updates=0,new_models=0,legacy_dataset_access=False,deployment_accepted=False))
    print('RL_READINESS_COLLECTION_COMPLETE')
if __name__=='__main__':main()
