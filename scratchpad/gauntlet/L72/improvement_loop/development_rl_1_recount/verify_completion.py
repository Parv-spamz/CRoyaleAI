"""Complete original recount while preserving exact-summary failures as false."""
import sys
from pathlib import Path
LEAF=Path(__file__).resolve().parent
sys.path.insert(0,str(LEAF.parent/'development_rl_1_recovery'))
from recovery import *
def main():
    check_recovery();d=read(LEAF/'diagnosed.json');assert d['complete']
    for path,digest in d['bindings'].items():assert sha(ROOT/path)==digest
    rr=read(ROOT/'scratchpad/gauntlet/L71/integration/checks/l72-outcome-rl-recount-diagnosis.json');assert rr['exit_code']==0 and rr['matched']
    assert d['all_per_row_original_ratio_limits_passed'] and not d['original_exact_summary_passed']
    seen=[]
    def record_ratio(u,log,maximum):
        # Initial32 invocations cover the complete cohort; later corruption probes
        # exercise the original per-row rules without appending duplicate evidence.
        if len(seen)<32:
            expected=d['updates'][u]
            assert u==len(seen) and maximum==expected['recounted'] and log['on_policy_maxdev']==expected['logged'] and log['rows']==expected['rows']
            seen.append(dict(update=u+1,logged=log['on_policy_maxdev'],recounted=maximum,exact=maximum==log['on_policy_maxdev']))
    source=verification_source()
    old="assert all(len(x)==pos for x in contract.values()) and log['rows']==pos and log['on_policy_maxdev']==ratio_max"
    new="assert all(len(x)==pos for x in contract.values()) and log['rows']==pos\n    record_ratio(u,log,ratio_max)"
    assert source.count(old)==1;source=source.replace(old,new)
    ns=dict(__name__='outcome_recount_completion',__file__=str(HERE/'verify.py'),record_ratio=record_ratio)
    exec(compile(source,str(HERE/'verify.py'),'exec'),ns);ns['main']()
    assert len(seen)==32
    r=read(HERE/'results_verified.json');r['policy_point_filters_passed']=r['continuation_passed']
    r['original_probability_summary_exact']=all(x['exact'] for x in seen)
    r['filters']['original_probability_summary_exact']=r['original_probability_summary_exact']
    r['continuation_passed']=all(r['filters'].values());assert not r['continuation_passed']
    r['ratio_summary_comparison']=seen;r['preserved_independent_failure_sha256']=sha(ROOT/'scratchpad/gauntlet/L71/integration/checks/l72-outcome-rl-independent.json')
    r['recount_completion_binding']={str(p.relative_to(ROOT)):sha(p) for p in (Path(__file__),LEAF/'PLAN.md',LEAF/'diagnosed.json')}
    write(HERE/'results_verified.json',r);check_recovery()
    print('OUTCOME_RL_RECOUNT_COMPLETE_WITH_FAILED_EXACTNESS')
if __name__=='__main__':main()
