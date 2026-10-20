"""Post-termination learning view. No simulator, policy or tactical action."""
import numpy as np
def late_view(result):
    phase=result['readiness']['phase'];regular=phase['regular_ticks'];overtime=phase['overtime_ticks']
    assert type(regular) is int and regular>0 and type(overtime) is int and overtime>0
    boundary=regular+overtime//2
    t=result['traj'];ticks=t['tick'];assert ticks.ndim==1 and np.all(np.diff(ticks)>0)
    assert all(isinstance(a,np.ndarray) and len(a)==len(ticks) for a in t.values())
    assert result['readiness']['native']['game_over'] and result['readiness']['native']['terminated']
    idx=np.flatnonzero(ticks>=boundary)
    return {**result,'traj':{k:a[idx].copy() for k,a in t.items()}},idx,boundary
