"""Production v3 SIM, batching and RL checks; no training or live client."""
import copy
import json
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest
import torch

from pipeline import e1_eval as E, e1_view as V, dataset_gen as D, obs_contract as O, rl_royale as RL
from pipeline.eval_gen import GenRows, load_model
from pipeline.model_gen import GenModel
from pipeline.royale_env import RoyaleSelfPlayEnv
from pipeline.tests.test_rl_gen import _cfg

HERE = Path(__file__).parent
NAMES = ['Knight@evolution','Tesla@evolution','MiniPekka@hero','Skeletons','IceSpirits','Zap','Log','Arrows']


def policy(version=3):
    torch.manual_seed(17)
    if version == 0:
        from pipeline.model_v3 import S1Model
        return S1Model(d=16,layers=1).eval()
    return E.GenPolicy(GenModel(d=16,layers=1,d_c=8,n_cards=9,feature_version=version).eval(),
                       ['<pad>']+[D.card_key(n) for n in NAMES])


def match(p=None, other=None, **cfg):
    p = p or policy()
    spec = dict(tag='v3-integration',learner_side=0,learner_deck=NAMES,opp_deck=NAMES,seed=0,opp={'id':'old'})
    return E.SelfPlayMatch(RoyaleSelfPlayEnv(forms_mode='deck',tail_cap=400),spec,0,
                          _cfg(record=False,**cfg),_cfg(record=False,**cfg),p,other or policy(1))


def test_public_log_acceptance_landing_coordinates_reset():
    m=match(action_delay_ticks=26)
    ds=m.due()
    for s in ds:s.prepare()
    s=m.opp
    st=m.env.core.state().players[1]
    idx=min((m.env.deck_ids[1].index(c) for c in st.hand),key=lambda i:m.env.costs(1)[i])
    slot=next(k for k,v in s.deck_index_of_slot.items() if v==idx)
    s.apply(.9,dict(play=True,slot=slot,cell=1600,why='test'))
    assert not m.env.public_plays
    while m.env.tick < 116:
        for side in m.due():
            side.prepare();side.apply(.1,dict(play=False,slot=-1,cell=-1,why='test'))
    assert len(m.env.public_plays)==1
    e=m.env.public_plays[0]
    assert e['tick']==116 and e['side']==1
    assert (e['x'],e['y'])==s.ep.cell_to_engine(1600,True,'lattice')
    assert not D.opponent_past(m.env.public_plays,116,0,m.learner.model.gid)[:,0].any()
    assert D.opponent_past(m.env.public_plays,117,0,m.learner.model.gid)[0,4]==np.float32(.05)
    # Rejected commands and ability presses do not create card-play events.
    assert not m.env.act(1,idx,-100000,-100000)['accepted']
    assert len(m.env.public_plays)==1
    m.env.reset(NAMES,NAMES,1)
    assert m.env.public_plays==[]


@pytest.mark.parametrize('noise',[V.Noise(),V.ALL_NOISE_OFF,V.Noise(recall=False)])
def test_noise_preserves_true_form_zeros_substitutions_and_rng(noise):
    from pipeline.tests.test_obs_contract import raw_obs,ENGINE_DECK
    from pipeline.tests.gen_v3.test_legacy import baseline
    from pipeline import engine_play as EP
    deck=O.load_deck('icebow')
    bs=O.from_engine(EP.compact_raw(raw_obs(0)),0,deck,engine_deck=ENGINE_DECK,unmapped=set())
    from dataclasses import replace
    bs=replace(bs,units=tuple(replace(u,form=1+i%2) for i,u in enumerate(bs.units)))
    # Instrument rolled construction, so even a same-class false positive must have form 0.
    seen=[]
    real=V.Unit
    def capture(*a,**kw):
        u=real(*a,**kw);seen.append(u);return u
    for seed in range(20):
        a=np.random.default_rng(seed);b=np.random.default_rng(seed)
        with patch.object(V,'Unit',capture):view=V.live_view(bs,a,deck,noise)
        old=baseline('sim_e1_view').live_view(bs,b,deck,noise)
        assert a.bit_generator.state==b.bit_generator.state
        assert O.to_tokens(view)[0].tobytes()==O.to_tokens(old)[0].tobytes()
    assert {u.form for u in seen}=={0,1,2}


@pytest.mark.parametrize('lv,ov',[(3,1),(1,3),(3,3),(2,3),(3,0),(0,3)])
def test_mixed_versions_prepare_extrapolation_and_fork(lv,ov):
    from pipeline.search_s0 import forward,fork_into
    m=match(policy(lv),policy(ov),obs='live',noise=V.ALL_NOISE_OFF,extrapolate_ticks=26)
    m.env.public_plays.append(dict(tick=89,side=1,card='Knight',form=1,x=3000,y=25000))
    for tick in (90,100):
        raw=m.env.advance_to(tick)
        # Hand-built public bodies test flag transfer without requiring a cycle first.
        raw['entities']=[dict(side=0,x=3000+tick,y=8000,name='Knight',hp=100,max_hp=100,
                              entity_id=123,card_id=m.env.ids['Knight'],status_flags=8),
                         dict(side=1,x=3000,y=25000,name='MiniPekka',hp=100,max_hp=100,
                              entity_id=124,card_id=m.env.ids['MiniPekka'],status_flags=16)]
        for s in m.sides:
            s.state=raw;s.prepare();forward(s)
            row=s._gen_row
            if s.feature_version>=3:
                assert {1,2} <= set(row['unit_form'])
                np.testing.assert_array_equal(row['unit_form'],O.to_unit_forms(s._cur[2]))
                np.testing.assert_array_equal(row['opp_past'],D.opponent_past(m.env.public_plays,
                                              tick+(26 if tick==100 else 0),s.side,s.model.gid))
            elif row is not None:assert not set(E.GEN_V3_KEYS)&row.keys()
    f=fork_into(m,RoyaleSelfPlayEnv(),m.env.core.save_state())
    f.env.public_plays.append(dict(tick=100,side=0,card='Zap',form=0,x=1,y=2))
    assert len(f.env.public_plays)==len(m.env.public_plays)+1


def test_shared_batches_and_proagreement_repacking_match_trainer():
    from pipeline.train_gen import GenRows as TrainRows
    arrs={k:v for k,v in np.load(HERE/'gen_dataset_v3.npz',allow_pickle=False).items() if k!='meta'}
    ids=np.array([0,3,12,100])
    a=GenRows(arrs,ids,'cpu').batch(ids);b=TrainRows(arrs,ids,'cpu').batch(ids)
    assert all(torch.equal(a[k],b[k]) for k in a)
    packed,meta=RL.gen_v3val_arrays(HERE/'gen_dataset_v3.npz',4)
    original=np.where(arrs['v3val']==1)[0][:4]
    a=GenRows(packed,np.arange(4),'cpu').batch(np.arange(4))
    b=GenRows(arrs,original,'cpu').batch(original)
    assert all(torch.equal(a[k],b[k]) for k in a)


def test_eval_loader_v3_and_empty_unit_batch():
    p=policy()
    path=HERE/'eval_loader_v3.pt'
    torch.save(dict(gen=True,args=dict(d=16,layers=1,feature_version=3),d_c=8,
                    card_vocab=list(p.gid),model=p.model.state_dict()),path)
    model,_=load_model(path,'cpu')
    assert model.feature_version==3
    assert all(torch.equal(v,model.state_dict()[k]) for k,v in p.model.state_dict().items())
    packed,_=RL.gen_v3val_arrays(HERE/'gen_dataset_v3.npz',1)
    packed['tok']=packed['tok'][:0];packed['unit_form']=packed['unit_form'][:0];packed['off'][:]=0
    b=GenRows(packed,np.array([0]),'cpu').batch(np.array([0]))
    assert not b['mask'].any() and not b['unit_form'].any() and not b['tok'].any()


def tiny_rollout():
    p=policy();op=policy(1)
    spec=dict(tag='v3-rl',learner_side=0,learner_deck=NAMES,opp_deck=NAMES,seed=0,opp={'id':'old'})
    out=[]
    E.run_selfplay_batch(lambda:RoyaleSelfPlayEnv(forms_mode='deck',tail_cap=600),p,
                        {'old':(op,_cfg(policy='live',record=False))},[(0,spec,0)],
                        _cfg(obs='live',noise=V.ALL_NOISE_OFF),1,out.append)
    bn,st=RL.collate(out,advantage='gae');b=RL.to_device(bn,'cpu')
    with torch.no_grad():
        terms=RL.policy_terms(p.model,b,torch.arange(len(b['A'])),.27,.5,value=True)
    for k in ('lp_gate','lp_card','lp_cell'):
        np.testing.assert_allclose(terms[k].numpy(),b[k].numpy(),atol=1e-5,rtol=0)
    stats=RL.gae_batch(p.model,b,RL.GAE_DEFAULTS|{'advantage':'gae'})
    assert torch.isfinite(b['A']).all() and torch.isfinite(b['ret']).all()
    assert b['opp_past'][:,:,0].any() and (b['unit_form']==2).any()
    return out[0],bn,st,stats


def test_rl_collate_policy_terms_and_gae():
    tiny_rollout()


def test_actor_constructs_v3_and_loads_weights_without_training():
    import queue
    cfg=RL.load_config(RL.REPO/'pipeline/rl_royale.yaml',[],smoke=False)
    learner=RL.Learner.__new__(RL.Learner)
    learner.cfg=cfg|dict(actor_device='cpu',actor_threads=2)
    learner.init_meta={'args':dict(d=16,layers=1,feature_version=3)}
    learner.grid='lattice'
    p=policy()
    learner.gen=dict(d_c=8,card_vocab=list(p.gid),feature_version=3)
    base=learner.actor_base()
    class Out(list):
        def cancel_join_thread(self):pass
        def put(self,m):self.append(m)
    iq=queue.Queue();oq=Out()
    iq.put(('screen',0,RL.state_bytes(p.model),[]));iq.put(None)
    seen=[]
    def inspect(make_env,model,*a,**kw):
        assert model.model.feature_version==3
        assert all(torch.equal(v,model.model.state_dict()[k]) for k,v in p.model.state_dict().items())
        seen.append(True)
    with patch.object(E,'run_batch',inspect):RL.actor_main(0,0,iq,oq,base)
    assert seen and not [m for m in oq if m[0]=='error'],oq
