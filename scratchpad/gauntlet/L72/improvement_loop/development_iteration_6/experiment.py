"""Bound all-card spatial-loss trial; no pipeline/live source changes."""
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;FIRST=HERE.parent/'development_iteration_1';SECOND=HERE.parent/'development_iteration_2';FOURTH=HERE.parent/'development_iteration_4';FIFTH=HERE.parent/'development_iteration_5'
sys.path.insert(0,str(FIRST))
import common as c
OUT=c.ROOT/'icebow/data/bench/development_iteration_6_20261005'
SECOND_OUT=c.ROOT/'icebow/data/bench/development_iteration_2_20261005'
DOUT=c.ROOT/'icebow/data/bench/match_adaptation_20261005'
SCHEDULE=c.OUT/'draws.npz';MASKS=c.ROOT/'icebow/data/bench/development_iteration_4_20261005/development_masks.npz'
ARM='spatial_cell_balance_v6'
PHASES=('single_clock','double_regulation_clock','early_overtime_clock','late_overtime_clock')

def prerequisites():
    c.check_prepared();c.check_frozen()
    assert c.read(FIFTH/'chain_complete.json')['complete'] and c.read(FIFTH/'reviewed_results.json')['complete']
    assert c.read(HERE.parent/'tower_aim_localization/verified.json')['complete']
    assert c.read(HERE.parent/'tower_aim_localization/exposure.json')['complete']
    assert c.sha(MASKS)==c.read(FOURTH/'prelaunch.json')['masks_sha256']
    r=c.read(FIRST/'results_verified_v2.json')
    for arm,folder in [('r1e_corrected','r1e_corrected_eval'),('ordinary_v6','ordinary_v6_eval_v2')]:
        for kind,file in [('cache','predictions.npz'),('report','report.json')]:assert r['hashes'][arm][kind]==c.sha(c.OUT/folder/file)

def sources():
    paths=list(HERE.glob('*.py'))+[HERE/n for n in ('PLAN.md','METRICS.md','prepared.json','verified.json')]
    paths += [FIFTH/'reviewed_results.json',FIRST/'results_verified_v2.json',FIRST/'ordinary_v6_portable.json',FOURTH/'prelaunch.json',SECOND/'prelaunch.json',SECOND_OUT/'schedule.npz',MASKS,SCHEDULE,
        c.OUT/'ordinary_v6/candidate_portable.pt',c.OUT/'ordinary_v6/train.jsonl',DOUT/'rows_v2.jsonl',OUT/'weights.npz']
    return {str(p.relative_to(c.ROOT)):c.sha(p) for p in paths}

def check_active():
    prerequisites();p=c.read(HERE/'prelaunch.json')
    assert p['complete'] and p['optimizer_allowed'] and p['sources']==sources()
    assert p['masks_sha256']==c.sha(MASKS) and p['schedule_sha256']==c.sha(SCHEDULE)
    return p

def checkpoint(state,model,config):
    result={k:v for k,v in state.items() if k not in ('model','val','eval','optimizer')}
    result.update(model=model.cpu().state_dict(),args=dict(state['args'],feature_version=6),development_iteration_6=config)
    return result
