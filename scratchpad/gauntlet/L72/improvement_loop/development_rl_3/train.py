"""One serial GPU chain, paired whole-game versus late-row outcome learning."""
import copy,os,time
from unittest.mock import patch
from shared import *
from selection import select,draws
def main():
    cutoff();assert not (HERE/'training_started.json').exists();p=check();runtime,RL=initialize_runtime();assert runtime==p['runtime']
    load=np.load
    def own_load(path,*a,**kw):
        assert OUT.resolve() in Path(path).resolve().parents,'External arrays forbidden during training'
        return load(path,*a,**kw)
    np.load=own_load
    from pipeline import e1_eval as E,search_s0 as S
    from pipeline.royale_env import RoyaleSelfPlayEnv
    from pipeline.eval_gen import load_model
    terminal=module('late_curriculum_terminal',HERE.parent/'terminal_wrapper/adapter.py')
    nets={};opts={};policies={};guards={};betas={}
    for arm in ARMS:
        net,state=load_model(INIT,'cuda');net.eval();nets[arm]=net;policies[arm]=E.GenPolicy(net,state['card_vocab'])
        opts[arm]=torch.optim.Adam(net.parameters(),lr=CONFIG['lr']);guards[arm]=RL.Guards(CONFIG);betas[arm]=.3
    assert tensor_hash(nets[ARMS[0]])==tensor_hash(nets[ARMS[1]])
    initial_nonvalue=tensor_hash(nets[ARMS[0]],True);ref=copy.deepcopy(nets[ARMS[0]]).eval()
    for v in ref.parameters():v.requires_grad_(False)
    opps={}
    for name,path in [('gen',g.OPP_GEN),('s1',g.OPP_S1)]:
        pol,info=E.load_policy(path,'cuda');opps[name]=(pol,S.live_cfg(.27,info['grid'],'cuda'))
    cfg=S.live_cfg(.35,state['args']['grid'],'cuda');cfg.update(policy='sample',T=.5,record=True,record_tick=True,noise_off='all')
    assert cfg['action_delay_ticks']==cfg['extrapolate_ticks']==26
    write(HERE/'training_started.json',dict(pid=os.getpid(),utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),prepared_sha256=sha(HERE/'prepared.json'),runtime=runtime,parent_sha256=sha(INIT)))
    logs=[]
    for u in range(UPDATES):
        for arm in ARMS:
            cutoff();check();t0=time.perf_counter();net=nets[arm];net.eval();torch.manual_seed(DRAW_SEED+u)
            ss=p['setups'][u*GAMES:(u+1)*GAMES];rd=OUT/arm/'rollouts';prefix=f'u{u:03d}'
            class BoundMatch(terminal.TerminalAwareMatch):
                def __init__(self,*a,**kw):
                    super().__init__(*a,stop_decisions_at_fulltime=True,**kw)
                    self.initial_bytes=bytes(self.env.core.save_state());self.initial_forms=self.env.loaded_forms
                    i=self.spec['index'];ex=ss[i]
                    assert self.spec==ex['spec'] and self.initial_bytes==(ROOT/ex['initial_state_path']).read_bytes()
                    assert form_match(self.initial_forms,ex['forms']) and not self.env.form_fallbacks
                def result(self):
                    r=super().result();st=self.env.core.state();i=r['entry_index'];fp=rd/f'{prefix}_{i}_final.bin'
                    assert not fp.exists();fp.write_bytes(bytes(self.env.core.save_state()))
                    r['readiness']=dict(initial=dict(path=ss[i]['initial_state_path'],sha256=g.blobsha(self.initial_bytes),forms=self.initial_forms),
                        phase=dict(regular_ticks=int(st.regular_ticks),overtime_ticks=int(st.overtime_ticks)),
                        native=dict(tick=int(st.tick),winner=int(st.winner),crowns=[int(x.crowns) for x in st.players],game_over=bool(st.game_over),
                            terminated=bool(self.env.terminated),path=str(fp.relative_to(ROOT)),sha256=sha(fp)),opponent_plays=self.opp.plays)
                    return r
            results=[];records=[]
            for lo in range(0,GAMES,4):
                cutoff();made=[];batch=[]
                def factory():
                    env=RoyaleSelfPlayEnv(decision_ticks=10,tail_cap=7200,forms_mode='deck',hero_abilities=True,ability_policy='v2');made.append(env);return env
                def save_finished(r):
                    i=int(r['entry_index']);fp=rd/f'{prefix}_{i}_full.npz';rp=rd/f'{prefix}_{i}_result.json'
                    assert not fp.exists() and not rp.exists();np.savez_compressed(fp,**r['traj']);write(rp,RL._py({k:v for k,v in r.items() if k!='traj'}))
                    records.append(dict(index=i,full=str(fp.relative_to(ROOT)),full_sha256=sha(fp),result=str(rp.relative_to(ROOT)),result_sha256=sha(rp)));batch.append(r)
                with patch.object(E,'SelfPlayMatch',BoundMatch):
                    E.run_selfplay_batch(factory,policies[arm],opps,RL.rollout_jobs([(i,ss[i]['spec'],0) for i in range(lo,lo+4)],u),cfg,4,on_result=save_finished)
                assert len(batch)==4;results.extend(batch)
                for env in made:env.close()
                write(HERE/'progress.json',dict(update=u+1,total_updates=UPDATES,arm=arm,games_in_update=len(results),total_games=len(logs)*GAMES+len(results),completed_arm_updates=len(logs)))
            results.sort(key=lambda r:r['entry_index']);records.sort(key=lambda r:r['index']);views=[]
            assert [r['entry_index'] for r in results]==list(range(GAMES))
            for r,x in zip(results,records):
                view,ix,bound=select(r,arm==ARMS[1]);views.append(view)
                x.update(selected_indices=ix.tolist(),boundary=bound,selected_contributing=int((view['traj']['played']|view['traj']['gate_sampled']).sum()))
            rp=rd/f'{prefix}_records.json';write(rp,records)
            eligible_games=sum(x['selected_contributing']>0 for x in records);eligible_rows=sum(x['selected_contributing'] for x in records)
            assert eligible_games>=4 and eligible_rows>=256,('Fixed cohort insufficient; no resampling',u,arm,eligible_games,eligible_rows)
            bn,stats=RL.collate(views,advantage='gae',gamma_tick=.99994,gae_terminal_gap=True);assert len(bn['A'])==eligible_rows
            public_keys=list(E.gen_row_keys(net));assert all(k in bn for k in public_keys) and 'phi_state' not in bn
            bp=rd/f'{prefix}_eligible.npz';np.savez_compressed(bp,**bn)
            B=RL.to_device(bn,'cuda');n=len(bn['A']);new_lp=[]
            with torch.no_grad():
                for lo in range(0,n,128):
                    terms=RL.policy_terms(net,B,torch.arange(lo,min(n,lo+128),device='cuda'),.35,.5)
                    new_lp.append((terms['lp_gate']+terms['lp_card']+terms['lp_cell']).cpu().numpy())
            lp=np.concatenate(new_lp);delta=np.abs(np.expm1(lp-bn['lp_old']));assert np.isfinite(delta).all() and delta.max()<1e-4
            value=RL.value_rows(net,B).cpu().numpy();adv,ret=RL.gae(bn['r_step'],value,bn['match'],bn['gamma_row'],.95)
            uniforms=np.random.default_rng(DRAW_SEED+u).random((DRAWS,2));draw=draws(bn['match'],uniforms)
            d={k:v[draw].copy() for k,v in bn.items()};da=adv[draw];d.update(A=(da-da.mean())/(da.std()+1e-8),w=np.full(DRAWS,1./DRAWS),ret=ret[draw],v_old=value[draw])
            dp=rd/f'{prefix}_drawn.npz';np.savez_compressed(dp,**d)
            cp=rd/f'{prefix}_contract.npz';np.savez_compressed(cp,lp_new=lp,value=value,raw_advantage=adv,returns=ret,uniforms=uniforms,draw=draw)
            del B
            B=RL.to_device(d,'cuda');R=RL.ref_terms(ref,B,.35,.5);warm=u<5;before=tensor_hash(net,True)
            mon=RL.rollout_monitors(results,.35,.5)
            if u==0:guards[arm].set_baselines(mon)
            upd=RL.ppo_update(net,opts[arm],B,R,CONFIG,betas[arm],np.random.default_rng(DRAW_SEED+1000+u),vf=dict(coef=.5,clip=.2,policy=not warm,trunk_grad=True))
            assert not upd['nonfinite'] and upd['steps']==16 and all(torch.isfinite(v).all() for v in net.state_dict().values())
            after=tensor_hash(net,True)
            if warm:assert before==after==initial_nonvalue
            reasons=guards[arm].after_update(mon,betas[arm],upd['kl_cell'] or 0,upd['kl_gate'] or 0,ent=upd['ent'],ent_init=R['ent'])
            if not warm:betas[arm]=RL.adapt_beta(betas[arm],RL.leash_kl(upd,'max')[0],.10,.03,3.)
            rec=dict(arm=arm,update=u+1,games=GAMES,eligible_games=eligible_games,rows=n,draws=DRAWS,critic_warmup=warm,nonvalue_before=before,nonvalue_after=after,
                on_policy_maxdev=float(delta.max()),ppo=upd,monitors=mon,beta_next=betas[arm],guards=guards[arm].s,stop=reasons,public_keys=public_keys,
                records_sha256=sha(rp),eligible_sha256=sha(bp),drawn_sha256=sha(dp),contract_sha256=sha(cp),wall_seconds=time.perf_counter()-t0)
            with (OUT/'train.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(RL._py(rec),allow_nan=False)+'\n')
            logs.append(rec)
            payload={k:state[k] for k in ('args','deck','epoch','n_params','gen','d_c','card_vocab')}
            payload.update(model={k:v.detach().cpu() for k,v in net.state_dict().items()},development_rl_3=dict(arm=arm,update=u+1,config=CONFIG,runtime=runtime,parent_sha256=sha(INIT),eligible_final=u==UPDATES-1 and not reasons))
            f=OUT/arm/'checkpoints'/f'u{u+1:03d}.pt';assert not f.exists();torch.save(payload,f)
            write(HERE/'progress.json',dict(update=u+1,total_updates=UPDATES,arm=arm,games_in_update=GAMES,total_games=len(logs)*GAMES,completed_arm_updates=len(logs),stop=reasons))
            print('CURRICULUM_UPDATE',u+1,arm,'ELIGIBLE',eligible_games,n,'WLD',mon['W'],mon['L'],mon['D'],'STOP',reasons,flush=True)
            if reasons:write(HERE/'stopped.json',dict(update=u+1,arm=arm,reasons=reasons));raise RuntimeError('Registered guard stopped paired trial')
            del B,R,results,views,bn,d,batch
    check();final={}
    for arm in ARMS:
        f=OUT/arm/'checkpoints'/f'u{UPDATES:03d}.pt';model,_=load_model(f,'cpu');assert tensor_hash(model)==tensor_hash(nets[arm])
        final[arm]=dict(checkpoint=str(f.relative_to(ROOT)),checkpoint_sha256=sha(f),tensor_sha256=tensor_hash(model))
    write(HERE/'trained.json',dict(complete=True,updates_per_arm=UPDATES,total_games=len(logs)*GAMES,total_optimizer_steps=sum(x['ppo']['steps'] for x in logs),arms=final,
        train_log_sha256=sha(OUT/'train.jsonl'),sources=p['sources'],runtime=runtime,deployment_accepted=False))
    print('LATE_CURRICULUM_TRAINED')
if __name__=='__main__':main()
