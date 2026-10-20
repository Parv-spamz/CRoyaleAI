"""pipeline/search_s0.py --scorer v2 (board value x current HP x position) and the scorer-validation tool's statistics.

    OMP_NUM_THREADS=2 research/ext/Royale/.venv/Scripts/python.exe -m pytest -q pipeline/tests/test_scorer_v2.py
"""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

try:
    from pipeline.royale_env import RoyaleSelfPlayEnv
    from pipeline import search_s0 as S
    from pipeline.tests import test_search_s0 as T0
except ImportError:                                   # no royalegym in this venv
    RoyaleSelfPlayEnv = None

P, K = 3052, 4824
Y0, Y1 = 117000, 459000                               # RoyaleSim princess y lines, team 0 / team 1 (engine frame)
MID = (Y0 + Y1) // 2


def state(units, tower_hp=(P, P, K)):
    """Full towers at the real engine's y lines + ``units`` = [(team, kind, hp, max_hp, card_id, y)]."""
    from royalegym.protocol import EntityKind
    ents = []
    for team, y, ky in ((0, Y0, 54000), (1, Y1, 522000)):
        l, r, k = tower_hp
        ents += [SimpleNamespace(team=team, kind=EntityKind.PRINCESS_TOWER, hp=l, max_hp=P, card_id=-1, y=y),
                 SimpleNamespace(team=team, kind=EntityKind.PRINCESS_TOWER, hp=r, max_hp=P, card_id=-1, y=y),
                 SimpleNamespace(team=team, kind=EntityKind.KING_TOWER, hp=k, max_hp=K, card_id=-1, y=ky)]
    ents += [SimpleNamespace(team=t, kind=kind, hp=hp, max_hp=mx, card_id=c, y=y) for t, kind, hp, mx, c, y in units]
    return SimpleNamespace(entities=ents, players=[SimpleNamespace(crowns=0), SimpleNamespace(crowns=0)])


CAT = [SimpleNamespace(card_id=0, name="Knight", elixir=3, count=1),
       SimpleNamespace(card_id=1, name="Xbow", elixir=6, count=1),
       SimpleNamespace(card_id=2, name="Valkyrie", elixir=4, count=1)]


@unittest.skipIf(RoyaleSelfPlayEnv is None, "royalegym not importable (run in research/ext/Royale/.venv)")
class TestScorerV2(unittest.TestCase):
    KN = T0.TestScorer.KNIGHT_FRAC if RoyaleSelfPlayEnv else 0.0

    def sc(self, v):
        return S.Scorer(CAT, tower_level=11, card_level=11, version=v)

    def test_v1_is_default_and_ignores_hp_and_position(self):
        from royalegym.protocol import EntityKind as EK
        self.assertEqual(S.Scorer(CAT, tower_level=11, card_level=11).version, "v1")
        self.assertEqual(S.make_scorer.__defaults__, ("v1",))
        self.assertEqual(T0.runner().scorer_version, "v1")
        v1 = self.sc("v1")
        for cid, want in ((0, self.KN), (1, 6 * 0.061)):                      # Knight (pooled) / Xbow (elixir-priced)
            vals = {v1.board_value(state([(t, EK.TROOP, hp, 1766, cid, y)]), t)
                    for t in (0, 1) for hp in (10, 1766) for y in (0, Y0, MID, Y1)}
            self.assertEqual(vals, {want})                                      # catalogue HP, position-blind
        with self.assertRaises(ValueError):
            S.Scorer(CAT, tower_level=11, card_level=11, version="v3")

    def test_v2_hp_and_position_hand_checked(self):
        """Lone Knight = v1 x hp_frac x pos; pos 0.5 at own princess line, 1.0 at the river, 1.5 at the enemy line."""
        from royalegym.protocol import EntityKind as EK
        v2 = self.sc("v2")
        bv = lambda team, hp, y: v2.board_value(state([(team, EK.TROOP, hp, 1000, 0, y)]), team)
        self.assertAlmostEqual(bv(0, 1000, MID), self.KN, places=12)            # full HP at the river = v1
        self.assertAlmostEqual(bv(0, 100, MID), 0.1 * self.KN, places=12)       # 10% HP
        self.assertAlmostEqual(bv(0, 1000, Y0), 0.5 * self.KN, places=12)       # ours, at our princess line
        self.assertAlmostEqual(bv(0, 1000, 0), 0.5 * self.KN, places=12)        #   behind it: clipped
        self.assertAlmostEqual(bv(0, 1000, Y1), 1.5 * self.KN, places=12)       # ours, at THEIR princess line
        self.assertAlmostEqual(bv(1, 1000, Y0), 1.5 * self.KN, places=12)       # theirs, at OUR princess line (danger)
        self.assertAlmostEqual(bv(1, 1000, Y1 + 30000), 0.5 * self.KN, places=12)   # theirs, behind their own line
        q = Y0 + (Y1 - Y0) // 4                                                   # ours, a quarter of the way
        self.assertAlmostEqual(bv(0, 400, q), 0.4 * 0.75 * self.KN, places=12)
        self.assertAlmostEqual(bv(1, 1000, q), 1.25 * self.KN, places=12)       # theirs, three quarters toward us
        self.assertEqual(self.sc("v1").board_value(state([(0, EK.TROOP, 100, 1000, 0, Y0)]), 0), self.KN)   # v1: as before

    def test_v2_mixed_pool_and_elixir_priced(self):
        """Two pooled bodies: threat_value's pooled value x elixir-weighted mean multiplier; an Xbow (no finite ignore
        cost) is v1's elixir price x its own multiplier; BOARD_CAP after."""
        from clashrl import threat_value as TV
        from royalegym.protocol import EntityKind as EK
        v2 = self.sc("v2")
        pooled = TV.bodies_ignore_frac(v2.db, ["knight", "valkyrie"], tower_level=11, enemy_level=11)
        m_kn, m_va, m_xb = 0.1 * 1.0, 0.2 * 1.5, 0.25 * 1.5          # Knight 10% at MID, Valk 20% / Xbow 25% at Y1
        st = state([(0, EK.TROOP, 100, 1000, 0, MID), (0, EK.TROOP, 200, 1000, 2, Y1),
                    (0, EK.BUILDING, 250, 1000, 1, Y1)])
        want = pooled * (3 * m_kn + 4 * m_va) / 7 + 6 * 0.061 * m_xb
        self.assertLess(want, 1.0)
        self.assertAlmostEqual(v2.board_value(st, 0), want, places=12)
        self.assertEqual(v2.board_value(st, 1), 0.0)
        many = state([(1, EK.TROOP, 1000, 1000, 0, Y0)] * 4)                    # 4 full Knights on our tower: capped
        self.assertEqual(v2.board_value(many, 1), S.BOARD_CAP)

    def test_v2_on_the_engine(self):
        """Real states: the cached y lines are the princess towers' (team 0 low y), and a v2 Runner's rollout scores are
        finite with the same candidate count as v1's."""
        env = RoyaleSelfPlayEnv()
        env.reset(T0.ICEBOW, T0.HOGEQ, seed=0)
        sc = S.make_scorer(env, "v2")
        self.assertEqual(sc.ylines(env.core.state()), {0: float(Y0), 1: float(Y1)})
        run = T0.runner()
        run.scorer_version = "v2"
        m, ds, p, enc, heads, allowed = T0.to_root(self, run, "s1", T0.ICEBOW, 3)
        cands = S.shortlist(run.learner, enc, heads, allowed, 4, 3)
        ws, scs = run.rollout_scores(m, ds, cands, p)
        self.assertEqual(run.scorer.version, "v2")
        self.assertEqual(len(scs), len(cands))
        self.assertTrue(np.all(np.isfinite([ws] + scs)))

    def test_ylines_need_both_princesses(self):
        """y lines come from a team's princess towers only when BOTH are present; otherwise the arena constants, never
        the king tower's y; once cached they stay."""
        from royalegym.protocol import EntityKind as EK

        def towers(p0, p1):            # princess y's present per team; kings always at 54000 / 522000
            t = lambda team, kind, y: SimpleNamespace(team=team, kind=kind, hp=P, max_hp=P, card_id=-1, y=y)
            return SimpleNamespace(entities=[t(0, EK.PRINCESS_TOWER, y) for y in p0] + [t(1, EK.PRINCESS_TOWER, y) for y in p1]
                                   + [t(0, EK.KING_TOWER, 54000), t(1, EK.KING_TOWER, 522000)])

        self.assertEqual(S.ARENA_PRINCESS_Y, (float(Y0), float(Y1)))
        v2 = self.sc("v2")
        self.assertEqual(v2.ylines(towers([100000, 100000], [])), {0: 100000.0, 1: float(Y1)})   # team 1: constant
        self.assertEqual(v2.ylines(towers([90000], [400000, 400000])), {0: 100000.0, 1: 400000.0})  # cached / now both
        fresh = self.sc("v2")
        self.assertEqual(fresh.ylines(towers([90000], [400000])), {0: float(Y0), 1: float(Y1)})   # one each: constants
        self.assertEqual(fresh.ylines(towers([90000, 95000], [])), {0: float(Y0), 1: float(Y1)})  # disagreeing ys


def load_validate():
    p = REPO / "scratchpad/gauntlet/L69/scorer_val/validate.py"
    spec = importlib.util.spec_from_file_location("scorer_validate", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@unittest.skipIf(RoyaleSelfPlayEnv is None, "royalegym not importable (run in research/ext/Royale/.venv)")
class TestValidateAggregation(unittest.TestCase):
    def test_statistics(self):
        V = load_validate()
        self.assertEqual(V.spearman([1, 2, 3, 4], [10, 20, 30, 40]), 1.0)
        self.assertAlmostEqual(V.spearman([1, 2, 3, 4], [4, 3, 2, 1]), -1.0)
        self.assertIsNone(V.spearman([1, 2, 3], [5, 5, 5]))                    # constant outcome: undefined
        self.assertAlmostEqual(V.spearman([1, 1, 2], [1, 2, 3]), 0.8660254037844387)   # tie -> average ranks
        self.assertEqual(V.top1([0.0, 0.0, 0.0], [0.5, 1.0, 0.0]), (False, 1 / 3, 0.5))  # tie -> WAIT (index 0)
        self.assertEqual(V.top1([0.0, 0.3, 0.1], [0.5, 1.0, 1.0]), (True, 2 / 3, 0.0))

    def test_aggregate_synthetic(self):
        """3 decisions x 3 candidates, K = 4. v1_idle ranks exactly like the win rate; v2_idle exactly against it;
        decision 3's outcome is constant (rho undefined for every scorer, top-1 hit by construction)."""
        V = load_validate()
        win = [[[0, 0, 0, 0], [1, 1, 0, 0], [1, 1, 1, 1]],
               [[1, 1, 1, 1], [0, 0, 0, 1], [0, 0, 1, 1]],
               [[1, 0, 1, 0]] * 3]
        good = [[0.0, 0.5, 1.0], [1.0, 0.25, 0.5], [0.3, 0.2, 0.1]]
        recs = [{"scores": {"v1_idle": g, "v2_idle": [-x for x in g]},
                 "outcome_k": {"win": w, "hp": (np.array(w) * 100).tolist()}} for g, w in zip(good, win)]
        recs.append({"skipped": "no loadable deck"})
        agg = V.aggregate(recs, n_boot=200)
        self.assertEqual(agg["n_decisions"], 3)
        a, b = agg["v1_idle|win"], agg["v2_idle|win"]
        self.assertEqual((a["n"], a["rho_n"], a["rho_undefined"], a["rho_mean"]), (3, 2, 1, 1.0))
        self.assertEqual(a["rho_ci95"], [1.0, 1.0])
        self.assertEqual((a["top1"], a["regret_mean"]), (1.0, 0.0))
        self.assertAlmostEqual(a["top1_chance"], (1 / 3 + 1 / 3 + 1) / 3, places=4)
        self.assertEqual((b["rho_mean"], b["top1"]), (-1.0, round(1 / 3, 4)))  # only the constant decision hits
        self.assertAlmostEqual(b["regret_mean"], (1.0 + 0.75 + 0.0) / 3, places=4)
        self.assertEqual(agg["v1_idle|hp"]["rho_mean"], 1.0)                    # hp = 100 x win here
        self.assertNotIn("v1_policy|win", agg)                                   # scorers absent from the input
        rel = agg["reliability|win"]                                             # even-k vs odd-k win rates per cand
        self.assertEqual((rel["n"], rel["undefined"]), (2, 1))                   # dec 3: even-k half is constant
        r_half = (1.0 + 0.8660254037844387) / 2                                  # dec 2: ranks tie once
        self.assertAlmostEqual(rel["r_half"], r_half, places=4)
        self.assertAlmostEqual(rel["r_K"], 2 * r_half / (1 + r_half), places=4)  # Spearman-Brown step-up to K
        self.assertAlmostEqual(rel["ceiling"], (2 * r_half / (1 + r_half)) ** 0.5, places=4)
        self.assertEqual(agg["n_matches"], 3)                                    # no opp/seed: each its own cluster
        idx = V.eval_indices("gen", 3, 5, 1000)
        self.assertEqual(idx, V.eval_indices("gen", 3, 5, 1000))
        self.assertEqual(len(idx), 5)
        self.assertEqual(V.eval_indices("gen", 3, 5, 3), frozenset({0, 1, 2}))  # short match: all of it
        many = set().union(*(V.eval_indices("gen", s, 5, 1000) for s in range(40)))
        self.assertGreater(max(many), 900)                                      # the whole match, not the first 300
        with self.assertRaises(ValueError):                                      # odd K is refused
            V.per_decision({"scores": {}, "outcome_k": {"win": [[0, 1, 1]] * 2, "hp": [[0, 1, 1]] * 2}})

    def test_cluster_bootstrap_and_spearman_brown(self):
        """Whole matches are resampled: 3 identical decisions of one match + 1 of another is 2 clusters, so the CI
        spans 0 .. 1; the plain bootstrap (4 independent items) never reaches 0 at the 2.5th percentile."""
        V = load_validate()
        x = [1.0, 1.0, 1.0, 0.0]
        self.assertEqual(V.boot_ci(x, ["a", "a", "a", "b"]), [0.0, 1.0])
        self.assertGreater(V.boot_ci(x)[0], 0.0)
        recs = [{"opp": "gen", "seed": s, "scores": {"v1_idle": [0.0, 1.0]},
                 "outcome_k": {"win": [[0, 0], [1, 1]], "hp": [[0, 0], [1, 1]]}} for s in (1, 1, 2)]
        self.assertEqual(V.aggregate(recs, n_boot=50)["n_matches"], 2)
        self.assertAlmostEqual(V.spearman_brown(0.5), 2 / 3)
        self.assertEqual(V.spearman_brown(-0.5), -1.0)                          # clamped
        self.assertIsNone(V.spearman_brown(None))
        self.assertEqual((V.ceiling(-0.2), V.ceiling(0.81)), (0.0, 0.9))


if __name__ == "__main__":
    unittest.main()
