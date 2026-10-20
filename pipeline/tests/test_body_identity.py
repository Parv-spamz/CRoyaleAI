"""Versioned public spawner identity through dataset, SIM and live contracts."""
import copy
import json
from pathlib import Path

import numpy as np
import pytest
import torch

from pipeline import obs_contract as O, vocab
from pipeline.body_identity import resolve
from pipeline.live_mem import deck_of, to_observe
from pipeline.native_recording import tag_native_recording
from pipeline.public_observation import body_only_board
from pipeline.tests.test_live_mem import FRAME, T
from pipeline.tests.test_live_gen_afford import pilot


@pytest.mark.parametrize('parent,maximum,child', [
    ('Witch', 81, 'skeletons'), ('DarkWitch', 81, 'bats'),
    ('FirespiritHut', 217, 'fire_spirit'), ('FirespiritHut', 215, 'fire_spirit'), ('GoblinHut', 133, 'spear_goblins'),
    ('BarbarianHut', 716, 'barbarians'), ('Tombstone', 81, 'skeletons')])
@pytest.mark.parametrize('side', [0, 1])
def test_native_sim_and_reader_body_agree(parent, maximum, child, side):
    from pipeline.obs_contract import _catalog_names
    cid = next(k for k,v in _catalog_names().items() if v == parent and k >= 20000000)
    native = dict(record_native=True, frames=[dict(tick=100, elixir=[5,5], towers=[],
        entities=[[1-side, 3000, 24000, parent, maximum, maximum, 15, cid, 5000010]])])
    compact = tag_native_recording(native, {})['frames'][0]
    raw = dict(tick=100, players=[], episode=dict(crown_towers=[]), entities=[dict(side=1-side,
        x=3000, y=24000, name=parent, hp=maximum, max_hp=maximum, kind=15,
        card_id=cid, entity_id=5000010, status_flags=0)])
    reader = copy.deepcopy(FRAME)
    reader['game_tick'] = 100
    reader['players'][1]['side'] = side
    reader['players'][0]['side'] = 1-side
    reader['entities'] = [T(5000010,15,1-side,3000,24000,maximum,maximum,cid,'0xchild')]
    deck, names = deck_of(reader, side)
    reader_raw = to_observe(reader, side, names)
    results = [body_only_board(O.from_engine(f, side, deck, feature_version=5)).units
               for f in (compact, raw, reader_raw)]
    assert results[0] == results[1] == results[2]
    assert results[0][0].cls == vocab.unit_id(child) and results[0][0].form == 0
    for version in (1,2,3,4):
        legacy = O.from_engine(compact, side, deck, feature_version=version)
        assert legacy.units[0].cls == vocab.engine_unit_id(parent, maximum)


@pytest.mark.parametrize('version,expected', [(4,'night_witch'), (5,'bats'), (6,'bats')])
def test_actual_live_row_honours_checkpoint_contract(version, expected):
    from pipeline.obs_contract import _catalog_names
    cid = next(k for k,v in _catalog_names().items() if v == 'DarkWitch' and k >= 20000000)
    p = pilot([1,2,3,4])
    p.feature_version = version
    p.use_counter = True
    p.public = p.public_battle = None
    frame = copy.deepcopy(FRAME)
    frame['entities'] = [T(5000020,15,0,3000,24000,81,81,cid,'0xbat')]
    frame['projectiles'] = []
    frame['effects'] = []
    p.observe(frame)
    batch, info = p.row(frame)
    assert batch['tok'][0,0,0] == vocab.unit_id(expected)
    assert batch['unit_form'][0,0] == 0
    before = {k:v.clone() for k,v in batch.items()}
    frame['players'][0].update(elixir_raw=999999, deck_card_ids=[999]*8, next_deck_index=999)
    after, _ = p.row(frame)
    assert all(torch.equal(before[k], after[k]) for k in before)


def test_unknown_parent_maximum_and_child_forms():
    for maximum in (None, 1, 81.5, 99999):
        assert resolve('DarkWitch', maximum).cls == vocab.unit_id('night_witch')
    assert resolve('Witch', 81, 1).form == 0
    assert resolve('Witch', 839, 1).form == 1
    assert resolve('Tombstone', 81, 2).form == 0
    assert resolve('Tombstone', 529, 2).form == 2
