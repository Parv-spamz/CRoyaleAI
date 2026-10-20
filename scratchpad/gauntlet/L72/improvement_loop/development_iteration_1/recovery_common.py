"""Additional immutable source/receipt binding for serialization-only continuation."""
import common as c

NAMES=('RECOVERY_PLAN.md','portable_checkpoint.py','evaluate_v2.py','recount_v2.py',
       'recovery_common.py','resume_chain.py','bind_recovery.py')


def check_recovery():
    bound=c.read(c.HERE/'recovery_bound.json')
    for path,h in bound['sources'].items():assert c.sha(c.ROOT/path)==h,path
    for path,h in bound['completed_evidence'].items():assert c.sha(c.ROOT/path)==h,path
    c.check_frozen()
    return bound
