import copy
from types import SimpleNamespace as NS

import numpy as np
import pytest
import torch

from pipeline.projectile_observation import tokens, sim_objects, require_complete_training, PROJECTILE_COLS, EFFECT_COLS
from pipeline.public_observation import _native_ids
from pipeline.rocket_context import row_weights, require_weight_artifact, weighted_ce


@pytest.mark.parametrize('side', [0, 1])
def test_three_sources_card_coordinates_timing_and_privacy(side):
    native = dict(projectiles=[[1, 3000, 21000, 4500, 6500, 'GoblinBarrel']],
                  area_effects=[[0, 4000, 7000, 'Poison']])
    reader = dict(projectiles=[dict(side=1, x=3000, y=21000, target_x=4500, target_y=6500,
                                    card_id=_native_ids()['goblin_barrel', 0])],
                  effects=[dict(side=0, x=4000, y=7000, card_id=_native_ids()['poison', 0])])
    sim = dict(projectiles=[dict(side=1, x=3000, y=21000, target_x=4500, target_y=6500, name='GoblinBarrel')],
               effects=[dict(side=0, x=4000, y=7000, name='Poison')])
    gid = {'goblin-barrel': 1, 'poison': 2}
    expected = tokens(native, side, gid, source='native')
    for source, frame in [('reader', reader), ('sim', sim)]:
        got = tokens(frame, side, gid, source=source)
        for key in expected:
            np.testing.assert_array_equal(expected[key], got[key])
        hidden = dict(frame, players=[dict(elixir=999, hand=['secret'])], target_uid=777)
        for key, val in tokens(hidden, side, gid, source=source).items():
            np.testing.assert_array_equal(expected[key], val)
    assert expected['projectiles'][0, 0] == 1
    assert expected['projectiles'][0, -2:].tolist() == [-1, 0]
    reader['projectiles'][0]['time_to_impact_ms'] = 500
    reader['effects'][0]['remaining_ms'] = 1000
    got = tokens(reader, side, gid, source='reader')
    assert got['projectiles'][0, -2:].tolist() == [.5, 1]
    assert got['effects'][0, -2:].tolist() == [1, 1]


def test_empty_objects_and_strict_missing_timing_preflight():
    for kind, a in tokens({}, 0, {}, source='reader').items():
        assert a.ndim == 2 and not a.any()
    meta = dict(feature_version=4, projectile_cols=list(PROJECTILE_COLS), effect_cols=list(EFFECT_COLS),
                stats=dict(projectiles_observed=4, effects_observed=5))
    require_complete_training(meta)
    for key in ('projectiles_missing_timing', 'effects_missing_timing', 'projectiles_unknown_card', 'effects_overflow', 'native_area_effects_unavailable'):
        other = copy.deepcopy(meta); other['stats'][key] = 1
        with pytest.raises(ValueError, match='incomplete'):
            require_complete_training(other)


def test_native_generic_effects_are_not_area_effect_tokens_or_spell_history():
    from pipeline.public_observation import PublicObserver
    frame = dict(tick=10, entities=[], effects=[[1, 4000, 8000, 'Poison']], projectiles=[])
    got=tokens(frame,0,{'poison':1},source='native')
    assert not got['effects'].any()
    observer=PublicObserver(0);observer.update(frame,source='native')
    assert observer.plays==[]
    frame['area_effects']=frame['effects'];frame['tick']=20
    observer.update(frame,source='native')
    assert observer.plays[0]['card']=='poison'
    assert tokens(frame,0,{'poison':1},source='native')['effects'][0,0]==1


def test_sim_delay_is_not_flight_time_to_impact():
    state = NS(projectiles=[], spells=[NS(team=1, card_id=3, motion=0, x=30, y=40,
                                          aim_x=50, aim_y=60, delay_ticks=7),
                                      NS(team=0, card_id=4, motion=4, x=30, y=40, delay_ticks=8)])
    got = sim_objects(state, {3:'Rocket', 4:'Poison'}, 1)
    assert got['projectiles'][0]['time_to_impact_ms'] == pytest.approx(2**.5*20/350*50)
    assert got['effects'][0]['remaining_ms'] == 400


def test_context_weights_are_continuous_and_no_finish_rule():
    p = torch.tensor([0., .25, 1.], requires_grad=True)
    assert torch.equal(row_weights(p, 1), torch.ones(3))
    assert torch.equal(row_weights(p, 5), torch.tensor([1., 2., 5.]))
    assert not row_weights(p, 5).requires_grad
    for bad in ([float('nan')], [-.1], [1.1]):
        with pytest.raises(ValueError): row_weights(torch.tensor(bad), 2)
    logits = torch.tensor([[0., 1.], [1., 0.]])
    target = torch.tensor([1, -1])
    assert torch.equal(weighted_ce(logits, target, torch.ones(2)), torch.nn.functional.cross_entropy(logits[:1], target[:1]))
    with pytest.raises(ValueError, match='Missing'):
        require_weight_artifact(dict(y_gate=np.zeros(2)), {}, 2)


def test_joint_weighting_refuses_rocket_only_artifact_and_overlapping_splits():
    arrays = dict(y_gate=np.zeros(2), rocket_context_probability=np.array([.2, .8]))
    evidence = dict(fit_tags=['fit'], tune_tags=['tune'], test_tags=['test'], public_only=True,
                    classifier_sha256='fixture', heldout_report_sha256='fixture', selected_weight=2)
    meta = dict(rocket_context=evidence)
    with pytest.raises(ValueError, match='Joint Rocket/X-Bow'):
        require_weight_artifact(arrays, meta, 2)
    evidence['context_targets'] = ['tower_rocket', 'xbow_lane', 'defensive_xbow_rocket_cycle']
    with pytest.raises(ValueError, match='BOTH Tornado-order'):
        require_weight_artifact(arrays, meta, 2)
    evidence['context_targets'] += ['defensive_rocket', 'rocket_then_tornado', 'tornado_then_rocket']
    require_weight_artifact(arrays, meta, 2)
    evidence['test_tags'] = ['fit']
    with pytest.raises(ValueError, match='disjoint'):
        require_weight_artifact(arrays, meta, 2)
