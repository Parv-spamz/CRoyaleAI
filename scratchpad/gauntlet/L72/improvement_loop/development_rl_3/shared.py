import datetime,hashlib,importlib.util,json,sys
from pathlib import Path
import numpy as np
import torch
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
sys.path.insert(0,str(ROOT))
def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
old=module('late_curriculum_scoring',HERE.parent/'development_rl_2/shared.py')
c=old.c;g=old.g;read=old.read;write=old.write;sha=old.sha
INIT=old.INIT;OUT=ROOT/'icebow/data/bench/development_rl_3_20261006'
ARMS=('full_budget_v5','late_budget_v5');UPDATES=16;GAMES=64;DRAWS=2048;DRAW_SEED=2026101600
CONFIG=dict(old.CONFIG,gae_lambda=.95,seed=2026101600)
metric_module=old.metric_module;independent_counter=old.independent_counter;masks=old.masks
form_match=old.form_match;initialize_runtime=old.initialize_runtime
def cutoff():
    if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime(2026,10,6,13,tzinfo=datetime.timezone.utc):raise RuntimeError('Owner overnight cutoff before next batch/update/job')
def sources():
    base=old.sources();paths=list(HERE.glob('*.py'))+[HERE/'PLAN.md',HERE/'METRICS.md',
        HERE.parent/'late_game_readiness_2/reviewed.json',HERE.parent/'late_game_readiness_2/report.json',
        HERE.parent/'late_game_readiness_2/verified.json',HERE.parent/'late_game_readiness_2/selection.py',
        HERE.parent/'OWNER_OVERNIGHT_EXTENSION_20261005.md',HERE.parent/'development_rl_2/shared.py',
        HERE.parent/'development_rl_2/evaluate.py',HERE.parent/'development_rl_2/verify.py']
    return dict(base,**{str(p.relative_to(ROOT)):sha(p) for p in paths})
def check():
    p=read(HERE/'prepared.json');assert p['complete'] and p['sources']==sources();return p
def schedule():
    from pipeline.e1_eval import ICEBOW_ENGINE_DECK
    decks=[s['opp_deck'] for s in read(g.HERE/'prepared.json')['scenarios'] if s['opp']=='gen'][:8]
    assert len(decks)==8
    return [dict(update=u,index=j,tag=f'late-curriculum-{2026102000+u*GAMES+j}',seed=2026102000+u*GAMES+j,
        learner_side=(j//2)%2,learner_deck=list(ICEBOW_ENGINE_DECK),opp_deck=decks[(j//2)%8] if j%2==0 else list(ICEBOW_ENGINE_DECK),
        opp=dict(id='gen' if j%2==0 else 's1')) for u in range(UPDATES) for j in range(GAMES)]
def arrays(p):
    with np.load(p,allow_pickle=False) as z:return {k:z[k] for k in z.files}
def tensor_hash(net,exclude_value=False):
    h=hashlib.sha256()
    for k,v in sorted(net.state_dict().items()):
        if exclude_value and k.startswith('value_head.'):continue
        a=v.detach().cpu().numpy();h.update(k.encode());h.update(str(a.dtype).encode());h.update(str(a.shape).encode());h.update(a.tobytes())
    return h.hexdigest()
