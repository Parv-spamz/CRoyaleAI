"""Bound historical phase exposure, reusing unchanged v6 training primitives."""
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;FIRST=HERE.parent/'development_iteration_1';SECOND=HERE.parent/'development_iteration_2'
sys.path.insert(0,str(FIRST))
import common as c
OUT=c.ROOT/'icebow/data/bench/development_iteration_4_20261005'
SECOND_OUT=c.ROOT/'icebow/data/bench/development_iteration_2_20261005'
DIAG=HERE.parent/'match_adaptation';DOUT=c.ROOT/'icebow/data/bench/match_adaptation_20261005'
ARM='phase_balanced_v6'
PHASES=('single_clock','double_regulation_clock','early_overtime_clock','late_overtime_clock')

def check_prepared():
    c.check_prepared();c.check_frozen()
    p=c.read(HERE/'prepared.json');v=c.read(HERE/'verified.json')
    assert v['complete'] and v['prepared_sha256']==c.sha(HERE/'prepared.json')
    for path,h in p['sources'].items():assert c.sha(c.ROOT/path)==h,path
    assert c.sha(OUT/'schedule.npz')==p['schedule_sha256']
    r=c.read(FIRST/'results_verified_v2.json')
    for arm,folder in [('r1e_corrected','r1e_corrected_eval'),('ordinary_v6','ordinary_v6_eval_v2')]:
        for kind,file in [('cache','predictions.npz'),('report','report.json')]:assert r['hashes'][arm][kind]==c.sha(c.OUT/folder/file)
    assert c.read(HERE.parent/'development_iteration_3/chain_complete.json')['complete']
    assert c.sha(SECOND_OUT/'development_masks.npz')==c.read(SECOND/'prelaunch.json')['masks_sha256']

def sources():
    paths=list(HERE.glob('*.py'))+[HERE/n for n in ('PLAN.md','METRICS.md','prepared.json','verified.json')]
    paths += [FIRST/n for n in ('results_verified_v2.json','ordinary_v6_portable.json')]
    paths += [SECOND/'prelaunch.json',SECOND_OUT/'schedule.npz',SECOND_OUT/'development_masks.npz',
        c.OUT/'ordinary_v6/candidate_portable.pt',c.OUT/'ordinary_v6/train.jsonl',OUT/'schedule.npz']
    return {str(p.relative_to(c.ROOT)):c.sha(p) for p in paths}

def check_active():
    check_prepared();p=c.read(HERE/'prelaunch.json')
    assert p['complete'] and p['optimizer_allowed'] and p['sources']==sources()
    assert p['masks_sha256']==c.sha(OUT/'development_masks.npz')
    return p

def checkpoint(state,model,config):
    result={k:v for k,v in state.items() if k not in ('model','val','eval','optimizer')}
    result.update(model=model.cpu().state_dict(),args=dict(state['args'],feature_version=6),development_iteration_4=config)
    return result
