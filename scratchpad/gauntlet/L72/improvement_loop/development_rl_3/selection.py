"""Pure training membership and fixed equal-match sampling; no policy decisions."""
import numpy as np
def select(result,late):
    t=result['traj'];p=result['readiness']['phase'];n=result['readiness']['native']
    assert n['game_over'] and n['terminated']
    assert all(type(p[k]) is int and p[k]>0 for k in ('regular_ticks','overtime_ticks'))
    ticks=t['tick'];assert len(ticks)>0 and ticks.ndim==1 and np.all(np.diff(ticks)>0)
    assert all(len(a)==len(ticks) for a in t.values()) and np.all(ticks<sum(p.values()))
    boundary=p['regular_ticks']+p['overtime_ticks']//2
    ix=np.flatnonzero(ticks>=boundary) if late else np.arange(len(ticks))
    return {**result,'traj':{k:v[ix].copy() for k,v in t.items()}},ix,boundary
def draws(match,uniforms):
    assert match.ndim==1 and len(match)>0 and np.all(np.diff(match)>=0)
    assert uniforms.ndim==2 and uniforms.shape[1]==2 and np.isfinite(uniforms).all()
    assert np.all((uniforms>=0)&(uniforms<1))
    ids=np.unique(match);by={j:np.flatnonzero(match==j) for j in ids}
    chosen=ids[(uniforms[:,0]*len(ids)).astype(np.int64)]
    return np.array([by[j][int(v*len(by[j]))] for j,v in zip(chosen,uniforms[:,1])],dtype=np.int64)
