import copy,hashlib,json
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4];OLD=HERE.parent/'late_game_readiness'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(p.read_text())
def arrays(p):
    with np.load(p,allow_pickle=False) as z:return {k:z[k] for k in z.files}
def count(rows):
    assert len(rows)==16 and [x['index'] for x in rows]==list(range(16))
    out=[]
    for x in rows:
        r=x['result'];f=x['full'];l=x['late'];p=r['readiness']['phase']
        assert r['league']['seed']==2026101400+x['index'] and r['entry_index']==x['index']
        assert r['readiness']['native']['game_over'] and r['end_tick']==r['readiness']['native']['tick']
        b=p['regular_ticks']+p['overtime_ticks']//2;idx=np.flatnonzero(f['tick']>=b)
        assert set(f)==set(l) and all(np.array_equal(f[k][idx],l[k]) for k in f)
        assert idx.tolist()==x['record']['late_indices'] and b==x['record']['boundary']
        k=l['gate_sampled']|l['played'];kf=f['gate_sampled']|f['played']
        out.append(dict(index=x['index'],boundary=b,end_tick=r['end_tick'],full_decisions=len(f['tick']),full_contributing=int(kf.sum()),
            late_decisions=len(l['tick']),late_contributing=int(k.sum()),late_play=int(l['played'][k].sum()),late_wait=int((~l['played'][k]).sum())))
    return dict(games=16,late_games=sum(x['late_contributing']>0 for x in out),full_rows=sum(x['full_contributing'] for x in out),late_rows=sum(x['late_contributing'] for x in out),per_game=out)
def main():
    assert not (HERE/'report.json').exists();r=read(OLD/'collected.json');receipt=ROOT/'scratchpad/gauntlet/L71/integration/checks/l72-late-game-readiness-collection.json'
    rr=read(receipt);assert rr['exit_code']==1 and not rr['matched'];assert not (OLD/'report.json').exists() and not (OLD/'verified.json').exists()
    for p,h in r['sources'].items():assert sha(ROOT/p)==h,p
    rows=[]
    for x in r['records']:
        for k in ('result','full','late'):assert sha(ROOT/x[k])==x[k+'_sha256']
        rows.append(dict(index=x['index'],record=x,result=read(ROOT/x['result']),full=arrays(ROOT/x['full']),late=arrays(ROOT/x['late'])))
    c=count(rows);assert c['late_games']==r['late_games']==4 and c['late_rows']==r['late_rows']==91
    bad=[rows[:-1],rows+[rows[0]]]
    for key in ('tick','past','opp_past','lp_gate'):
        q=copy.deepcopy(rows);q[0]['late'][key].flat[0]+=1;bad.append(q)
    q=copy.deepcopy(rows);q[0]['record']['late_indices']=[];bad.append(q)
    q=copy.deepcopy(rows);q[0]['result']['readiness']['native']['game_over']=False;bad.append(q)
    for q in bad:
        try:count(q)
        except (AssertionError,KeyError,IndexError,ValueError):pass
        else:raise AssertionError('Corruption accepted')
    out=dict(complete=True,original_readiness_pass=False,coverage=c,controls=dict(positive=1,negative=len(bad)),new_games=0,model_inference=False,backward=False,optimizer_updates=0,
        original_collected_sha256=sha(OLD/'collected.json'),failed_receipt_sha256=sha(receipt),sources={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),HERE/'PLAN.md',OLD/'collect.py',OLD/'selection.py',OLD/'PLAN.md',OLD/'METRICS.md']})
    (HERE/'report.json').write_text(json.dumps(out,indent=2)+'\n');print('LATE_COVERAGE_DIAGNOSED')
if __name__=='__main__':main()
