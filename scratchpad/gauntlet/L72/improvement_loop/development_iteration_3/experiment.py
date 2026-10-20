"""Frozen ordinary-exposure v6 comparison; no live imports."""
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
FIRST=HERE.parent/'development_iteration_1';SECOND=HERE.parent/'development_iteration_2'
sys.path.insert(0,str(FIRST))
import common as c
OUT=c.ROOT/'icebow/data/bench/development_iteration_3_20261005'
SECOND_OUT=c.ROOT/'icebow/data/bench/development_iteration_2_20261005'
ARM='rocket_aim3_v6'

def prerequisites():
    c.check_prepared();c.check_frozen()
    r=c.read(FIRST/'results_verified_v2.json');d=c.read(SECOND/'results_verified.json')
    assert r['complete'] and d['complete'] and c.read(SECOND/'chain_complete.json')['complete']
    for arm,folder in [('r1e_corrected','r1e_corrected_eval'),('ordinary_v6','ordinary_v6_eval_v2')]:
        for kind,file in [('cache','predictions.npz'),('report','report.json')]:assert r['hashes'][arm][kind]==c.sha(c.OUT/folder/file)
    assert c.sha(SECOND_OUT/'development_masks.npz')==c.read(SECOND/'prelaunch.json')['masks_sha256']

def sources():
    paths=list(HERE.glob('*.py'))+[HERE/n for n in ('PLAN.md','METRICS.md')]
    paths += [FIRST/n for n in ('results_verified_v2.json','ordinary_v6_portable.json')]
    paths += [SECOND/n for n in ('results_verified.json','chain_complete.json','prelaunch.json')]
    paths += [SECOND_OUT/'schedule.npz',SECOND_OUT/'development_masks.npz',c.OUT/'ordinary_v6'/'candidate_portable.pt',c.OUT/'ordinary_v6'/'train.jsonl']
    return {str(p.relative_to(c.ROOT)):c.sha(p) for p in paths}

def check_active():
    prerequisites();p=c.read(HERE/'prelaunch.json')
    assert p['complete'] and p['optimizer_allowed'] and p['sources']==sources()
    return p

def checkpoint(state,model,config):
    result={k:v for k,v in state.items() if k not in ('model','val','eval','optimizer')}
    result.update(model=model.cpu().state_dict(),args=dict(state['args'],feature_version=6),development_iteration_3=config)
    return result
