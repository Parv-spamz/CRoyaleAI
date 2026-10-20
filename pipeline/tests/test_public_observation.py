"""Public observer contract: independent expected events, privacy and adapter parity."""
import copy
import json
from pathlib import Path

import numpy as np
import pytest

from pipeline.public_observation import PublicObserver, public_frame, opponent_cycle, recording_observers, _native_ids
from pipeline.native_recording import tag_native_recording


def body(key='knight', eid=10, form=0, side=1, hp=1000, x=3000, y=25000):
    return dict(side=side, x=x, y=y, hp=hp, max_hp=hp, card_id=_native_ids()[key, form],
                address=str(eid), category=eid, kind=15)


def spell(key='rocket', side=1, x=3500, y=6500):
    return dict(side=side, x=x, y=y, target_x=x, target_y=y, card_id=_native_ids()[key, 0])


def frame(tick=10, bodies=(), projectiles=(), effects=()):
    return dict(game_tick=tick, entities=list(bodies), projectiles=list(projectiles), effects=list(effects))


def test_body_identity_generation_and_forms():
    o = PublicObserver(0)
    f = frame(bodies=[body(form=1), body('knight', 11, form=1)])
    o.update(f, source='reader')
    assert len(o.plays) == 1 and o.plays[0]['form'] == 1
    assert o.features(10, {'knight': 1})['opp_past'][0, 0] == 0
    assert o.features(11, {'knight': 1})['opp_past'][0, 0] == 1
    o.update(dict(f, game_tick=300), source='reader')
    assert len(o.plays) == 1
    other = body(eid=10, form=1)
    other['category'] = 50  # same address, different generation
    o.update(frame(400, [other]), source='reader')
    assert len(o.plays) == 2


def test_spells_swarm_projectile_effect_body_dedup_and_repeat():
    o = PublicObserver(0)
    for t in (10, 20, 30):
        o.update(frame(t, projectiles=[spell('goblin_barrel')]*3 + [spell('musketeer')]), source='reader')
    o.update(frame(70, [body('goblin_barrel', i) for i in range(3)], effects=[spell('goblin_barrel')]), source='reader')
    assert [e['card'] for e in o.plays] == ['goblin_barrel']
    o.update(frame(300, projectiles=[spell('goblin_barrel')]), source='reader')
    assert len(o.plays) == 2
    assert o.plays[0]['x'] == 3500


def test_persistent_effect_does_not_repeat_and_enemy_side_only():
    o = PublicObserver(0)
    for t in range(10, 800, 20):
        o.update(frame(t, effects=[spell('poison'), spell('rocket', side=0)]), source='reader')
    assert [e['card'] for e in o.plays] == ['poison']
    o.update(frame(950, effects=[spell('poison')]), source='reader')
    assert len(o.plays) == 2


def test_hidden_fields_commands_and_future_do_not_change_features():
    a, b = PublicObserver(0), PublicObserver(0)
    f = frame(10, [body(form=2)], [spell()])
    hidden = dict(players=[dict(side=1, hand=['secret'], elixir=999, deck_form_flags=[2]*8)],
                  final_decks={'1': ['secret']*8}, log=[dict(card='secret', accepted=True)])
    a.update(f, source='reader')
    b.update(dict(f, **hidden), source='reader')
    gid = {'knight': 1, 'rocket': 2, 'zap': 3}
    expected = a.features(11, gid)
    a.update(frame(500, effects=[spell('zap')]), source='reader')
    for k in expected:
        np.testing.assert_array_equal(expected[k], b.features(11, gid)[k])
        np.testing.assert_array_equal(expected[k], a.features(11, gid)[k])
    assert a.estimate_at(11) == b.estimate_at(11)
    # Positive control: changing an actually public card must change features.
    c = PublicObserver(0)
    c.update(frame(10, projectiles=[spell('zap')]), source='reader')
    assert not np.array_equal(c.features(11, gid)['opp_past'], expected['opp_past'])


def test_cycle_has_all_eight_observed_cards_and_no_readiness_claim():
    keys = ['knight', 'rocket', 'zap', 'goblins', 'musketeer', 'the-log', 'poison', 'arrows']
    plays = [dict(tick=10+i*10, side=1, card=k, form=i%3) for i, k in enumerate(keys)]
    gid = {k: i+1 for i, k in enumerate(keys)}
    c = opponent_cycle(plays, 90, 0, gid)
    np.testing.assert_array_equal(c[:, 0], np.arange(8, 0, -1))
    np.testing.assert_array_equal(c[:, 2], np.arange(8))
    assert c[0, 3] == .5
    plays.append(dict(tick=80, side=1, card='knight', form=0))
    c = opponent_cycle(plays, 90, 0, gid)
    assert c[0, 0] == 1 and c[0, 2] == 0 and c[1, 2] == 0
    assert opponent_cycle(plays, 10, 0, gid)[:, 0].sum() == 0


def test_reset_duplicate_frame_and_troop_attack_projectile():
    o = PublicObserver(0)
    f = frame(500, [body()], [spell('musketeer')])
    o.update(f, source='reader'); o.update(f, source='reader')
    assert len(o.plays) == 1
    o.update(frame(1), source='reader')
    assert o.plays == [] and o.estimate_at(1) > 6


def test_native_reader_sim_representations_match():
    reader = frame(10, [body(form=1)], projectiles=[spell()])
    b = reader['entities'][0]
    rec = dict(record_native=True, record_full=True, frames=[dict(tick=10,
        entities=[[1, b['x'], b['y'], 'Knight', b['hp'], b['max_hp'], 15, b['card_id'], 10]],
        projectiles=[[1, 3500, 6500, 4500, 7500, 'Rocket']], effects=[])])
    tagged = tag_native_recording(rec, {})
    sim = dict(tick=10, entities=[dict(side=1,x=b['x'],y=b['y'],hp=b['hp'],max_hp=b['max_hp'],
                                      entity_id=10,name='Knight',card_id=999,status_flags=8)],
               projectiles=[dict(side=1,x=3500,y=6500,name='Rocket')])
    obs = [PublicObserver(0) for _ in range(3)]
    for o, f, source in zip(obs, (reader, tagged['frames'][0], sim), ('reader','native','sim')):
        o.update(f, source=source)
    assert obs[0].plays == obs[1].plays == obs[2].plays
    assert obs[0].estimate_at(11) == obs[1].estimate_at(11) == obs[2].estimate_at(11)


def test_real_sample_adapter_parity_and_command_frames_excluded():
    path = Path('.foreman/codex_autopilot/runs/native_public_sample.json')
    rec = tag_native_recording(json.loads(path.read_text(encoding='utf-8-sig')), {})
    native = recording_observers(rec)
    reader = [PublicObserver(0), PublicObserver(1)]
    for f in rec['frames']:
        rf = dict(game_tick=f['tick'], entities=[], projectiles=[], effects=[])
        for i, e in enumerate(f['entities']):
            rf['entities'].append(dict(side=e[0],x=e[1],y=e[2],hp=e[4],max_hp=e[5],kind=e[6],
                card_id=f['native_card_ids'][i],address=str(f['entity_ids'][i]),category=f['entity_ids'][i]))
        for name in ('projectiles','effects'):
            for e in f.get(name, []):
                key = __import__('pipeline.vocab', fromlist=['engine_key']).engine_key(e[5 if name=='projectiles' else 3])
                rf[name].append(dict(side=e[0],x=e[1],y=e[2],card_id=_native_ids().get((key,0),-1)))
        for o in reader:
            o.update(rf, source='reader')
    assert [o.plays for o in native] == [o.plays for o in reader]
    assert sum(len(o.plays) for o in native) > 10
    rec['play_frames'] = [dict(tick=9999, entities=[['this must never be read']])]
    assert [o.plays for o in recording_observers(rec)] == [o.plays for o in native]


@pytest.mark.parametrize('missing', ['record_full','record_native'])
def test_unmarked_recordings_rejected(missing):
    rec = dict(record_native=True, record_full=True, frames=[])
    del rec[missing]
    with pytest.raises(ValueError):
        recording_observers(rec)
