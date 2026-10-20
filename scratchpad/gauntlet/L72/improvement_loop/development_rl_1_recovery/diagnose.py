"""Targeted constructor diagnosis, with no policy decisions or optimizer."""
import copy
from recovery import *
def main():
    assert not (RECOVERY/'verified.json').exists();p=check();f=failure_inputs();bound=binding()
    receipt=read(ROOT/'scratchpad/gauntlet/L71/integration/checks/l72-outcome-rl-train.json')
    assert receipt['exit_code']!=0 and not receipt['matched'] and read(HERE/'chain_failed.json')['job']=='train'
    assert not list(OUT.rglob('*.*')) and not (HERE/'progress.json').exists() and not (HERE/'trained.json').exists()
    assert len(p['setups'])==256
    for s in p['setups']:
        assert form_match({int(k):v for k,v in s['forms'].items()},s['forms'])
    runtime,RL=initialize_runtime();assert runtime==p['runtime']
    from pipeline import e1_eval as E,search_s0 as S
    from pipeline.royale_env import RoyaleSelfPlayEnv
    terminal=module('recovery_terminal',HERE.parent/'terminal_wrapper/adapter.py')
    pol,info=E.load_policy(INIT,'cpu');opp,oi=E.load_policy(g.OPP_GEN,'cpu')
    env=RoyaleSelfPlayEnv(decision_ticks=10,tail_cap=7200,forms_mode='deck',hero_abilities=True,ability_policy='v2')
    s=p['setups'][0];m=terminal.TerminalAwareMatch(env,s['spec'],0,S.live_cfg(.35,info['grid'],'cpu'),S.live_cfg(.27,oi['grid'],'cpu'),pol,opp,stop_decisions_at_fulltime=True)
    raw_equal=env.loaded_forms==s['forms'];canonical=form_match(env.loaded_forms,s['forms']);state_sha=g.blobsha(env.core.save_state())
    assert not raw_equal and canonical and state_sha==s['initial_state_sha256'] and not env.form_fallbacks
    actual=copy.deepcopy(env.loaded_forms);env.close()
    bad=[]
    q=copy.deepcopy(s['forms']);q['0'][0]=(q['0'][0]+1)%3;bad.append(q)
    q=copy.deepcopy(s['forms']);del q['1'];bad.append(q)
    q=copy.deepcopy(s['forms']);q['0']=q['0'][:-1];bad.append(q)
    q=copy.deepcopy(s['forms']);q['0'][0]=True;bad.append(q)
    q=copy.deepcopy(s['forms']);q['1'][0]=9;bad.append(q)
    for q in bad:
        try:assert form_match(actual,q)
        except AssertionError:pass
        else:raise AssertionError('Corrupt setup forms accepted')
    # Check the separate warmup concern against the actual optimizer wrapper.
    tree=ast.parse(Path(RL.__file__).read_text());fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='ppo_update')
    observed=[]
    def probe(model,*args):
        observed.append({k:q.requires_grad for k,q in model.named_parameters()});return dict(probe=True)
    ns=dict(Optional=__import__('typing').Optional,dict=dict,np=np,_ppo_steps=probe)
    exec(compile(ast.Module(body=[fn],type_ignores=[]),RL.__file__,'exec'),ns)
    model=pol.model;original={k:q.requires_grad for k,q in model.named_parameters()}
    ns['ppo_update'](model,None,None,None,{},.3,None,dict(policy=False,trunk_grad=True))
    assert all(v==k.startswith('value_head.') for k,v in observed[0].items()) and {k:q.requires_grad for k,q in model.named_parameters()}==original
    compile(training_source(),str(RECOVERY/'train_v2.py'),'exec');compile(verification_source(),str(RECOVERY/'verify_v2.py'),'exec')
    assert failure_inputs()==f and binding()==bound
    write(RECOVERY/'verified.json',dict(complete=True,sources=bound,original_failure=f,runtime=runtime,original_raw_form_comparison=False,canonical_form_comparison=True,native_initial_sha256=state_sha,prepared_setups_structurally_checked=256,native_setups_diagnosed=1,policy_decisions=0,optimizer_updates=0,outputs_empty=True,warmup_freezes_nonvalue=True,controls=dict(positive=1,negative=len(bad))))
    print('OUTCOME_RL_SETUP_RECOVERY_VERIFIED')
if __name__=='__main__':main()
