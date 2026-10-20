"""Bind reused native setup evidence and prove the one-factor full-return recipe."""
import copy,datetime,os
from shared import *
def main():
    assert not (HERE/'prepared.json').exists() and not OUT.exists()
    original=module('lambda1_original_shared',HERE.parent/'development_rl_1/shared.py')
    previous=original.check();prerequisites()
    changed={k:(previous['config'][k],v) for k,v in CONFIG.items() if previous['config'].get(k)!=v}
    assert changed=={'gae_lambda':(.95,1.)} and set(CONFIG)==set(previous['config'])
    credit=read(HERE.parent/'rl_credit_audit/verified.json');review=read(HERE.parent/'rl_credit_audit/reviewed.json')
    assert credit['complete'] and review['complete'] and review['verified_sha256']==sha(HERE.parent/'rl_credit_audit/verified.json')
    assert credit['report_sha256']==sha(HERE.parent/'rl_credit_audit/report.json')
    for name in ('producer','independent','reviewed'):
        rec=read(ROOT/f'scratchpad/gauntlet/L71/integration/checks/l72-rl-credit-{name}.json');assert rec['exit_code']==0 and rec['matched']
    bound=sources();runtime,RL=initialize_runtime();assert runtime==previous['runtime']
    assert sha(INIT)==previous['initial_checkpoint_sha256']
    setups=previous['setups'];assert len(setups)==256 and [s['spec'] for s in setups]==schedule()
    for s in setups:
        assert len(s['initial_state_sha256'])==64
        assert form_match({int(k):v for k,v in s['forms'].items()},s['forms'])
    positives=0
    for reward in (-1.,0.,1.):
        for values in ([0.,0.,0.],[.8,-.5,.2]):
            ticks=np.array([0,17,53]);end=87;step=np.array([0.,0.,reward*.99994**(end-ticks[-1])]);gam=np.r_[.99994**np.diff(ticks),1.]
            adv,returns=RL.gae(step,np.array(values),np.zeros(3),gam,CONFIG['gae_lambda'])
            expected=reward*.99994**(end-ticks)
            assert np.allclose(returns,expected,rtol=0,atol=1e-12) and np.allclose(adv,expected-values,rtol=0,atol=1e-12)
            positives+=1
    # Multiple contiguous matches must reset terminal propagation.
    a,ret=RL.gae([0.,1.,0.,-1.],[.4,.3,.2,.1],[0,0,1,1],[.9,1.,.8,1.],1.)
    assert np.allclose(ret,[.9,1.,-.8,-1.],rtol=0,atol=1e-12);positives+=1
    # Same return target at lambda1 despite a change in fixed critic values.
    expect=setups[0]['forms'];actual={int(k):v.copy() for k,v in expect.items()}
    bad=[{'0':actual[0],1:actual[1]},copy.deepcopy(actual),copy.deepcopy(actual),copy.deepcopy(actual)]
    bad[1][0]=bad[1][0][:-1];bad[2][0][0]=7;bad[3][0][0]=(bad[3][0][0]+1)%3
    negatives=0
    for q in bad:
        try:assert form_match(q,expect)
        except AssertionError:negatives+=1
        else:raise AssertionError('Corrupt form map accepted')
    try:assert np.allclose(ret,[.9,1.,.8,1.],rtol=0,atol=1e-12)
    except AssertionError:negatives+=1
    else:raise AssertionError('Corrupt return accepted')
    assert sources()==bound
    OUT.mkdir();(OUT/'rollouts').mkdir();(OUT/'checkpoints').mkdir()
    write(HERE/'prepared.json',dict(complete=True,sources=bound,runtime=runtime,config=CONFIG,setups=setups,initial_checkpoint_sha256=sha(INIT),original_prepared_sha256=sha(original.HERE/'prepared.json'),one_factor=changed,controls=dict(positive=positives,negative=negatives),optimizer_steps=0,new_native_resets=0,candidate_optimization_updates=0,development_ids_sha256=sha(c.OUT/'indices.npz'),production_changed=False,utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
    print('OUTCOME_LAMBDA1_PREPARED')
if __name__=='__main__':main()
