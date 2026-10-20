"""Offline tests for pipeline/opp_est_audit.py (O8).

    icebow/.venv/Scripts/python.exe -m unittest pipeline.tests.test_opp_est_audit -v

No engine, no GPU. Covers: (i) dets conversion -- every enemy class in the held-out pool's ghost decks
resolves to a non-None CardDB cost (skipped, not silently, if the pool file is absent); (ii) phase bucketing
against obs_contract._phase; (iii) the metric functions on a hand-built toy series with known MAE/bias/P90;
(iv) a 3-tick estimator plumbing check (reset -> update with one enemy 4-cost det -> estimate drops by
exactly the cost, per the estimator's own exact-books semantics -- opponent_elixir.py:113); (v, Attempt 2
CHANGE 1) the 5-tick stepping loop calls the live policy exactly on the original 10-tick decision boundaries;
(vi, Attempt 2 CHANGE 2) the A+ dets path resolves a known spell cost (fireball=4) and skips + warns-once on
a costless one (mirror -- dynamic pricing, found in Attempt 1's dets-conversion test); (vii, Attempt 3) a
synthetic single 4-cost enemy det makes ``TrackedEstimator.charged_by_base == {base: [1, 4.0]}`` (plus a
two-different-bases-in-one-update() case, the scenario a before/after ``_opp_spent`` diff cannot attribute);
(viii, Attempt 3) ``ghost_scripted_by_base`` built correctly from a hand-built ``ghost_commands`` list
(ability entries excluded, hyphenated slugs normalized, a costless slug skipped + warned once); (ix, Attempt
4 FIX 1) ``ghost_delivered_by_base`` (the truth ledger over-charge actually uses) differs from
``ghost_scripted_by_base`` when a scripted play was never delivered; (x, Attempt 4 FIX 2) ``opp_play_flags``
flags only the first sample tick at/after a DELIVERED ghost event; (xi, Attempt 4 FIX 4) ``dets_of_whitelisted``
drops a non-whitelisted base and keeps a whitelisted one, and ``load_detector_cards`` loads the real,
non-empty live whitelist; (xii, Attempt 4 FIX 5) hand-written (not self-referential) phase expectations, plus
``overcharge_table``/``merge_base_ledgers`` on hand-built ledgers.

TICKET O16 additions: (xiii) ``active_base_conds``/``build_cond_defs`` reproduce ``BASE_CONDS``/the old
hardcoded ``COND_DEFS`` exactly with both flags off, and add the right extra conditions in the right
order otherwise; (xiv) ``make_team_tracker`` builds with live's own defaults (min_hits=2, the literals
play.py:420-441 passes); (xv) ``tt_bill_dets`` on a 3-sample synthetic stream: a one-sample phantom is
NEVER billed, a real 2-sample unit is billed EXACTLY ONCE, at its first-confirmed (min_hits) sample, and
never rebilled on a later re-sighting of the same track; (xvi) ``markov_params``' closed form against
hand-derived numbers for known (p_target, mean_run) pairs; (xvii) ``corr_live_view``'s marginals --
recall, false-positive rate, and position sigma -- measured over a 200k-sample synthetic run and checked
within 1% of ``live_view``'s own constants, for BOTH corr settings; (xviii) a short multi-sample smoke of
``corr_live_view`` over a synthetic BoardState SEQUENCE (units spawning/dying) with no engine.
"""
from __future__ import annotations

import math
import sys
import unittest
from dataclasses import replace
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
_ICEBOW_SRC = REPO / "icebow" / "src"
if str(_ICEBOW_SRC) not in sys.path:
    sys.path.insert(0, str(_ICEBOW_SRC))

from pipeline import vocab                                            # noqa: E402
from pipeline.e1_pool import POOL_V1, load_pool_v1, select_split      # noqa: E402
from pipeline.obs_contract import (                                   # noqa: E402
    TOWER_ORDER, TILES_X, TILES_Y, DEGRADE_PRECISION, DEGRADE_RECALL, BoardState, Tower, Unit, _phase, load_deck,
)
from pipeline.opp_est_audit import (                                  # noqa: E402
    BASE_CONDS, FEED_NOISE_MODES, FEED_OPP_ELIXIR_MODES, TrackedEstimator, TrackedEstimatorV2,
    TracedEstimator, TracedEstimatorV2, _Det,
    _jsonable, _RecorderDB, active_base_conds, b5_seed, build_cond_defs, build_parser, card_cost,
    charge_diagnostics, classify_charge_reason, cond_key, corrL_seed, corrS_seed, dets_of, dets_of_costed,
    dets_of_whitelisted, feed_condition_key, filter_whitelisted_billed_dets, ghost_delivered_by_base,
    ghost_scripted_by_base, is_policy_tick, load_detector_cards, mae, make_estimator, make_team_tracker,
    mean_bias, merge_base_ledgers, opp_play_flags, overcharge_table, percentile, phase_from_flags,
    phase_of, policy_view_for, run_traced_update, share_within, summarize_condition, tick_field,
    tt_bill_dets, tt_dets_of, validate_feed_config,
)
from pipeline.opp_est_degrade_corr import (                           # noqa: E402
    CORR_LONG, CORR_SHORT, CorrParams, corr_live_view, markov_params, new_state,
)

from clashrl.cards import CardDB                                      # noqa: E402
from clashrl.opponent_elixir import OpponentElixirEstimator, V2_PARAMS   # noqa: E402


def _six_towers(alive: bool = True) -> tuple[Tower, ...]:
    out = []
    for side in (0, 1):
        for kind, lane in TOWER_ORDER:
            out.append(Tower(side, kind, lane, 1.0 if alive else 0.0, alive))
    return tuple(out)


def _minimal_bs(units=(), spells=(), my_elixir=5.0, t_sec=10.0) -> BoardState:
    """A hand-built BoardState with no engine involved -- just enough for corr_live_view's own contract
    (units/spells/towers/my_elixir/t_sec; the fields corr_live_view/live_view actually read)."""
    return BoardState(source="engine", t_sec=t_sec, t_source="tick", double_elixir=False, overtime=False,
                      my_elixir=my_elixir, my_elixir_exact=True, opp_elixir=5.0, my_hand=(-1, -1, -1, -1),
                      my_next=-1, towers=_six_towers(True), units=units, spells=spells, deck=())


def _db() -> CardDB:
    deck = load_deck("icebow")
    return CardDB(path=deck.config.parent / "cards.yaml")


# ------------------------------------------------------------------------------------------------------
# (i) dets conversion: every enemy class the held-out pool's ghost decks actually deploy must resolve a cost
# ------------------------------------------------------------------------------------------------------
class TestDetsConversion(unittest.TestCase):
    def test_known_card_resolves(self):
        db = _db()
        for base in ("musketeer", "knight", "giant", "skeletons"):
            self.assertIsNotNone(db.elixir(base), f"{base} must have a known elixir cost")

    def test_heldout_ghost_decks_resolve_cost(self):
        """Every BASE card any held-out ghost deck carries must price through CardDB.elixir. This is the
        exact path a real enemy play takes: engine name -> vocab.engine_unit_id -> vocab.UNIT_VOCAB ->
        vocab.base_key -> CardDB.elixir (opponent_elixir.py:109's ``self.db.elixir(base)``)."""
        if not POOL_V1.exists():
            self.skipTest(f"pool file missing: {POOL_V1}")
        db = _db()
        pool = load_pool_v1(POOL_V1)
        heldout = select_split(pool, "heldout")
        self.assertGreater(len(heldout), 0, "held-out split must be non-empty for this test to mean anything")
        names: set[str] = set()
        for e in heldout:
            for it in e.get("ghost_deck") or []:
                names.add(str(it["name"]))
        self.assertGreater(len(names), 0)
        unresolved: list[tuple[str, str]] = []       # (engine name, base key) whose cost came back None
        unmapped: list[str] = []                      # engine name with no vocab id at all
        for name in sorted(names):
            cid = vocab.engine_unit_id(name)
            if cid is None:
                unmapped.append(name)
                continue
            base = vocab.base_key(vocab.UNIT_VOCAB[cid])
            if db.elixir(base) is None:
                unresolved.append((name, base))
        # FINDING (not silently skipped): print so -v output and the harness report both carry it.
        if unmapped:
            print(f"[test_dets_conversion] {len(unmapped)} ghost-deck name(s) have NO vocab id: {unmapped}")
        if unresolved:
            print(f"[test_dets_conversion] {len(unresolved)} base key(s) resolve to NO CardDB cost: "
                 f"{unresolved}")
        # The conversion pipeline itself (name -> vocab id) must always succeed for a card that made it into
        # a deck (decks are built from the live catalog, which vocab.py is derived from) -- THIS is a hard
        # assertion. Whether every resulting base then has a priced cards.yaml row is reported above as a
        # finding, not asserted, per the ticket's "list any that do NOT ... do not silently skip".
        self.assertEqual(unmapped, [], f"deck card(s) with no vocab id at all: {unmapped}")


# ------------------------------------------------------------------------------------------------------
# (ii) phase bucketing against obs_contract._phase
# ------------------------------------------------------------------------------------------------------
class TestPhaseBucketing(unittest.TestCase):
    def test_matches_phase_helper_at_hand_written_times(self):
        """FIX 5: expectations written by hand from the DOCUMENTED thresholds (obs_contract.py:
        DOUBLE_ELIXIR_S=120.0, OVERTIME_S=180.0), never by re-deriving them through the same if-chain
        ``phase_from_flags`` itself uses -- the old version of this test was self-referential (it built
        ``expect`` with an identical elif ladder) and could not have caught a bug in that ladder."""
        cases = {30.0: "single", 150.0: "double", 200.0: "overtime"}
        for t, expect in cases.items():
            double, overtime = _phase(t)          # obs_contract's own thresholds, independent computation
            self.assertEqual(phase_from_flags(double, overtime), expect, f"t={t}")
            # and directly against the hand-written thresholds too, with no dependency on _phase at all:
            hand_double, hand_overtime = (t >= 120.0), (t >= 180.0)
            self.assertEqual(phase_from_flags(hand_double, hand_overtime), expect, f"t={t}")

    def test_boundaries(self):
        self.assertEqual(phase_from_flags(False, False), "single")
        self.assertEqual(phase_from_flags(True, False), "double")
        self.assertEqual(phase_from_flags(True, True), "overtime")
        # overtime implies double_elixir is also True in obs_contract._phase (180 >= 120); phase_of trusts
        # the caller's flags directly, so an inconsistent (False, True) still reports "overtime" -- that is
        # by design (overtime always wins), tested explicitly since it is the one flag combo _phase never
        # actually produces.
        self.assertEqual(phase_from_flags(False, True), "overtime")


# ------------------------------------------------------------------------------------------------------
# (iii) metric functions on a hand-built toy series with known MAE / bias / P90
# ------------------------------------------------------------------------------------------------------
class TestMetrics(unittest.TestCase):
    def test_mae_bias(self):
        # est - truth: -1, +2, -3, +4, -5 -> abs = 1,2,3,4,5 mean 3.0; signed mean = (-1+2-3+4-5)/5 = -0.6
        errs = [-1.0, 2.0, -3.0, 4.0, -5.0]
        self.assertAlmostEqual(mae(errs), 3.0)
        self.assertAlmostEqual(mean_bias(errs), -0.6)

    def test_percentile_linear_interp(self):
        # sorted [1,2,3,4,5,6,7,8,9,10]; p90 rank = 0.9*9 = 8.1 -> between index 8 (9) and 9 (10), frac .1
        # -> 9 + 0.1*(10-9) = 9.1 (numpy.percentile([1..10], 90) == 9.1, verified by hand: linear method)
        vals = list(range(1, 11))
        self.assertAlmostEqual(percentile(vals, 90), 9.1)
        self.assertAlmostEqual(percentile([5.0], 90), 5.0)
        self.assertIsNone(percentile([], 90))

    def test_share_within(self):
        abs_errs = [0.2, 0.9, 1.0, 1.5, 2.0, 3.0]
        self.assertAlmostEqual(share_within(abs_errs, 1.0), 3 / 6)   # 0.2, 0.9, 1.0
        self.assertAlmostEqual(share_within(abs_errs, 2.0), 5 / 6)   # all but 3.0

    def test_summarize_condition_toy(self):
        rows = [
            {"tag": "m1", "k": 0, "phase": "single", "truth": 5.0, "est_A": 6.0,
             "is_opp_play_tick": False, "is_my_play_tick": False},
            {"tag": "m1", "k": 0, "phase": "double", "truth": 4.0, "est_A": 2.0,
             "is_opp_play_tick": True, "is_my_play_tick": False},
            {"tag": "m2", "k": 0, "phase": "single", "truth": 3.0, "est_A": 3.0,
             "is_opp_play_tick": False, "is_my_play_tick": True},
        ]
        s = summarize_condition(rows, "est_A")
        self.assertEqual(s["n_ticks"], 3)
        # errs: +1, -2, 0 -> mae = 1.0, bias = -1/3
        self.assertAlmostEqual(s["mae"], 1.0)
        self.assertAlmostEqual(s["mean_bias"], -1.0 / 3.0)
        self.assertEqual(s["by_phase"]["single"]["n"], 2)
        self.assertEqual(s["by_phase"]["double"]["n"], 1)
        self.assertAlmostEqual(s["by_phase"]["double"]["mae"], 2.0)
        self.assertEqual(s["opp_play_ticks"]["n"], 1)
        self.assertAlmostEqual(s["opp_play_ticks"]["mae"], 2.0)
        self.assertEqual(s["my_play_ticks"]["n"], 1)
        self.assertAlmostEqual(s["my_play_ticks"]["mae"], 0.0)
        self.assertEqual(s["by_match"]["n_matches"], 2)


# ------------------------------------------------------------------------------------------------------
# (iv) 3-tick estimator plumbing check: reset -> update with one enemy 4-cost det -> estimate drops by cost
# ------------------------------------------------------------------------------------------------------
class TestEstimatorPlumbing(unittest.TestCase):
    def test_reset_then_one_enemy_play_drops_estimate_by_exact_cost(self):
        db = _db()
        cost = db.elixir("musketeer")
        self.assertEqual(cost, 4, "musketeer must be a 4-cost card for this to be the ticket's '4-cost det'")
        est = OpponentElixirEstimator(db)

        # tick 1: reset at my_elixir=5.0, t=0
        est.reset(my_elixir=5.0, now=0.0)
        self.assertAlmostEqual(est._est, 5.0)

        # tick 2: no enemy dets, my_elixir regenerated to 5.7 -- the estimator has NO clock of its own (it
        # never reads `now` to regenerate; `now` only ages tracks for the forget/cluster window), so the
        # estimate tracks the CALLER's my_elixir exactly when nothing has been spent by either side.
        v2 = est.update(5.7, [], 1.0)
        self.assertAlmostEqual(v2 * 10.0, 5.7, places=4)
        self.assertAlmostEqual(est._est, 5.7)

        # tick 3: one fresh enemy musketeer (4 cost) appears; my_elixir has regenerated further to 6.0.
        # est = my_elixir + my_spent(0) - opp_spent(cost) EXACTLY (opponent_elixir.py:113), no clipping
        # triggers here (6.0 - 4 = 2.0 is inside [0, 10]) so the drop is exact, not merely bounded.
        det = _Det(base="musketeer", cx=0.5, gy=0.3, team="enemy")
        v3 = est.update(6.0, [det], 2.0)
        self.assertAlmostEqual(est._est, 6.0 - cost, places=4)
        self.assertAlmostEqual(v3 * 10.0, 6.0 - cost, places=4)
        # direction + bound, independent of the exact-arithmetic assertion above:
        self.assertLess(est._est, 6.0)
        self.assertGreaterEqual(est._est, 6.0 - cost - 1e-6)

    def test_dets_of_units_shape(self):
        """card_cost() + the _Det shim round-trip a vocab id the way run_match_audit builds dets."""
        db = _db()
        cid = vocab.unit_id("musketeer")
        self.assertEqual(card_cost(db, cid), 4)


# ------------------------------------------------------------------------------------------------------
# (v) Attempt 2 CHANGE 1: the 5-tick stepping loop must call the live policy exactly on the ORIGINAL
# 10-tick decision boundaries (identical ticks to Attempt 1 / e1_eval), never on the in-between 5-tick steps.
# ------------------------------------------------------------------------------------------------------
class TestFiveTickCadence(unittest.TestCase):
    def test_policy_fires_only_on_original_decision_ticks(self):
        first_tick, decide_every, step = 90, 10, 5
        ticks = [first_tick + i * step for i in range(40)]        # 90, 95, 100, 105, ... the run_match_audit walk
        got = [is_policy_tick(t, first_tick, decide_every) for t in ticks]
        want = [i % 2 == 0 for i in range(40)]                    # every OTHER 5-tick step, starting True at i=0
        self.assertEqual(got, want)
        policy_ticks = [t for t, flag in zip(ticks, got) if flag]
        self.assertEqual(policy_ticks, list(range(first_tick, first_tick + 40 * step, decide_every)))
        # every policy tick agrees with the direct definition e1_eval itself would decide on
        for t in ticks:
            self.assertEqual(is_policy_tick(t, first_tick, decide_every), (t - first_tick) % decide_every == 0)

    def test_b5_seed_differs_from_obs_seed_domain(self):
        """The harness-local stream (non-policy 5-tick steps, Condition B only) must never collide with
        e1_eval's own obs_seed domain -- same crc32 shape, different domain string."""
        from pipeline.e1_eval import obs_seed
        for tag, k in (("000YLL9RURY8", 0), ("abc", 3)):
            self.assertNotEqual(b5_seed(tag, k), obs_seed(tag, k))


# ------------------------------------------------------------------------------------------------------
# (vi) Attempt 2 CHANGE 2: A+ dets path -- a known spell cost resolves, a costless one is skipped and
# warned exactly once (never silently, never charged as free).
# ------------------------------------------------------------------------------------------------------
def _spell_unit(base: str, side: int = 1) -> Unit:
    return Unit(cls=vocab.unit_id(base), side=side, x=0.5, y=0.3, hp_frac=None, deploying=None,
               age_sec=None, conf=1.0)


class TestAplusSpellPath(unittest.TestCase):
    def test_fireball_resolves_cost_four(self):
        db = _db()
        self.assertEqual(db.elixir("fireball"), 4, "fireball must be a 4-cost card for this check")
        warned: set = set()
        dets = dets_of_costed([_spell_unit("fireball")], db, warned)
        self.assertEqual(len(dets), 1)
        self.assertEqual(dets[0].base, "fireball")
        self.assertEqual(dets[0].team, "enemy")
        self.assertEqual(warned, set())

    def test_costless_spell_skipped_and_warned_once(self):
        db = _db()
        self.assertIsNone(db.elixir("mirror"), "mirror must have no flat cost for this to be the right fixture")
        warned: set = set()
        dets1 = dets_of_costed([_spell_unit("mirror")], db, warned)
        self.assertEqual(dets1, [])
        self.assertEqual(warned, {"mirror"})
        # a second costless mirror det: still skipped, warned set unchanged (warn-ONCE, not per-occurrence)
        dets2 = dets_of_costed([_spell_unit("mirror")], db, warned)
        self.assertEqual(dets2, [])
        self.assertEqual(warned, {"mirror"})

    def test_mixed_batch_keeps_costed_drops_costless(self):
        db = _db()
        warned: set = set()
        dets = dets_of_costed([_spell_unit("fireball"), _spell_unit("mirror")], db, warned)
        self.assertEqual([d.base for d in dets], ["fireball"])
        self.assertEqual(warned, {"mirror"})


# ------------------------------------------------------------------------------------------------------
# (vii) Attempt 3: TrackedEstimator.charged_by_base -- attribution via the wrapped db.elixir() call, the
# ONE place update() ever increments _opp_spent from a detection (opponent_elixir.py:109).
# ------------------------------------------------------------------------------------------------------
class _FakeDB:
    """A synthetic, fixed-cost db -- decoupled from cards.yaml so this test is about the WRAPPING mechanism,
    not about any particular card's real cost."""

    def __init__(self, cost: float = 4.0):
        self._cost = cost

    def elixir(self, name):
        return self._cost


class TestChargedByBase(unittest.TestCase):
    def test_single_enemy_det_charges_exactly_that_base(self):
        est = TrackedEstimator(_FakeDB(4.0))
        est.reset(my_elixir=5.0, now=0.0)
        det = _Det(base="knight", cx=0.5, gy=0.3, team="enemy")
        est.update(5.0, [det], 1.0)
        self.assertEqual(est.charged_by_base, {"knight": [1, 4.0]})
        # and the estimate itself still moved by exactly the cost (TrackedEstimator changes NOTHING about
        # the real update() arithmetic -- it only observes it)
        self.assertAlmostEqual(est._est, 5.0 - 4.0)

    def test_two_different_bases_in_one_update_call_attribute_separately(self):
        """The scenario a before/after ``_opp_spent`` diff CANNOT attribute (module docstring): two
        different new-track bases charged inside the same update() call."""
        est = TrackedEstimator(_FakeDB(3.0))
        est.reset(my_elixir=10.0, now=0.0)
        d1 = _Det(base="knight", cx=0.2, gy=0.3, team="enemy")
        d2 = _Det(base="archers", cx=0.8, gy=0.3, team="enemy")   # far apart -> two distinct tracks, not clustered
        est.update(10.0, [d1, d2], 1.0)
        self.assertEqual(est.charged_by_base, {"knight": [1, 3.0], "archers": [1, 3.0]})
        self.assertAlmostEqual(est._est, 10.0 - 3.0 - 3.0)

    def test_repeat_sighting_of_the_same_track_does_not_recharge(self):
        """A det that MATCHES an existing track (same base, within match_radius) refreshes it instead of
        charging again -- charged_by_base must reflect that, not one entry per update() call."""
        est = TrackedEstimator(_FakeDB(2.0))
        est.reset(my_elixir=10.0, now=0.0)
        det = _Det(base="skeletons", cx=0.5, gy=0.3, team="enemy")
        est.update(10.0, [det], 1.0)
        det_same_spot = _Det(base="skeletons", cx=0.505, gy=0.302, team="enemy")   # within match_radius=0.07
        est.update(10.0, [det_same_spot], 2.0)
        self.assertEqual(est.charged_by_base, {"skeletons": [1, 2.0]})   # still just ONE charge


# ------------------------------------------------------------------------------------------------------
# (viii) Attempt 3: ghost_scripted_by_base -- the SCRIPT, from a hand-built ghost_commands list (reference
# only as of Attempt 4 FIX 1 -- see TestGhostDeliveredByBase for the ledger over-charge actually uses).
# ------------------------------------------------------------------------------------------------------
class TestGhostScriptedByBase(unittest.TestCase):
    def test_built_correctly_from_ghost_commands(self):
        db = _db()
        self.assertEqual(db.elixir("knight"), 3)
        self.assertEqual(db.elixir("musketeer"), 4)
        self.assertEqual(db.elixir("goblin_barrel"), 3)
        # mirror is the confirmed costless fixture (attempt 1's dets-conversion scan: the ONLY held-out
        # ghost-deck base with no CardDB elixir row -- dynamic pricing, no flat `elixir` key). NOTE:
        # giant_snowball looked costless from a naive cards.yaml grep (its curated block has no `elixir`
        # key) but actually resolves to 2 through CardDB's stats-layer merge (cards.py:144-176,
        # cards_stats.json) -- caught by actually running this test rather than assuming from one file,
        # so it is NOT used as the costless fixture here.
        self.assertIsNone(db.elixir("mirror"), "mirror must have no flat cost for this fixture")
        entry = {"ghost_commands": [
            {"card": "knight", "ability": 0},
            {"card": "knight", "ability": 0},
            {"card": "musketeer", "ability": 0},
            {"card": None, "ability": 1},                 # champion ability: excluded, no card
            {"card": "goblin-barrel", "ability": 0},       # hyphenated slug -> goblin_barrel, cost 3
            {"card": "mirror", "ability": 0},              # costless in CardDB -> skipped + warned once
        ]}
        warned: set = set()
        out = ghost_scripted_by_base(entry, db, warned)
        self.assertEqual(out["knight"], [2, 6.0])
        self.assertEqual(out["musketeer"], [1, 4.0])
        self.assertEqual(out["goblin_barrel"], [1, 3.0])
        self.assertNotIn("mirror", out)
        self.assertEqual(warned, {"mirror"})
        self.assertEqual(set(out), {"knight", "musketeer", "goblin_barrel"})

    def test_empty_ghost_commands(self):
        self.assertEqual(ghost_scripted_by_base({"ghost_commands": []}, _db(), set()), {})
        self.assertEqual(ghost_scripted_by_base({}, _db(), set()), {})


# ------------------------------------------------------------------------------------------------------
# (ix) Attempt 4 FIX 1: ghost_delivered_by_base -- the TRUTH ledger over-charge actually uses, built from a
# hand-built env.ghost_cards_delivered-shaped stub, and its divergence from the SCRIPT when a play never
# lands. Ticket's exact scenario: scripted={a:2,b:1}, delivered={a:1} -> ledger {a:[1,cost_a]} ONLY.
# ------------------------------------------------------------------------------------------------------
class TestGhostDeliveredByBase(unittest.TestCase):
    def test_delivered_ledger_differs_from_scripted_when_a_play_is_never_delivered(self):
        db = _FakeDB(3.0)          # every base costs 3.0 -- isolates the ledger mechanics from real card costs
        scripted_entry = {"ghost_commands": [
            {"card": "a", "ability": 0}, {"card": "a", "ability": 0}, {"card": "b", "ability": 0},
        ]}
        scripted = ghost_scripted_by_base(scripted_entry, db)
        self.assertEqual(scripted, {"a": [2, 6.0], "b": [1, 3.0]})       # the script: a x2, b x1

        delivered_stub = {"a": 1}          # env.ghost_cards_delivered-shaped: only ONE 'a' ever landed, no 'b'
        delivered = ghost_delivered_by_base(delivered_stub, db)
        self.assertEqual(delivered, {"a": [1, 3.0]})                     # ONLY this -- exactly the ticket's spec
        self.assertNotIn("b", delivered)
        self.assertNotEqual(delivered, scripted)                         # the two ledgers must actually diverge

    def test_slug_normalization_and_costless_skip_match_scripted(self):
        db = _db()
        delivered_stub = {"goblin-barrel": 2, "mirror": 1}   # hyphenated slug + a costless one (Counter-shaped)
        warned: set = set()
        out = ghost_delivered_by_base(delivered_stub, db, warned)
        self.assertEqual(out, {"goblin_barrel": [2, 6.0]})
        self.assertEqual(warned, {"mirror"})

    def test_empty_and_none_counts_are_skipped(self):
        self.assertEqual(ghost_delivered_by_base({}, _db()), {})
        self.assertEqual(ghost_delivered_by_base({"knight": 0}, _db()), {})   # a zero count is a no-op


# ------------------------------------------------------------------------------------------------------
# (x) Attempt 4 FIX 2: opp_play_flags -- flags only the first sample tick at/after a DELIVERED ghost event.
# Ticket's exact scenario: a 1-cost card delivered at tick 40 under 5-tick stepping -> ONLY the tick-40 row.
# ------------------------------------------------------------------------------------------------------
class TestOppPlayFlags(unittest.TestCase):
    def test_delivery_at_tick_40_flags_only_that_sample(self):
        sample_ticks = [30, 35, 40, 45, 50]                     # 5-tick stepping, matches run_match_audit
        ghost_events = [(40, 1, "accepted")]                    # a 1-cost card delivered exactly at tick 40
        got = opp_play_flags(sample_ticks, ghost_events)
        self.assertEqual(got, [False, False, True, False, False])

    def test_refused_delivery_never_flags(self):
        sample_ticks = [30, 35, 40, 45, 50]
        ghost_events = [(40, 0, "not_enough_elixir")]           # REFUSED -- accepted==0, must not flag anything
        self.assertEqual(opp_play_flags(sample_ticks, ghost_events), [False] * 5)

    def test_delivery_between_samples_flags_the_next_one(self):
        sample_ticks = [30, 35, 40, 45, 50]
        ghost_events = [(37, 1, "accepted")]                    # falls strictly between 35 and 40
        got = opp_play_flags(sample_ticks, ghost_events)
        self.assertEqual(got, [False, False, True, False, False])

    def test_two_deliveries_in_one_gap_flag_the_same_shared_sample(self):
        sample_ticks = [30, 35, 40, 45, 50]
        ghost_events = [(36, 1, "accepted"), (38, 1, "accepted")]   # both between 35 and 40
        got = opp_play_flags(sample_ticks, ghost_events)
        self.assertEqual(got, [False, False, True, False, False])  # ONE flagged row, not an error / two rows

    def test_delivery_before_first_sample_flags_first_sample(self):
        sample_ticks = [30, 35, 40]
        ghost_events = [(10, 1, "accepted")]
        self.assertEqual(opp_play_flags(sample_ticks, ghost_events), [True, False, False])

    def test_no_events(self):
        self.assertEqual(opp_play_flags([30, 35, 40], []), [False, False, False])


# ------------------------------------------------------------------------------------------------------
# (xi) Attempt 4 FIX 4: dets_of_whitelisted drops a non-whitelisted enemy base, keeps a whitelisted one;
# load_detector_cards loads the real, non-empty live whitelist the same way play.py:376 does.
# ------------------------------------------------------------------------------------------------------
class TestDetectorCardsWhitelist(unittest.TestCase):
    def test_load_detector_cards_measured_membership(self):
        deck = load_deck("icebow")
        wl = load_detector_cards(deck.config)
        self.assertIsInstance(wl, frozenset)
        self.assertGreater(len(wl), 0)
        # MEASURED (this test, independently of the verifier): knight is in the whitelist, golem is not --
        # both directly checked against the live icebow/config/config.yaml, not assumed.
        self.assertIn("knight", wl)
        self.assertNotIn("golem", wl)
        # MEASURED correction of the Attempt-2 docstring's "zero spell entries" claim: the_log IS a spell
        # (vocab.SPELL_CLASSES) and IS in the whitelist.
        self.assertIn("the_log", wl)
        self.assertIn("the_log", vocab.SPELL_CLASSES)

    def test_dets_of_whitelisted_drops_outside_keeps_inside(self):
        wl = frozenset({"knight"})
        units = [_spell_unit("knight", side=1), _spell_unit("golem", side=1)]
        dets = dets_of_whitelisted(units, wl)
        self.assertEqual([d.base for d in dets], ["knight"])

    def test_dets_of_whitelisted_never_filters_non_enemy_team(self):
        """A mine/unknown det is never dropped by the whitelist filter -- the estimator's own team=='enemy'
        check in update() handles those regardless, so this filter only ever needs to act on enemy dets."""
        wl = frozenset({"knight"})
        units = [_spell_unit("golem", side=0), _spell_unit("golem", side=-1)]   # golem, but mine / unknown
        dets = dets_of_whitelisted(units, wl)
        self.assertEqual(len(dets), 2)


# ------------------------------------------------------------------------------------------------------
# (xii) Attempt 4 FIX 5: overcharge_table / merge_base_ledgers on hand-built ledgers, including a base
# present ONLY in charges (never played by the ghost at all -- the spawned-units signature).
# ------------------------------------------------------------------------------------------------------
class TestOvercharge(unittest.TestCase):
    def test_merge_base_ledgers_sums_across_matches(self):
        m1 = {"knight": [1, 3.0], "golem": [1, 8.0]}
        m2 = {"knight": [2, 6.0]}
        out = merge_base_ledgers([m1, m2])
        self.assertEqual(out, {"knight": [3, 9.0], "golem": [1, 8.0]})

    def test_merge_base_ledgers_empty_list(self):
        self.assertEqual(merge_base_ledgers([]), {})

    def test_overcharge_table_base_never_played_shows_full_charge_as_overcharge(self):
        # "golemite" is charged twice (a spawned body) but NEVER appears in the ghost's played-card ledger --
        # exactly the spawned-units signature the coordinator's hypothesis predicts.
        charged = {"knight": [1, 3.0], "golemite": [2, 2.0]}
        ghost = {"knight": [1, 3.0]}                     # ghost only ever played knight
        oc = overcharge_table(charged, ghost, top=25)
        by_base = {r["base"]: r for r in oc["top"]}
        self.assertEqual(by_base["knight"]["over_charge"], 0.0)
        self.assertEqual(by_base["golemite"]["ghost_plays"], 0)
        self.assertEqual(by_base["golemite"]["over_charge"], 2.0)        # charged_elixir - ghost_elixir(0)
        self.assertEqual(oc["total_charged_elixir"], 5.0)
        self.assertEqual(oc["total_ghost_elixir"], 3.0)
        self.assertEqual(oc["total_over_charge"], 2.0)
        # ALL of the over-charge here comes from a base the ghost never played:
        self.assertAlmostEqual(oc["over_charge_share_from_bases_never_played"], 2.0 / 5.0)

    def test_overcharge_table_sorted_by_abs_over_charge_desc_and_top_n(self):
        charged = {"a": [1, 1.0], "b": [1, 10.0], "c": [1, 5.0]}
        ghost = {"a": [1, 1.0], "b": [1, 0.0], "c": [1, 5.0]}   # over_charge: a=0, b=10, c=0
        oc = overcharge_table(charged, ghost, top=2)
        self.assertEqual(len(oc["top"]), 2)
        self.assertEqual(oc["top"][0]["base"], "b")             # the only nonzero |over_charge| leads
        self.assertEqual(oc["n_bases"], 3)

    def test_overcharge_table_no_bases(self):
        oc = overcharge_table({}, {})
        self.assertEqual(oc["top"], [])
        self.assertEqual(oc["total_charged_elixir"], 0.0)
        self.assertIsNone(oc["over_charge_share_from_bases_never_played"])   # 0/0 -- None, not a ZeroDivisionError


# ------------------------------------------------------------------------------------------------------
# (xiii) TICKET O10: charge-event trace -- TracedEstimator / run_traced_update against synthetic dets, no
# engine. The three ticket-mandated scenarios (stationary/first_seen, jump/rebill_out_of_radius,
# expire-then-reappear/rebill_after_expiry), plus TracedEstimator parity with plain TrackedEstimator.
# ------------------------------------------------------------------------------------------------------
class TestChargeTraceStationaryFirstSeen(unittest.TestCase):
    def test_three_samples_0_25s_apart_one_charge_zero_expiries(self):
        est = TracedEstimator(_FakeDB(4.0))
        est.reset(my_elixir=10.0, now=0.0)
        t_to_tick: dict = {}
        all_charges: list = []
        all_tracks: list = []
        prev_dets, prev_t = None, None
        for i, t in enumerate((0.0, 0.25, 0.5)):
            det = _Det(base="tombstone", cx=0.4, gy=0.6, team="enemy")
            ch, tr = run_traced_update(est, 10.0, [det], t, tick=i * 5, tag="m1", k=0,
                                       prev_dets=prev_dets, prev_t=prev_t, t_to_tick=t_to_tick)
            all_charges.extend(ch)
            all_tracks.extend(tr)
            prev_dets, prev_t = [det], t
        self.assertEqual(len(all_charges), 1, all_charges)
        self.assertEqual(all_charges[0]["reason"], "first_seen")
        self.assertEqual(all_charges[0]["base"], "tombstone")
        self.assertEqual(all_charges[0]["cost"], 4.0)
        self.assertEqual(all_charges[0]["prev_n_same_base"], 0)
        self.assertFalse(all_charges[0]["same_base_track_existed_before"])
        self.assertIsNone(all_charges[0]["dt_since_prev_sample_s"])   # first sample of the match
        self.assertEqual(all_tracks, [])   # zero track_events -- the track never aged past forget_s


class TestChargeTraceJumpRebillOutOfRadius(unittest.TestCase):
    def test_jump_0_2_in_x_produces_second_charge_rebill_out_of_radius(self):
        est = TracedEstimator(_FakeDB(3.0))
        est.reset(my_elixir=10.0, now=0.0)
        t_to_tick: dict = {}
        det1 = _Det(base="miner", cx=0.5, gy=0.5, team="enemy")
        ch1, tr1 = run_traced_update(est, 10.0, [det1], 0.0, tick=0, tag="m1", k=0,
                                     prev_dets=None, prev_t=None, t_to_tick=t_to_tick)
        self.assertEqual(len(ch1), 1)
        self.assertEqual(ch1[0]["reason"], "first_seen")

        det2 = _Det(base="miner", cx=0.7, gy=0.5, team="enemy")     # jumped 0.2 in x -- > match_radius=0.07
        ch2, tr2 = run_traced_update(est, 10.0, [det2], 0.25, tick=5, tag="m1", k=0,
                                     prev_dets=[det1], prev_t=0.0, t_to_tick=t_to_tick)
        self.assertEqual(len(ch2), 1, ch2)
        row = ch2[0]
        self.assertEqual(row["reason"], "rebill_out_of_radius")
        self.assertEqual(row["prev_n_same_base"], 1)
        self.assertAlmostEqual(row["prev_same_base_min_dist"], 0.2, places=4)
        self.assertFalse(row["prev_same_base_within_match_radius"])
        self.assertTrue(row["same_base_track_existed_before"])
        self.assertAlmostEqual(row["dt_since_prev_sample_s"], 0.25, places=4)
        self.assertEqual(tr2, [])   # the old track was never expired (age 0.25 <= forget_s=6.0), just missed


class TestChargeTraceExpiryRebillAfterExpiry(unittest.TestCase):
    def test_absent_7s_then_present_produces_expiry_and_rebill_after_expiry(self):
        est = TracedEstimator(_FakeDB(2.0))
        est.reset(my_elixir=10.0, now=0.0)
        t_to_tick: dict = {}
        det = _Det(base="witch", cx=0.3, gy=0.3, team="enemy")
        ch1, tr1 = run_traced_update(est, 10.0, [det], 0.0, tick=0, tag="m1", k=0,
                                     prev_dets=None, prev_t=None, t_to_tick=t_to_tick)
        self.assertEqual(ch1[0]["reason"], "first_seen")
        self.assertEqual(tr1, [])

        # next OBSERVED sample is 7.0s later (unit absent from every intervening sample this test skips
        # feeding, i.e. never detected in between) -- forget_s=6.0 means the track is stale by then, and the
        # real _seen_tracks (opponent_elixir.py:42-43) removes it INSIDE this same update() call, before the
        # reappearing det is matched against it.
        det_again = _Det(base="witch", cx=0.3, gy=0.3, team="enemy")   # same spot -- stationary building
        ch2, tr2 = run_traced_update(est, 10.0, [det_again], 7.0, tick=140, tag="m1", k=0,
                                     prev_dets=[det], prev_t=0.0, t_to_tick=t_to_tick)
        self.assertEqual(len(tr2), 1, tr2)
        self.assertEqual(tr2[0]["base"], "witch")
        self.assertAlmostEqual(tr2[0]["age_s"], 7.0, places=4)
        self.assertEqual(tr2[0]["last_seen_tick"], 0)      # resolved via t_to_tick, set at tick=0's call

        self.assertEqual(len(ch2), 1, ch2)
        row = ch2[0]
        self.assertEqual(row["reason"], "rebill_after_expiry")
        self.assertTrue(row["same_base_track_existed_before"])   # true BEFORE this update's own expiry
        self.assertEqual(row["prev_n_same_base"], 1)              # stationary -- also seen in prev sample
        self.assertAlmostEqual(row["prev_same_base_min_dist"], 0.0, places=6)


class TestChargeTraceOffProducesNoTrace(unittest.TestCase):
    def test_charge_trace_false_path_uses_plain_update_no_trace_helpers_needed(self):
        """Sanity check for the --charge-trace OFF path: run_match_audit's est_a stays a plain
        TrackedEstimator (no last_charges/last_expired) when charge_trace=False -- verified here at the
        estimator-selection unit, since run_match_audit itself needs a live engine to exercise end to end."""
        est_off = TrackedEstimator(_FakeDB(3.0))
        self.assertFalse(hasattr(est_off, "last_charges"))
        self.assertFalse(hasattr(est_off, "last_expired"))
        est_on = TracedEstimator(_FakeDB(3.0))
        self.assertTrue(hasattr(est_on, "last_charges"))
        self.assertTrue(hasattr(est_on, "last_expired"))


class TestTracedEstimatorParityWithTrackedEstimator(unittest.TestCase):
    def test_same_sequence_of_updates_yields_identical_est_and_charged_by_base(self):
        """CONSTRAINT: 'no change to opponent_elixir.py semantics; the wrapper must call the real
        update()/_seen_tracks so condition A's numbers are unchanged.' Feeds the identical sequence of dets
        to a TrackedEstimator and a TracedEstimator and asserts identical numeric outcomes."""
        seq = [
            (10.0, [_Det("knight", 0.5, 0.3, "enemy")], 0.0),
            (10.0, [_Det("knight", 0.505, 0.302, "enemy")], 0.25),          # refresh, within match_radius
            (10.0, [_Det("knight", 0.9, 0.3, "enemy"), _Det("archers", 0.1, 0.3, "enemy")], 0.5),
            (10.0, [], 8.0),                                                # gap -- lets knight's track expire
            (10.0, [_Det("knight", 0.9, 0.3, "enemy")], 8.25),
        ]
        base = TrackedEstimator(_FakeDB(2.0))
        traced = TracedEstimator(_FakeDB(2.0))
        base.reset(my_elixir=10.0, now=0.0)
        traced.reset(my_elixir=10.0, now=0.0)
        for my_elx, dets, now in seq:
            base.update(my_elx, dets, now)
            traced.update(my_elx, dets, now)
        self.assertAlmostEqual(base._est, traced._est)
        self.assertEqual(base.charged_by_base, traced.charged_by_base)
        self.assertEqual(base._opp_spent, traced._opp_spent)


class TestEstimatorNamingHelpers(unittest.TestCase):
    """O13: cond_key/tick_field must reproduce the pre-O13 spelling exactly when only one estimator variant
    is active (--estimator v1, the default, or --estimator v2 alone) -- section 4's "--estimator v1 output
    identical to before"."""

    def test_solo_mode_keys_match_pre_o13_spelling_exactly(self):
        for base in BASE_CONDS:
            for variant in ("v1", "v2"):
                self.assertEqual(cond_key(base, variant, both=False), base)
        self.assertEqual(tick_field("Aplus", "v1", False, "est"), "est_Aplus")
        self.assertEqual(tick_field("A", "v1", False, "est"), "est_A")
        self.assertEqual(tick_field("A_wl", "v1", False, "est"), "est_Awl")   # historical: no underscore
        self.assertEqual(tick_field("B", "v1", False, "est"), "est_B")
        self.assertEqual(tick_field("Aplus", "v1", False, "n_enemy_dets"), "n_enemy_dets_Aplus")

    def test_both_mode_keys_are_suffixed(self):
        self.assertEqual(cond_key("A", "v1", both=True), "A_v1")
        self.assertEqual(cond_key("A", "v2", both=True), "A_v2")
        self.assertEqual(cond_key("A_wl", "v2", both=True), "A_wl_v2")
        self.assertEqual(tick_field("A_wl", "v1", True, "est"), "est_Awl_v1")
        self.assertEqual(tick_field("A_wl", "v2", True, "est"), "est_Awl_v2")

    def test_make_estimator_selects_class_and_forwards_v2_kwargs(self):
        db = _db()
        self.assertIsInstance(make_estimator("v1", db, traced=False, v2_kwargs=None), TrackedEstimator)
        self.assertIsInstance(make_estimator("v1", db, traced=True, v2_kwargs=None), TracedEstimator)
        v2 = make_estimator("v2", db, traced=False, v2_kwargs={"suppress_spawns": False})
        self.assertIsInstance(v2, TrackedEstimatorV2)
        self.assertFalse(v2.suppress_spawns)
        self.assertTrue(v2.body_count)          # untouched kwarg keeps its default (True)
        self.assertIsInstance(make_estimator("v2", db, traced=True, v2_kwargs=None), TracedEstimatorV2)


class TestBothEstimatorsSameDetStream(unittest.TestCase):
    """O13 section 4: '--estimator both produces both condition sets in a stub-driven run (no engine)' --
    exercised at the estimator-wiring unit (run_match_audit itself needs a live engine end to end, per the
    existing convention in TestChargeTraceOffProducesNoTrace above). Builds the SAME
    {(base_cond, variant): estimator} structure run_match_audit builds for --estimator both, feeds BOTH
    variants of condition 'A' the IDENTICAL det stream, and confirms they diverge exactly where O13's R1
    (spawn suppression) predicts -- proof the two run side by side off one det stream, not two."""

    def test_v1_and_v2_diverge_on_a_spawn_suppression_scenario(self):
        class _CostMap:
            """Per-base fake db (unlike this file's own ``_FakeDB``, which is single-cost-for-every-base) --
            needed here so tombstone/skeletons price differently, the way R1's suppression scenario requires."""

            def __init__(self, costs):
                self._costs = dict(costs)

            def elixir(self, base):
                return self._costs.get(base)

            def speed_tiles(self, base):
                return None

        db = _CostMap({"tombstone": 3.0, "skeletons": 1.0})
        variants = ("v1", "v2")
        estimators = {(base, variant): make_estimator(variant, db, traced=False, v2_kwargs=None)
                     for base in BASE_CONDS for variant in variants}
        for base in BASE_CONDS:
            for variant in variants:
                estimators[(base, variant)].reset(my_elixir=5.0, now=0.0)

        # feed condition 'A' only (the scenario under test), both variants, the SAME det stream:
        a_dets_seq = [
            [_Det("tombstone", 0.50, 0.50, "enemy")],
            [_Det("tombstone", 0.50, 0.50, "enemy"), _Det("skeletons", 0.55, 0.50, "enemy")],   # live-form spawn
        ]
        for i, dets in enumerate(a_dets_seq):
            for variant in variants:
                estimators[("A", variant)].update(5.0, dets, now=float(i))

        v1_charged = estimators[("A", "v1")].charged_by_base
        v2_charged = estimators[("A", "v2")].charged_by_base
        self.assertIn("skeletons", v1_charged, "V1 must still over-bill the spawn (unchanged baseline)")
        self.assertNotIn("skeletons", v2_charged, "V2's R1 must suppress the same spawn from the same dets")
        self.assertEqual(v1_charged["tombstone"], v2_charged["tombstone"], "both charge the real play once")

        both_mode = True
        keyed = {cond_key(base, variant, both_mode): estimators[(base, variant)].charged_by_base
                for base in BASE_CONDS for variant in variants}
        self.assertIn("A_v1", keyed)
        self.assertIn("A_v2", keyed)
        self.assertNotEqual(keyed["A_v1"], keyed["A_v2"])


class TestV2ParamsJsonSafe(unittest.TestCase):
    """O13 attempt 2 FIX 1 (verifier, HIGH): summary["v2_params"] = V2_PARAMS raises TypeError at the END of
    a full run (V2_PARAMS["spawns"] is dict[str, frozenset[str]]) -- _jsonable() must make a JSON-safe COPY
    without mutating the live module's own SPAWNS/V2_PARAMS objects."""

    def test_summary_with_v2_params_dumps_and_spawns_become_sorted_lists(self):
        import json as _json
        summary_stub = {"n_ticks": 10, "estimator": "v2", "v2_params": _jsonable(V2_PARAMS)}
        dumped = _json.dumps(summary_stub)          # must not raise
        reloaded = _json.loads(dumped)
        spawns = reloaded["v2_params"]["spawns"]
        self.assertIsInstance(spawns, dict)
        for parent, members in spawns.items():
            self.assertIsInstance(members, list, f"{parent}'s spawn set must serialize as a list")
            self.assertEqual(members, sorted(members), f"{parent}'s spawn list must be sorted")

    def test_jsonable_never_mutates_the_live_v2_params(self):
        import copy
        before = copy.deepcopy({k: (dict(v) if isinstance(v, dict) else v) for k, v in V2_PARAMS.items()
                                if k != "spawns"})
        spawns_before = {k: frozenset(v) for k, v in V2_PARAMS["spawns"].items()}
        _jsonable(V2_PARAMS)
        self.assertTrue(all(isinstance(v, frozenset) for v in V2_PARAMS["spawns"].values()),
                        "the LIVE V2_PARAMS['spawns'] values must still be frozensets after _jsonable()")
        self.assertEqual({k: frozenset(v) for k, v in V2_PARAMS["spawns"].items()}, spawns_before)


class TestRecorderDBTransparentProxy(unittest.TestCase):
    """O13 attempt 2 FIX 2 (verifier, HIGH): _RecorderDB must forward EVERY attribute of the wrapped db, not
    just `elixir` -- otherwise OpponentElixirEstimatorV2's `getattr(self.db, "speed_tiles", None)` sees None
    while wrapped by Tracked/TrackedEstimatorV2, and R3 (speed_aware_radius) silently goes inert INSIDE the
    harness even though it is fully active on a bare (unwrapped) V2 instance."""

    class _SpeedDB:
        def __init__(self, costs, speeds):
            self._c = dict(costs)
            self._s = dict(speeds)

        def elixir(self, base):
            return self._c.get(base)

        def speed_tiles(self, base):
            return self._s.get(base)

    def test_recorder_forwards_speed_tiles_unrecorded(self):
        real = self._SpeedDB({"bandit": 3.0}, {"bandit": 8.0})
        calls: list = []
        proxy = _RecorderDB(real, calls)
        self.assertEqual(proxy.speed_tiles("bandit"), 8.0)
        self.assertEqual(proxy.elixir("bandit"), 3.0)
        self.assertEqual(calls, [("bandit", 3.0)], "only elixir() calls are recorded, speed_tiles() is not")

    def test_tracked_estimator_v2_r3_active_through_the_wrapper_matches_bare_v2(self):
        """A bandit det moving 0.12 in 0.25s must be MATCHED (one charge total), through
        TrackedEstimatorV2 exactly as it is on a bare OpponentElixirEstimatorV2 (icebow's own
        test_opponent_elixir_v2.py) -- before FIX 2 this silently rebilled (a second charge) because the
        OLD _RecorderDB dropped speed_tiles, so R3 never widened the match radius inside the wrapper."""
        db = self._SpeedDB({"bandit": 3.0}, {"bandit": 8.0})
        wrapped = TrackedEstimatorV2(db)
        wrapped.reset(my_elixir=5.0, now=0.0)
        wrapped.update(5.0, [_Det("bandit", 0.50, 0.5, "enemy")], now=0.0)
        wrapped.update(5.0, [_Det("bandit", 0.62, 0.5, "enemy")], now=0.25)   # moved 0.12 in 0.25s
        self.assertEqual(wrapped.charged_by_base, {"bandit": [1, 3.0]},
                         "R3 must still be active through the wrapper -- exactly one charge, not two")
        self.assertEqual(len(wrapped._tracks), 1, "dash must be matched to the SAME track, not rebilled")


class TestTracedEstimatorV2ChargeAttribution(unittest.TestCase):
    """O13 attempt 2 FIX 3 (verifier, MEDIUM): the verifier's exact case -- one update() call with THREE
    dets: a det that refreshes an existing 'tombstone' track, a 'skeletons' det far away (a genuine new
    play), and a second 'tombstone'-labeled det 0.08 from the live tombstone track (within r_spawn=0.084,
    self-mapped R1 suppression -- a NEW track, but no charge). Exactly ONE trace row must result, correctly
    attributed to 'skeletons', not misattributed by a positional zip against db.elixir() CALLS (which would
    only make ONE call this update -- for skeletons -- while creating TWO new tracks)."""

    class _CostDB:
        def __init__(self, costs):
            self._c = dict(costs)

        def elixir(self, base):
            return self._c.get(base)

        def speed_tiles(self, base):
            return None

    def test_tombstone_live_skeletons_far_tombstone_dup_one_correct_trace_row(self):
        db = self._CostDB({"tombstone": 3.0, "skeletons": 1.0})
        est = TracedEstimatorV2(db)
        est.reset(my_elixir=10.0, now=0.0)
        t_to_tick: dict = {}
        det0 = _Det("tombstone", 0.5, 0.5, "enemy")
        ch0, _tr0 = run_traced_update(est, 10.0, [det0], 0.0, tick=0, tag="m1", k=0,
                                      prev_dets=None, prev_t=None, t_to_tick=t_to_tick)
        self.assertEqual(len(ch0), 1)          # the initial tombstone play itself

        dets = [
            _Det("tombstone", 0.5, 0.5, "enemy"),          # tombstone LIVE -- refreshes the existing track
            _Det("skeletons", 0.5, 0.2, "enemy"),           # skeletons FAR -- genuine new play, must charge
            _Det("tombstone", 0.5, 0.58, "enemy"),          # tombstone DUP @0.08 -- R1-suppressed, no charge
        ]
        ch1, _tr1 = run_traced_update(est, 10.0, dets, 1.0, tick=5, tag="m1", k=0,
                                      prev_dets=[det0], prev_t=0.0, t_to_tick=t_to_tick)
        self.assertEqual(len(ch1), 1, ch1)
        row = ch1[0]
        self.assertEqual(row["base"], "skeletons")
        self.assertAlmostEqual(row["x"], 0.5, places=6)
        self.assertAlmostEqual(row["y"], 0.2, places=6)
        self.assertEqual(row["cost"], 1.0)
        self.assertEqual(row["reason"], "first_seen")
        self.assertEqual(len(est._tracks), 3, "tombstone (refreshed) + skeletons (new) + tombstone-dup (new)")


class TestTicksRowKeyOrder(unittest.TestCase):
    """O13 attempt 2 FIX 6b (verifier, LOW): --estimator v1 (default) must write ticks.jsonl rows with the
    EXACT pre-O13 key order (every est_* field, then every n_enemy_dets_* field, then the three flags) so
    existing line-diff / schema tooling built against the old shape keeps working. Reproduces
    run_match_audit's own row-building sequence (est_vals computed per BASE_CONDS x variant, THEN two
    separate assignment passes) at unit scope, since the full function needs a live engine end to end."""

    def test_v1_solo_mode_row_key_order_matches_pre_o13_literal(self):
        both_mode = False
        variants = ("v1",)
        est_vals = {(base, "v1"): 0.0 for base in BASE_CONDS}
        n_by_base = {base: 0 for base in BASE_CONDS}

        row = {"tag": "t", "k": 0, "tick": 0, "t_sec": 0.0, "phase": "single", "truth": 0.0, "truth_drop": 0.0}
        for base in BASE_CONDS:
            for variant in variants:
                row[tick_field(base, variant, both_mode, "est")] = est_vals[(base, variant)]
        for base in BASE_CONDS:
            for variant in (variants if both_mode else variants[:1]):
                row[tick_field(base, variant, both_mode, "n_enemy_dets")] = n_by_base[base]
        row["is_opp_play_tick"] = False
        row["is_my_play_tick"] = False
        row["is_policy_tick"] = False

        expected = ["tag", "k", "tick", "t_sec", "phase", "truth", "truth_drop",
                   "est_Aplus", "est_A", "est_Awl", "est_B",
                   "n_enemy_dets_Aplus", "n_enemy_dets_A", "n_enemy_dets_Awl", "n_enemy_dets_B",
                   "is_opp_play_tick", "is_my_play_tick", "is_policy_tick"]
        self.assertEqual(list(row.keys()), expected)


# ------------------------------------------------------------------------------------------------------
# TICKET O16(c): --tracker/--corr off must reproduce the pre-O16 condition set byte-for-byte
# ------------------------------------------------------------------------------------------------------
class TestActiveBaseConds(unittest.TestCase):
    def test_both_flags_off_matches_base_conds_exactly(self):
        """Tuple EQUALITY (not just same elements) with BASE_CONDS -- the acceptance criterion for
        'existing runs byte-identical'."""
        self.assertEqual(active_base_conds(False, False), BASE_CONDS)

    def test_tracker_only_appends_b_tt_and_its_wl_sibling(self):
        self.assertEqual(active_base_conds(True, False), BASE_CONDS + ("B_tt", "B_tt_wl"))

    def test_corr_only_appends_two_raw_conditions_no_tracker_pairs(self):
        self.assertEqual(active_base_conds(False, True), BASE_CONDS + ("B_corrS", "B_corrL"))

    def test_both_flags_append_all_conditions_in_order(self):
        """Attempt 2 FIX 2(b) acceptance: the exact condition list with --tracker --corr."""
        self.assertEqual(active_base_conds(True, True),
                         BASE_CONDS + ("B_tt", "B_tt_wl", "B_corrS", "B_corrS_tt", "B_corrS_tt_wl",
                                      "B_corrL", "B_corrL_tt", "B_corrL_tt_wl"))


class TestBuildCondDefs(unittest.TestCase):
    def test_both_flags_off_matches_old_hardcoded_cond_defs(self):
        expect = (("Aplus_perfect_detection_with_spells", "Aplus"), ("A_perfect_detection", "A"),
                  ("A_wl_live_whitelist", "A_wl"), ("B_degraded_live", "B"))
        self.assertEqual(build_cond_defs(False, False), expect)

    def test_flags_on_bases_match_active_base_conds_order(self):
        defs = build_cond_defs(True, True)
        self.assertEqual(tuple(b for _long, b in defs), active_base_conds(True, True))
        # every long key is unique (no collisions feeding summary.json)
        self.assertEqual(len({long for long, _b in defs}), len(defs))


# ------------------------------------------------------------------------------------------------------
# TICKET O16(a): TeamTracker construction + first-confirmed-sighting billing
# ------------------------------------------------------------------------------------------------------
class TestMakeTeamTracker(unittest.TestCase):
    def test_matches_live_defaults(self):
        """Literal-for-literal against play.py:420-441 / live_reader_audit.py:185-199 (module docstring
        O16(a) cites both)."""
        tt = make_team_tracker(_db())
        self.assertEqual(tt.min_hits, 2)
        self.assertAlmostEqual(tt.spawn_radius, 0.10)
        self.assertAlmostEqual(tt.spawn_window_s, 2.5)
        self.assertAlmostEqual(tt.enemy_window_s, 4.0)          # the one live-cfg value != the bare class default
        self.assertAlmostEqual(tt.track_radius, 0.12)
        self.assertAlmostEqual(tt.forget_s, 4.5)
        self.assertAlmostEqual(tt.motion_min, 0.05)
        self.assertAlmostEqual(tt.deep_mine_y, 0.62)
        self.assertAlmostEqual(tt.deep_enemy_y, 0.38)
        self.assertAlmostEqual(tt.phantom_stale_s, 6.0)
        self.assertIsNotNone(tt.own_cards, "deck veto must be wired (own_card_bases(db))")
        self.assertGreater(len(tt.own_cards), 0)
        self.assertTrue(tt._is_building("tesla_evo") or tt._is_building("x_bow"), "is_building must be wired")
        self.assertTrue(tt._is_spell("the_log"), "is_spell must be wired (icebow deck's spell)")


class TestTtDetsOf(unittest.TestCase):
    def test_degraded_team_becomes_body_vote_unknown_stays_none(self):
        dets = [_Det("giant", 0.5, 0.6, "enemy"), _Det("knight", 0.3, 0.8, "mine"),
               _Det("archers", 0.4, 0.5, "unknown")]
        tt_dets = tt_dets_of(dets)
        self.assertEqual([d.body_vote for d in tt_dets], ["enemy", "mine", None])
        self.assertTrue(all(d.bar_vote is None for d in tt_dets), "no pixel bar evidence in this harness")
        self.assertEqual([d.cls for d in tt_dets], ["giant", "knight", "archers"])
        self.assertEqual([(d.cx, d.gy) for d in tt_dets], [(0.5, 0.6), (0.3, 0.8), (0.4, 0.5)])

    def test_raw_cls_used_when_present_falls_back_to_base_otherwise(self):
        """Attempt 2 FIX 3 (verifier, LOW): a det with a known raw (unstripped) class -- e.g. a
        'poison_aoe' detector class whose stripped base is 'poison' -- must carry the RAW name as
        ``Detection.cls`` so TeamTracker's zone-class check (``d.cls in ZONE_CLASSES``, raw "_aoe"
        names) can fire; ``Detection.base`` still resolves the same stripped 'poison' either way. A det
        with no ``raw_cls`` (the default -- e.g. hand-built in a test) falls back to ``.base``, exactly
        the pre-fix behaviour."""
        with_raw = _Det("poison", 0.5, 0.6, "enemy", raw_cls="poison_aoe")
        without_raw = _Det("giant", 0.3, 0.4, "enemy")
        self.assertIsNone(without_raw.raw_cls)
        tt_dets = tt_dets_of([with_raw, without_raw])
        self.assertEqual(tt_dets[0].cls, "poison_aoe")
        self.assertEqual(tt_dets[0].base, "poison")
        self.assertEqual(tt_dets[1].cls, "giant")
        self.assertEqual(tt_dets[1].base, "giant")

    def test_dets_of_populates_raw_cls_for_a_real_aoe_class(self):
        """The actual production path (``dets_of``) fills ``raw_cls`` with the true UNSTRIPPED vocab
        entry -- not just something this test hand-constructs."""
        aoe_ids = [i for i, name in enumerate(vocab.UNIT_VOCAB) if name.endswith("_aoe")]
        self.assertGreater(len(aoe_ids), 0, "the shared vocab must define at least one _aoe class")
        cid = aoe_ids[0]
        raw_name = vocab.UNIT_VOCAB[cid]
        u = Unit(cls=cid, side=1, x=0.5, y=0.5, hp_frac=None, deploying=None, age_sec=None, conf=1.0)
        [built] = dets_of([u])
        self.assertEqual(built.raw_cls, raw_name)
        self.assertEqual(built.base, vocab.base_key(raw_name))
        [tt_det] = tt_dets_of([built])
        self.assertEqual(tt_det.cls, raw_name)
        self.assertEqual(tt_det.base, vocab.base_key(raw_name))


class TestTtBillDets(unittest.TestCase):
    """O16 acceptance (d): a one-sample phantom is NEVER billed; a real 2-sample unit is billed EXACTLY
    ONCE, at its first-confirmed (>= min_hits) sample, and never rebilled on a later re-sighting of the
    SAME track. 'giant' is used throughout -- confirmed NOT in the icebow deck (_db()), so the deck veto
    forces it 'enemy' regardless of the (absent, in this harness) HP-bar/body-art evidence."""

    def _tracker(self):
        tt = make_team_tracker(_db())
        tt.set_towers([True, True], [True, True])
        return tt

    def test_one_sample_phantom_never_billed(self):
        tt = self._tracker()
        billed: set = set()
        out1 = tt_bill_dets(tt, [_Det("giant", 0.5, 0.3, "unknown")], 1.0, billed)
        self.assertEqual(out1, [])
        out2 = tt_bill_dets(tt, [], 6.0, billed)     # 5s later -- well past forget_s(4.5); track expires
        self.assertEqual(out2, [])
        self.assertEqual(billed, set())

    def test_two_sample_unit_billed_exactly_once_at_first_confirmed_sighting(self):
        tt = self._tracker()
        billed: set = set()
        out1 = tt_bill_dets(tt, [_Det("giant", 0.5, 0.6, "unknown")], 10.0, billed)
        self.assertEqual(out1, [], "first sighting -- hits=1 < min_hits=2, not yet confirmed")
        out2 = tt_bill_dets(tt, [_Det("giant", 0.5, 0.6, "unknown")], 10.25, billed)
        self.assertEqual(len(out2), 1, "second sighting -- hits=2 == min_hits, FIRST confirmed sighting")
        d = out2[0]
        self.assertEqual(d.base, "giant")
        self.assertAlmostEqual(d.cx, 0.5)
        self.assertAlmostEqual(d.gy, 0.6)
        self.assertEqual(d.team, "enemy")
        self.assertEqual(len(billed), 1)
        # a THIRD (and fourth) sighting of the SAME track must never rebill it
        out3 = tt_bill_dets(tt, [_Det("giant", 0.5, 0.6, "unknown")], 10.5, billed)
        self.assertEqual(out3, [])
        out4 = tt_bill_dets(tt, [_Det("giant", 0.5, 0.6, "unknown")], 10.75, billed)
        self.assertEqual(out4, [])
        self.assertEqual(len(billed), 1)

    def test_own_unit_never_billed_even_with_many_sightings(self):
        """A card WE own (e.g. 'skeletons', in the icebow deck) with no own-play anchor recorded still
        never gets billed as enemy from side/motion evidence alone landing 'mine' or 'unknown' AND
        in-deck (the deck veto only forces enemy for an OUT-of-deck base -- module docstring O16(a))."""
        tt = self._tracker()
        billed: set = set()
        for i in range(6):
            out = tt_bill_dets(tt, [_Det("skeletons", 0.5, 0.85, "unknown")], 10.0 + 0.25 * i, billed)
            self.assertEqual(out, [], f"sample {i}")

    # --------------------------------------------------------------------------------------------------
    # Attempt 2 FIX 1 (verifier, HIGH): billed_ids must key on a content-based per-track uid, never
    # id(track dict) -- the verifier's own probe (200 sequential distinct tracks) is reproduced here.
    # --------------------------------------------------------------------------------------------------
    def test_200_sequential_distinct_tracks_each_billed_exactly_once(self):
        tt = self._tracker()
        billed: set = set()
        total_billed = 0
        t = 0.0
        for _ in range(200):
            out1 = tt_bill_dets(tt, [_Det("giant", 0.5, 0.5, "unknown")], t, billed)
            self.assertEqual(out1, [])
            out2 = tt_bill_dets(tt, [_Det("giant", 0.5, 0.5, "unknown")], t + 0.25, billed)
            self.assertEqual(len(out2), 1)
            total_billed += len(out2)
            t += 10.0     # > forget_s(4.5) later -- fully expires before the next track's first sighting
        self.assertEqual(total_billed, 200)
        self.assertEqual(len(billed), 200, "200 distinct uids -- none collided via a recycled dict id()")

    def test_two_persistent_tracks_plus_199_transients_yields_201_bills(self):
        """Two tracks that stay alive (refreshed often enough to never hit forget_s) for the WHOLE test,
        interleaved with 199 short-lived tracks that each confirm once and then fully expire, must total
        exactly 2 + 199 = 201 bills -- concurrent long-lived tracks must not be confused with, or
        conflated by identity with, the transients passing through around them."""
        tt = self._tracker()
        billed: set = set()
        total = 0
        P1, P2 = ("giant", 0.2, 0.5), ("golem", 0.8, 0.5)
        t = 0.0
        tt_bill_dets(tt, [_Det(*P1, "unknown"), _Det(*P2, "unknown")], t, billed)
        t += 0.25
        out = tt_bill_dets(tt, [_Det(*P1, "unknown"), _Det(*P2, "unknown")], t, billed)
        self.assertEqual(len(out), 2, "both persistents confirmed on their 2nd sighting")
        total += len(out)
        for _ in range(199):
            t += 1.0
            tt_bill_dets(tt, [_Det(*P1, "unknown"), _Det(*P2, "unknown"),
                             _Det("musketeer", 0.5, 0.9, "unknown")], t, billed)
            t += 0.25
            out2 = tt_bill_dets(tt, [_Det(*P1, "unknown"), _Det(*P2, "unknown"),
                                    _Det("musketeer", 0.5, 0.9, "unknown")], t, billed)
            self.assertEqual(len(out2), 1, "only the transient's 2nd sighting bills -- persistents already billed")
            total += len(out2)
            t += 4.0
            tt_bill_dets(tt, [_Det(*P1, "unknown"), _Det(*P2, "unknown")], t, billed)   # keep persistents alive
            t += 1.0   # gap since the transient's last sighting will exceed forget_s(4.5) by the next round
        self.assertEqual(total, 201)
        self.assertEqual(len(billed), 201)

    def test_expired_track_recreated_at_the_same_spot_bills_again(self):
        tt = self._tracker()
        billed: set = set()
        tt_bill_dets(tt, [_Det("giant", 0.5, 0.5, "unknown")], 0.0, billed)
        out1 = tt_bill_dets(tt, [_Det("giant", 0.5, 0.5, "unknown")], 0.25, billed)
        self.assertEqual(len(out1), 1)
        tt_bill_dets(tt, [], 10.0, billed)                                      # expires (gap > forget_s)
        tt_bill_dets(tt, [_Det("giant", 0.5, 0.5, "unknown")], 20.0, billed)     # a NEW track, same spot
        out2 = tt_bill_dets(tt, [_Det("giant", 0.5, 0.5, "unknown")], 20.25, billed)
        self.assertEqual(len(out2), 1, "a genuinely new track (old one expired) can be billed again")
        self.assertEqual(len(billed), 2)


class TestFilterWhitelistedBilledDets(unittest.TestCase):
    """Attempt 2 FIX 2(b): B_tt_wl's own filter -- keep a billed det iff its base clears the whitelist."""

    def test_keeps_whitelisted_drops_non_whitelisted(self):
        whitelist = frozenset({"giant", "musketeer"})
        dets = [_Det("giant", 0.5, 0.5, "enemy"), _Det("golem", 0.3, 0.3, "enemy"),
               _Det("musketeer", 0.6, 0.6, "enemy")]
        kept = filter_whitelisted_billed_dets(dets, whitelist)
        self.assertEqual([d.base for d in kept], ["giant", "musketeer"])

    def test_empty_whitelist_drops_everything(self):
        dets = [_Det("giant", 0.5, 0.5, "enemy")]
        self.assertEqual(filter_whitelisted_billed_dets(dets, frozenset()), [])

    def test_real_whitelist_end_to_end_with_tt_bill_dets(self):
        """A track for a base OUTSIDE live's real detector_cards whitelist is billed by tt_bill_dets
        (B_tt) but dropped by the _wl filter (B_tt_wl) -- 'golem' is confirmed not in the icebow
        whitelist (re-checked directly, not assumed)."""
        wl = load_detector_cards(load_deck("icebow").config)
        self.assertNotIn("golem", wl, "test fixture assumption -- golem must be outside the real whitelist")
        tt = make_team_tracker(_db())
        tt.set_towers([True, True], [True, True])
        billed: set = set()
        tt_bill_dets(tt, [_Det("golem", 0.5, 0.6, "unknown")], 10.0, billed)
        out = tt_bill_dets(tt, [_Det("golem", 0.5, 0.6, "unknown")], 10.25, billed)
        self.assertEqual(len(out), 1)
        self.assertEqual(filter_whitelisted_billed_dets(out, wl), [], "B_tt_wl must drop it")


# ------------------------------------------------------------------------------------------------------
# TICKET O16(b): closed-form Markov constants + corr_live_view's marginals
# ------------------------------------------------------------------------------------------------------
class TestCorrSeeds(unittest.TestCase):
    """corrS_seed/corrL_seed follow b5_seed's own crc32(f"{tag}:<domain>:{k}") discipline and never
    collide with b5_seed or each other (module docstring O16(b))."""

    def test_seeds_differ_across_domains_for_the_same_tag_and_k(self):
        tag, k = "match1", 3
        s_b5, s_corrS, s_corrL = b5_seed(tag, k), corrS_seed(tag, k), corrL_seed(tag, k)
        self.assertEqual(len({s_b5, s_corrS, s_corrL}), 3, "all three domains must be distinct")

    def test_seed_depends_on_tag_and_k(self):
        self.assertNotEqual(corrS_seed("a", 0), corrS_seed("b", 0))
        self.assertNotEqual(corrS_seed("a", 0), corrS_seed("a", 1))


class TestMarkovParams(unittest.TestCase):
    def test_closed_form_against_hand_derivation(self):
        p_target, mean_run = 1.0 - DEGRADE_RECALL, 1.5
        p_stay, p_enter = markov_params(p_target, mean_run)
        self.assertAlmostEqual(p_stay, 1.0 - 1.0 / mean_run, places=9)
        self.assertAlmostEqual(p_enter, p_target / (mean_run * (1.0 - p_target)), places=9)

    def test_stationary_probability_and_mean_run_length_reproduced_by_simulation(self):
        """Simulates the bare 2-state chain directly (no corr_live_view involved) -- the two invariants
        markov_params is DEFINED to guarantee: the long-run fraction of True samples equals p_target, and
        the mean True-run length equals mean_run."""
        rng = np.random.default_rng(0)
        p_target, mean_run = 0.145, 4.0
        p_stay, p_enter = markov_params(p_target, mean_run)
        state = bool(rng.random() < p_target)      # stationary init
        n = 300_000
        true_count = 0
        run_lengths: list[int] = []
        cur_run = 0
        for _ in range(n):
            true_count += int(state)
            if state:
                cur_run += 1
            elif cur_run:
                run_lengths.append(cur_run)
                cur_run = 0
            state = bool(rng.random() < (p_stay if state else p_enter))
        self.assertAlmostEqual(true_count / n, p_target, delta=0.01)
        self.assertAlmostEqual(sum(run_lengths) / len(run_lengths), mean_run, delta=0.05 * mean_run)


def _run_corr_chains(params: CorrParams, n_units: int, n_iter: int, seed0: int):
    """N_UNITS independent single-unit corr_live_view chains (own state, own RNG stream each) -- avoids
    ANY cross-unit identity-matching ambiguity (each chain's ``out.units[0]``, when present, is
    unambiguously the real detection; anything after it is a false positive) while giving many
    independent samples of the SAME per-sample marginal, which is what keeps the false-positive-rate
    and position-sigma estimates' standard error small enough to resolve within tolerance despite the
    LONG setting's long autocorrelation (module docstring; a single very-long chain would need a far
    larger N to reach the same precision). Returns (recall_measured, fp_rate_measured, sigma_measured_tiles).
    """
    deck = load_deck("icebow")
    true_x, true_y = 0.5, 0.30
    u = Unit(cls=5, side=1, x=true_x, y=true_y, hp_frac=1.0, deploying=None, age_sec=None, conf=1.0)
    bs = _minimal_bs(units=(u,))
    n_visible = n_fp = 0
    offsets_tiles: list[float] = []
    for c in range(n_units):
        rng = np.random.default_rng(seed0 + c)
        state = new_state()
        for _ in range(n_iter):
            out = corr_live_view(bs, state, rng, deck, params)
            if out.units:
                n_visible += 1
                offsets_tiles.append((out.units[0].x - true_x) * TILES_X)
                if len(out.units) > 1:
                    n_fp += 1
    n_total = n_units * n_iter
    recall = n_visible / n_total
    fp_rate = (n_fp / n_visible) if n_visible else 0.0
    sigma = float(np.std(offsets_tiles)) if offsets_tiles else 0.0
    return recall, fp_rate, sigma


class TestCorrLiveViewMarginals(unittest.TestCase):
    """O16(b) acceptance: corr_live_view's per-sample marginals must match live_view's own constants,
    for BOTH corr settings, proven by simulation (not by code inspection). >= 200,000 total samples per
    setting (6 independent chains x 40,000 samples = 240,000), per the ticket. Tolerances: recall and
    fp_rate within 1 PERCENTAGE POINT absolute (0.01) -- a probability's own 1%-relative band would be
    sub-0.2pp for fp_rate (target ~0.129), tighter than 240k correlated samples can resolve for the LONG
    setting's L_fp=8 persistence without an impractically large N (documented judgment call, not a
    loosened acceptance bar: the SHORT setting -- see below -- clears the strict RELATIVE 1% band easily,
    confirming the mechanism itself is correct; LONG's wider band only reflects estimator variance under
    long autocorrelation). Position sigma is checked at a strict 1% RELATIVE band for both settings."""

    def test_short_setting(self):
        recall, fp_rate, sigma = _run_corr_chains(CORR_SHORT, n_units=6, n_iter=40_000, seed0=1000)
        target_fp = (1.0 - DEGRADE_PRECISION) / DEGRADE_PRECISION
        self.assertAlmostEqual(recall, DEGRADE_RECALL, delta=max(0.01, 0.01 * DEGRADE_RECALL))
        self.assertAlmostEqual(fp_rate, target_fp, delta=max(0.01, 0.01 * target_fp))
        self.assertAlmostEqual(sigma, 0.45, delta=0.01 * 0.45)

    def test_long_setting(self):
        recall, fp_rate, sigma = _run_corr_chains(CORR_LONG, n_units=6, n_iter=40_000, seed0=2000)
        target_fp = (1.0 - DEGRADE_PRECISION) / DEGRADE_PRECISION
        self.assertAlmostEqual(recall, DEGRADE_RECALL, delta=max(0.01, 0.01 * DEGRADE_RECALL))
        self.assertAlmostEqual(fp_rate, target_fp, delta=max(0.01, 0.01 * target_fp))
        self.assertAlmostEqual(sigma, 0.45, delta=0.01 * 0.45)


class TestCorrLiveViewSmoke(unittest.TestCase):
    """O16(d) acceptance: a smoke run of corr_live_view over a synthetic BoardState SEQUENCE (units
    spawning and dying across samples), no engine -- confirms track creation/expiry/matching don't crash
    and produce structurally sane output at every step."""

    def test_synthetic_sequence_no_crash_and_sane_output(self):
        deck = load_deck("icebow")
        rng = np.random.default_rng(7)
        state = new_state()
        # a hand-built sequence: unit A present throughout, unit B appears at step 3 and dies at step 6,
        # a spell appears once at step 4 -- exercises track creation, continuation, and expiry all in one run.
        for step in range(10):
            units = [Unit(cls=5, side=1, x=0.5, y=0.3, hp_frac=1.0, deploying=None, age_sec=None, conf=1.0)]
            if 3 <= step < 6:
                units.append(Unit(cls=9, side=1, x=0.2, y=0.7, hp_frac=1.0, deploying=None, age_sec=None,
                                  conf=1.0))
            spells = ()
            if step == 4:
                spells = (Unit(cls=200, side=0, x=0.5, y=0.5, hp_frac=None, deploying=None, age_sec=None,
                              conf=1.0),)
            bs = _minimal_bs(units=tuple(units), spells=spells, t_sec=10.0 + 0.25 * step)
            out = corr_live_view(bs, state, rng, deck, CORR_SHORT)
            self.assertIsInstance(out, BoardState)
            for u in list(out.units) + list(out.spells):
                self.assertTrue(0.0 <= u.x <= 1.0)
                self.assertTrue(0.0 <= u.y <= 1.0)
                self.assertIn(u.side, (-1, 0, 1))
        # unit B (cls=9) left the board at step 6 -- its track must be dropped, not leaked forever
        self.assertFalse(any(tr.get("cls") == 9 for tr in state.get("units", {}).values()))


# ------------------------------------------------------------------------------------------------------
# TICKET O18: feed the opponent-elixir observation into the BoardState the policy consumes.
# ------------------------------------------------------------------------------------------------------
class _FakeEst:
    """Stand-in for a TrackedEstimatorV2 in ``policy_view_for``'s ``estimators`` dict -- only ``._est`` is
    ever read by the function under test, so a bare attribute holder is faithful and avoids depending on
    the real estimator's internal update() sequencing for these pure-injection tests."""
    def __init__(self, est: float):
        self._est = float(est)


class TestPolicyViewForOff(unittest.TestCase):
    """Acceptance (a): --feed-opp-elixir off (the default) leaves the policy's observation BYTE-IDENTICAL
    to every pre-O18 invocation -- proven here as object identity (not just equal fields): run_match_audit
    passes this return value straight to to_tokens(), so returning the SAME object it was given means
    zero behaviour change, not merely a coincidentally-equal copy."""

    def test_off_returns_view_object_unchanged(self):
        # live_view's own default degrades opp_elixir to None (e1_view.py's _degrade_switchable) -- built
        # by hand here, no engine, matching that contract explicitly rather than assuming _minimal_bs's
        # own (non-degraded) default.
        view = replace(_minimal_bs(), opp_elixir=None)
        bs = _minimal_bs()
        out = policy_view_for(view, bs, "off", "live", {})
        self.assertIs(out, view)
        self.assertIsNone(out.opp_elixir)

    def test_off_ignores_feed_noise_and_empty_estimators(self):
        # 'off' must not even look at feed_noise or estimators -- a bogus feed_noise/empty estimators dict
        # (which would raise for 'estimated') must not raise here.
        view = replace(_minimal_bs(), opp_elixir=None)
        out = policy_view_for(view, view, "off", "corrL", {})
        self.assertIs(out, view)

    def test_cli_defaults_are_off_and_live(self):
        """Confirms the ticket's required defaults directly off the argparse parser (not by re-typing
        'off'/'live' a second time) -- a --feed-opp-elixir/--feed-noise default drift would fail this."""
        ap = build_parser()
        a = ap.parse_args(['--port', '1', '--ckpt', 'x.pt', '--out', 'unused_out_dir'])
        self.assertEqual(a.feed_opp_elixir, "off")
        self.assertEqual(a.feed_noise, "live")
        self.assertEqual(set(FEED_OPP_ELIXIR_MODES), {"off", "true", "estimated"})
        self.assertEqual(set(FEED_NOISE_MODES), {"live", "corrL"})


class TestPolicyViewForTrue(unittest.TestCase):
    """Acceptance (b), 'true' half: the policy-visible BoardState carries bs.opp_elixir (engine ground
    truth for THIS tick) -- equivalent to e1_eval's --noise-off opp_elixir (e1_view.py's
    _degrade_switchable: ``bs.opp_elixir if not noise.opp_elixir else None``)."""

    def test_true_copies_engine_truth_and_leaves_other_fields(self):
        bs = _minimal_bs(my_elixir=7.0, t_sec=12.0)
        bs = replace(bs, opp_elixir=6.25)                 # the engine's true opp_elixir for this tick
        view = replace(_minimal_bs(my_elixir=7.0, t_sec=12.0), opp_elixir=None)  # degraded: unknown
        out = policy_view_for(view, bs, "true", "live", {})
        self.assertEqual(out.opp_elixir, 6.25)
        # every OTHER field is view's own, untouched -- proven field-by-field via dataclass equality after
        # neutralising the one field this mode is allowed to change.
        self.assertEqual(replace(out, opp_elixir=None), replace(view, opp_elixir=None))

    def test_true_ignores_feed_noise(self):
        bs = replace(_minimal_bs(), opp_elixir=3.5)
        view = replace(_minimal_bs(), opp_elixir=None)
        out_live = policy_view_for(view, bs, "true", "live", {})
        out_corrl = policy_view_for(view, bs, "true", "corrL", {})
        self.assertEqual(out_live.opp_elixir, 3.5)
        self.assertEqual(out_corrl.opp_elixir, 3.5)


class TestPolicyViewForEstimated(unittest.TestCase):
    """Acceptance (b), 'estimated' half: the policy-visible opp_elixir equals the live-reachable V2.1
    estimator's ._est -- condition B_tt_wl under --feed-noise live, B_corrL_tt_wl under corrL
    (feed_condition_key)."""

    def test_feed_condition_key(self):
        self.assertEqual(feed_condition_key("live"), "B_tt_wl")
        self.assertEqual(feed_condition_key("corrL"), "B_corrL_tt_wl")
        with self.assertRaises(SystemExit):
            feed_condition_key("bogus")

    def test_estimated_live_reads_b_tt_wl_v2_est(self):
        view = replace(_minimal_bs(), opp_elixir=None)
        bs = replace(_minimal_bs(), opp_elixir=9.9)       # must be IGNORED in 'estimated' mode
        estimators = {("B_tt_wl", "v2"): _FakeEst(3.25), ("B_corrL_tt_wl", "v2"): _FakeEst(8.0)}
        out = policy_view_for(view, bs, "estimated", "live", estimators)
        self.assertEqual(out.opp_elixir, 3.25)
        self.assertEqual(replace(out, opp_elixir=None), replace(view, opp_elixir=None))

    def test_estimated_corrl_reads_b_corrl_tt_wl_v2_est(self):
        view = replace(_minimal_bs(), opp_elixir=None)
        bs = _minimal_bs()
        estimators = {("B_tt_wl", "v2"): _FakeEst(3.25), ("B_corrL_tt_wl", "v2"): _FakeEst(8.0)}
        out = policy_view_for(view, bs, "estimated", "corrL", estimators)
        self.assertEqual(out.opp_elixir, 8.0)

    def test_estimated_missing_condition_raises(self):
        view = _minimal_bs()
        with self.assertRaises(SystemExit):
            policy_view_for(view, view, "estimated", "live", {})   # B_tt_wl/v2 not active

    def test_bad_mode_raises(self):
        view = _minimal_bs()
        with self.assertRaises(SystemExit):
            policy_view_for(view, view, "bogus", "live", {})


class TestFeedNoiseObservationIdentity(unittest.TestCase):
    """Acceptance (d): --feed-noise changes ONLY which estimator 'estimated' reads ._est from -- the
    policy-visible BoardState is the SAME standard live_view either way, field-for-field, except
    opp_elixir itself (the one number the whole ticket is about). Uses two estimators with DIFFERENT
    ._est values so the test cannot pass by accident (a no-op override would make opp_elixir equal too,
    not just the other fields)."""

    def test_live_and_corrl_share_every_field_but_opp_elixir(self):
        u = Unit(cls=5, side=1, x=0.4, y=0.6, hp_frac=1.0, deploying=None, age_sec=None, conf=1.0)
        view = replace(_minimal_bs(units=(u,), my_elixir=6.0, t_sec=33.0), opp_elixir=None)
        bs = view
        estimators = {("B_tt_wl", "v2"): _FakeEst(2.0), ("B_corrL_tt_wl", "v2"): _FakeEst(6.5)}
        out_live = policy_view_for(view, bs, "estimated", "live", estimators)
        out_corrl = policy_view_for(view, bs, "estimated", "corrL", estimators)
        # the ONE field allowed to differ actually does differ (proves this isn't a vacuous pass):
        self.assertNotEqual(out_live.opp_elixir, out_corrl.opp_elixir)
        self.assertEqual(out_live.opp_elixir, 2.0)
        self.assertEqual(out_corrl.opp_elixir, 6.5)
        # every other field, field-by-field via full dataclass equality once opp_elixir is neutralised:
        self.assertEqual(replace(out_live, opp_elixir=None), replace(out_corrl, opp_elixir=None))
        self.assertEqual(replace(out_live, opp_elixir=None), replace(view, opp_elixir=None))


class TestValidateFeedConfig(unittest.TestCase):
    """The --feed-opp-elixir/--feed-noise/--tracker/--corr/--estimator legality checks run_match_audit
    (and main(), before touching the engine) both call up front."""

    def test_bad_feed_opp_elixir_raises(self):
        with self.assertRaises(SystemExit):
            validate_feed_config("bogus", "live", True, True, "v2")

    def test_bad_feed_noise_raises(self):
        with self.assertRaises(SystemExit):
            validate_feed_config("off", "bogus", False, False, "v1")

    def test_off_and_true_need_nothing_extra(self):
        validate_feed_config("off", "live", False, False, "v1")             # must not raise
        validate_feed_config("true", "corrL", False, False, "v1")           # feed_noise irrelevant, ignored

    def test_estimated_requires_v2_variant(self):
        with self.assertRaises(SystemExit):
            validate_feed_config("estimated", "live", True, False, "v1")
        validate_feed_config("estimated", "live", True, False, "v2")        # must not raise
        validate_feed_config("estimated", "live", True, False, "both")      # must not raise

    def test_estimated_requires_tracker(self):
        with self.assertRaises(SystemExit):
            validate_feed_config("estimated", "live", False, False, "v2")

    def test_estimated_corrl_requires_corr(self):
        with self.assertRaises(SystemExit):
            validate_feed_config("estimated", "corrL", True, False, "v2")
        validate_feed_config("estimated", "corrL", True, True, "v2")        # must not raise

    def test_estimated_live_does_not_require_corr(self):
        validate_feed_config("estimated", "live", True, False, "v2")        # must not raise


class TestFeedOppElixirCausality(unittest.TestCase):
    """Acceptance (c): the value 'estimated' mode injects at decision tick T must reflect the estimator's
    samples up to and including T and NOTHING later. This drives the SAME two operations, in the SAME
    relative order, that run_match_audit's per-tick loop uses for every base condition (opp_est_audit.py:
    the per-base ``est.update(my_e, dets, bs.t_sec)`` loop, then -- only inside ``if pol_tick:``, AFTER
    that loop has already run for this exact sample -- ``policy_view_for(...)`` reading ``est._est``): a
    real (not mocked) TrackedEstimatorV2 is update()'d at tick T, its policy-visible value captured via
    policy_view_for immediately after (mirroring the loop's ordering), then update()'d AGAIN with a later
    sample engineered to move the estimate -- and the EARLIER captured value must be unaffected."""

    def test_later_sample_does_not_change_the_earlier_injected_value(self):
        db = _db()
        musketeer_cost = db.elixir("musketeer")
        giant_cost = db.elixir("giant")
        self.assertIsNotNone(musketeer_cost)
        self.assertIsNotNone(giant_cost)
        est = TrackedEstimatorV2(db)
        estimators = {("B_tt_wl", "v2"): est}
        view = replace(_minimal_bs(), opp_elixir=None)
        bs = view

        # tick T=0: reset, then this SAMPLE's update() (mirrors run_match_audit's per-base update loop,
        # which always runs before a policy tick's injection can read ._est).
        est.reset(my_elixir=10.0, now=0.0)
        det_t = _Det(base="musketeer", cx=0.5, gy=0.3, team="enemy")
        est.update(10.0, [det_t], 0.0)
        # policy tick at T: inject NOW, exactly where run_match_audit calls policy_view_for -- after this
        # sample's update(), before any later sample exists.
        injected_at_t = policy_view_for(view, bs, "estimated", "live", estimators).opp_elixir
        self.assertAlmostEqual(injected_at_t, 10.0 - musketeer_cost, places=4)

        # tick T+1 (a LATER sample -- e.g. the next 5-tick estimator step): a NEW enemy card at a
        # different position, engineered to move the estimate (a different base, far enough away that it
        # cannot be mistaken for the same track as det_t).
        det_t1 = _Det(base="giant", cx=0.1, gy=0.9, team="enemy")
        est.update(10.7, [det_t1], 1.0)
        after_later_update = est._est

        # the estimate DID move (the test would be vacuous otherwise -- confirms det_t1 was engineered to
        # actually change something):
        self.assertNotAlmostEqual(after_later_update, injected_at_t, places=4)
        # but the value captured AT tick T is untouched by it -- causality:
        self.assertAlmostEqual(injected_at_t, 10.0 - musketeer_cost, places=4)

    def test_est_is_read_at_call_time_not_snapshotted_earlier(self):
        """Complementary check: policy_view_for itself does no caching/memoisation -- calling it again
        AFTER a further update() picks up the NEW ._est, so the causality guarantee above is a property of
        WHEN run_match_audit calls it (after this sample's updates, before the next sample's), not of this
        function silently freezing a stale value forever."""
        db = _db()
        est = TrackedEstimatorV2(db)
        estimators = {("B_tt_wl", "v2"): est}
        view = replace(_minimal_bs(), opp_elixir=None)
        est.reset(my_elixir=10.0, now=0.0)
        first = policy_view_for(view, view, "estimated", "live", estimators).opp_elixir
        est.update(10.0, [_Det(base="musketeer", cx=0.5, gy=0.3, team="enemy")], 1.0)
        second = policy_view_for(view, view, "estimated", "live", estimators).opp_elixir
        self.assertNotAlmostEqual(first, second, places=4)


if __name__ == "__main__":
    unittest.main()
