"""Independent saved-record reconciliation; no engine/model/producer imports."""
import copy,hashlib,json
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
def read(p):return json.loads(p.read_text())
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def arrays(p):
    with np.load(p,allow_pickle=False) as z:return {k:z[k] for k in z.files}
def recurrence(r,v,m,g,lam):
    ans=np.zeros(len(r),dtype=np.float64)
    for group in np.unique(m):
        ix=np.flatnonzero(m==group);carry=0.;next_value=0.
        for i in ix[::-1]:
            delta=float(r[i])+float(g[i])*next_value-float(v[i])
            carry=delta+float(g[i])*lam*carry;ans[i]=carry;next_value=float(v[i])
    return ans,ans+v
def validate(rows,caches):
    assert len(rows)==64 and [x['index'] for x in rows]==list(range(64))
    nlate=sum(int((x['late']['gate_sampled']|x['late']['played']).any()) for x in rows)
    expected={name:dict(match=[],tick=[],lp_old=[],r_step=[],gamma_row=[],w=[]) for name in ('full','late')}
    ns={name:[int((x[name]['gate_sampled']|x[name]['played']).sum()) for x in rows] for name in ('full','late')}
    for x in rows:
        i=x['index'];r=x['result'];f=x['full'];t=x['late'];p=r['readiness']['phase'];nat=r['readiness']['native'];sp=r['league']
        assert sp['seed']==2026101500+i and sp['learner_side']==(i//2)%2 and sp['opp']['id']==('gen' if i%2==0 else 's1')
        assert sp['tag']==f'late-ready-{2026101500+i}' and r['entry_index']==i
        assert nat['game_over'] and nat['terminated'] and nat['tick']==r['end_tick'] and not r['form_fallbacks']
        assert nat['winner'] in (0,1,2)
        outcome='draw' if nat['winner']==2 else 'win' if nat['winner']==sp['learner_side'] else 'loss'
        assert r['outcome']==outcome
        assert (r['crowns_for'],r['crowns_against'])==(nat['crowns'][sp['learner_side']],nat['crowns'][1-sp['learner_side']])
        assert all(type(p[k]) is int and p[k]>0 for k in ('regular_ticks','overtime_ticks'))
        boundary=p['regular_ticks']+p['overtime_ticks']//2
        idx=np.flatnonzero(f['tick']>=boundary)
        assert x['record']['boundary']==boundary and x['record']['late_indices']==idx.tolist()
        assert set(f)==set(t) and 'phi_state' not in f
        assert all(len(a)==len(f['tick']) for a in f.values())
        assert all(np.array_equal(t[k],f[k][idx]) for k in f)
        assert len(f['tick']) and np.all(np.diff(f['tick'])>0) and np.all(f['tick']<p['regular_ticks']+p['overtime_ticks'])
        assert len(f['tick'])==x['record']['full_decisions'] and len(idx)==x['record']['late_decisions'] and ns['late'][i]==x['record']['late_contributing']
        assert np.all(f['T']==.5) and np.array_equal(f['gate_sampled'],f['allowed'].any(1)&~f['stalled'])
        assert np.all(f['allowed'][f['played'],f['slot'][f['played']]])
        assert np.all((f['cell'][f['played']]>=0)&(f['cell'][f['played']]<2304))
        assert np.all(f['lp_card'][~f['played']]==0) and np.all(f['lp_cell'][~f['played']]==0)
        for name in ('full','late'):
            t=x[name];keep=t['gate_sampled']|t['played'];ticks=t['tick'][keep];n=len(ticks)
            if not n:continue
            target={'win':1.,'loss':-1.,'draw':0.}[outcome]*.99994**(r['end_tick']-ticks[-1])
            reward=np.zeros(n);reward[-1]=target
            vals=dict(match=np.full(n,i),tick=ticks,lp_old=sum(t[k][keep] for k in ('lp_gate','lp_card','lp_cell')),
                r_step=reward,gamma_row=np.r_[.99994**np.diff(ticks).astype(np.float64),1.],w=np.full(n,1./(n*sum(z>0 for z in ns[name]))))
            for k,a in vals.items():expected[name][k].append(a)
    for name in ('full','late'):
        c=caches[name];ex={k:np.concatenate(v) for k,v in expected[name].items()};n=len(ex['tick'])
        assert all(len(a)==n and np.isfinite(a).all() for a in c.values())
        for k,a in ex.items():assert np.array_equal(c[k],a),(name,k)
        for s,lam in [('95',.95),('1',1.)]:
            adv,ret=recurrence(c['r_step'],c['value'],c['match'],c['gamma_row'],lam)
            assert np.allclose(c['adv'+s],adv,rtol=0,atol=1e-12) and np.allclose(c['ret'+s],ret,rtol=0,atol=1e-12)
        norm=(c['adv95']-c['adv95'].mean())/(c['adv95'].std()+1e-8)
        assert np.array_equal(c['normalized_adv95'],norm)
        analytic=np.array([{'win':1.,'loss':-1.,'draw':0.}[rows[int(m)]['result']['outcome']]*.99994**(rows[int(m)]['result']['end_tick']-t) for m,t in zip(c['match'],c['tick'])])
        assert np.allclose(c['ret1'],analytic,rtol=0,atol=1e-12)
    f=caches['full'];c=caches['late'];idx=np.array([t>=rows[int(m)]['record']['boundary'] for m,t in zip(f['match'],f['tick'])])
    for k in ('match','tick','lp_old','value','r_step','gamma_row','adv95','adv1','ret95','ret1'):assert np.array_equal(f[k][idx],c[k]),k
    value_delta=float(np.max(np.abs(c['value']-c['separately_recomputed_value'])));assert value_delta<1e-5
    ratio=np.abs(np.expm1(c['lp_gate']+c['lp_card']+c['lp_cell']-c['lp_old']))
    assert np.isfinite(ratio).all() and ratio.max()<1e-4
    assert nlate>=4 and len(c['tick'])>=256
    return dict(games=64,late_games=nlate,full_rows=len(f['tick']),late_rows=len(c['tick']),ratio_maxdev=float(ratio.max()),value_batch_max_difference=value_delta)
def main():
    assert not (HERE/'verified.json').exists();report=read(HERE/'report.json')
    assert report['complete'] and report['optimizer_updates']==report['new_models']==0 and report['unchanged_parameters'] and not report['deployed']
    rr=read(ROOT/'scratchpad/gauntlet/L71/integration/checks/l72-late-game-readiness2-collection.json');assert rr['exit_code']==0 and rr['matched']
    for p,h in report['sources'].items():assert sha(ROOT/p)==h,p
    rows=[];caches={}
    for x in report['records']:
        for k in ('full','late','result'):assert sha(ROOT/x[k])==x[k+'_sha256']
        r=read(ROOT/x['result'])
        for k in ('initial','native'):
            d=r['readiness'][k];assert sha(ROOT/d['path'])==d['sha256']
        rows.append(dict(index=x['index'],record=x,result=r,full=arrays(ROOT/x['full']),late=arrays(ROOT/x['late'])))
    for name,s in report['summaries'].items():
        assert sha(ROOT/s['cache'])==s['cache_sha256'];caches[name]=arrays(ROOT/s['cache'])
    totals=validate(rows,caches)
    for k in ('late_games','late_rows','ratio_maxdev','value_batch_max_difference'):assert totals[k]==report[k]
    assert all(np.isfinite(v) and v>0 for v in report['policy_gradient_squares'].values())
    assert np.isfinite(report['critic_gradient_square']) and report['critic_gradient_square']>0
    # Each corruption changes a distinct contract and must fail the same validator.
    bad=[(rows[:-1],caches),(rows+[rows[0]],caches)]
    j=next(i for i,r in enumerate(rows) if len(r['late']['tick']))
    for key in ('tick','past','opp_past','lp_gate'):
        q=copy.deepcopy(rows);q[j]['late'][key].flat[0]+=.1 if key!='tick' else 1;bad.append((q,caches))
    q=copy.deepcopy(rows);q[j]['result']['outcome']='invalid';bad.append((q,caches))
    q=copy.deepcopy(rows);q[j]['result']['readiness']['native']['game_over']=False;bad.append((q,caches))
    q=copy.deepcopy(rows);q[j]['record']['late_indices']=[];bad.append((q,caches))
    for key in ('w','r_step','gamma_row','lp_gate','adv95','ret1'):
        c=copy.deepcopy(caches);c['late'][key][0]+=.1;bad.append((rows,c))
    for q,c in bad:
        try:validate(q,c)
        except (AssertionError,KeyError,ValueError,IndexError):pass
        else:raise AssertionError('Corruption accepted')
    out=dict(complete=True,report_sha256=sha(HERE/'report.json'),totals=totals,controls=dict(positive=1,negative=len(bad)),optimizer_updates=0,new_models=0,deployed=False,source_sha256=sha(Path(__file__)))
    (HERE/'verified.json').write_text(json.dumps(out,indent=2)+'\n');print('LATE_GAME_READINESS_VERIFIED')
if __name__=='__main__':main()
