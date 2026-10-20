import hashlib,importlib.util,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
sys.path.insert(0,str(ROOT))
OUT=ROOT/'icebow/data/bench/rl_readiness_20261005'
spec=importlib.util.spec_from_file_location('ready_gameplay',HERE.parent/'development_gameplay_1/common.py')
g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
read=g.read;write=g.write;sha=g.sha;blobsha=g.blobsha
ARMS=('r1e','ordinary_v5');GAMMA=.99994;RATIO_LIMIT=1e-4
def scenarios():
    ds=[x['opp_deck'] for x in read(g.HERE/'prepared.json')['scenarios'] if x['opp']=='gen'][:2]
    from pipeline.e1_eval import ICEBOW_ENGINE_DECK
    return [dict(opp=o,seed=s,side=s%2,opp_deck=ds[i] if o=='gen' else list(ICEBOW_ENGINE_DECK),tag=f'rl-readiness-{s}-{o}') for i,s in enumerate(range(2026100600,2026100602)) for o in ('gen','s1')]
def sources():
    inherited=g.check()['sources']
    own=list(HERE.glob('*.py'))+[HERE/'PLAN.md',HERE.parent/'terminal_wrapper/adapter.py',HERE.parent/'terminal_wrapper_policy/reviewed_results.json']
    return dict(inherited,**{str(p.relative_to(ROOT)):sha(p) for p in own})
