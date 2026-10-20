"""Isolated binding for the registered defense exposure experiment."""
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
FIRST=HERE.parent/'development_iteration_1'
sys.path.insert(0,str(FIRST))
import common as c
OUT=c.ROOT/'icebow/data/bench/development_iteration_2_20261005'
ARM='defense_sequence_v5'

def check_prepared():
    c.check_prepared();c.check_frozen()
    p=c.read(HERE/'prepared.json');v=c.read(HERE/'verified.json')
    assert v['complete'] and v['prepared_sha256']==c.sha(HERE/'prepared.json')
    for path,h in p['sources'].items():assert c.sha(c.ROOT/path)==h,path
    assert p['schedule_sha256']==c.sha(OUT/'schedule.npz')
    complete=c.read(FIRST/'resume_complete.json');r=c.read(FIRST/'results_verified_v2.json')
    assert complete['complete'] and r['complete']
    for arm,folder in [('r1e_corrected','r1e_corrected_eval'),('ordinary_v5','ordinary_v5_eval_v2')]:
        for kind,file in [('cache','predictions.npz'),('report','report.json')]:
            assert r['hashes'][arm][kind]==c.sha(c.OUT/folder/file)
    return p

def sources():
    paths=list(HERE.glob('*.py'))+[HERE/n for n in ('PLAN.md','METRICS.md','prepared.json','verified.json')]
    paths += [FIRST/n for n in ('results_verified_v2.json','resume_complete.json','ordinary_v5_portable.json')]
    paths += [c.OUT/'ordinary_v5'/'candidate_portable.pt',c.OUT/'ordinary_v5'/'train.jsonl']
    return {str(p.relative_to(c.ROOT)):c.sha(p) for p in paths}

def check_active():
    check_prepared();p=c.read(HERE/'prelaunch.json')
    assert p['complete'] and p['optimizer_allowed'] and p['sources']==sources()
    assert p['masks_sha256']==c.sha(OUT/'development_masks.npz')
    return p

def checkpoint(state,model,config):
    result={k:v for k,v in state.items() if k not in ('model','val','eval','optimizer')}
    result.update(model=model.cpu().state_dict(),args=dict(state['args'],feature_version=5),development_iteration_2=config)
    return result
