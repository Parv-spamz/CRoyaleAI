import datetime,hashlib,importlib.util,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
sys.path.insert(0,str(ROOT))
OUT=ROOT/'icebow/data/bench/late_game_readiness_2_20261005';GAMMA=.99994
def module(name,path):
    sp=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
g=module('late_gameplay_provenance',HERE.parent/'development_gameplay_1/common.py')
read=g.read;write=g.write;sha=g.sha;blobsha=g.blobsha
def cutoff():
    if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime(2026,10,6,13,tzinfo=datetime.timezone.utc):raise RuntimeError('Owner overnight cutoff before next batch/job')
def scenarios():
    from pipeline.e1_eval import ICEBOW_ENGINE_DECK
    ds=[x['opp_deck'] for x in read(g.HERE/'prepared.json')['scenarios'] if x['opp']=='gen'][:8]
    assert len(ds)==8
    return [dict(tag=f'late-ready-{2026101500+j}',seed=2026101500+j,learner_side=(j//2)%2,
        learner_deck=list(ICEBOW_ENGINE_DECK),opp_deck=ds[(j//2)%8] if j%2==0 else list(ICEBOW_ENGINE_DECK),
        opp=dict(id='gen' if j%2==0 else 's1')) for j in range(64)]
def sources():
    base=g.check()['sources'];paths=list(HERE.glob('*.py'))+[HERE/'PLAN.md',HERE/'METRICS.md',
        HERE.parent/'terminal_wrapper/adapter.py',HERE.parent/'terminal_wrapper_policy/reviewed_results.json',
        HERE.parent/'rl_readiness/verified.json',HERE.parent/'OWNER_OVERNIGHT_EXTENSION_20261005.md',
        HERE.parent/'impact_learnability_2_recovery/reviewed_results.json',
        HERE.parent/'late_game_readiness_coverage/report.json',HERE.parent/'late_game_readiness/collected.json',
        ROOT/'scratchpad/gauntlet/L71/integration/checks/l72-late-game-readiness-collection.json',
        *list((HERE.parent/'late_game_readiness').glob('*.py')),HERE.parent/'late_game_readiness/PLAN.md',HERE.parent/'late_game_readiness/METRICS.md']
    return dict(base,**{str(p.relative_to(ROOT)):sha(p) for p in paths})
