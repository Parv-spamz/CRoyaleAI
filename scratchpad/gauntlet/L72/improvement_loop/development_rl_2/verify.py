"""Independent raw rollout/reward/cache recount; no new model inference."""
import math
from shared import *
def arrays(p):
    with np.load(p,allow_pickle=False) as z:return {k:z[k] for k in z.files}
def verify_update(u,log,raw,contract,setups):
    assert len(raw)==8 and [r['entry_index'] for r in raw]==list(range(8))
    pos=0;outcomes=[];ratio_max=0.
    for i,r in enumerate(raw):
        sp=r['league'];expected=setups[u*8+i]
        assert sp==expected['spec'] and r['native']['initial_state_sha256']==expected['initial_state_sha256']
        n=r['native'];assert n['winner'] in (0,1,2) and n['game_over'] and n['terminated'] and n['tick']==r['end_tick'] and not r['form_fallbacks']
        outcome='draw' if n['winner']==2 else 'win' if n['winner']==sp['learner_side'] else 'loss';assert outcome==r['outcome'];outcomes.append(outcome)
        assert (r['crowns_for'],r['crowns_against'])==(n['crowns'][sp['learner_side']],n['crowns'][1-sp['learner_side']])
        f=ROOT/r['trajectory'];assert sha(f)==r['trajectory_sha256'];t=arrays(f)
        assert np.all(t['tick']<6000) and np.all(np.diff(t['tick'])>0)
        pl=t['played'];assert np.all(t['allowed'][pl,t['slot'][pl]]) and np.all((t['cell'][pl]>=0)&(t['cell'][pl]<2304))
        assert np.array_equal(t['gate_sampled'],t['allowed'].any(1)&~t['stalled'])
        keep=pl|t['gate_sampled'];ticks=t['tick'][keep];count=len(ticks);assert count
        sl=slice(pos,pos+count);assert np.all(contract['match'][sl]==i)
        lp=sum(t[k][keep] for k in ('lp_gate','lp_card','lp_cell'))
        delta=np.abs(np.expm1(contract['lp_new'][sl]-lp));assert np.isfinite(delta).all() and delta.max()<1e-4;ratio_max=max(ratio_max,float(delta.max()))
        reward={'win':1.,'loss':-1.,'draw':0.}[outcome];step=np.zeros(count);step[-1]=reward*.99994**(n['tick']-ticks[-1])
        gam=np.r_[.99994**np.diff(ticks),1.]
        assert np.array_equal(contract['r_step'][sl],step) and np.array_equal(contract['gamma_row'][sl],gam)
        pos+=count
    assert all(len(x)==pos for x in contract.values()) and log['rows']==pos and log['on_policy_maxdev']==ratio_max
    adv=np.zeros(pos);next_a=next_v=0.
    for j in range(pos-1,-1,-1):
        if j==pos-1 or contract['match'][j]!=contract['match'][j+1]:next_a=next_v=0.
        adv[j]=contract['r_step'][j]+contract['gamma_row'][j]*next_v-contract['v_old'][j]+contract['gamma_row'][j]*1.0*next_a
        next_a=adv[j];next_v=contract['v_old'][j]
    assert np.allclose(adv+contract['v_old'],contract['returns'],rtol=0,atol=1e-12)
    assert np.allclose((adv-adv.mean())/(adv.std()+1e-8),contract['advantage'],rtol=0,atol=1e-12)
    for key,label in [('W','win'),('L','loss'),('D','draw')]:assert log['monitors'][key]==outcomes.count(label)
    assert math.isfinite(log['on_policy_torch_maxdev']) and log['on_policy_torch_maxdev']<1e-4
    assert log['critic_warmup']==(u<5) and log['ppo']['nonfinite'] is None and not log['stop']
    assert log['ppo']['steps']==2*math.ceil(pos/256)
    assert all(math.isfinite(log['ppo'][k]) for k in ('l_pg','l_v','grad_norm_mean','ratio_mean'))
    return dict(games=8,rows=pos,ratio_maxdev=ratio_max)
def main():
    assert not (HERE/'results_verified.json').exists();prepared=check();trained=read(HERE/'trained.json');ev=read(HERE/'evaluated.json')
    for stage in ('prepare','train','eval'):
        r=read(ROOT/f'scratchpad/gauntlet/L71/integration/checks/l72-outcome-lambda1-{stage}.json');assert r['exit_code']==0 and r['matched']
    assert trained['complete'] and trained['updates']==32 and trained['games']==256 and sha(ROOT/trained['checkpoint'])==trained['checkpoint_sha256']
    assert sha(OUT/'train.jsonl')==trained['train_log_sha256'];logs=[json.loads(s) for s in (OUT/'train.jsonl').read_text().splitlines()]
    assert [l['update'] for l in logs]==list(range(1,33));updates=[]
    for u,log in enumerate(logs):
        rp=OUT/'rollouts'/f'u{u:03d}.json';cp=OUT/'rollouts'/f'u{u:03d}_contract.npz'
        assert sha(rp)==log['rollouts_sha256'] and sha(cp)==log['contract_sha256']
        raw=read(rp);con=arrays(cp);updates.append(verify_update(u,log,raw,con,prepared['setups']))
    # Deliberate edits exercise the actual frozen verifier on one complete update.
    raw=read(OUT/'rollouts/u000.json');con=arrays(OUT/'rollouts/u000_contract.npz');import copy
    corrupt=[(raw[:-1],con),(raw+[raw[0]],con)]
    for key in ('lp_new','r_step','returns','advantage'):
        q=copy.deepcopy(con);q[key][0]+=.1;corrupt.append((raw,q))
    q=copy.deepcopy(raw);q[0]['native']['winner']=7;corrupt.append((q,con))
    for rr,cc in corrupt:
        try:verify_update(0,logs[0],rr,cc,prepared['setups'])
        except (AssertionError,KeyError,ValueError,IndexError):pass
        else:raise AssertionError('Corrupt rollout contract accepted')
    ids=c.indices('development');sub,meta=c.load_subset(c.DATA,ids);cv=meta['card_vocab'];ms,target=masks(ids)
    count=independent_counter();reports={};hashes={}
    locations={'r1e_corrected':c.OUT/'r1e_corrected_eval/predictions.npz','ordinary_v5':c.OUT/'ordinary_v5_eval_v2/predictions.npz',ARM:OUT/'predictions.npz'}
    reference=read(HERE.parent/'development_iteration_7/results_verified_v2.json')
    for arm,path in locations.items():
        a=arrays(path);assert np.array_equal(a.pop('ids'),ids)
        if arm!=ARM:assert sha(path)==reference['hashes'][arm]['cache']
        else:assert sha(path)==ev['cache_sha256']
        reports[arm]=count(sub,a,cv,ms,target);hashes[arm]=dict(cache=sha(path))
    assert reports[ARM]==ev['counts'];a,b=reports['ordinary_v5'],reports[ARM]
    f=dict(rocket_aim_material=(b['rocket']['aim1']-a['rocket']['aim1'])/a['rocket']['rows']>=.05,
       rocket_action_material=(b['rocket']['action']-a['rocket']['action'])/a['rocket']['rows']>=.02,
       late_rocket_material=(b['rocket_late_overtime_clock']['action']-a['rocket_late_overtime_clock']['action'])/a['rocket_late_overtime_clock']['rows']>=.02,
       general_card_noninferior=(b['all']['card']-a['all']['card'])/a['all']['play']>=-.005,
       barrel_correct_nonregression=b['barrel_pro']['log_correct']>=a['barrel_pro']['log_correct'],barrel_wrong_nonregression=b['barrel_pro']['log_wrong']<=a['barrel_pro']['log_wrong'])
    for key in ('witch','night_witch','furnace','defensive_sequence','phase_late_overtime_clock'):f[key+'_nonregression']=b[key]['action']>=a[key]['action']
    paired={control:{group:{rep:{key:value-reports[control][group]['by_replay'][rep][key] for key,value in vals.items()} for rep,vals in groupvals['by_replay'].items()} for group,groupvals in b.items()} for control in ('ordinary_v5','r1e_corrected')}
    write(OUT/'all_replay_counts.json',reports);write(OUT/'paired_replay_counts.json',paired)
    summary={arm:{group:{k:v for k,v in val.items() if k!='by_replay'} for group,val in groups.items()} for arm,groups in reports.items()}
    write(HERE/'results_verified.json',dict(complete=True,updates=updates,rows=len(ids),hashes=hashes,counts=summary,filters=f,continuation_passed=all(f.values()),controls=dict(positive=1,negative=len(corrupt)),paired_sha256=sha(OUT/'paired_replay_counts.json'),replay_counts_sha256=sha(OUT/'all_replay_counts.json'),checkpoint_sha256=trained['checkpoint_sha256'],developmental_only=True,deployment_accepted=False))
    check();print(json.dumps(f));print('OUTCOME_RL_VERIFIED')
if __name__=='__main__':main()
