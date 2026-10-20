"""Independent record-only verifier: no model, RL helper or engine imports."""
import copy,hashlib,json
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
def read(p):return json.loads(p.read_text())
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def arrays(p):
    with np.load(p,allow_pickle=False) as z:return {k:z[k] for k in z.files}
def validate(rows,caches):
    keys={(r['arm'],r['scenario']) for r in rows}
    assert len(rows)==len(keys)==8 and keys=={(a,i) for a in ('r1e','ordinary_v5') for i in range(4)}
    totals={}
    for arm in ('r1e','ordinary_v5'):
        rs=sorted([x for x in rows if x['arm']==arm],key=lambda x:x['scenario']);c=caches[arm]
        pos=0;ratio_max=0.;plays=0;fulltime=0
        for x in rs:
            i=x['scenario'];r=x['result'];t=x['trajectory'];d=r['readiness'];nat=d['native'];sp=r['league']
            assert sp['seed']==2026100600+i//2 and sp['learner_side']==sp['seed']%2 and sp['opp']['id']==('gen' if i%2==0 else 's1')
            assert sp['tag']==f"rl-readiness-{sp['seed']}-{sp['opp']['id']}"
            assert nat['game_over'] and nat['terminated'] and nat['tick']==r['end_tick'] and not r['form_fallbacks']
            assert nat['winner'] in (0,1,2)
            outcome='draw' if nat['winner']==2 else 'win' if nat['winner']==sp['learner_side'] else 'loss'
            assert r['outcome']==outcome and nat['winner_side']==(-1 if nat['winner']==2 else nat['winner'])
            assert (r['crowns_for'],r['crowns_against'])==(nat['crowns'][sp['learner_side']],nat['crowns'][1-sp['learner_side']])
            assert d['boundary']==6000 and len(t['tick']) and np.all(np.diff(t['tick'])>0) and np.all(t['tick']<d['boundary'])
            assert np.all(t['T']==.5)
            assert np.array_equal(t['gate_sampled'],t['allowed'].any(1)&~t['stalled'])
            pl=t['played'];wait=~pl
            assert np.all(t['allowed'][pl,t['slot'][pl]]) and np.all((t['slot'][pl]>=0)&(t['slot'][pl]<8))
            assert np.all((t['cell'][pl]>=0)&(t['cell'][pl]<2304))
            assert np.all(t['lp_card'][wait]==0) and np.all(t['lp_cell'][wait]==0) and np.all(t['lp_gate'][~t['gate_sampled']]==0)
            keep=t['gate_sampled']|pl;n=int(keep.sum());assert n>0
            sl=slice(pos,pos+n);assert np.all(c['match'][sl]==i)
            lp=sum(t[k][keep] for k in ('lp_gate','lp_card','lp_cell'))
            rp=sum(c[k][sl] for k in ('lp_gate','lp_card','lp_cell'))
            assert np.all(np.isfinite(lp)) and np.all(np.isfinite(rp))
            ratio=np.abs(np.expm1(rp-lp));assert np.max(ratio)<1e-4;ratio_max=max(ratio_max,float(np.max(ratio)))
            ticks=t['tick'][keep];reward={'win':1.,'loss':-1.,'draw':0.}[outcome]
            expected=reward*.99994**(nat['tick']-ticks)
            assert np.allclose(c['analytic'][sl],expected,rtol=0,atol=1e-12)
            step=np.zeros(n);step[-1]=expected[-1]
            assert np.array_equal(c['r_step'][sl],step)
            gam=np.r_[.99994**np.diff(ticks),1.]
            assert np.array_equal(c['gamma_row'][sl],gam)
            other=next(z for z in rows if z['scenario']==i and z['arm']!=arm)
            assert d['initial']==other['result']['readiness']['initial']
            plays+=int(pl.sum());fulltime+=nat['tick']>=6000;pos+=n
        assert all(len(v)==pos for v in c.values())
        totals[arm]=dict(rows=pos,sampled_plays=plays,ratio_maxdev=ratio_max,fulltime_games=fulltime)
    return totals
def main():
    assert not (HERE/'verified.json').exists();p=read(HERE/'report.json');assert p['complete'] and p['optimizer_updates']==p['new_models']==0
    receipt=read(ROOT/'scratchpad/gauntlet/L71/integration/checks/l72-rl-readiness-collection.json');assert receipt['exit_code']==0 and receipt['matched']
    for path,h in p['sources'].items():assert sha(ROOT/path)==h,path
    rows=[];caches={}
    for x in p['records']:
        for k in ('result','trajectory'):assert sha(ROOT/x[k])==x[k+'_sha256']
        rows.append(dict(arm=x['arm'],scenario=x['scenario'],result=read(ROOT/x['result']),trajectory=arrays(ROOT/x['trajectory'])))
    for arm,g in p['gradients'].items():
        assert sha(ROOT/g['recomputed'])==g['recomputed_sha256'];caches[arm]=arrays(ROOT/g['recomputed'])
        assert g['unchanged_parameters'] and g['optimizer_updates']==0
        assert all(np.isfinite(v) and v>0 for v in g['policy_gradient_squares'].values()) and np.isfinite(g['critic_gradient_square']) and g['critic_gradient_square']>0
    totals=validate(rows,caches)
    for arm,g in p['gradients'].items():assert totals[arm]['rows']==g['rows'] and totals[arm]['ratio_maxdev']==g['ratio_maxdev']
    bad=[(rows[:-1],caches),(rows+[rows[0]],caches)]
    for key,value in [('outcome','impossible')]:
        q=copy.deepcopy(rows);q[0]['result'][key]=value;bad.append((q,caches))
    q=copy.deepcopy(rows);q[0]['result']['readiness']['native']['game_over']=False;bad.append((q,caches))
    q=copy.deepcopy(rows);q[0]['trajectory']['allowed'][:]=False;bad.append((q,caches))
    for key in ('lp_gate','analytic','gamma_row'):
        c=copy.deepcopy(caches);c['r1e'][key][0]+=.1;bad.append((rows,c))
    q=copy.deepcopy(rows);q[0]['trajectory']['tick'][-1]=6000;bad.append((q,caches))
    for q,c in bad:
        try:validate(q,c)
        except (AssertionError,KeyError,ValueError,IndexError):pass
        else:raise AssertionError('Corruption accepted')
    out=dict(complete=True,report_sha256=sha(HERE/'report.json'),totals=totals,controls=dict(positive=1,negative=len(bad)),optimizer_updates=0,new_models=0,legacy_dataset_access=False,deployment_accepted=False)
    (HERE/'verified.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out));print('RL_READINESS_VERIFIED')
if __name__=='__main__':main()
