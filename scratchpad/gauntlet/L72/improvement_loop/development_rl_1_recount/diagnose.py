import hashlib,json
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
BASE=HERE.parent;ORIGINAL=BASE/'development_rl_1';OUT=ROOT/'icebow/data/bench/development_rl_1_20261005'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def arrays(p):
    with np.load(p,allow_pickle=False) as z:return {k:z[k] for k in z.files}
def main():
    assert not (HERE/'diagnosed.json').exists()
    checks=ROOT/'scratchpad/gauntlet/L71/integration/checks'
    fail=read(checks/'l72-outcome-rl-independent.json');assert fail['exit_code']!=0 and not fail['matched']
    t=read(ORIGINAL/'trained.json');assert t['complete'] and t['updates']==32 and t['games']==256
    assert sha(OUT/'train.jsonl')==t['train_log_sha256']
    logs=[json.loads(x) for x in (OUT/'train.jsonl').read_text().splitlines()];assert len(logs)==32
    result=[]
    for u,log in enumerate(logs):
        rp=OUT/'rollouts'/f'u{u:03d}.json';cp=OUT/'rollouts'/f'u{u:03d}_contract.npz'
        assert sha(rp)==log['rollouts_sha256'] and sha(cp)==log['contract_sha256']
        raw=read(rp);con=arrays(cp);pos=0;maximum=0.
        for r in raw:
            p=ROOT/r['trajectory'];assert sha(p)==r['trajectory_sha256'];a=arrays(p)
            keep=a['played']|a['gate_sampled'];count=int(keep.sum());lp=sum(a[k][keep] for k in ('lp_gate','lp_card','lp_cell'))
            delta=np.abs(np.expm1(con['lp_new'][pos:pos+count]-lp));assert np.isfinite(delta).all() and delta.max()<1e-4
            maximum=max(maximum,float(delta.max()));pos+=count
        lengths=all(len(x)==pos for x in con.values());rows=log['rows']==pos;assert lengths and rows
        result.append(dict(update=u+1,rows=pos,contract_lengths_exact=lengths,row_count_exact=rows,logged=log['on_policy_maxdev'],recounted=maximum,difference=maximum-log['on_policy_maxdev'],exact=maximum==log['on_policy_maxdev']))
    assert any(not x['exact'] for x in result)
    paths=[Path(__file__),HERE/'PLAN.md',ORIGINAL/'verify.py',BASE/'development_rl_1_recovery/verify_v2.py',checks/'l72-outcome-rl-independent.json',checks/'l72-outcome-rl-independent.out',ORIGINAL/'trained.json',ORIGINAL/'evaluated.json']
    output=dict(complete=True,updates=result,rows=sum(x['rows'] for x in result),original_exact_summary_passed=all(x['exact'] for x in result),all_per_row_original_ratio_limits_passed=True,max_summary_difference=max(abs(x['difference']) for x in result),bindings={str(p.relative_to(ROOT)):sha(p) for p in paths},new_inference=False,new_optimization=False)
    (HERE/'diagnosed.json').write_text(json.dumps(output,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:output[k] for k in ('rows','original_exact_summary_passed','max_summary_difference')}));print('OUTCOME_RL_RECOUNT_DIAGNOSED')
if __name__=='__main__':main()
