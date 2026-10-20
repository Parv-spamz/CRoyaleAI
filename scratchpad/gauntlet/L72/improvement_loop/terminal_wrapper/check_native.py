"""New CPU engineering fixtures; no models, inference or learned labels."""
import hashlib,json,sys,types
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
sys.path.insert(0,str(ROOT))
from pipeline.royale_runtime import activate
STAMP=activate()
from pipeline import e1_eval as E
from pipeline.search_s0 import live_cfg
from pipeline.royale_env import RoyaleSelfPlayEnv
from adapter import TerminalAwareMatch,frozen
OUT=ROOT/'icebow/data/bench/terminal_wrapper_20261005'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def blob(b):return hashlib.sha256(bytes(b)).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def sources():
    paths=list(HERE.glob('*.py'))+[HERE/'PLAN.md',ROOT/'pipeline/e1_eval.py',ROOT/'pipeline/royale_env.py',ROOT/'pipeline/royale_runtime.py',ROOT/'scratchpad/gauntlet/L71/royale_update_20261005/build_manifest.json']
    return {str(p.relative_to(ROOT)):sha(p) for p in paths}
def run(seed,cap,mode):
    env=RoyaleSelfPlayEnv(decision_ticks=10,tail_cap=cap,forms_mode='deck',hero_abilities=True,ability_policy='v2')
    cfg=live_cfg(.35,'lattice','cpu');cfg['behaviour_telemetry']=True
    side=seed%2;deck=list(E.ICEBOW_ENGINE_DECK)
    spec=dict(learner_side=side,learner_deck=deck,opp_deck=deck,seed=seed,tag=f'terminal-fixture-{seed}-{cap}',opp=dict(id='fixture'))
    cls=E.SelfPlayMatch if mode=='original' else TerminalAwareMatch
    kw={} if mode=='original' else dict(stop_decisions_at_fulltime=mode=='enabled')
    m=cls(env,spec,0,cfg,cfg,None,None,**kw)
    initial=blob(env.core.save_state());env._advance_to(5700)
    # Fixed fixture command from the learner's current public hand. No policy.
    rocket=env.card_id('Rocket');st=env.core.state();sent=False
    if rocket in st.players[side].hand:
        target=next(e for e in st.entities if e.team==1-side and e.kind==E.EntityKind.PRINCESS_TOWER) if hasattr(E,'EntityKind') else None
        if target is None:
            from royalegym.protocol import EntityKind
            target=next(e for e in st.entities if e.team==1-side and e.kind==EntityKind.PRINCESS_TOWER)
        command=env.eng.act(side=side,deck_index=env.deck_ids[side].index(rocket),x=round(target.x/18),y=round(target.y/18))
        assert command['accepted'];sent=True
    env._advance_to(5980)
    for s in m.sides:s.next_tick=5980
    boundary=env.core.state().regular_ticks+env.core.state().overtime_ticks
    prefix_state=blob(env.core.save_state());decisions=[];calls=0
    while True:
        ds=m.due()
        if not ds:break
        calls+=1;assert calls<200
        for s in ds:
            s.prepare();t=int(env.tick)
            d=dict(play=False,slot=-1,cell=-1,why='fixture_wait')
            if t==5990 or t>=boundary:
                cid=env.core.state().players[s.side].hand[0]
                deckindex=env.deck_ids[s.side].index(cid)
                slot=next(k for k,v in s.deck_index_of_slot.items() if v==deckindex)
                d=dict(play=True,slot=slot,cell=14*37+18,why='fixture_play')
            decisions.append(dict(tick=t,side=s.side,decision=d))
            s.apply(1.0,d)
    st=env.core.state()
    telemetry=env.behaviour_telemetry
    result=dict(seed=seed,cap=cap,mode=mode,learner_side=side,rocket_fixture=sent,boundary=boundary,
        initial=initial,prefix_state=prefix_state,decisions=decisions,
        plays={str(s.side):s.plays for s in m.sides},accepted=telemetry.plays,
        frames_sha256=hashlib.sha256(json.dumps(telemetry.frames,sort_keys=True).encode()).hexdigest(),
        final_state=blob(env.core.save_state()),end_tick=int(st.tick),native_game_over=bool(st.game_over),
        terminated=bool(env.terminated),winner=int(st.winner),crowns=[int(p.crowns) for p in st.players],
        outcome=[env.outcome(s)[0] for s in (0,1)],episode=env.episode)
    env.close();return result
def main():
    OUT.mkdir(exist_ok=False)
    bind=sources();write(HERE/'started.json',dict(sources=bind,runtime=STAMP,models_loaded=0))
    # Exact phase-boundary controls, including nonstandard durations and early end.
    def state(t=6000,o=True,g=False,r=3600,e=2400):return types.SimpleNamespace(tick=t,overtime=o,game_over=g,regular_ticks=r,overtime_ticks=e)
    checks=[(state(5999),False),(state(),True),(state(6001),True),(state(o=False),False),(state(g=True),False),(state(400,r=300,e=100),True),(state(399,r=300,e=100),False)]
    assert all(frozen(s)==expected for s,expected in checks)
    records=[]
    for seed,cap in [(s,7200) for s in range(8)]+[(s,5995) for s in range(2)]:
        group=[]
        for mode in ('original','disabled','enabled'):
            result=run(seed,cap,mode);group.append(result);records.append(result)
            write(OUT/f'{seed}_{cap}_{mode}.json',result)
        original,disabled,enabled=group
        assert {k:v for k,v in original.items() if k!='mode'}=={k:v for k,v in disabled.items() if k!='mode'}
        for key in ('initial','prefix_state','accepted','final_state','end_tick','native_game_over','terminated','winner','crowns','outcome','episode'):
            assert original[key]==enabled[key],(seed,cap,key)
        cutoff=original['boundary']
        assert [d for d in original['decisions'] if d['tick']<cutoff]==enabled['decisions']
        assert not any(d['tick']>=cutoff for d in enabled['decisions'])
        if cap>cutoff:assert enabled['native_game_over'] and enabled['end_tick']>cutoff
        print('FIXTURE',seed,cap,len(original['decisions']),len(enabled['decisions']),enabled['outcome'],flush=True)
    full=[r for r in records if r['mode']=='enabled' and r['cap']==7200]
    assert any(r['outcome'][0]=='draw' for r in full)
    assert any(r['outcome'][0]!='draw' for r in full)
    assert sources()==bind
    write(HERE/'report.json',dict(complete=True,cases=10,runs=30,runtime=STAMP,sources=bind,
        boundary_controls=len(checks),records={str(p.relative_to(ROOT)):sha(p) for p in sorted(OUT.glob('*.json'))},
        model_inference=False,production_changed=False,performance_acceptance=False))
    print('TERMINAL_WRAPPER_NATIVE_COMPLETE')
if __name__=='__main__':main()
