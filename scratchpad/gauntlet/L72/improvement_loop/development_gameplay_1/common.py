"""Frozen developmental reactive setup, with no learning or tactical overrides."""
import hashlib,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
sys.path.insert(0,str(ROOT))
OUT=ROOT/'icebow/data/bench/development_gameplay_1_20261005'
BASE=ROOT/'icebow/data/bench/development_iteration_1_20261005'
CKPTS={'r1e':ROOT/'icebow/data/bench/rl_royale/rseries_r1e31/rseries_r1e31_u0155.pt',
       'ordinary_v5':BASE/'ordinary_v5/candidate_portable.pt','ordinary_v6':BASE/'ordinary_v6/candidate_portable.pt'}
OPP_GEN=ROOT/'icebow/data/pipeline/gen_v1_s0/gen_s0.pt'
OPP_S1=ROOT/'icebow/data/pipeline/s1_icebow_v6aug_s1.pt'
CENSUS=ROOT/'scratchpad/gauntlet/L70/pool_forms/loadable_decks.json'
SEEDS=list(range(2026100500,2026100532));ARMS=list(CKPTS)
def read(p):return json.loads(Path(p).read_text())
def write(p,v):Path(p).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def blobsha(b):return hashlib.sha256(bytes(b)).hexdigest()
def initialize(device='cpu'):
    import torch
    torch.set_num_threads(1)
    from pipeline.royale_runtime import activate
    stamp=activate()
    from pipeline import search_s0 as S
    from pipeline.royale_env import RoyaleSelfPlayEnv
    policies={a:S.E.load_policy(p,device) for a,p in CKPTS.items()}
    og,oi=S.E.load_policy(OPP_GEN,device);os,si=S.E.load_policy(OPP_S1,device)
    opponents={'gen':(og,S.live_cfg(.27,oi['grid'],device)), 's1':(os,S.live_cfg(.27,str(si.get('grid','floor')),device))}
    def factory():return RoyaleSelfPlayEnv(decision_ticks=10,tail_cap=7200,forms_mode='deck',hero_abilities=True,ability_policy='v2')
    runners={}
    for arm,(policy,info) in policies.items():
        cfg=S.live_cfg(.35,info['grid'],device);cfg['behaviour_telemetry']=True
        runners[arm]=S.Runner(policy,opponents,cfg,factory)
    return stamp,S,runners
def sources():
    paths=list((ROOT/'pipeline').rglob('*.py'))+list((ROOT/'icebow/src/clashrl').rglob('*.py'))+list(HERE.glob('*.py'))
    paths += list((ROOT/'icebow/config').rglob('*.yaml'))
    paths += [HERE/'PLAN.md',CENSUS,OPP_GEN,OPP_S1,*CKPTS.values(),
              HERE.parent/'development_iteration_1/results_verified_v2.json',
              HERE.parent/'development_iteration_1/ordinary_v5_portable.json',
              HERE.parent/'development_iteration_1/ordinary_v6_portable.json',
              ROOT/'scratchpad/gauntlet/L70/abilities/ability_models_v2.json',
              ROOT/'scratchpad/gauntlet/L71/royale_update_20261005/build_manifest.json']
    return {str(p.relative_to(ROOT)):sha(p) for p in sorted(set(paths))}
def check():
    p=read(HERE/'prepared.json');assert sources()==p['sources'],'Bound sources changed'
    return p
def setup(run,spec):
    m=run.setup(spec['opp'],spec['seed'],spec['opp_deck'],tag=spec['tag'])
    if m.env.form_fallbacks:raise ValueError('Unsupported original deck form')
    assert m.learner.side==spec['side']
    return m
