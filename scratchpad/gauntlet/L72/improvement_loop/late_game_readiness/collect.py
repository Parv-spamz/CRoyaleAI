"""Fresh complete games, then a read-only late learning view; zero updates."""
import math,os
from unittest.mock import patch
import numpy as np
import torch
from common import *
from selection import late_view
def forbidden(*args,**kwargs):raise AssertionError('Legacy dataset/stock learner access forbidden')
def main():
    cutoff();assert not (HERE/'started.json').exists()
    assert read(HERE.parent/'rl_readiness/verified.json')['complete']
    assert read(HERE.parent/'terminal_wrapper_policy/reviewed_results.json')['complete']
    bound=sources();OUT.mkdir(exist_ok=False);torch.set_num_threads(1)
    from pipeline.royale_runtime import activate
    runtime=activate()
    from pipeline import e1_eval as E,rl_royale as RL,search_s0 as S
    from pipeline.royale_env import RoyaleSelfPlayEnv
    terminal=module('late_terminal',HERE.parent/'terminal_wrapper/adapter.py')
    orig_load=np.load
    def local_load(path,*args,**kwargs):
        assert OUT.resolve() in Path(path).resolve().parents,'External arrays forbidden'
        return orig_load(path,*args,**kwargs)
    np.load=local_load;RL.gen_v3val_arrays=forbidden;RL.Learner.__init__=forbidden
    pol,info=E.load_policy(g.CKPTS['ordinary_v5'],'cuda');net=pol.model
    original={k:v.detach().cpu().clone() for k,v in net.state_dict().items()}
    opps={}
    for name,path in [('gen',g.OPP_GEN),('s1',g.OPP_S1)]:
        p,inf=E.load_policy(path,'cuda');opps[name]=(p,S.live_cfg(.27,inf['grid'],'cuda'))
    cfg=S.live_cfg(.35,info['grid'],'cuda');cfg.update(policy='sample',T=.5,record=True,record_tick=True,noise_off='all')
    assert cfg['action_delay_ticks']==cfg['extrapolate_ticks']==26
    ss=scenarios();write(HERE/'started.json',dict(pid=os.getpid(),utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),sources=bound,runtime=runtime,scenarios=ss))
    class RecordedMatch(terminal.TerminalAwareMatch):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,stop_decisions_at_fulltime=True,**kwargs)
            self.initial_bytes=bytes(self.env.core.save_state())
            self.initial_forms=self.env.loaded_forms
        def result(self):
            r=super().result();st=self.env.core.state();idx=int(r['entry_index'])
            ip=OUT/f'{idx}_initial.bin';fp=OUT/f'{idx}_final.bin'
            assert not ip.exists() and not fp.exists()
            ip.write_bytes(self.initial_bytes);fp.write_bytes(bytes(self.env.core.save_state()))
            r['readiness']=dict(initial=dict(path=str(ip.relative_to(ROOT)),sha256=sha(ip),forms=self.initial_forms),
                phase=dict(regular_ticks=int(st.regular_ticks),overtime_ticks=int(st.overtime_ticks)),
                native=dict(tick=int(st.tick),winner=int(st.winner),crowns=[int(x.crowns) for x in st.players],
                    game_over=bool(st.game_over),terminated=bool(self.env.terminated),path=str(fp.relative_to(ROOT)),sha256=sha(fp)),
                opponent_plays=self.opp.plays)
            return r
    results=[]
    for lo in range(0,16,4):
        cutoff();made=[];batch=[]
        def save_finished(r):
            i=int(r['entry_index']);fp=OUT/f'{i}_full.npz';rp=OUT/f'{i}_result.json'
            assert not fp.exists() and not rp.exists()
            np.savez_compressed(fp,**r['traj'])
            write(rp,RL._py({k:v for k,v in r.items() if k!='traj'}));batch.append(r)
        def factory():
            e=RoyaleSelfPlayEnv(decision_ticks=10,tail_cap=7200,forms_mode='deck',hero_abilities=True,ability_policy='v2');made.append(e);return e
        with patch.object(E,'SelfPlayMatch',RecordedMatch):
            E.run_selfplay_batch(factory,pol,opps,RL.rollout_jobs([(i,ss[i],0) for i in range(lo,lo+4)],0),cfg,4,on_result=save_finished)
        assert len(batch)==4
        results.extend(sorted(batch,key=lambda r:r['entry_index']))
        for e in made:e.close()
        write(HERE/'progress.json',dict(games=len(results),total=16,optimizer_updates=0));print('GAMES',len(results),flush=True)
    records=[];late=[];raw_late_rows=0;late_games=0
    for i,r in enumerate(results):
        assert r['entry_index']==i and r['league']==ss[i] and not r['form_fallbacks']
        t=r['traj'];d=r['readiness'];assert d['native']['game_over'] and d['native']['terminated']
        assert np.all(t['tick']<sum(d['phase'].values())) and len(t['tick'])
        assert set(E.gen_row_keys(net))<=set(t) and 'phi_state' not in t
        view,idx,boundary=late_view(r);late.append(view)
        assert all(np.array_equal(view['traj'][k],t[k][idx]) for k in t)
        paths={}
        for name,a in [('full',t),('late',view['traj'])]:
            p=OUT/f'{i}_{name}.npz'
            if name=='late':
                assert not p.exists();np.savez_compressed(p,**a)
            else:assert p.exists()
            paths[name]=str(p.relative_to(ROOT));paths[name+'_sha256']=sha(p)
        p=OUT/f'{i}_result.json';assert p.exists()
        keep=view['traj']['gate_sampled']|view['traj']['played'];n=int(keep.sum());late_games+=n>0;raw_late_rows+=n
        records.append(dict(index=i,**paths,result=str(p.relative_to(ROOT)),result_sha256=sha(p),boundary=boundary,
            late_indices=idx.tolist(),full_decisions=len(t['tick']),late_decisions=len(idx),late_contributing=n))
    # Preserve completed games before checking whether this fixed curriculum has enough coverage.
    write(HERE/'collected.json',dict(complete=True,records=records,late_games=late_games,late_rows=raw_late_rows,sources=bound,runtime=runtime,optimizer_updates=0))
    assert late_games>=4 and raw_late_rows>=256,('Insufficient fixed late coverage',late_games,raw_late_rows)
    batches={};caches={};summaries={}
    for name,rs in [('full',results),('late',late)]:
        bn,counts=RL.collate(rs,advantage='gae',gamma_tick=GAMMA,gae_terminal_gap=True);b=RL.to_device(bn,'cuda');batches[name]=b
        ticks=np.concatenate([r['traj']['tick'][r['traj']['gate_sampled']|r['traj']['played']] for r in rs])
        n=len(ticks);v=RL.value_rows(net,b).cpu().numpy();cache={k:bn[k] for k in ('match','w','r_step','gamma_row','lp_old')};cache.update(tick=ticks,value=v)
        for lam in (.95,1.):
            a,ret=RL.gae(bn['r_step'],v,bn['match'],bn['gamma_row'],lam);s='95' if lam==.95 else '1'
            cache['adv'+s]=a;cache['ret'+s]=ret
        cache['normalized_adv95']=(cache['adv95']-cache['adv95'].mean())/(cache['adv95'].std()+1e-8)
        caches[name]=cache
        lags=np.array([results[int(j)]['end_tick'] for j in bn['match']])-ticks
        summaries[name]=dict(counts=counts,rows=n,played=int(bn['played'].sum()),median_terminal_seconds=float(np.median(lags)/20),max_terminal_seconds=float(lags.max()/20))
    fc=caches['full'];lc=caches['late'];select=np.array([t>=records[int(j)]['boundary'] for j,t in zip(fc['match'],fc['tick'])])
    assert np.array_equal(fc['match'][select],lc['match']) and np.array_equal(fc['tick'][select],lc['tick'])
    # Value evaluation may use a different batch shape; use full-row values in both recurrences.
    # This is the unchanged same-state critic, with separately measured numerical differences.
    value_delta=float(np.max(np.abs(fc['value'][select]-lc['value'])))
    assert value_delta<1e-5
    lc['separately_recomputed_value']=lc['value'].copy();lc['value']=fc['value'][select].copy()
    for s,lam in [('95',.95),('1',1.)]:
        lc['adv'+s],lc['ret'+s]=RL.gae(lc['r_step'],lc['value'],lc['match'],lc['gamma_row'],lam)
        assert np.array_equal(fc['adv'+s][select],lc['adv'+s]) and np.array_equal(fc['ret'+s][select],lc['ret'+s])
    lc['normalized_adv95']=(lc['adv95']-lc['adv95'].mean())/(lc['adv95'].std()+1e-8)
    b=batches['late'];n=len(lc['tick']);re={k:[] for k in ('lp_gate','lp_card','lp_cell')}
    with torch.no_grad():
        for lo in range(0,n,128):
            terms=RL.policy_terms(net,b,torch.arange(lo,min(lo+128,n),device='cuda'),.35,.5)
            for k in re:re[k].append(terms[k].cpu().numpy())
    lc.update({k:np.concatenate(v) for k,v in re.items()})
    ratio=np.abs(np.expm1(lc['lp_gate']+lc['lp_card']+lc['lp_cell']-lc['lp_old']))
    assert np.isfinite(ratio).all() and ratio.max()<1e-4
    for name,cache in caches.items():
        p=OUT/f'{name}_cache.npz';np.savez_compressed(p,**cache);summaries[name].update(cache=str(p.relative_to(ROOT)),cache_sha256=sha(p))
    b['A']=torch.from_numpy(lc['normalized_adv95']).to('cuda');b['v_old']=torch.from_numpy(lc['value']).to('cuda');b['ret']=torch.from_numpy(lc['ret95']).to('cuda')
    ref=RL.ref_terms(net,b,.35,.5);idx=torch.arange(min(256,n),device='cuda');net.zero_grad(set_to_none=True)
    loss,_=RL.minibatch_loss(net,b,ref,idx,tau=.35,T=.5,clip=.2,beta=.3,n_total=n);loss.backward()
    groups={}
    for prefix in ('gate_head','card','query','cell_key'):
        groups[prefix]=sum(float(p.grad.double().square().sum()) for name,p in net.named_parameters() if prefix in name and p.grad is not None)
    assert all(math.isfinite(x) and x>0 for x in groups.values()),groups
    assert all(torch.isfinite(p.grad).all() for p in net.parameters() if p.grad is not None)
    net.zero_grad(set_to_none=True)
    vloss,_=RL.minibatch_loss(net,b,ref,idx,tau=.35,T=.5,clip=.2,beta=.3,n_total=n,vf=dict(coef=.5,clip=.2,policy=False,trunk_grad=False));vloss.backward()
    vg=sum(float(p.grad.double().square().sum()) for name,p in net.named_parameters() if name.startswith('value_head') and p.grad is not None)
    assert math.isfinite(vg) and vg>0 and all(torch.isfinite(p.grad).all() for p in net.parameters() if p.grad is not None)
    assert all(torch.equal(original[k],v.detach().cpu()) for k,v in net.state_dict().items());net.zero_grad(set_to_none=True)
    assert sources()==bound
    write(HERE/'report.json',dict(complete=True,records=records,summaries=summaries,late_games=late_games,late_rows=raw_late_rows,
        ratio_maxdev=float(ratio.max()),value_batch_max_difference=value_delta,policy_gradient_squares=groups,critic_gradient_square=vg,
        unchanged_parameters=True,optimizer_updates=0,new_models=0,deployed=False,sources=bound,runtime=runtime,public_keys=list(E.gen_row_keys(net))))
    print('LATE_GAME_READINESS_COLLECTED')
if __name__=='__main__':main()
