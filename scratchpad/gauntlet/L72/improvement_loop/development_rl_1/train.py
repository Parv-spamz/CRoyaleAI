import copy,datetime,os,time
from unittest.mock import patch
from shared import *
def main():
    assert not (HERE/'training_started.json').exists();p=check();runtime,RL=initialize_runtime();assert runtime==p['runtime']
    np.load=forbidden  # This phase consumes fresh simulated trajectories only, never an expert npz.
    from pipeline import e1_eval as E,search_s0 as S
    from pipeline.royale_env import RoyaleSelfPlayEnv
    from pipeline.eval_gen import load_model
    terminal=module('outcome_terminal',HERE.parent/'terminal_wrapper/adapter.py')
    net,state=load_model(INIT,'cuda');net.eval();ref=copy.deepcopy(net).eval()
    for q in ref.parameters():q.requires_grad_(False)
    policy=E.GenPolicy(net,state['card_vocab']);opps={}
    for name,path in [('gen',g.OPP_GEN),('s1',g.OPP_S1)]:
        pol,info=E.load_policy(path,'cuda');opps[name]=(pol,S.live_cfg(.27,info['grid'],'cuda'))
    cfg=S.live_cfg(.35,state['args']['grid'],'cuda');cfg.update(policy='sample',T=.5,record=True,record_tick=True)
    opt=torch.optim.Adam(net.parameters(),lr=CONFIG['lr']);rng=np.random.default_rng(CONFIG['seed']);beta=.3;guards=RL.Guards(CONFIG)
    write(HERE/'training_started.json',dict(pid=os.getpid(),utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),prepared_sha256=sha(HERE/'prepared.json'),runtime=runtime,parent_sha256=sha(INIT)))
    setups={s['spec']['tag']:s for s in p['setups']};total_games=0;logs=[]
    class BoundMatch(terminal.TerminalAwareMatch):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,stop_decisions_at_fulltime=True,**kwargs)
            expected=setups[self.spec['tag']]
            self.initial=g.blobsha(self.env.core.save_state())
            assert self.initial==expected['initial_state_sha256'] and self.env.loaded_forms==expected['forms'] and not self.env.form_fallbacks
        def result(self):
            r=super().result();st=self.env.core.state()
            r['native']=dict(tick=int(st.tick),winner=int(st.winner),game_over=bool(st.game_over),terminated=bool(self.env.terminated),crowns=[int(x.crowns) for x in st.players],state_sha256=g.blobsha(self.env.core.save_state()),initial_state_sha256=self.initial)
            assert r['native']['game_over'] and r['native']['terminated'] and r['form_fallbacks']==[]
            assert np.all(r['traj']['tick']<int(st.regular_ticks+st.overtime_ticks))
            return r
    for u in range(32):
        if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime(2026,10,6,4,tzinfo=datetime.timezone.utc):
            write(HERE/'cutoff.json',dict(completed_updates=u,completed_games=total_games));raise RuntimeError('Tuesday cutoff before next update')
        t0=time.perf_counter();ss=[x['spec'] for x in p['setups'] if x['spec']['update']==u];assert len(ss)==8
        made=[]
        def factory():
            e=RoyaleSelfPlayEnv(decision_ticks=10,tail_cap=7200,forms_mode='deck',hero_abilities=True,ability_policy='v2');made.append(e);return e
        results=[]
        with patch.object(E,'SelfPlayMatch',BoundMatch):
            E.run_selfplay_batch(factory,policy,opps,RL.rollout_jobs([(s['index'],s,0) for s in ss],u),cfg,8,on_result=results.append)
        for env in made:env.close()
        results.sort(key=lambda r:r['entry_index']);assert [r['entry_index'] for r in results]==list(range(8))
        raw=[]
        for r in results:
            i=r['entry_index'];f=OUT/'rollouts'/f'u{u:03d}_{i}.npz';np.savez_compressed(f,**r['traj'])
            record={k:RL._py(v) for k,v in r.items() if k!='traj'};record['trajectory']=str(f.relative_to(ROOT));record['trajectory_sha256']=sha(f);raw.append(record)
        rawpath=OUT/'rollouts'/f'u{u:03d}.json';write(rawpath,raw)
        bn,bst=RL.collate(results,advantage='gae',gamma_tick=CONFIG['gae_gamma_tick'],gae_terminal_gap=True)
        B=RL.to_device(bn,'cuda');n=len(bn['A']);maxdev=0.;new_lp=[]
        with torch.no_grad():
            for lo in range(0,n,128):
                ix=torch.arange(lo,min(lo+128,n),device='cuda');terms=RL.policy_terms(net,B,ix,.35,.5)
                lp=terms['lp_gate']+terms['lp_card']+terms['lp_cell'];new_lp.append(lp.cpu().numpy())
                d=torch.expm1(lp-B['lp_old'][ix]).abs()
                assert torch.isfinite(d).all();maxdev=max(maxdev,float(d.max()))
        assert maxdev<1e-4,('on-policy discrepancy before optimization',u,maxdev)
        R=RL.ref_terms(ref,B,.35,.5);gs=RL.gae_batch(net,B,CONFIG);warm=u<5
        contract=OUT/'rollouts'/f'u{u:03d}_contract.npz'
        np.savez_compressed(contract,lp_new=np.concatenate(new_lp),match=bn['match'],r_step=bn['r_step'],gamma_row=bn['gamma_row'],v_old=B['v_old'].cpu().numpy(),advantage=B['A'].cpu().numpy(),returns=B['ret'].cpu().numpy())
        mon=RL.rollout_monitors(results,.35,.5)
        if u==0:guards.set_baselines(mon)
        upd=RL.ppo_update(net,opt,B,R,CONFIG,beta,rng,vf=dict(coef=.5,clip=.2,policy=not warm,trunk_grad=True))
        assert not upd['nonfinite'] and all(torch.isfinite(v).all() for v in net.state_dict().values())
        reasons=guards.after_update(mon,beta,upd['kl_cell'] or 0,upd['kl_gate'] or 0,ent=upd['ent'],ent_init=R['ent'])
        if not warm:beta=RL.adapt_beta(beta,RL.leash_kl(upd,'max')[0],.10,.03,3.)
        total_games+=8
        rec=dict(update=u+1,games=8,total_games=total_games,rows=n,critic_warmup=warm,on_policy_maxdev=maxdev,ppo=upd,gae=gs,monitors=mon,beta_next=beta,guards=guards.s,stop=reasons,rollouts_sha256=sha(rawpath),contract_sha256=sha(contract),wall_seconds=time.perf_counter()-t0)
        logs.append(rec)
        with (OUT/'train.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(RL._py(rec),allow_nan=False)+'\n')
        payload={k:state[k] for k in ('args','deck','epoch','n_params','gen','d_c','card_vocab')}
        payload.update(model={k:v.detach().cpu() for k,v in net.state_dict().items()},development_rl_1=dict(update=u+1,runtime=runtime,config=CONFIG,parent_sha256=sha(INIT),prepared_sha256=sha(HERE/'prepared.json'),eligible_final=u==31 and not reasons))
        cp=OUT/'checkpoints'/f'u{u+1:03d}.pt';assert not cp.exists();torch.save(payload,cp)
        write(HERE/'progress.json',dict(update=u+1,total_updates=32,games=total_games,last_checkpoint_sha256=sha(cp),stop=reasons))
        print('OUTCOME_UPDATE',u+1,total_games,'WLD',mon['W'],mon['L'],mon['D'],'STOP',reasons,flush=True)
        if reasons:write(HERE/'stopped.json',dict(update=u+1,reasons=reasons,qualifying_candidate=False));raise RuntimeError('Registered training guard stopped candidate')
        del B,R,results,bn
    check();assert total_games==256
    final=OUT/'checkpoints/u032.pt';checkmodel,_=load_model(final,'cpu');assert all(torch.equal(v.detach().cpu(),checkmodel.state_dict()[k]) for k,v in net.state_dict().items())
    write(HERE/'trained.json',dict(complete=True,updates=32,games=256,checkpoint=str(final.relative_to(ROOT)),checkpoint_sha256=sha(final),train_log_sha256=sha(OUT/'train.jsonl'),runtime=runtime,prepared_sha256=sha(HERE/'prepared.json'),deployment_accepted=False))
    print('OUTCOME_RL_TRAIN_COMPLETE')
if __name__=='__main__':main()
