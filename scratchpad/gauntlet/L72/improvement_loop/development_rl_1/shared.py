import ast,hashlib,importlib.util,json,sys
from pathlib import Path
import numpy as np
import torch
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
sys.path.insert(0,str(ROOT))
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
c=module('outcome_first_common',HERE.parent/'development_iteration_1/common.py')
g=module('outcome_gameplay_common',HERE.parent/'development_gameplay_1/common.py')
read=c.read;write=c.write;sha=c.sha
OUT=ROOT/'icebow/data/bench/development_rl_1_20261005';ARM='outcome_rl_v5'
INIT=g.CKPTS['ordinary_v5'];MASKS=ROOT/'icebow/data/bench/development_iteration_4_20261005/development_masks.npz'
CONFIG=dict(advantage='gae',gae_gamma_unit='tick',gae_gamma_tick=.99994,gae_terminal_gap=True,gae_lambda=.95,critic_warmup_updates=5,
    shaping='none',vf_coef=.5,vf_clip=.2,vf_trunk_grad=True,tau=.35,T=.5,clip=.2,lr=1e-5,grad_clip=.5,ppo_epochs=2,minibatch=256,
    beta0=.3,beta_min=.03,beta_max=3.,kl_target=.10,leash='max',seed=2026100509,stop_consecutive=2,plays_lo=.6,plays_hi=1.6,
    kl_cell_stop=.5,kl_gate_stop=.1,entropy_floor_frac=.5)
def forbidden(*args,**kwargs):raise AssertionError('Inherited validation/stock learner access forbidden')
def initialize_runtime():
    torch.set_num_threads(1)
    from pipeline.royale_runtime import activate
    runtime=activate()
    from pipeline import rl_royale as RL
    RL.gen_v3val_arrays=forbidden;RL.Learner.__init__=forbidden
    return runtime,RL
def prerequisites():
    c.check_prepared();c.check_frozen();g.check()
    rv=read(HERE.parent/'rl_readiness/verified.json');assert rv['complete'] and rv['optimizer_updates']==0
    assert sha(HERE.parent/'rl_readiness/report.json')==rv['report_sha256']
    for stage in ('collection','independent'):
        r=read(ROOT/f'scratchpad/gauntlet/L71/integration/checks/l72-rl-readiness-{stage}.json');assert r['exit_code']==0 and r['matched']
    assert sha(MASKS)==read(HERE.parent/'development_iteration_4/prelaunch.json')['masks_sha256']
def sources():
    base=g.sources();base.update(c.frozen_sources())
    files=list(HERE.glob('*.py'))+[HERE/'PLAN.md',HERE/'METRICS.md',MASKS,c.OUT/'indices.npz',HERE.parent/'terminal_wrapper/adapter.py',HERE.parent/'rl_readiness/verified.json',HERE.parent/'rl_readiness/report.json',HERE.parent/'development_iteration_1/metrics.py',HERE.parent/'development_iteration_1/recount_v2.py']
    return dict(base,**{str(p.relative_to(ROOT)):sha(p) for p in files})
def check():
    p=read(HERE/'prepared.json');assert p['complete'] and p['sources']==sources();return p
def schedule():
    from pipeline.e1_eval import ICEBOW_ENGINE_DECK
    ds=read(g.CENSUS)['decks'];ds=[d for d in ds if sorted(x.split('@')[0] for x in d['engine'])!=sorted(ICEBOW_ENGINE_DECK)]
    w=np.sqrt([d['sides'] for d in ds]);w=w/w.sum();rng=np.random.default_rng(CONFIG['seed']);out=[]
    for u in range(32):
        for j in range(8):
            n=u*8+j;opp='gen' if j%2==0 else 's1';d=ds[int(rng.choice(len(ds),p=w))] if opp=='gen' else None
            out.append(dict(update=u,index=j,tag=f'outcome-rl-{2026110000+n}-{opp}',seed=2026110000+n,learner_side=(j//2)%2,
                learner_deck=list(ICEBOW_ENGINE_DECK),opp_deck=list(d['engine']) if d else list(ICEBOW_ENGINE_DECK),
                opp=dict(id=opp),deck_rank=d['rank'] if d else None))
    return out
def metric_module():
    # Existing pure scorer without importing its dataset-mask producer.
    p=HERE.parent/'development_iteration_1/metrics.py';tree=ast.parse(p.read_text());keep=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('allowed','row_values','summarize')]
    from pipeline.opp_elixir_count import card_cost
    ns=dict(np=np,card_cost=card_cost);exec(compile(ast.Module(body=keep,type_ignores=[]),str(p),'exec'),ns);return ns
def independent_counter():
    p=HERE.parent/'development_iteration_1/recount_v2.py';tree=ast.parse(p.read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='independently_count')
    ns=dict(np=np);exec(compile(ast.Module(body=[fn],type_ignores=[]),str(p),'exec'),ns);return ns['independently_count']
def masks(ids):
    with np.load(MASKS) as z:
        assert np.array_equal(z['ids'],ids)
        return {k[5:]:z[k] for k in z.files if k.startswith('mask_')},z['target']
