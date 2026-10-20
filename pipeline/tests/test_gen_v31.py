"""Version 4 integration checks; CPU only, never touches the active live bot."""
import copy
import json
from pathlib import Path
import uuid
from unittest.mock import patch

import numpy as np
import pytest
import torch

from pipeline import dataset_gen as D, e1_eval as E, e1_view as V, rl_royale as RL
from pipeline.eval_gen import GenRows as EvalRows
from pipeline.train_gen import GenRows, losses
from pipeline.model_gen import GenModel, load_model
from pipeline.public_observation import PublicObserver, recording_observers
from pipeline.native_recording import tag_native_recording
from pipeline.tests.test_model_gen import toy
from pipeline.tests.test_live_gen_afford import pilot
from pipeline.tests.test_live_mem import FRAME
from pipeline.tests.test_public_observation import body, spell

SAMPLE = Path('.foreman/codex_autopilot/runs/native_full_sample.json')


def workdir():
    p = Path('.foreman/codex_autopilot/runs/v31_tests')/uuid.uuid4().hex
    p.mkdir(parents=True)
    return p


def test_real_dataset_privacy_and_exact_forms():
    rec = json.loads(SAMPLE.read_text(encoding='utf-8'))
    original = D.replay_rows(str(SAMPLE), feature_version=4)
    assert 'error' not in original, original.get('error')
    assert len(original['sc']) > 100 and {1, 2} <= set(original['unit_form'])
    observers = recording_observers(tag_native_recording(rec, {}))
    for t, s, sc in zip(original['tick'], original['side'], original['sc']):
        assert sc[5] == np.float32(observers[int(s)].estimate_at(int(t))/10)
        assert sc[6] == 1
    # All opponent private fields for side zero can change without changing its inputs.
    other = copy.deepcopy(rec)
    for source in ('frames','play_frames'):
        for f in other.get(source, []):
            f['elixir'][1] = 9999
            for player in f.get('players', []):
                if player['side'] == 1:
                    player.update(hand=['secret']*4, next=777, elixir=9999, cycle_pos=[777]*4)
    other['final_decks']['1']=[n.split('@')[0] for n in other['final_decks']['1']]
    changed=workdir()/'mutated.json'
    changed.write_text(json.dumps(other),encoding='utf-8')
    mutated = D.replay_rows(str(changed), feature_version=4)
    assert 'error' not in mutated, mutated.get('error')
    idx = original['side'] == 0
    for key in ('sc','past_card','past_form','past_xydt','hand_card','hand_form','next_card','next_form','deck_card','deck_form'):
        np.testing.assert_array_equal(original[key][idx], mutated[key][idx], err_msg=key)
    assert original['actual_plays'] == mutated['actual_plays']
    np.testing.assert_array_equal(original['tok'],mutated['tok'])
    np.testing.assert_array_equal(original['unit_form'],mutated['unit_form'])
    # Positive control: the legacy generic rows really do expose the changed truth.
    legacy = D.replay_rows(str(SAMPLE), feature_version=3)
    bad = D.replay_rows(str(changed), feature_version=3)
    assert not np.array_equal(legacy['sc'][idx, 5], bad['sc'][idx, 5])


def test_build_batch_checkpoint_roundtrip_and_backward():
    wd = workdir(); corpus = wd/'corpus'; corpus.mkdir()
    (corpus/'replay_sample.json').write_bytes(SAMPLE.read_bytes())
    out = wd/'data.npz'
    report = D.build([corpus], out, feature_version=4, workers=1, log=None)
    assert report['failed'] == 0 and report['rows'] > 100
    with np.load(out, allow_pickle=False) as z:
        a = {k: z[k] for k in z if k not in ('tags','meta')}
        meta = json.loads(str(z['meta']))
    assert meta['feature_version'] == 4 and meta['opp_cycle_cols'][2] == 'subsequent_detected_plays'
    ids = np.arange(4)
    b = GenRows(a, ids, 'cpu').batch(ids)
    eb = EvalRows(a, ids, 'cpu').batch(ids)
    assert all(torch.equal(b[k], eb[k]) for k in b)
    model = GenModel(d=16, layers=1, d_c=8, n_cards=len(meta['card_vocab']), feature_version=4).eval()
    loss, _ = losses(model, b, mirror=True, grid='lattice')
    assert torch.isfinite(loss)
    loss.backward()
    assert model.global_in[0].weight.grad.abs().sum() > 0
    path = wd/'model.pt'
    torch.save(dict(gen=True,args=dict(d=16,layers=1,feature_version=4),d_c=8,
                    card_vocab=meta['card_vocab'],model=model.state_dict()), path)
    loaded, _ = load_model(path, torch.device('cpu')); loaded.eval()
    assert torch.equal(model(b)['g'], loaded(b)['g'])
    modified = dict(b, opp_cycle=b['opp_cycle'].clone())
    modified['opp_cycle'][:, 0] = torch.tensor([1, 0, 3, 4.])
    assert not torch.equal(model(b)['g'], model(modified)['g'])
    a['v3val'][:] = 1
    np.savez(out, meta=json.dumps(meta), **a)
    packed, _ = RL.gen_v3val_arrays(out, 4)
    np.testing.assert_array_equal(packed['opp_cycle'], a['opp_cycle'][:4])


@pytest.mark.parametrize('horizon', [0, 26])
def test_live_features_privacy_reset_and_extrapolation(horizon):
    p = pilot([1,2,3,4], ext_h=horizon)
    p.feature_version=4; p.use_counter=True; p.public=None; p.public_battle=None
    p.gid['rocket'] = len(p.gid)+1
    f = copy.deepcopy(FRAME)
    f['entities'].append(body(side=0, form=2)); f['projectiles']=[spell(side=0)]
    f['effects']=[]
    p.observe(f)
    b, info = p.row(f)
    expected = p.public.features(f['game_tick']+horizon, p.gid)
    for k, v in expected.items():
        np.testing.assert_array_equal(b[k][0].numpy(), v)
    assert b['sc'][0, 5] == np.float32(p.public.estimate_at(f['game_tick']+horizon)/10)
    assert 2 in b['unit_form'][0]
    f['players'][0].update(elixir_raw=99999,deck_card_ids=[999]*8,next_deck_index=999,deck_form_flags=[2]*8)
    # Opponent hand visibility is only used to select our side; its contents never enter a row.
    other, _ = p.row(f)
    assert all(torch.equal(b[k], other[k]) for k in b)
    p.reset_match()
    assert p.public.plays == []


@pytest.mark.parametrize('other_version', [1, 3, 4])
def test_sim_features_use_sightings_not_commands_and_fork_isolation(other_version):
    from pipeline.tests.gen_v3.test_sim_integration import match, policy
    from pipeline.search_s0 import forward, fork_into
    from pipeline.royale_env import RoyaleSelfPlayEnv
    m = match(policy(4), policy(other_version), obs='live', noise=V.ALL_NOISE_OFF)
    side = m.learner
    raw = m.env.raw()
    raw['entities']=[dict(side=1,x=3000,y=25000,name='Knight',hp=100,max_hp=100,
                         entity_id=12,card_id=m.env.ids['Knight'],status_flags=8)]
    raw['effects']=[dict(side=1,x=3000,y=5000,name='Zap')]
    side.state=raw; side.prepare(); forward(side)
    assert side._gen_row['opp_cycle'][:,0].sum() == 0  # strict same-tick exclusion
    m.env.advance_to(m.env.tick+10); raw['tick']=m.env.tick
    side.state=raw; side.prepare(); forward(side)
    before=copy.deepcopy(side._gen_row)
    assert before['opp_cycle'][:,0].sum() > 0
    m.env.public_plays.append(dict(side=1,tick=1,card='Arrows',form=1,x=1,y=2))
    raw['players'][1].update(elixir_exact=9999,hand=[dict(hand_index=0,name='secret')],next_deck_index=999)
    side.state=raw; side.prepare(); forward(side)
    assert all(np.array_equal(before[k], side._gen_row[k]) for k in before)
    f = fork_into(m, RoyaleSelfPlayEnv(), m.env.core.save_state())
    f.learner.public.reset()
    assert len(side.public.plays) == 2


def test_rl_trajectory_carries_cycle_through_collation():
    from pipeline.tests.gen_v3.test_sim_integration import policy, NAMES
    from pipeline.tests.test_rl_gen import _cfg
    from pipeline.royale_env import RoyaleSelfPlayEnv
    p, op = policy(4), policy(1)
    spec=dict(tag='v31-rl',learner_side=0,learner_deck=NAMES,opp_deck=NAMES,seed=0,opp={'id':'old'})
    out=[]
    E.run_selfplay_batch(lambda: RoyaleSelfPlayEnv(forms_mode='deck',tail_cap=600),p,
        {'old':(op,_cfg(policy='live',record=False))},[(0,spec,0)],
        _cfg(obs='live',noise=V.ALL_NOISE_OFF),1,out.append)
    assert out[0]['traj']['opp_cycle'].shape[1:] == (8,4)
    batch, _=RL.collate(out,advantage='gae')
    assert batch['opp_cycle'].shape[1:] == (8,4)
    assert batch['opp_cycle'][:,:,0].any()
    b=RL.to_device(batch,'cpu')
    with torch.no_grad():
        terms=RL.policy_terms(p.model,b,torch.arange(len(b['A'])),.27,.5,value=True)
    for key in ('lp_gate','lp_card','lp_cell'):
        np.testing.assert_allclose(terms[key].numpy(),b[key].numpy(),atol=1e-5,rtol=0)


def test_version_four_refuses_legacy_recordings():
    wd=workdir(); corpus=wd/'corpus';corpus.mkdir()
    rec=json.loads(SAMPLE.read_text());rec.pop('record_native')
    (corpus/'replay_bad.json').write_text(json.dumps(rec))
    with pytest.raises(ValueError,match='refuses failed recordings'):
        D.build([corpus],wd/'bad.npz',feature_version=4,workers=1,log=None)


def test_full_and_play_compact_board_features_identical():
    from dataclasses import replace
    from pipeline.dataset import _as_compact
    from pipeline import obs_contract as O
    from pipeline.public_observation import body_only_board
    rec=tag_native_recording(json.loads(SAMPLE.read_text()),{})
    checked=0
    for fr in rec['frames']:
        for side in (0,1):
            # Same state, encoded as a full WAIT and reduced PLAY board.
            a=O.from_engine(fr,side,O.load_deck('icebow'),feature_version=4,unmapped=set())
            b=O.from_engine(_as_compact(fr),side,O.load_deck('icebow'),feature_version=4,unmapped=set())
            a,b=body_only_board(a),body_only_board(b)
            for x,y in zip(O.to_tokens(a),O.to_tokens(b)):
                np.testing.assert_array_equal(x,y)
            np.testing.assert_array_equal(O.to_unit_forms(a),O.to_unit_forms(b))
            assert all(u.deploying is None and u.age_sec is None for u in a.units)
            checked+=1
    assert checked==576
