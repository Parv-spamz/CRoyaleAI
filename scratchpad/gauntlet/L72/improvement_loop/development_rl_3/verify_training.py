"""Independent saved training recount. No policy inference, engine or RL imports."""
import copy,hashlib,json,math
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4];OUT=ROOT/'icebow/data/bench/development_rl_3_20261006'
ARMS=('full_budget_v5','late_budget_v5')
def read(p):return json.loads(p.read_text())
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def arrays(p):
    with np.load(p,allow_pickle=False) as z:return {k:z[k] for k in z.files}
def tensor_hash(state,exclude_value=False):
    h=hashlib.sha256()
    for k,v in sorted(state.items()):
        if exclude_value and k.startswith('value_head.'):continue
        a=v.detach().cpu().numpy();h.update(k.encode());h.update(str(a.dtype).encode());h.update(str(a.shape).encode());h.update(a.tobytes())
    return h.hexdigest()
def recurrence(r,v,m,g):
    out=np.zeros(len(r),np.float64)
    for group in np.unique(m):
        carry=nv=0.
        for j in np.flatnonzero(m==group)[::-1]:
            carry=float(r[j])+float(g[j])*nv-float(v[j])+float(g[j])*.95*carry;out[j]=carry;nv=float(v[j])
    return out,out+v
def validate(u,arm,log,records,rows,b,d,con,setups):
    assert len(records)==len(rows)==64 and [x['index'] for x in records]==list(range(64))
    assert log['arm']==arm and log['update']==u+1 and log['games']==64
    expected={k:[] for k in b};counts=[];outcomes=[]
    for i,(r,t,x) in enumerate(zip((z[0] for z in rows),(z[1] for z in rows),records)):
        s=setups[u*64+i];spec=s['spec'];nat=r['readiness']['native'];phase=r['readiness']['phase'];ini=r['readiness']['initial']
        assert r['league']==spec and r['entry_index']==i and spec['seed']==2026102000+u*64+i
        assert spec['learner_side']==(i//2)%2 and spec['opp']['id']==('gen' if i%2==0 else 's1')
        assert ini['path']==s['initial_state_path'] and ini['sha256']==s['initial_state_sha256'] and ini['forms']==s['forms']
        assert nat['game_over'] and nat['terminated'] and nat['winner'] in (0,1,2) and nat['tick']==r['end_tick'] and not r['form_fallbacks']
        outcome='draw' if nat['winner']==2 else 'win' if nat['winner']==spec['learner_side'] else 'loss'
        assert r['outcome']==outcome;outcomes.append(outcome)
        assert [r['crowns_for'],r['crowns_against']]==[nat['crowns'][spec['learner_side']],nat['crowns'][1-spec['learner_side']]]
        assert all(type(phase[k]) is int and phase[k]>0 for k in ('regular_ticks','overtime_ticks'))
        boundary=phase['regular_ticks']+phase['overtime_ticks']//2
        assert len(t['tick']) and np.all(np.diff(t['tick'])>0) and np.all(t['tick']<sum(phase.values()))
        assert all(len(a)==len(t['tick']) for a in t.values()) and 'phi_state' not in t
        assert np.array_equal(t['gate_sampled'],t['allowed'].any(1)&~t['stalled']) and np.all(t['T']==.5)
        pl=t['played'];assert np.all(t['allowed'][pl,t['slot'][pl]]) and np.all((t['cell'][pl]>=0)&(t['cell'][pl]<2304))
        assert np.all(t['lp_card'][~pl]==0) and np.all(t['lp_cell'][~pl]==0)
        selected=np.flatnonzero(t['tick']>=boundary) if arm==ARMS[1] else np.arange(len(t['tick']))
        assert x['selected_indices']==selected.tolist() and x['boundary']==boundary
        keep=selected[(t['gate_sampled']|pl)[selected]];n=len(keep);counts.append(n);assert x['selected_contributing']==n
        if not n:continue
        ticks=t['tick'][keep];rew=np.zeros(n);rew[-1]={'win':1.,'loss':-1.,'draw':0.}[outcome]*.99994**(r['end_tick']-ticks[-1])
        derived=dict(A=np.zeros(n),match=np.full(n,i),lp_old=sum(t[k][keep] for k in ('lp_gate','lp_card','lp_cell')),r_step=rew,gamma_row=np.r_[.99994**np.diff(ticks).astype(np.float64),1.])
        for k in b:
            if k=='w':continue
            assert k in t or k in derived,k
            expected[k].append(t[k][keep] if k in t else derived[k])
    eligible=sum(n>0 for n in counts);n=sum(counts);assert eligible>=4 and n>=256
    expected['w']=[np.full(x,1./(eligible*x)) for x in counts if x]
    assert log['public_keys']==read(HERE.parent/'late_game_readiness_2/report.json')['public_keys']
    assert set(log['public_keys'])<=set(b) and log['rows']==n and log['eligible_games']==eligible and log['draws']==2048
    for k,vals in expected.items():assert np.array_equal(b[k],np.concatenate(vals)),k
    assert all(np.isfinite(a).all() for a in b.values()) and all(np.isfinite(a).all() for a in con.values())
    assert len(con['value'])==len(con['lp_new'])==len(con['raw_advantage'])==len(con['returns'])==n
    ratio=np.abs(np.expm1(con['lp_new']-b['lp_old']));assert ratio.max()<1e-4 and float(ratio.max())==log['on_policy_maxdev']
    adv,ret=recurrence(b['r_step'],con['value'],b['match'],b['gamma_row'])
    assert np.allclose(adv,con['raw_advantage'],rtol=0,atol=1e-12) and np.allclose(ret,con['returns'],rtol=0,atol=1e-12)
    uv=np.random.default_rng(2026101600+u).random((2048,2));assert np.array_equal(con['uniforms'],uv)
    groups=[i for i,x in enumerate(counts) if x];starts=np.r_[0,np.cumsum(counts)];want=[]
    for a,z in uv:
        group=groups[int(a*len(groups))];want.append(starts[group]+int(z*counts[group]))
    ix=np.asarray(want,dtype=np.int64);assert np.array_equal(con['draw'],ix)
    assert set(d)==set(b)|{'v_old','ret'} and all(len(a)==2048 and np.isfinite(a).all() for a in d.values())
    drawadv=con['raw_advantage'][ix]
    overrides=dict(w=np.full(2048,1./2048),A=(drawadv-drawadv.mean())/(drawadv.std()+1e-8),v_old=con['value'][ix],ret=con['returns'][ix])
    for k,a in d.items():assert np.array_equal(a,overrides[k] if k in overrides else b[k][ix]),k
    for k,name in [('W','win'),('L','loss'),('D','draw')]:assert log['monitors'][k]==outcomes.count(name)
    assert log['monitors']['matches']==64 and log['critic_warmup']==(u<5) and not log['stop']
    assert log['ppo']['steps']==16 and log['ppo']['nonfinite'] is None
    for k in ('l_pg','l_v','grad_norm_mean','ratio_mean'):assert math.isfinite(log['ppo'][k])
    if u<5:assert log['nonvalue_before']==log['nonvalue_after']
    return dict(arm=arm,update=u+1,games=64,eligible_games=eligible,rows=n,draws=2048,steps=16,ratio_maxdev=float(ratio.max()))
def load_update(u,arm):
    rd=OUT/arm/'rollouts';prefix=f'u{u:03d}';records=read(rd/f'{prefix}_records.json');rows=[]
    for x in records:
        assert sha(ROOT/x['full'])==x['full_sha256'] and sha(ROOT/x['result'])==x['result_sha256'];r=read(ROOT/x['result'])
        for k in ('initial','native'):
            q=r['readiness'][k];assert sha(ROOT/q['path'])==q['sha256']
        rows.append((r,arrays(ROOT/x['full'])))
    return records,rows,arrays(rd/f'{prefix}_eligible.npz'),arrays(rd/f'{prefix}_drawn.npz'),arrays(rd/f'{prefix}_contract.npz')
def main():
    assert not (HERE/'training_verified.json').exists();p=read(HERE/'prepared.json');tr=read(HERE/'trained.json')
    assert tr['complete'] and tr['updates_per_arm']==16 and tr['total_games']==2048 and tr['total_optimizer_steps']==512
    assert tr['sources']==p['sources'] and tr['runtime']==p['runtime']
    for f,h in p['sources'].items():assert sha(ROOT/f)==h,f
    assert sha(OUT/'train.jsonl')==tr['train_log_sha256'];logs=[json.loads(s) for s in (OUT/'train.jsonl').read_text().splitlines()]
    assert [(x['update'],x['arm']) for x in logs]==[(u+1,a) for u in range(16) for a in ARMS]
    import torch
    initial=torch.load(ROOT/'icebow/data/bench/development_iteration_1_20261005/ordinary_v5/candidate_portable.pt',map_location='cpu',weights_only=False)
    initial_hash=tensor_hash(initial['model'],True);previous={a:initial_hash for a in ARMS};updates=[]
    for log in logs:
        u=log['update']-1;arm=log['arm'];rd=OUT/arm/'rollouts';prefix=f'u{u:03d}'
        for key in ('records','eligible','drawn','contract'):
            f=rd/f'{prefix}_{key}.{ "json" if key=="records" else "npz" }';assert sha(f)==log[key+'_sha256']
        data=load_update(u,arm);updates.append(validate(u,arm,log,*data,p['setups']));del data
        ck=OUT/arm/'checkpoints'/f'u{u+1:03d}.pt';st=torch.load(ck,map_location='cpu',weights_only=False)
        assert all(torch.isfinite(v).all() for v in st['model'].values())
        assert st['development_rl_3']['arm']==arm and st['development_rl_3']['update']==u+1 and st['development_rl_3']['eligible_final']==(u==15)
        assert st['development_rl_3']['config']==p['config'] and st['development_rl_3']['runtime']==p['runtime'] and st['development_rl_3']['parent_sha256']==p['initial_checkpoint_sha256']
        assert log['nonvalue_before']==previous[arm] and log['nonvalue_after']==tensor_hash(st['model'],True);previous[arm]=log['nonvalue_after']
        if u<5:assert previous[arm]==initial_hash
    # Same actual validator, serial corruptions avoid retaining duplicate full cohorts.
    base=load_update(0,ARMS[1]);log=logs[1];negative=0
    kinds=['missing_game','duplicate_game','membership','history','outcome','native','probability','reward','gamma','value','advantage','return','uniform','draw','weight','draw_history','normalization']
    for kind in kinds:
        records,rows,b,d,con=copy.deepcopy(base);j=next(i for i,x in enumerate(records) if x['selected_contributing'])
        if kind=='missing_game':records.pop()
        elif kind=='duplicate_game':records.append(records[0])
        elif kind=='membership':records[j]['selected_indices']=[]
        elif kind=='history':b['past'].flat[0]+=.1
        elif kind=='outcome':rows[j][0]['outcome']='invalid'
        elif kind=='native':rows[j][0]['readiness']['native']['game_over']=False
        elif kind=='probability':con['lp_new'][0]+=.1
        elif kind=='reward':b['r_step'][0]+=.1
        elif kind=='gamma':b['gamma_row'][0]+=.1
        elif kind=='value':con['value'][0]+=.1
        elif kind=='advantage':con['raw_advantage'][0]+=.1
        elif kind=='return':con['returns'][0]+=.1
        elif kind=='uniform':con['uniforms'][0,0]=1.
        elif kind=='draw':con['draw'][0]=(con['draw'][0]+1)%len(b['A'])
        elif kind=='weight':d['w'][0]+=.1
        elif kind=='draw_history':d['past'].flat[0]+=.1
        elif kind=='normalization':d['A'][0]+=.1
        try:validate(0,ARMS[1],log,records,rows,b,d,con,p['setups'])
        except (AssertionError,KeyError,ValueError,IndexError):negative+=1
        else:raise AssertionError('Corruption accepted: '+kind)
    for arm,a in tr['arms'].items():assert sha(ROOT/a['checkpoint'])==a['checkpoint_sha256']
    result=dict(complete=True,updates=updates,games=2048,optimizer_steps=512,controls=dict(positive=32,negative=negative),trained_sha256=sha(HERE/'trained.json'),source_sha256=sha(Path(__file__)),deployment_accepted=False)
    (HERE/'training_verified.json').write_text(json.dumps(result,indent=2)+'\n');print('LATE_CURRICULUM_TRAINING_VERIFIED')
if __name__=='__main__':main()
