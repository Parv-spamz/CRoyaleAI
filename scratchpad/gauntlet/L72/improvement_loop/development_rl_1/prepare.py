"""Freeze all native setups and run one excluded, unsaved PPO smoke step."""
import copy,datetime,os
from shared import *
def main():
    assert not (HERE/'prepared.json').exists();prerequisites();bound=sources();runtime,RL=initialize_runtime()
    OUT.mkdir(exist_ok=False);(OUT/'rollouts').mkdir();(OUT/'checkpoints').mkdir()
    write(HERE/'preparation_started.json',dict(pid=os.getpid(),utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),sources=bound))
    from pipeline.royale_env import RoyaleSelfPlayEnv
    from pipeline.eval_gen import load_model
    ss=schedule();setups=[];env=RoyaleSelfPlayEnv(decision_ticks=10,tail_cap=7200,forms_mode='deck',hero_abilities=True,ability_policy='v2');env.feature_version=5
    for s in ss:
        decks={s['learner_side']:s['learner_deck'],1-s['learner_side']:s['opp_deck']};env.reset(decks[0],decks[1],s['seed']);assert not env.form_fallbacks
        setups.append(dict(spec=s,initial_state_sha256=g.blobsha(env.core.save_state()),forms=env.loaded_forms))
    env.close();assert len({s['spec']['seed'] for s in setups})==256
    model,_=load_model(INIT,'cuda');model.eval();ref=copy.deepcopy(model).eval()
    for p in ref.parameters():p.requires_grad_(False)
    rd=ROOT/'icebow/data/bench/rl_readiness_20261005';rs=[]
    for i in range(4):
        r=read(rd/f'{i}_ordinary_v5_result.json')
        with np.load(rd/f'{i}_ordinary_v5_trajectory.npz') as z:r['traj']={k:z[k] for k in z.files}
        rs.append(r)
    bn,_=RL.collate(rs,advantage='gae',gamma_tick=CONFIG['gae_gamma_tick'],gae_terminal_gap=True);B=RL.to_device(bn,'cuda')
    RL.gae_batch(model,B,CONFIG)
    # One fixed small prefix avoids an unbounded full-trajectory training batch.
    B={k:v[:min(128,len(bn['A']))] for k,v in B.items()}
    R=RL.ref_terms(ref,B,CONFIG['tau'],CONFIG['T']);before={k:v.clone() for k,v in model.state_dict().items()}
    opt=torch.optim.Adam(model.parameters(),lr=CONFIG['lr'])
    small=dict(CONFIG,ppo_epochs=1,minibatch=128)
    upd=RL.ppo_update(model,opt,B,R,small,.3,np.random.default_rng(CONFIG['seed']),vf=dict(coef=.5,clip=.2,policy=False,trunk_grad=False))
    assert not upd['nonfinite'] and upd['steps']==1 and upd['first']['ratio_maxdev']<1e-4
    changed=[k for k,v in model.state_dict().items() if not torch.equal(before[k],v)]
    assert changed and all(k.startswith('value_head.') for k in changed)
    assert all(torch.isfinite(v).all() for v in model.state_dict().values())
    # The readiness records are excluded from later training; no smoke state is saved.
    assert sources()==bound
    write(HERE/'prepared.json',dict(complete=True,sources=bound,runtime=runtime,config=CONFIG,setups=setups,initial_checkpoint_sha256=sha(INIT),smoke=dict(optimizer_steps=1,saved_checkpoint=False,changed_tensors=changed,first=upd['first']),candidate_optimization_updates=0,development_ids_sha256=sha(c.OUT/'indices.npz'),production_changed=False))
    print('OUTCOME_RL_PREPARED')
if __name__=='__main__':main()
