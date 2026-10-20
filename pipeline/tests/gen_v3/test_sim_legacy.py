"""Byte and RNG oracles from pre-edit files, without git."""
import copy
import numpy as np
import torch
from pipeline import e1_eval as E, royale_env as RE, rl_royale as RL, eval_gen as EV
from pipeline.tests.gen_v3.test_legacy import baseline, CHECKPOINT, same
from pipeline.tests.test_rl_gen import _rollouts, _cfg
from pipeline.tests.test_royale_forms import ICEBOW, HOGEQ, scripted_trace, digest


def test_legacy_sim_raw_and_engine_rng_bytes():
    for version in (1,2):
        for forms in ('base','deck'):
            a=baseline('sim_royale_env').RoyaleSelfPlayEnv(forms_mode=forms,tail_cap=400)
            b=RE.RoyaleSelfPlayEnv(forms_mode=forms,tail_cap=400,feature_version=version)
            assert digest(scripted_trace(a,ICEBOW,HOGEQ,5))==digest(scripted_trace(b,ICEBOW,HOGEQ,5))
            assert a.core.save_state()==b.core.save_state()


def test_rseries_sim_rows_decisions_trajectory_and_rng_bytes():
    oldE=baseline('sim_e1_eval');oldRE=baseline('sim_royale_env')
    pol,_=E.load_policy(CHECKPOINT,'cpu')
    opol=oldE.GenPolicy(pol.model,list(pol.gid))
    for version in (1,2):
        pol.model.feature_version=version
        spec=dict(tag='legacy-rseries',learner_side=0,learner_deck=ICEBOW,opp_deck=HOGEQ,seed=3,opp={'id':'old'})
        cfg=_cfg(obs='live',extrapolate_ticks=26,action_delay_ticks=26,entry_index=0)
        a=oldE.SelfPlayMatch(oldRE.RoyaleSelfPlayEnv(forms_mode='deck',tail_cap=400),spec,0,cfg,cfg,opol,opol)
        b=E.SelfPlayMatch(RE.RoyaleSelfPlayEnv(forms_mode='deck',tail_cap=400),spec,0,cfg,cfg,pol,pol)
        while True:
            da,db=a.due(),b.due()
            assert len(da)==len(db)
            if not da:break
            for sa,sb in zip(da,db):
                sa.prepare();sb.prepare()
                ra,rb=sa.gen_row(opol),sb.gen_row(pol);same(ra,rb)
                ea,ha,pa,ma=opol.forward_batch([ra]);eb,hb,pb,mb=pol.forward_batch([rb])
                same(ea,eb);same(ha,hb);assert pa==pb and ma.tobytes()==mb.tobytes()
                xa=sa.decide_row(opol,ea,ha,pa[0],ma[0]);xb=sb.decide_row(pol,eb,hb,pb[0],mb[0])
                assert digest(xa)==digest(xb)
                sa.apply(pa[0],xa);sb.apply(pb[0],xb)
                assert sa.rng_obs.bit_generator.state==sb.rng_obs.bit_generator.state
                assert sa.rng_behave.bit_generator.state==sb.rng_behave.bit_generator.state
                assert sa.rng_rand.getstate()==sb.rng_rand.getstate()
        assert digest(a.result())==digest(b.result())
        assert a.env.core.save_state()==b.env.core.save_state()


def test_legacy_rl_collate_terms_values_and_shared_rows_bytes():
    from pipeline.tests.test_e1_eval_gen import _tiny_gen,VOCAB
    from pathlib import Path
    model=_tiny_gen(5)
    res=_rollouts(E.GenPolicy(model,VOCAB),n_matches=2)
    old=baseline('sim_rl_royale')
    a,sa=old.collate(res,advantage='gae');b,sb=RL.collate(res,advantage='gae')
    same(a,b);assert sa==sb
    b=RL.to_device(b,'cpu');idx=torch.arange(len(b['A']))
    same(old.policy_terms(model,b,idx,.27,.5,value=True),RL.policy_terms(model,b,idx,.27,.5,value=True))
    assert torch.equal(old.value_rows(model,b),RL.value_rows(model,b))
    arrs={k:v for k,v in np.load(Path(__file__).parent/'gen_dataset_v3.npz',allow_pickle=False).items()
          if k not in ('meta','unit_form','opp_past')}
    ids=np.arange(16)
    same(baseline('sim_eval_gen').GenRows(arrs,ids,'cpu').batch(ids),EV.GenRows(arrs,ids,'cpu').batch(ids))


def test_previous_worker_snapshot_hashes_unchanged():
    import hashlib,json
    from pathlib import Path
    root=Path(__file__).resolve().parents[3]
    hashes=json.loads((Path(__file__).parent/'baseline_hashes.json').read_text())
    for name,want in hashes.items():
        assert hashlib.sha256((root/name).read_bytes()).hexdigest()==want
