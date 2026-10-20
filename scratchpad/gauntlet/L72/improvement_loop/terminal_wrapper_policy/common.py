import functools,hashlib,importlib.util,json,sys
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(HERE.parent/'terminal_wrapper'))
spec=importlib.util.spec_from_file_location('old_gameplay_common',HERE.parent/'development_gameplay_1/common.py')
g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
OUT=ROOT/'icebow/data/bench/terminal_wrapper_policy_20261005'
ARMS=('r1e','ordinary_v5');MODES=('disabled','enabled')
read=g.read;write=g.write;sha=g.sha;blobsha=g.blobsha
def sources():
    old=g.check()
    own=list(HERE.glob('*.py'))+[HERE/'PLAN.md',HERE.parent/'terminal_wrapper/adapter.py',HERE.parent/'terminal_wrapper/verified.json',HERE.parent/'terminal_wrapper/pending_verified.json']
    return dict(old['sources'],**{str(p.relative_to(ROOT)):sha(p) for p in own})
def scenarios():
    old=read(g.HERE/'prepared.json');decks=[s['opp_deck'] for s in old['scenarios'] if s['opp']=='gen'][:4]
    from pipeline.e1_eval import ICEBOW_ENGINE_DECK
    return [dict(opp=opp,seed=seed,side=seed%2,opp_deck=(decks[i] if opp=='gen' else list(ICEBOW_ENGINE_DECK)),tag=f'terminal-policy-{seed}-{opp}') for i,seed in enumerate(range(2026100580,2026100584)) for opp in ('gen','s1')]
def initialize():
    import torch
    torch.set_num_threads(1)
    from pipeline.royale_runtime import activate
    stamp=activate()
    from pipeline import search_s0 as S
    from pipeline.royale_env import RoyaleSelfPlayEnv
    opponents={}
    for name,path in [('gen',g.OPP_GEN),('s1',g.OPP_S1)]:
        policy,info=S.E.load_policy(path,'cuda');opponents[name]=(policy,S.live_cfg(.27,info['grid'],'cuda'))
    runners={}
    for arm in ARMS:
        policy,info=S.E.load_policy(g.CKPTS[arm],'cuda');cfg=S.live_cfg(.35,info['grid'],'cuda');cfg['behaviour_telemetry']=True
        runners[arm]=S.Runner(policy,opponents,cfg,lambda:RoyaleSelfPlayEnv(decision_ticks=10,tail_cap=7200,forms_mode='deck',hero_abilities=True,ability_policy='v2'))
    return stamp,S,runners
def setup(S,runner,scenario,enabled):
    from adapter import TerminalAwareMatch
    with patch.object(S.E,'SelfPlayMatch',functools.partial(TerminalAwareMatch,stop_decisions_at_fulltime=enabled)):
        match=runner.setup(scenario['opp'],scenario['seed'],scenario['opp_deck'],tag=scenario['tag'])
    assert not match.env.form_fallbacks and match.learner.side==scenario['side']
    return match
