"""GenPilot.decide() follows the sim's live rule: argmax over AFFORDABLE hand slots, wait if none (e1_eval.live_decide),
on the elixir of the (extrapolated) board the model sees. No checkpoint: a fake model returns fixed logits."""
import copy

import numpy as np
import pytest
import torch
from collections import deque

from pipeline.dataset_gen import card_key
from pipeline.live_gen import GenPilot
from pipeline.live_mem import deck_of
from pipeline.opp_elixir_count import regen_between
from pipeline.tests.test_live_mem import FRAME

# FRAME side 1, hand deck idx [2, 1, 6, 7] = Goblins 2, GoblinHut 4, Musketeer 4, MiniPekka 4 (icebow/config/cards.yaml)


class FakeModel:
    def __init__(self, card_logits):
        self.card = torch.tensor([card_logits], dtype=torch.float32)

    def __call__(self, b, card=None, form=None):
        if card is not None:
            return {"cell": torch.zeros(1, 4)}
        return {"gate": torch.tensor([5.0]), "card": self.card}


def pilot(card_logits, ext_h=0):
    p = object.__new__(GenPilot)
    _, names = deck_of(FRAME, 1)
    p.gid = {card_key(n): i + 1 for i, n in enumerate(names)}
    p.grid, p.dev, p.gate_tau = "lattice", torch.device("cpu"), 0.5
    p.past, p.history, p.opp, p.opp_est = [], {}, None, None
    p.ext_h, p.frames = ext_h, deque(maxlen=30)
    p.model = FakeModel(card_logits)
    return p


def frame(elixir):
    f = copy.deepcopy(FRAME)
    f["players"][1]["elixir_raw"] = int(elixir * 1e4)
    return f


def test_unaffordable_top_slot_is_skipped():
    d = pilot([1, 9, 8, 7]).decide(frame(3.5))       # slots 1-3 (cost 4) hold the top logits but 3 < 4
    assert d["play"] and d["hand_pos"] == 0 and d["name"] == "Goblins" and d["no_affordable"] is False


def test_nothing_affordable_waits():
    d = pilot([0, 9, 1, 2]).decide(frame(1.9))
    assert d["play"] is False and d["no_affordable"] is True and d["card"] == 0


def test_all_affordable_is_plain_argmax():
    d = pilot([0, 9, 1, 2]).decide(frame(10.0))
    assert d["play"] and d["hand_pos"] == 1 and d["no_affordable"] is False


def test_uses_extrapolated_elixir():
    t = FRAME["game_tick"]
    g = regen_between(t, t + 26)
    assert g > 0.1
    # now below the cost, affordable at tick+H -> allowed with extrapolation, not without
    e = 4.0 - g / 2
    assert pilot([1, 9, 8, 7], ext_h=26).decide(frame(e))["hand_pos"] == 1
    assert pilot([1, 9, 8, 7], ext_h=0).decide(frame(e))["hand_pos"] == 0
    # affordable now stays affordable after extrapolating
    assert pilot([1, 9, 8, 7], ext_h=26).decide(frame(4.0))["hand_pos"] == 1
    # the reverse direction cannot happen (regen only adds), so also pin: unaffordable at both -> still masked
    assert pilot([1, 9, 8, 7], ext_h=26).decide(frame(3.0))["hand_pos"] == 0
