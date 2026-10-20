"""CPU gates for ``ability_policy`` v2 (pipeline/royale_env.py): the L70 per-ability calibrated press models drive the
sim's hero / champion buttons. Default ("generic") stays byte-identical to the commit before v2 (d32c67e).

    CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=2 research/ext/Royale/.venv/Scripts/python.exe -m pytest -q pipeline/tests/test_ability_policy_sim.py

Needs royalegym/royalesim (the Royale stack venv); skipped elsewhere.
"""
import json
import random
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch

import numpy as np
import pytest

pytest.importorskip("royalegym")
from royalegym.protocol import EntityKind, STATUS_HERO
from pipeline import royale_env as RE
from pipeline.tests.test_hero_abilities import BERSERKER, HERO, ICEBOW, drive, match

REPO = Path(__file__).resolve().parents[2]
PRE_V2 = "d32c67e"                                    # the commit before ability_policy
ABIL = REPO / "scratchpad/gauntlet/L70/abilities"
CHAMP_DECK = ["GoldenKnight", "BossBandit", "Giant", "Zap", "Musketeer", "Knight@hero", "Fireball", "Log"]   # seed 0 deals idx 1,7,5,3 first


def run(env, hero_side=1, delay=0, deck=HERO):
    result, hashes = drive(match(env, hero_side, delay, deck))
    return result, hashes


def run_prefer(env, hero_side, deck, prefer, reserve=0):
    """test_hero_abilities.drive with a card priority list and a smaller elixir reserve (a 6-cost champion needs it)."""
    m = match(env, hero_side, 0, deck)
    while True:
        due = m.due()
        if not due:
            break
        for side in due:
            side.prepare()
        for side in due:
            hand = set(m.env.core.state().players[side.side].hand)
            choices = [(prefer.index(m.env.names[cid]) if m.env.names[cid] in prefer else len(prefer), side.costs[slot], slot)
                       for slot, ix in side.deck_index_of_slot.items()
                       if (cid := m.env.deck_ids[side.side][ix]) in hand and side.costs[slot] <= side._cur[1].my_elixir - reserve]
            side.apply(.5, {"play": True, "slot": min(choices)[2], "cell": 44 * 36 + 7, "why": "script"} if choices
                       else {"play": False, "slot": -1, "cell": -1, "why": "wait"})
    return m.result()


def v2(**kw):
    return RE.RoyaleSelfPlayEnv(forms_mode="deck", hero_abilities=True, ability_policy="v2", **kw)


def test_default_is_byte_identical_to_pre_v2_code():
    import subprocess
    import sys
    import types
    mod = types.ModuleType("royale_env_pre_v2")
    mod.__file__ = str(REPO / "pipeline/royale_env.py")
    sys.modules[mod.__name__] = mod
    exec(compile(subprocess.check_output(["git", "show", f"{PRE_V2}:pipeline/royale_env.py"], cwd=REPO),
                 mod.__file__, "exec"), mod.__dict__)
    ref = run(mod.RoyaleSelfPlayEnv(forms_mode="deck", hero_abilities=True), 1, 26, BERSERKER)
    assert ref[0]["ability_presses"][1], "the reference match must press something"
    for kw in ({}, {"ability_policy": "generic"}):
        env = RE.RoyaleSelfPlayEnv(forms_mode="deck", hero_abilities=True, **kw)
        got = run(env, 1, 26, BERSERKER)
        assert got[1] == ref[1]                                   # engine state hash after every decision
        assert got[0]["ability_presses"] == ref[0]["ability_presses"]
        assert "ability_policy" not in got[0]


def test_v2_validation():
    with pytest.raises(ValueError, match="ability_policy"):
        RE.RoyaleSelfPlayEnv(hero_abilities=True, ability_policy="v3")
    with pytest.raises(ValueError, match="hero_abilities"):
        RE.RoyaleSelfPlayEnv(ability_policy="v2")


def test_v2_deterministic_and_seeded():
    outs = []
    for _ in range(2):
        env = v2()
        outs.append(run(env, 1, 0, BERSERKER))
    assert outs[0][1] == outs[1][1]
    assert outs[0][0]["ability_presses"] == outs[1][0]["ability_presses"]
    assert outs[0][0]["ability_policy"] == "v2"


def test_v2_one_use_and_boss_bandit_charges():
    """Force every draw to succeed: each deployment still presses at most once, Boss Bandit twice, >= 3 s apart."""
    calls, pressed = [], []

    def always(key, feats, version="v1", charge=0):
        assert version == "v2" and len(feats) == 14 and np.isfinite(feats).all()
        calls.append((key, charge))
        return 1.0
    with patch.object(RE._v2_policy(), "predict", always):
        env = v2()
        act = env.eng.act

        def spy(**kw):
            r = act(**kw)
            if "ability_button" in kw and r["accepted"]:
                pressed.append((env.tick, kw["side"], kw["ability_button"]))
            return r
        env.eng.act = spy
        result = run_prefer(env, 1, CHAMP_DECK, ["BossBandit", "GoldenKnight", "Knight"])
    presses, dep = result["ability_presses"][1], env.ability_deployments[1]
    assert presses["BossBandit"] and presses["GoldenKnight"] and presses["Knight"]
    assert presses["GoldenKnight"] <= dep["GoldenKnight"] and presses["Knight"] <= dep["Knight"]
    assert presses["BossBandit"] <= 2 * dep["BossBandit"]
    assert sum(i["presses"] == 2 for i in env._ability_uid.values()) <= dep["BossBandit"]   # only the bandit repeats
    assert max(i["presses"] for i in env._ability_uid.values()) == 2
    assert ("boss-bandit", 1) in calls and all(c == 0 for k, c in calls if k != "boss-bandit")
    for button in {b for _, _, b in pressed}:
        ts = [t for t, _, b in pressed if b == button]
        assert all(b - a >= RE.V2_REPRESS_TICKS for a, b in zip(ts, ts[1:]))
    assert result["ability_fallback_generic"] == {}


def test_v2_fallback_for_a_model_less_ability_is_counted():
    with patch.dict(RE.V2_KEYS, clear=False):
        del RE.V2_KEYS["Knight"]
        env = v2()
        result, _ = run(env, 1, 0, HERO)
    assert result["ability_fallback_generic"].get("Knight", 0) == result["ability_presses"][1]["Knight"] > 0


def test_v2_decision_probability_uses_dt():
    """q = 1 - (1-p)^dt with dt = seconds since this side's previous check; the draw is a seeded function of the tick."""
    env = v2(seed=7)
    env.reset(CHAMP_DECK, ICEBOW, 7)
    hits = []
    with patch.object(RE._v2_policy(), "predict", lambda *a, **k: 0.5):
        for tick in range(200, 4000, 10):
            env.tick = tick
            env._v2_dt = .5
            hero = NS(uid=6, team=0, card_id=env.ids["GoldenKnight"], hp=1, max_hp=1, x=0, y=0, kind=EntityKind.TROOP,
                      status_flags=STATUS_HERO)
            env._ability_uid.clear()
            st = NS(entities=[hero], players=[NS(elixir_milli=0, crowns=0), NS(elixir_milli=0, crowns=0)])
            hits.append(env._v2_gate(0, hero.card_id, hero, st))
            assert hits[-1] == env._v2_gate(0, hero.card_id, hero, st)            # same tick, same answer
    rate = sum(hits) / len(hits)
    assert abs(rate - (1 - .5 ** .5)) < .06, rate


def test_feature_extraction_matches_phase2_build():
    import importlib.util
    import sys
    import types
    try:
        import orjson  # noqa: F401  (phase2_build imports it for its replay reader only; the features need none)
    except ImportError:
        sys.modules["orjson"] = types.ModuleType("orjson")
    spec = importlib.util.spec_from_file_location("l70_phase2_build", ABIL / "phase2_build.py")
    pb = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pb)
    env = v2()
    env.reset(CHAMP_DECK, ICEBOW, 0)
    S = RE.SCALE * 1000
    cannon_hp = int(pb.BUILDING_BASE_HP["cannon"] * pb.LEVEL_PCT[10] / 100)   # phase2 tells a building by its level-11 max HP
    tile = lambda x, y: (int(x * S), int(y * S))
    ids = env.ids
    knight, cannon = ids["Knight"], ids["Cannon"]
    # (team, card, x, y, hp, max_hp, kind): the hero (side 0), two enemy troops inside 3 and 5 tiles, one far, a dead one, an
    # enemy cannon, an own unit (ignored), 3 towers of side 1 (one destroyed) and 2 of side 0.
    rows = [(0, "GoldenKnight", 9, 20, 900, 1200, EntityKind.TROOP),
            (1, "Knight", 10, 22, 500, 690, EntityKind.TROOP), (1, "Knight", 12, 22, 300, 690, EntityKind.TROOP),
            (1, "Knight", 9, 30, 690, 690, EntityKind.TROOP), (1, "Knight", 9, 21, 0, 690, EntityKind.TROOP),
            (1, "Cannon", 7, 18, 400, cannon_hp, EntityKind.BUILDING), (0, "Knight", 9, 21, 690, 690, EntityKind.TROOP),
            (1, "king", 9, 29, 4000, 4824, EntityKind.KING_TOWER), (1, "princess", 3.5, 25.5, 2000, 3052, EntityKind.PRINCESS_TOWER),
            (1, "princess", 14.5, 25.5, 0, 3052, EntityKind.PRINCESS_TOWER),
            (0, "king", 9, 3, 4824, 4824, EntityKind.KING_TOWER)]
    ents = []
    for uid, (team, name, x, y, hp, mhp, kind) in enumerate(rows):
        X, Y = tile(x, y)
        ents.append(NS(uid=uid, team=team, card_id=ids.get(name, -1), x=X, y=Y, hp=hp, max_hp=mhp, kind=kind,
                       status_flags=STATUS_HERO if uid == 0 else 0))
    st = NS(entities=ents, players=[NS(elixir_milli=7250, crowns=1), NS(elixir_milli=3000, crowns=0)])
    env.tick = 2500
    got = env._ability_features(0, ents[0], st, 2000)
    # the same board as a phase-2 recorded frame: [side, x, y, name, hp, max_hp]; x, y in 1/1000 tile; towers
    # [side, type, _, x, y, hp]; crowns by destroyed enemy princess towers.
    frame_entities = [[t, int(x * 1000), int(y * 1000), name.lower() if name not in ("king", "princess") else "-1", hp, mhp]
                      for t, name, x, y, hp, mhp, k in rows]
    frame = {"tick": 2500, "elixir": [7.25, 3.0], "entities": frame_entities,
             "towers": [[1, "king", 0, 9000, 29000, 4000], [1, "princess", 0, 3500, 25500, 2000],
                        [1, "princess", 0, 14500, 25500, 0], [0, "king", 0, 9000, 3000, 4824]]}
    want = pb.features(frame, frame_entities[0], 2000)
    assert pb.FEATURES == RE._v2_policy().FEATURE_NAMES
    assert got == pytest.approx(want), dict(zip(pb.FEATURES, zip(got, want)))
    assert got[13] == 1 and got[11] == 2 and got[12] == 2 and got[8] == 1.0 and got[2] == pytest.approx(5 ** .5)
    # side 1 mirrors: in_enemy_half flips with the side
    hero1 = ents[1]
    assert env._ability_features(1, hero1, st, 2000)[8] == float(hero1.y < 16 * RE.SCALE * 1000)


def test_champion_buttons_exist_only_under_v2():
    g = RE.RoyaleSelfPlayEnv(forms_mode="deck", hero_abilities=True)
    g.reset(CHAMP_DECK, ICEBOW, 0)
    e = v2()
    e.reset(CHAMP_DECK, ICEBOW, 0)
    assert len(g._hero_ids[0]) == 1 and len(e._hero_ids[0]) == 3
    assert e._champ_ids[0] == {e.ids["BossBandit"], e.ids["GoldenKnight"]} and g._champ_ids[0] == set()


def test_config_flag_and_search_plumbing(tmp_path):
    from pipeline import rl_royale as RL
    from pipeline import search_s0 as S
    import hashlib
    import yaml
    base = RL.load_config(REPO / "pipeline/rl_royale.yaml", [], False)
    assert "ability_policy" not in base                          # absent = generic: the historical config and hash
    legacy = {k: v for k, v in base.items() if k != "hero_abilities"}
    assert RL.config_sha(base) == hashlib.sha256(json.dumps(legacy, sort_keys=True, default=str).encode()).hexdigest()
    assert RL.config_sha(dict(base, ability_policy="generic")) == RL.config_sha(base)
    on = RL.load_config(REPO / "pipeline/rl_royale.yaml", ["hero_abilities=true", "ability_policy=v2"], False)
    assert on["ability_policy"] == "v2" and RL.config_sha(on) != RL.config_sha(dict(on, ability_policy="generic"))
    for bad, ov in (("v3", ["hero_abilities=true", "ability_policy=v3"]), ("needs", ["ability_policy=v2"])):
        with pytest.raises(SystemExit, match="ability_policy"):
            RL.load_config(REPO / "pipeline/rl_royale.yaml", ov, False)
    learner = object.__new__(RL.Learner)
    learner.cfg, learner.init_meta, learner.grid = on, {"args": {}}, "lattice"
    assert learner.actor_base()["ability_policy"] == "v2"
    learner.cfg = base
    assert learner.actor_base()["ability_policy"] == "generic"
    with patch.object(S, "_init_worker") as init, patch.object(S, "_run_job", return_value={"skipped": "t", "arm": "plain", "opp": "gen", "seed": 0}):
        S.main(["--out", str(tmp_path / "run"), "--seeds", "0,", "--opps", "gen", "--arms", "plain",
                "--hero-abilities", "--ability-policy", "v2"])
    assert init.call_args.args[0]["ability_policy"] == "v2"
    with pytest.raises(SystemExit):
        S.main(["--out", str(tmp_path / "run2"), "--seeds", "0,", "--ability-policy", "v2"])
