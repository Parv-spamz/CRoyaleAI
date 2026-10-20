"""R8 inference-only latency projection; no GPU, capture, training or live client."""
import copy
import json
from types import SimpleNamespace as NS

import numpy as np
import pytest
import torch

from pipeline.extrapolate import extrapolate, advance_public_objects
from pipeline.projectile_observation import constant_projectile_speeds, sim_objects, objects, tokens_from_objects
from pipeline.projectile_motion import ProjectileMotion
from pipeline.public_observation import PublicObserver, _native_ids


def snapshot(seconds=2):
    speed = constant_projectile_speeds()['goblin-barrel']
    return dict(projectiles=[('goblin-barrel', 1, 5000., 22000.-seconds*20*speed, 5000., 22000., seconds*1000)],
                effects=[('poison', 1, 5000., 22000., 2000.), ('poison', 0, 5000., 4000., 1000.),
                         ('lightning', 1, 5000., 22000., None)])


@pytest.mark.parametrize('seconds,remaining,landed', [(2., 700., 0), (1., 0., 1), (1.3, 0., 1)])
def test_barrel_catalog_motion_landing_and_effect_expiry(seconds, remaining, landed):
    obs = snapshot(seconds)
    original = copy.deepcopy(obs)
    out = extrapolate(dict(tick=100), None, 26, 0, public_objects=obs)
    p = out['extrapolated_public_objects']['projectiles'][0]
    assert p[-1] == pytest.approx(remaining)
    assert p[3] == pytest.approx(22000 - remaining/50*constant_projectile_speeds()['goblin-barrel'])
    assert out['public_lookahead_counts'] == dict(landed_in_lookahead=landed, expired_in_lookahead=1)
    assert out['extrapolated_public_objects']['effects'] == [('poison', 1, 5000., 22000., 700.),
                                                           ('lightning', 1, 5000., 22000., None)]
    assert obs == original and 'entities' not in out  # never invent barrel spawns


def test_unknown_motion_unique_only_stale_and_missing_remain_unknown():
    prev = dict(projectiles=[('the-log', 1, 1000., 2000., None, None, None)], effects=[])
    obs = dict(projectiles=[('the-log', 1, 1100., 2200., None, None, None)], effects=[])
    out, _ = advance_public_objects(obs, prev, 10, 26)
    assert out['projectiles'][0] == ('the-log', 1, 1360., 2720., None, None, None)
    for previous, gap in [(prev, 21), (prev, 0), (None, 10), (dict(prev, projectiles=prev['projectiles']*2), 10)]:
        assert advance_public_objects(obs, previous, gap, 26)[0] == obs
    ambiguous = dict(obs, projectiles=obs['projectiles']*2)
    assert advance_public_objects(ambiguous, prev, 10, 26)[0] == ambiguous
    # Multi-stage motion-derived TTI has no catalog speed override.
    obs['projectiles'] = [('the-log', 1, 1000., 2000., 3000., 2000., 2000.)]
    assert advance_public_objects(obs, None, 0, 26)[0]['projectiles'][0] == ('the-log', 1, 2300., 2000., 3000., 2000., 700.)


@pytest.mark.parametrize('side', [0, 1])
def test_sim_native_reader_adapters_produce_identical_advanced_tokens(side):
    ids = _native_ids()
    p = snapshot()['projectiles'][0]
    shot = dict(side=1, x=p[2], y=p[3], target_x=p[4], target_y=p[5], card_id=ids['goblin_barrel', 0])
    area = dict(side=1, x=5000., y=22000., card_id=ids['poison', 0], remaining_ms=2000)
    reader = dict(game_tick=100, projectiles=[shot], effects=[area])
    native = dict(tick=100, public_objects=dict(projectiles=[shot], area_effects=[area]))
    state = NS(projectiles=[], spells=[NS(team=1, card_id=1, motion=0, x=p[2]*1000, y=p[3]*1000,
        aim_x=p[4]*1000, aim_y=p[5]*1000, delay_ticks=0),
        NS(team=1, card_id=2, motion=4, x=5000000, y=22000000, delay_ticks=40)])
    sim = dict(tick=100, **sim_objects(state, {1:'GoblinBarrel', 2:'Poison'}, 1000))
    encoded = []
    for source, frame in [('reader', reader), ('sim', sim), ('native', native)]:
        normalized = ProjectileMotion(catalog_fallback=True).update(objects(frame, source=source), 100)
        advanced = extrapolate(frame, None, 26, side, public_objects=normalized)
        encoded.append(tokens_from_objects(advanced['extrapolated_public_objects'], side, {'goblin-barrel':1, 'poison':2}))
    for other in encoded[1:]:
        for k in other:
            np.testing.assert_array_equal(encoded[0][k], other[k])
    assert encoded[0]['projectiles'][0, -2] == np.float32(.7)
    assert encoded[0]['effects'][0, -2] == np.float32(.7)


def test_h0_and_legacy_raw_bytes_no_mutation():
    from pipeline.tests.test_gen_v31_legacy import head
    obs = dict(tick=100, entities=[], players=[], projectiles=[dict(private='ignored')], effects=[])
    for h in (0, 26):
        before = json.dumps(obs)
        legacy = head('extrapolate').extrapolate(obs, None, h, 0)
        assert json.dumps(extrapolate(obs, None, h, 0)) == json.dumps(legacy)
        if h == 0:
            assert json.dumps(extrapolate(obs, None, h, 0, public_objects=snapshot())) == json.dumps(legacy)
        assert json.dumps(obs) == before


def test_live_row_uses_advanced_snapshot_without_poisoning_history():
    from pipeline.tests.test_live_gen_afford import pilot
    from pipeline.tests.test_live_mem import FRAME
    p = pilot([1,2,3,4], ext_h=26)
    p.feature_version=4; p.use_counter=True; p.public=None; p.public_battle=None
    p.gid.update({'goblin-barrel': len(p.gid)+1, 'poison':len(p.gid)+2})
    frame = copy.deepcopy(FRAME)
    shot = snapshot()['projectiles'][0]
    frame['projectiles']=[dict(card_id=_native_ids()['goblin_barrel',0], side=0,
        x=shot[2], y=shot[3], target_x=shot[4], target_y=shot[5])]
    frame['effects']=[dict(card_id=_native_ids()['poison',0], side=0, x=5000., y=22000., remaining_ms=2000)]
    p.observe(frame)
    history = copy.deepcopy(p.public.object_rows)
    b, info = p.row(frame)
    assert b['projectiles'][0,0,-2] == np.float32(.7)
    assert b['effects'][0,0,-2] == np.float32(.7)
    assert info['public_lookahead_counts']['landed_in_lookahead'] == 0
    again, _ = p.row(frame)
    assert all(torch.equal(b[k], again[k]) for k in b)
    assert p.public.object_rows == history
    assert history[-1]['projectiles'][0][-1] == 2000
    # H=0 exactly returns the current historical public tokens.
    p.ext_h = 0
    zero, _ = p.row(frame)
    for k, value in p.public.features(frame['game_tick'], p.gid).items():
        np.testing.assert_array_equal(zero[k][0].numpy(), value)


def test_sim_prepare_and_live_decide_use_advanced_tokens():
    from pipeline.tests.gen_v3.test_sim_integration import match, policy
    from pipeline import e1_eval as E
    p = policy(4)
    p.gid.update({'goblin-barrel':1, 'poison':2})
    m = match(p, extrapolate_ticks=26)
    m.due()
    s = m.learner
    s.prepare()  # original first-decision H=0 is retained
    assert s._public_object_view is None
    normalized = snapshot()
    s.state['projectiles']=[dict(name='GoblinBarrel',side=1,x=normalized['projectiles'][0][2],
        y=normalized['projectiles'][0][3],target_x=5000.,target_y=22000.)]
    s.state['effects']=[dict(name='Poison',side=1,x=5000.,y=22000.,remaining_ms=2000)]
    s.prepare()
    row=s.gen_row(p)
    assert row['projectiles'][0,-2] == np.float32(.7)
    assert row['effects'][0,-2] == np.float32(.7)
    # Exercise the actual model decision route and compare rows used by it.
    enc, heads, gate, hand = p.forward_batch([row])
    _, allowed, stalled = s.pre(hand[0])
    E.live_decide(p, enc, heads, gate[0], allowed, tau=s.cfg['tau'], stalled=stalled)
    assert s.public.object_rows[-1]['projectiles'][0][-1] == 2000


def test_public_context_excludes_future_and_retains_unknown_clock():
    p=PublicObserver(0)
    p.object_ticks=[100,110,120]
    p.object_rows=[snapshot(3),snapshot(2),snapshot(1)]
    ctx=p.object_context(110)
    assert ctx['public_objects']==snapshot(2) and ctx['previous_objects']==snapshot(3)
    assert ctx['object_gap_ticks']==10
