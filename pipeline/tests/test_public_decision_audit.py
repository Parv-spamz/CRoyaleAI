"""Audit opt-in cannot alter policy decisions or expose opponent secrets."""
import copy
import json

import numpy as np
import pytest
import torch

from pipeline.decision_options import DecisionOptions
from pipeline.live_gen_v2 import GenPilot
from pipeline.tests.test_live_gen_afford import pilot as legacy_fixture, frame
from pipeline.tests.test_public_observation import spell


def pilot(audit, options, elixir=10):
    p=legacy_fixture([1,9,8,7],ext_h=26)
    p.__class__=GenPilot
    p.feature_version=5;p.use_counter=True;p.public=None;p.public_battle=None
    p.public_audit=audit;p._public_audit_snapshot=None
    p.decision_options=options;p.rng_decisions=np.random.default_rng(10)
    p.gid['rocket']=len(p.gid)+1
    f=frame(elixir);f['projectiles']=[spell(side=0)];f['effects']=[]
    p.observe(f)
    return p,f


@pytest.mark.parametrize('options',[DecisionOptions(),DecisionOptions(card_choice='filtered',card_ratio=.7,card_T=1)])
@pytest.mark.parametrize('elixir',[1,10])
def test_audit_preserves_wait_and_play_and_random_stream(options,elixir):
    before,f=pilot(False,options,elixir)
    after,g=pilot(True,options,elixir)
    a,b=before.decide(f),after.decide(g)
    audit=b.pop('public_audit')
    assert a==b
    assert before.rng_decisions.bit_generator.state==after.rng_decisions.bit_generator.state
    assert audit['raw_tick']==f['game_tick'] and audit['model_tick']==f['game_tick']+26
    assert len(audit['raw_projectiles'])==len(audit['normalized_current_projectiles'])==len(audit['model_projectiles'])==1
    # Actual model target remains the target encoded from the reader after lookahead.
    np.testing.assert_allclose(audit['model_projectiles'][0][4:6],audit['normalized_current_projectiles'][0][4:6])
    json.dumps(audit,allow_nan=False)


def test_opponent_private_values_never_enter_audit():
    p,f=pilot(True,DecisionOptions())
    a=p.decide(f)['public_audit']
    f['players'][0].update(elixir_raw=87654321,deck_card_ids=[987654321]*8,
        next_deck_index=999,deck_form_flags=[2]*8,private_secret='DO_NOT_LOG')
    b=p.decide(f)['public_audit']
    assert a==b
    assert 'DO_NOT_LOG' not in json.dumps(b)
    assert b['own_hand'] and b['model_bodies'] and len(b['model_towers'])==6
