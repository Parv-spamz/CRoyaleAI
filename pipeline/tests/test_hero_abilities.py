"""CPU acceptance gates for opt-in hero abilities; uses the installed Royale engine.

Run: CUDA_VISIBLE_DEVICES='' Royale/.venv/Scripts/python.exe -m pytest -q -s this_file
Default parity is against the unmodified modules at PRE_ABILITIES (including RNG/trajectories).
"""
import json
import random
import subprocess
import sys
import types
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

pytest.importorskip("royalegym")
from royalegym.protocol import DeployCommand, DeployStatus, EntityKind, HAND_SIZE, STATUS_HERO
from pipeline import e1_eval as E, royale_env as RE
from pipeline.tests.test_royale_forms import ICEBOW, HOGEQ, digest, selfplay_rows

REPO = Path(__file__).resolve().parents[2]
PRE_ABILITIES = "576e5953d6c8c2fe6eb32a2e2dc124c4e490105c"
HERO = [n.replace("Knight@evolution", "Knight@hero") for n in ICEBOW]
CENSUS = json.loads((REPO / "scratchpad/gauntlet/L70/pool_forms/loadable_decks.json").read_text())
BERSERKER = next(d["engine"] for d in CENSUS["decks"] if "Berserker@hero" in d["engine"])


def original(path):
    mod = types.ModuleType("hero_baseline_" + Path(path).stem)
    mod.__file__ = str(REPO / path)
    sys.modules[mod.__name__] = mod
    src = subprocess.check_output(["git", "show", f"{PRE_ABILITIES}:{path}"], cwd=REPO)
    exec(compile(src, mod.__file__, "exec"), mod.__dict__)
    return mod


def cfg(delay=0):
    return {"policy": "live", "tau": .27, "afford_mask": True, "stall_elixir": 9.,
            "stall_seconds": 12., "obs": "clean", "noise": E.parse_noise_off("all"),
            "p_random": 0., "random_hand_only": False, "grid": "lattice", "device": "cpu",
            "decide_every": 10, "slot": 0, "port": 0, "entry_index": 0, "action_delay_ticks": delay}


def match(env, hero_side=1, delay=0, hero_deck=HERO):
    spec = {"tag": "hero_acceptance", "learner_side": 0, "learner_deck": hero_deck if hero_side == 0 else ICEBOW,
            "opp_deck": hero_deck if hero_side == 1 else ICEBOW, "seed": 0, "opp": {"id": "script"}}
    return E.SelfPlayMatch(env, spec, 0, cfg(delay), cfg(delay))


def drive(m):
    """Scripted card policy through SelfPlaySide; left lane, with 3 elixir reserved on BOTH sides."""
    hashes = []
    while True:
        due = m.due()
        if not due:
            break
        for side in due:
            side.prepare()
        for side in due:
            player = m.env.core.state().players[side.side]
            hand = set(player.hand)
            choices = [(0 if m.env.names[cid] == "Knight" else 1, side.costs[slot], slot)
                       for slot, ix in side.deck_index_of_slot.items()
                       if (cid := m.env.deck_ids[side.side][ix]) in hand
                       and side.costs[slot] <= side._cur[1].my_elixir - 3]
            d = {"play": False, "slot": -1, "cell": -1, "why": "wait"}
            if choices:
                slot = min(choices)[2]
                d = {"play": True, "slot": slot, "cell": 44 * 36 + 7, "why": "script"}
            side.apply(.5, d)
        hashes.append(m.env.core.state_hash())
    return m.result(), hashes


def test_default_and_false_equal_unmodified_outcome_trajectory_and_rng():
    old_e, old_re = original("pipeline/e1_eval.py"), original("pipeline/royale_env.py")
    def run(emod, factory):
        random.seed(1903)
        np.random.seed(1903)
        result = selfplay_rows(emod, factory, [ICEBOW, HERO])
        return digest(result), random.getstate(), digest(np.random.get_state())
    ref = run(old_e, lambda: old_re.RoyaleSelfPlayEnv(forms_mode="deck", tail_cap=7200))
    for kwargs in ({}, {"hero_abilities": False}):
        assert run(E, lambda: RE.RoyaleSelfPlayEnv(forms_mode="deck", tail_cap=7200, **kwargs)) == ref


@pytest.mark.parametrize("hero_deck,hero_name", [(HERO, "Knight"), (BERSERKER, "Berserker")])
@pytest.mark.parametrize("side", [0, 1])
@pytest.mark.parametrize("delay", [0, 26])
def test_full_match_pressable_and_charge_used(side, delay, hero_deck, hero_name):
    env = RE.RoyaleSelfPlayEnv(forms_mode="deck", hero_abilities=True)
    m = match(env, side, delay, hero_deck)
    actual, queued = [], []
    act, queue = env.eng.act, env.queue_abilities
    def audited_queue(s, commands, d):
        queued.extend((env.tick + d, s, *c) for c in commands)
        return queue(s, commands, d)
    def audited_act(**kw):
        if "ability_button" not in kw:
            return act(**kw)
        s, b = kw["side"], kw["ability_button"]
        st = env.core.state()
        assert env.core.check_deploy(DeployCommand(s, HAND_SIZE + b, 0, 0)) == DeployStatus.OK
        assert st.players[s].abilities[b][0] == 1
        assert st.players[s].abilities[b][1] == 0
        assert any(t == env.tick and team == s and button == b for t, team, button, _, _ in queued)
        assert (b, st.players[s].abilities[b][3], max(e.uid for e in st.entities
                if e.team == s and e.status_flags >= 0 and e.status_flags & STATUS_HERO)) in env.ability_commands(s)
        before_hand = list(st.players[s].hand)
        r = act(**kw)
        assert r["accepted"]
        after = env.core.state().players[s]
        assert after.abilities[b][1] == 1, after.abilities
        assert after.hand == before_hand
        actual.append((s, b))
        return r
    with patch.object(env.eng, "act", audited_act), patch.object(env, "queue_abilities", audited_queue):
        result, _ = drive(m)
    assert env.terminated, "must finish the full engine match, not just a tail cap"
    assert actual
    assert result["ability_presses"][side][hero_name] == len(actual)
    assert result["ability_presses"][1-side] == {}
    print(f"hero_side={side} delay={delay}: ability_presses={result['ability_presses']}")
    env.reset(ICEBOW, ICEBOW, 0)
    assert env.ability_presses == {0: {}, 1: {}}
    assert env._ability_pending == []
    assert env.ability_commands(side) == []


def test_no_heroes_zero_presses_identical_full_match():
    def run(flag):
        env = RE.RoyaleSelfPlayEnv(forms_mode="deck", hero_abilities=flag)
        result, hashes = drive(match(env, hero_side=-1, delay=26))
        assert sum(sum(c.values()) for c in env.ability_presses.values()) == 0
        result.pop("hero_abilities", None)
        result.pop("ability_presses", None)
        return digest(result), hashes
    assert run(True) == run(False)


def test_engine_refusals_and_unaffordable_never_queued():
    env = RE.RoyaleSelfPlayEnv(forms_mode="deck", hero_abilities=True)
    env.reset(HERO, ICEBOW, 0)
    assert env.ability_commands(0) == []  # no living hero
    for status in (DeployStatus.NO_HERO, DeployStatus.ABILITY_NOT_READY, DeployStatus.ABILITY_SPENT,
                   DeployStatus.NOT_ENOUGH_ELIXIR):
        with patch.object(env.core, "check_deploy", return_value=status), patch.object(env.eng, "act") as act:
            assert env.ability_commands(0) == []
            env.queue_abilities(0, [(0, env.ids["Knight"], 6)], 0)
            act.assert_not_called()


def test_config_old_yaml_default_validation_and_actor(tmp_path):
    from pipeline import rl_royale as RL
    import yaml
    path = REPO / "pipeline/rl_royale.yaml"
    base = RL.load_config(path, [], False)
    assert base["hero_abilities"] is False
    legacy = {k: v for k, v in base.items() if k != "hero_abilities"}
    import hashlib
    assert RL.config_sha(base) == hashlib.sha256(json.dumps(legacy, sort_keys=True, default=str).encode()).hexdigest()
    assert RL.config_sha(dict(base, hero_abilities=True)) != RL.config_sha(base)
    del base["hero_abilities"]
    old = tmp_path / "old.yaml"
    old.write_text(yaml.safe_dump(base))
    assert RL.load_config(old, [], False)["hero_abilities"] is False
    on = RL.load_config(old, ["hero_abilities=true"], False)
    learner = object.__new__(RL.Learner)
    learner.cfg, learner.init_meta, learner.grid = on, {"args": {}}, "lattice"
    assert learner.actor_base()["hero_abilities"] is True
    for bad in ('"false"', '1', 'null'):
        with pytest.raises(SystemExit, match="hero_abilities"):
            RL.load_config(old, ["hero_abilities=" + bad], False)
    assert json.loads(json.dumps(on))["hero_abilities"] is True  # persisted config metadata
    with pytest.raises(ValueError, match="hero_abilities"):
        RE.RoyaleSelfPlayEnv(hero_abilities="false")


def test_search_flag_metadata_and_env(tmp_path):
    from pipeline import search_s0 as S
    with patch.object(S, "_init_worker") as init, patch.object(S, "_run_job", return_value={"skipped": "test", "arm": "plain", "opp": "gen", "seed": 0}):
        S.main(["--out", str(tmp_path / "run"), "--seeds", "0,", "--opps", "gen", "--arms", "plain",
                "--hero-abilities"])
    assert init.call_args.args[0]["hero_abilities"] is True
    assert json.loads((tmp_path / "run/run.json").read_text())["hero_abilities"] is True
    # The worker constructs the actual environment from its args (policies are tiny test models).
    from pipeline.tests.test_search_s0 import TestOppGen
    _, _, _ = TestOppGen()._worker(hero_abilities=True)
    runner = S._W["runner"]
    assert runner.make_env().hero_abilities is True
    result = runner.play("plain", runner.setup("gen", 0, HERO))
    assert result["hero_abilities"] is True
    assert set(result["ability_presses"]) == {0, 1}


@pytest.mark.parametrize("kind", [EntityKind.TROOP, EntityKind.BUILDING,
                                   EntityKind.KING_TOWER, EntityKind.PRINCESS_TOWER])
def test_exact_range_boundary_cost_and_stale_delay(kind):
    """Positive controls around each guard, including troop/building/crown tower geometry."""
    from types import SimpleNamespace as NS
    env = RE.RoyaleSelfPlayEnv(forms_mode="deck", hero_abilities=True)
    env.reset(HERO, ICEBOW, 0)
    cid = env.ids["Knight"]
    hero = NS(uid=6, team=0, card_id=cid, hp=100, status_flags=STATUS_HERO, x=0, y=0, kind=EntityKind.TROOP)
    foe = NS(uid=7, team=1, card_id=-1, hp=100, status_flags=0,
             x=env._hero_ranges["Knight_hero"] + 1500 * RE.SCALE, y=0, kind=kind)
    players = [NS(abilities=[[1, 0, 2, cid, 0]], elixir_milli=2000), NS(abilities=[], elixir_milli=0)]
    state = NS(players=players, entities=[hero, foe])
    command = (0, cid, hero.uid)
    with patch.object(env.core, "state", return_value=state), \
         patch.object(env.core, "check_deploy", return_value=DeployStatus.OK), \
         patch.object(env.core, "_battle", NS(debug_units=lambda: [(6, "Knight_hero"), (8, "Knight_hero")])):
        rng = random.getstate(), digest(np.random.get_state())
        assert env.ability_commands(0) == [command]
        assert (random.getstate(), digest(np.random.get_state())) == rng
        foe.x += 1
        assert env.ability_commands(0) == []
        foe.x -= 1
        players[0].elixir_milli = 1999
        assert env.ability_commands(0) == []
        players[0].elixir_milli = 2000
        foe.hp = 0
        assert env.ability_commands(0) == []
        foe.hp = 100
        for status in (DeployStatus.NO_HERO, DeployStatus.ABILITY_NOT_READY, DeployStatus.ABILITY_SPENT):
            with patch.object(env.core, "check_deploy", return_value=status):
                assert env.ability_commands(0) == []
        with patch.object(env.eng, "act") as act:
            env.queue_abilities(0, [command], 26)
            assert env.ability_commands(0) == []  # no duplicate while queued
            env.tick += 25
            env._fire_abilities()
            act.assert_not_called()
            hero.uid = 8  # old hero died and another copy took over before landing
            env.tick += 1
            env._fire_abilities()
            act.assert_not_called()
        assert env.ability_presses == {0: {}, 1: {}}



def test_hero_flag_building_uses_its_own_zero_range():
    from types import SimpleNamespace as NS
    env = RE.RoyaleSelfPlayEnv(forms_mode="deck", hero_abilities=True)
    deck = [n.replace("Knight@hero", "Goblins@hero") for n in HERO]
    env.reset(deck, ICEBOW, 0)
    cid = env.ids["Goblins"]
    flag = NS(uid=6, team=0, card_id=cid, hp=100, status_flags=STATUS_HERO,
              x=0, y=0, kind=EntityKind.BUILDING)
    foe = NS(uid=7, team=1, hp=100, x=1500 * RE.SCALE, y=0)
    state = NS(players=[NS(abilities=[[1, 0, env._hero_costs[cid], cid, 0]], elixir_milli=10000)],
               entities=[flag, foe])
    with patch.object(env.core, "state", return_value=state), \
         patch.object(env.core, "check_deploy", return_value=DeployStatus.OK), \
         patch.object(env.core, "_battle", NS(debug_units=lambda: [])):
        assert env.ability_commands(0) == [(0, cid, 6)]
        foe.x += 1
        assert env.ability_commands(0) == []
