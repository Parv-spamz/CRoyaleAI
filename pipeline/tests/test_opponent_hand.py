"""Independent queue oracles and public/private boundary controls."""
import copy
import itertools
import random

import numpy as np
import pytest

from pipeline.opponent_hand import HandBelief, PublicHandObserver, from_public_plays
from pipeline.public_observation import PublicObserver
from pipeline.tests.test_public_observation import body, frame, spell


def test_all_starting_hand_sets_and_queues():
    cards = tuple("abcdefgh")
    checked = 0
    for start_hand in itertools.combinations(cards, 4):
        for start_queue in itertools.permutations(set(cards) - set(start_hand)):
            hand, queue = set(start_hand), list(start_queue)
            reader = HandBelief(complete_events=True)
            rng = random.Random(checked)
            for t in range(48):
                played = rng.choice(sorted(hand))
                hand.remove(played)
                hand.add(queue.pop(0))
                queue.append(played)
                reader.observe([played], tick=t)
                s = reader.snapshot()
                assert set(s['in_hand']) <= hand
                assert set(s['out_of_hand']).isdisjoint(hand)
                assert s['certified'] and not s['issues']
                assert set(s['revealed']) == set(reader.last)
                if s['full_hand']:
                    assert set(s['in_hand']) == hand
                for card, bounds in s['plays_to_return'].items():
                    true = 0 if card in hand else queue.index(card) + 1
                    assert bounds[0] <= true <= bounds[1]
            checked += 1
    assert checked == 1680


def test_unordered_batches_against_enumerated_possible_worlds():
    cards = tuple("abcdefgh")
    worlds = [(set(h), list(q)) for h in itertools.combinations(cards, 4)
              for q in itertools.permutations(set(cards) - set(h))]
    reader = HandBelief(complete_events=True)
    for tick, batch in enumerate([['a', 'b'], ['c'], ['d', 'e'], ['f'], ['a', 'g'], ['h']]):
        next_worlds = []
        for h, q in worlds:
            for order in itertools.permutations(batch):
                hand, queue = set(h), list(q)
                for card in order:
                    if card not in hand:
                        break
                    hand.remove(card); hand.add(queue.pop(0)); queue.append(card)
                else:
                    next_worlds.append((hand, queue))
        worlds = next_worlds
        assert worlds
        reader.observe(batch, tick=tick)
        s = reader.snapshot()
        for hand, queue in worlds:
            assert set(s['in_hand']) <= hand
            assert not set(s['out_of_hand']) & hand
            for card, bounds in s['plays_to_return'].items():
                true = 0 if card in hand else queue.index(card) + 1
                assert bounds[0] <= true <= bounds[1]


def test_partial_reveal_and_four_subsequent_plays():
    r = HandBelief()
    for i, card in enumerate('abcde'):
        r.observe([card], tick=i)
    s = r.snapshot()
    assert s['in_hand'] == ['a'] and s['out_of_hand'] == list('bcde')
    assert s['unrevealed_slots'] == 3 and not s['full_hand'] and not s['certified']
    r.observe(['f', 'g'], tick=10)
    assert r.snapshot()['in_hand'] == list('abc')
    assert r.snapshot()['out_of_hand'] == list('defg')
    for t, c in enumerate('abc', 11):
        r.observe([c], tick=t)
    assert r.snapshot()['uncertain'] == ['f', 'g']  # tie now straddles queue end


def test_gap_contradiction_unknown_identity_and_reset():
    r = HandBelief(complete_events=True)
    for i, c in enumerate('abcdefgh'):
        r.observe([c], tick=i)
    assert r.snapshot()['full_hand']
    r.gap()
    assert not r.snapshot()['in_hand'] and not r.snapshot()['out_of_hand']
    assert len(r.snapshot()['uncertain']) == 8
    r.observe(['a'], tick=10)
    r.observe(['a'], tick=11)
    assert r.snapshot()['issues']['impossible_early_replay'] == 1
    assert not r.snapshot()['certified']
    r.observe([None], tick=12)
    assert not r.snapshot()['in_hand'] and not r.snapshot()['out_of_hand']
    r.reset()
    assert not r.snapshot()['revealed'] and not r.snapshot()['issues']
    r.observe(['i'], tick=0)
    with pytest.raises(ValueError):
        r.observe(['a'], tick=-1)


def test_duplicate_event_ids_and_impossible_deck():
    r = HandBelief()
    r.observe(['a'], tick=1, event_ids=['x'])
    before = r.snapshot()
    r.observe(['a'], tick=1, event_ids=['x'])
    assert r.snapshot() == before
    with pytest.raises(ValueError):
        r.observe(['b'], tick=1, event_ids=['x'])
    for i, c in enumerate('bcdefghi'):
        r.observe([c], tick=i+2)
    assert not r.snapshot()['full_hand'] and not r.snapshot()['in_hand']
    assert r.snapshot()['issues']['unsupported_rules_or_deck']


def test_forms_abilities_mirror_and_strict_past():
    plays = [dict(tick=1, side=1, card='Knight@evolution'),
             dict(tick=2, side=1, card='Mirror'),
             dict(tick=3, side=1, card='Knight', ability=True),
             dict(tick=4, side=1, card='Zap', accepted=False),
             dict(tick=5, side=0, card='Rocket'),
             dict(tick=6, side=1, card='Log')]
    s = from_public_plays(plays, 6, 0)
    assert s['revealed'] == ['knight', 'mirror']
    assert s['plays_to_return']['knight'] == [3, 3]
    plays.append(dict(tick=7, side=1, card='Arrows', identity_unknown=True))
    assert not from_public_plays(plays, 8, 0)['out_of_hand']
    assert from_public_plays(plays, 6, 0) == s
    assert not from_public_plays(plays, 7, 0, rules='historical_champion_3_cycle')['out_of_hand']


def test_split_timestamp_is_not_fake_order():
    r = HandBelief()
    r.observe(['a'], tick=1)
    r.observe(['b'], tick=1)
    assert r.snapshot()['issues']['split_same_tick_batch'] == 1
    assert r.snapshot()['uncertain'] == ['a']


def test_adapter_private_invariance_future_causality_and_v4_compatibility():
    a, b, old = PublicHandObserver(0), PublicHandObserver(0), PublicObserver(0)
    frames = [frame(10, [body()], [spell('rocket')]), frame(300, effects=[spell('zap')])]
    for f in frames:
        private = copy.deepcopy(f)
        private.update(players=[dict(side=1, hand=['secret']*4, next='secret', elixir_raw=999999)],
                       final_decks={'1':['secret']*8}, log=[{'card':'secret'}],
                       play_frames=[{'card':'secret'}])
        a.update(f, source='reader'); b.update(private, source='reader'); old.update(f, source='reader')
    expected = a.hand_at(301)
    assert expected == b.hand_at(301) and not expected['certified']
    gid = {'knight':1, 'rocket':2, 'zap':3}
    for k, v in old.features(301, gid).items():
        np.testing.assert_array_equal(v, a.features(301, gid)[k])
    a.update(frame(900, effects=[spell('poison')]), source='reader')
    assert a.hand_at(301) == expected
    assert a.hand_at(901) != expected  # positive public-input sensitivity control
    a.reset()
    assert not a.hand_at(1000)['revealed']
