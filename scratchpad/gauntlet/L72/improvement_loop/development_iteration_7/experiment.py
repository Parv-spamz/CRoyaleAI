"""Fixed-base projectile branch learning; no production source changes."""
import sys
from pathlib import Path
import torch
HERE=Path(__file__).resolve().parent;FIRST=HERE.parent/'development_iteration_1';SECOND=HERE.parent/'development_iteration_2';FOURTH=HERE.parent/'development_iteration_4'
sys.path.insert(0,str(FIRST))
import common as c
from pipeline.train_gen import losses
OUT=c.ROOT/'icebow/data/bench/development_iteration_7_20261005'
SECOND_OUT=c.ROOT/'icebow/data/bench/development_iteration_2_20261005';DOUT=c.ROOT/'icebow/data/bench/match_adaptation_20261005'
SCHEDULE=c.OUT/'draws.npz';MASKS=c.ROOT/'icebow/data/bench/development_iteration_4_20261005/development_masks.npz'
INIT=c.OUT/'ordinary_v5/candidate_portable.pt';ARM='frozen_base_projectile_v6'
PHASES=('single_clock','double_regulation_clock','early_overtime_clock','late_overtime_clock')
def prerequisites():
    c.check_prepared();c.check_frozen()
    assert c.read(HERE.parent/'development_gameplay_1/reviewed_results.json')['complete']
    assert c.read(HERE.parent/'gameplay_failure_audit/verified_v2.json')['complete']
    assert c.sha(MASKS)==c.read(FOURTH/'prelaunch.json')['masks_sha256']
    r=c.read(FIRST/'results_verified_v2.json')
    for arm,folder in [('r1e_corrected','r1e_corrected_eval'),('ordinary_v5','ordinary_v5_eval_v2'),('ordinary_v6','ordinary_v6_eval_v2')]:
        for kind,file in [('cache','predictions.npz'),('report','report.json')]:assert r['hashes'][arm][kind]==c.sha(c.OUT/folder/file)
def sources():
    paths=list(HERE.glob('*.py'))+[HERE/n for n in ('PLAN.md','METRICS.md')]
    paths += [INIT,FIRST/'results_verified_v2.json',FIRST/'ordinary_v5_portable.json',FOURTH/'prelaunch.json',SECOND/'prelaunch.json',SECOND_OUT/'schedule.npz',MASKS,SCHEDULE,DOUT/'rows_v2.jsonl',HERE.parent/'development_gameplay_1/reviewed_results.json',HERE.parent/'gameplay_failure_audit/verified_v2.json']
    return {str(p.relative_to(c.ROOT)):c.sha(p) for p in paths}
def check_active():
    prerequisites();p=c.read(HERE/'prelaunch.json');assert p['complete'] and p['optimizer_allowed'] and p['sources']==sources();return p
def initialize(state,meta):
    model=c.initialize(state,6,meta)
    for name,p in model.named_parameters():p.requires_grad_(name.startswith('projectile_target_'))
    model.eval();return model
def optimizer(model):
    ps=[p for p in model.parameters() if p.requires_grad];assert len(ps)==5
    return torch.optim.AdamW(ps,lr=1e-3,weight_decay=.01)
def assert_base(state,model):
    for name,p in model.state_dict().items():
        if not name.startswith('projectile_target_'):assert torch.equal(p.detach().cpu(),state['model'][name]),name
def train_step(model,b,opt,grid):
    model.eval();loss,parts=losses(model,b,mirror=False,grid=grid)
    assert torch.isfinite(loss);opt.zero_grad(set_to_none=True);loss.backward()
    for name,p in model.named_parameters():
        if not p.requires_grad:assert p.grad is None,name
        elif p.grad is not None:assert torch.isfinite(p.grad).all(),name
    torch.nn.utils.clip_grad_norm_([p for p in model.parameters() if p.requires_grad],1.0);opt.step()
    return float(loss.detach()),parts
def checkpoint(state,model,config):
    result={k:v for k,v in state.items() if k not in ('model','val','eval','optimizer') and not k.startswith('development_iteration_')}
    result.update(model=model.cpu().state_dict(),args=dict(state['args'],feature_version=6),development_iteration_7=config);return result
