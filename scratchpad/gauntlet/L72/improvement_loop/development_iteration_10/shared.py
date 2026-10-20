"""Frozen additional-fit recipe and explicit dependency access."""
import ast
import datetime
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from zipfile import ZipFile
import numpy as np
import torch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location('extended_original_common', HERE.parent/'development_iteration_1/common.py')
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)
OUT = ROOT/'icebow/data/bench/development_iteration_10_20261006'
INIT = c.OUT/'ordinary_v5/candidate_portable.pt'
ARM = 'ordinary_no_dropout_v5'
STEPS = 8000
SEED = 2026100609
MASKS = ROOT/'icebow/data/bench/development_iteration_4_20261005/development_masks.npz'
DEFENSE = ROOT/'icebow/data/bench/development_iteration_2_20261005/schedule.npz'
CONTEXT = ROOT/'icebow/data/bench/context_teaching_20261005/cohorts.npz'
CONTEXT_ROWS = ROOT/'icebow/data/bench/match_adaptation_20261005/rows_v2.jsonl'
PRIOR = HERE.parent/'development_iteration_9'
PRIOR_OUT = ROOT/'icebow/data/bench/development_iteration_9_20261006'
FIT = HERE.parent/'dropout_free_fit'
CONTROLS = dict(ordinary_extended_v5=PRIOR_OUT/'predictions.npz',r1e_corrected=c.OUT/'r1e_corrected_eval/predictions.npz', ordinary_v5=c.OUT/'ordinary_v5_eval_v2/predictions.npz')


def read(p): return json.loads(p.read_text(encoding='utf-8'))
def write(p, d): p.write_text(json.dumps(d, allow_nan=False, separators=(',', ':'))+'\n', encoding='utf-8')
def sha(p):
    with p.open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
def arrays(p):
    with np.load(p, allow_pickle=False) as z: return {k:z[k] for k in z.files}
def cutoff():
    assert datetime.datetime.now(datetime.timezone.utc) < datetime.datetime(2026,10,6,13,tzinfo=datetime.timezone.utc), 'Owner cutoff'
def sources():
    files = list((ROOT/'pipeline').glob('*.py')) + list(HERE.glob('*.py'))
    files += [HERE/'PLAN.md', HERE/'METRICS.md', c.HERE/'common.py', c.HERE/'metrics.py', c.HERE/'recount_v2.py',
        c.HERE/'prepared.json', c.HERE/'verified.json', c.HERE/'ordinary_v5_portable.json',
        HERE.parent/'development_iteration_4/extra_masks.py', HERE.parent/'development_iteration_4/prelaunch.json',
        HERE.parent/'development_rl_3/results_verified.json', HERE.parent/'training_fit_audit/reviewed.json',
        PRIOR/'prepared.json', PRIOR/'trained.json', PRIOR/'training_verified.json', PRIOR/'evaluated.json', PRIOR/'results_verified.json', PRIOR/'reviewed_results.json', PRIOR_OUT/'schedule.npz', FIT/'prepared.json', FIT/'results_verified.json', FIT/'reviewed_results.json', FIT/'model.py', INIT, c.DATA, c.SOURCE, c.OUT/'indices.npz', MASKS, DEFENSE, CONTEXT, CONTEXT_ROWS, *CONTROLS.values()]
    return {str(p.relative_to(ROOT)):sha(p) for p in files}
def check():
    p = read(HERE/'prepared.json'); assert p['complete'] and p['sources'] == sources()
    assert p['schedule_sha256'] == sha(OUT/'schedule.npz')
    assert p['runtime'] == dict(torch=str(torch.__version__), python=sys.version, cuda=torch.version.cuda)
    return p
def validate_schedule(draws, mirrors, train):
    assert draws.shape == (STEPS,128) and draws.dtype.kind in 'iu'
    assert mirrors.shape == (STEPS,) and mirrors.dtype == bool
    pos = np.searchsorted(train, draws)
    assert np.all(pos < len(train)) and np.array_equal(train[pos],draws)
    return pos
def masks(ids):
    z=arrays(MASKS); assert np.array_equal(z['ids'],ids)
    return {k[5:]:v for k,v in z.items() if k.startswith('mask_')},z['target']
def functions(path, names, namespace):
    tree=ast.parse(path.read_text(encoding='utf-8'))
    selected=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
    assert {n.name for n in selected} == set(names)
    exec(compile(ast.Module(body=selected,type_ignores=[]),str(path),'exec'),namespace)
    return namespace
def scoring():
    from pipeline.opp_elixir_count import card_cost
    return functions(c.HERE/'metrics.py',('allowed','row_values','summarize'),dict(np=np,card_cost=card_cost))
def independent():
    from pipeline import vocab
    from pipeline.opp_elixir_count import card_cost
    from pipeline.train_rocket_curriculum import take
    return functions(c.HERE/'recount_v2.py',('independent_masks','independently_count','controls'),
        dict(np=np,c=c,vocab=vocab,card_cost=card_cost,take=take,ZipFile=ZipFile))
def extra_independent(ids,s,cv,actual):
    ns=functions(HERE.parent/'development_iteration_4/extra_masks.py',('independently_verify_extra',),
        dict(np=np,c=c,DOUT=CONTEXT_ROWS.parent,PHASES=('single_clock','double_regulation_clock','early_overtime_clock','late_overtime_clock')))
    return ns['independently_verify_extra'](ids,s,cv,actual)
def filters(a,b):
    required=('rocket','rocket_late_overtime_clock','all','barrel_pro','witch','night_witch','furnace','defensive_sequence','phase_late_overtime_clock')
    f=dict(denominators_present=all(a[k]['rows']>0 and a[k]['rows']==b[k]['rows'] for k in required),
        rocket_aim_material=(b['rocket']['aim1']-a['rocket']['aim1'])/a['rocket']['rows']>=.05,
        rocket_action_material=(b['rocket']['action']-a['rocket']['action'])/a['rocket']['rows']>=.02,
        late_rocket_material=(b['rocket_late_overtime_clock']['action']-a['rocket_late_overtime_clock']['action'])/a['rocket_late_overtime_clock']['rows']>=.02,
        general_card_noninferior=(b['all']['card']-a['all']['card'])/a['all']['play']>=-.005,
        barrel_correct_nonregression=b['barrel_pro']['log_correct']>=a['barrel_pro']['log_correct'],
        barrel_wrong_nonregression=b['barrel_pro']['log_wrong']<=a['barrel_pro']['log_wrong'])
    for k in ('witch','night_witch','furnace','defensive_sequence','phase_late_overtime_clock'):
        f[k+'_nonregression']=b[k]['action']>=a[k]['action']
    return f
