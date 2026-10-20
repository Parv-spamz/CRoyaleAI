"""Freeze initial setups and qualify the shared fixed optimizer budget mechanism."""
import os,copy
from shared import *
from selection import select,draws
def main():
    cutoff();assert not (HERE/'prepared.json').exists() and not OUT.exists();old.prerequisites()
    rr=read(HERE.parent/'late_game_readiness_2/reviewed.json');assert rr['complete'] and rr['optimizer_updates']==0
    assert rr['report_sha256']==sha(HERE.parent/'late_game_readiness_2/report.json') and rr['verified_sha256']==sha(HERE.parent/'late_game_readiness_2/verified.json')
    # Hand-calculated unequal-length groups, edge draws and empty phase views.
    m=np.array([0,0,0,3,3,7]);uv=np.array([[0.,0.],[.32,.99],[.34,0.],[.66,.99],[.99,.99]])
    assert np.array_equal(draws(m,uv),[0,2,3,4,5]);positive=1;negative=0
    for q in [np.array([[1.,0.]]),np.array([[0.,-1.]]),np.array([[np.nan,0.]]),np.zeros((2,3))]:
        try:draws(m,q)
        except AssertionError:negative+=1
        else:raise AssertionError('Malformed uniforms accepted')
    rr0=dict(readiness=dict(phase=dict(regular_ticks=10,overtime_ticks=10),native=dict(game_over=True,terminated=True)),traj=dict(tick=np.array([0,14,15,19]),past=np.arange(8).reshape(4,2)))
    for late,expected in [(False,[0,1,2,3]),(True,[2,3])]:
        r,ix,b=select(rr0,late);assert b==15 and ix.tolist()==expected and np.array_equal(r['traj']['past'],rr0['traj']['past'][ix]);positive+=1
    q=copy.deepcopy(rr0);q['traj']={k:v[:2] for k,v in q['traj'].items()};assert not len(select(q,True)[1]);positive+=1
    for kind in ('phase','unfinished','ticks','length'):
        q=copy.deepcopy(rr0)
        if kind=='phase':q['readiness']['phase']['regular_ticks']=0
        if kind=='unfinished':q['readiness']['native']['game_over']=False
        if kind=='ticks':q['traj']['tick'][1]=0
        if kind=='length':q['traj']['past']=q['traj']['past'][:-1]
        try:select(q,True)
        except AssertionError:negative+=1
        else:raise AssertionError('Malformed projection accepted')
    # Separate literal sampler implementation, independent of producer grouping.
    u=np.random.default_rng(DRAW_SEED).random((DRAWS,2));actual=draws(m,u);literal=[]
    for a,b in u:
        group=[0,3,7][int(a*3)];rows=[i for i,x in enumerate(m.tolist()) if x==group];literal.append(rows[int(b*len(rows))])
    assert np.array_equal(actual,literal);positive+=1
    runtime,RL=initialize_runtime();bound=sources();OUT.mkdir()
    # New budget integration only: excluded saved readiness trajectories, no
    # replay/inference/backward/optimizer or repetition of their readiness audit.
    ready=read(HERE.parent/'late_game_readiness_2/report.json');excluded=[]
    for x in ready['records']:
        r=read(ROOT/x['result']);r['traj']=arrays(ROOT/x['full']);excluded.append(r)
    budget_probes=[]
    for arm in ARMS:
        views=[select(r,arm==ARMS[1])[0] for r in excluded]
        bn,_=RL.collate(views,advantage='gae',gamma_tick=.99994,gae_terminal_gap=True)
        ix=draws(bn['match'],np.random.default_rng(DRAW_SEED).random((DRAWS,2)))
        probe={k:v[ix].copy() for k,v in bn.items()};probe['w']=np.full(DRAWS,1./DRAWS)
        device_probe=RL.to_device(probe,'cpu')
        assert all(len(a)==DRAWS for a in probe.values()) and all(np.array_equal(device_probe[k].numpy(),a) for k,a in probe.items())
        assert np.array_equal(probe['w'],np.full(DRAWS,1./DRAWS)) and int(np.unique(ix).size)>0
        budget_probes.append(dict(arm=arm,eligible_rows=len(bn['A']),draws=len(ix),unique_rows=int(np.unique(ix).size),optimizer_steps=0))
        positive+=1
    del excluded,views,bn,probe,device_probe
    for arm in ARMS:
        (OUT/arm/'rollouts').mkdir(parents=True);(OUT/arm/'checkpoints').mkdir()
    (OUT/'setups').mkdir()
    write(HERE/'preparation_started.json',dict(pid=os.getpid(),utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),sources=bound))
    from pipeline.royale_env import RoyaleSelfPlayEnv
    env=RoyaleSelfPlayEnv(decision_ticks=10,tail_cap=7200,forms_mode='deck',hero_abilities=True,ability_policy='v2');env.feature_version=5
    setups=[]
    for i,s in enumerate(schedule()):
        cutoff();decks={s['learner_side']:s['learner_deck'],1-s['learner_side']:s['opp_deck']};env.reset(decks[0],decks[1],s['seed']);assert not env.form_fallbacks
        f=OUT/'setups'/f'{i}.bin';f.write_bytes(bytes(env.core.save_state()))
        setups.append(dict(spec=s,initial_state_path=str(f.relative_to(ROOT)),initial_state_sha256=sha(f),forms=env.loaded_forms))
    env.close();assert len(setups)==UPDATES*GAMES and sources()==bound
    write(HERE/'prepared.json',dict(complete=True,sources=bound,runtime=runtime,config=CONFIG,setups=setups,initial_checkpoint_sha256=sha(INIT),
        arms=ARMS,updates=UPDATES,games_per_update=GAMES,draws=DRAWS,budget_probes=budget_probes,controls=dict(positive=positive,negative=negative),optimizer_steps=0))
    print('LATE_CURRICULUM_PREPARED')
if __name__=='__main__':main()
