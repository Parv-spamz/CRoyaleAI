"""Isolated tower representation with frozen ordinary exposure and old controls."""
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;FIRST=HERE.parent/'development_iteration_1';SECOND=HERE.parent/'development_iteration_2';FOURTH=HERE.parent/'development_iteration_4'
sys.path.insert(0,str(FIRST))
import common as c
import torch
OUT=c.ROOT/'icebow/data/bench/development_iteration_5_20261005'
FOURTH_OUT=c.ROOT/'icebow/data/bench/development_iteration_4_20261005'
SECOND_OUT=c.ROOT/'icebow/data/bench/development_iteration_2_20261005'
DOUT=c.ROOT/'icebow/data/bench/match_adaptation_20261005'
SCHEDULE=c.OUT/'draws.npz';MASKS=FOURTH_OUT/'development_masks.npz'
ARM='tower_spatial_v7'
PHASES=('single_clock','double_regulation_clock','early_overtime_clock','late_overtime_clock')

def check_prepared():
    c.check_prepared();c.check_frozen()
    assert c.read(FOURTH/'chain_complete.json')['complete']
    assert c.read(FOURTH/'reviewed_results.json')['complete']
    assert c.sha(MASKS)==c.read(FOURTH/'prelaunch.json')['masks_sha256']
    r=c.read(FIRST/'results_verified_v2.json')
    for arm,folder in [('r1e_corrected','r1e_corrected_eval'),('ordinary_v6','ordinary_v6_eval_v2')]:
        for kind,file in [('cache','predictions.npz'),('report','report.json')]:assert r['hashes'][arm][kind]==c.sha(c.OUT/folder/file)

def sources():
    paths=list(HERE.glob('*.py'))+[HERE/n for n in ('PLAN.md','METRICS.md')]
    paths += [FIRST/n for n in ('results_verified_v2.json','ordinary_v6_portable.json')]
    paths += [FOURTH/n for n in ('prelaunch.json','results_verified.json','reviewed_results.json','extra_masks.py')]
    paths += [SECOND/'prelaunch.json',SECOND_OUT/'schedule.npz',MASKS,SCHEDULE,
        c.OUT/'ordinary_v6/candidate_portable.pt',c.OUT/'ordinary_v6/train.jsonl',DOUT/'rows_v2.jsonl']
    return {str(p.relative_to(c.ROOT)):c.sha(p) for p in paths}

def check_active():
    check_prepared();p=c.read(HERE/'prelaunch.json')
    assert p['complete'] and p['optimizer_allowed'] and p['sources']==sources()
    assert p['masks_sha256']==c.sha(MASKS) and p['schedule_sha256']==c.sha(SCHEDULE)
    return p

def initialize(state,meta):
    from tower_model import migrate
    return migrate(state,c.initialize(state,6,meta))

def optimizer(model):
    base=[];target=[];tower=[]
    for k,p in model.named_parameters():
        (tower if k.startswith('tower_spatial_') else target if k.startswith('projectile_target_') else base).append(p)
    assert base and target and tower
    return torch.optim.AdamW([dict(params=base,lr=1e-5),dict(params=target,lr=1e-3),dict(params=tower,lr=1e-3)],weight_decay=.01)

def checkpoint(state,model,config):
    from tower_model import TAG
    result={k:v for k,v in state.items() if k not in ('model','val','eval','optimizer')}
    result.update(model=model.cpu().state_dict(),args=dict(state['args'],feature_version=7),architecture=TAG,development_iteration_5=config)
    return result
