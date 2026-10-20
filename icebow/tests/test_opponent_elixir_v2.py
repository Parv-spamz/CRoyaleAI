"""O13/O15: OpponentElixirEstimatorV2 -- hand-computed expectations for R1 (suppress_spawns), R2
(body_count), R3 (speed_aware_radius), R4 (singleton_resight), R5 (lifetime_absorb), R6 (SPAWNS additions),
R7 (r_spawn 0.084->0.12), and V1 parity when all rules are ablated off. See
scratchpad/gauntlet/L67/opp_fix/O13_v2.md (R1-R3) and O15_v21.md (R4-R7) for the data-derived/ticket-given
constants and the SPAWNS/BODIES verification against pipeline.vocab / CardDB.

NOTE on R3's bandit scenario: real ``CardDB.speed_tiles('bandit') == 1.5`` does NOT, by the ticket's own
formula/constants (K=1.5, cap=0.25), raise the effective radius above 0.07 -- MEASURED in O13_v2.md, and
arithmetically incapable of covering the ticket's own 0.12 scenario. The test below uses a stub speed value
large enough to demonstrate the R3 MECHANISM (matching, radius widening, ablation), not real bandit data;
that finding is not silently worked around.

NOTE on R5's body-budget semantics (O15_v21.md attempts 1-3): a group's live-member budget spend is
`sum(min(tr.n, tr.matched_n) for tr in live members)` -- `tr.n` is a track's CREATION size (bodies it
represented when clustered) and never changes; `tr.matched_n` is how many dets `update()` actually matched
to that exact track THIS call, reset to 0 every update(). Two earlier, wrong versions of this: (attempt 1)
counting live TRACK OBJECTS regardless of body count -- silently absorbed an entire second N-body play next
to a live member as if it were one drifted body; (attempt 2) summing each member's FULL creation size
whenever refreshed at all this tick -- over-counted a partially-rematched blob as fully present and wrongly
BLOCKED the very drift/relocation it needs to allow. The `min(tr.n, tr.matched_n)` form (O15.2) is what makes
BOTH directions correct at once: a body that visibly walks off a blob reduces that blob's OWN spend for this
tick (freeing exactly the room it needs elsewhere), while a group whose every original body is still being
matched in full correctly has no free room for a genuinely new arrival. Tests below are lettered (a)-(j) to
match the verifier's own attempt-3 scenario list one-to-one; every one feeds ALL currently-alive same-base
detections each tick (what perfect detection actually reports), never omitting a still-present body to make
a scenario pass by construction (a mistake attempt 2's own drift test made and this attempt corrects).
"""
from __future__ import annotations

import unittest

from clashrl.opponent_elixir import (
    BODIES, SPAWNS, V2_PARAMS, OpponentElixirEstimator, OpponentElixirEstimatorV2,
)


class _FakeDB:
    """Same stand-in convention as icebow/tests/test_opponent_elixir.py, extended with `speed_tiles` for R3."""

    def __init__(self, costs, speeds=None):
        self._costs = dict(costs)
        self._speeds = dict(speeds or {})

    def elixir(self, base):
        return self._costs.get(base)

    def speed_tiles(self, base):
        return self._speeds.get(base)


class _Det:
    def __init__(self, base, cx, gy, team="enemy"):
        self.base = base
        self.cx = cx
        self.gy = gy
        self.team = team


# ------------------------------------------------------------------------------------------------------
# SPAWNS / BODIES table sanity -- every class name must be a real vocab class (never asserted against
# vocab here to avoid a circular import assumption; pipeline's own test suite cross-checks against
# pipeline.vocab -- see test_opp_est_audit.py's TestV2Params). This just checks the tables are internally
# consistent (no empty sets, all string keys/members) and match the ticket's corrections (O13_v2.md).
# ------------------------------------------------------------------------------------------------------
class TestSpawnsBodiesTables(unittest.TestCase):
    def test_every_spawner_maps_to_itself(self):
        for parent, spawns in SPAWNS.items():
            self.assertIn(parent, spawns, f"{parent} must map to itself (engine self-naming)")

    def test_corrections_applied(self):
        # ticket's "fire_spirits"/"cursed_hog"/"lava_pup"(singular)/"phoenix" were dropped or corrected --
        # see O13_v2.md for why each is not a real vocab class.
        self.assertNotIn("fire_spirits", SPAWNS.get("furnace", ()))
        self.assertIn("fire_spirit", SPAWNS.get("furnace", ()))
        self.assertNotIn("cursed_hog", SPAWNS.get("mother_witch", ()))
        self.assertNotIn("hog", SPAWNS.get("mother_witch", ()))
        self.assertIn("mother_witch_hog", SPAWNS.get("mother_witch", ()))
        self.assertNotIn("lava_pup", SPAWNS.get("lava_hound", ()))
        self.assertIn("lava_pups", SPAWNS.get("lava_hound", ()))
        self.assertNotIn("phoenix", SPAWNS)
        self.assertNotIn("fire_spirits", BODIES)
        self.assertNotIn("cursed_hog", BODIES)

    def test_lava_pups_body_count_from_spawner_on_death(self):
        # ticket says 6; verified against CardDB.spawner('lava_hound')['on_death'], not the lava_pups card's
        # own 'count' field (which describes one pup, not the death-spawn burst) -- O13_v2.md.
        self.assertEqual(BODIES["lava_pups"], 6)

    def test_o15_r6_measured_additions(self):
        # CardDB.spawner(parent)["unit"] confirmed for both -- O15_v21.md.
        self.assertEqual(SPAWNS["skeleton_barrel"], frozenset({"skeletons", "skeleton_barrel"}))
        self.assertEqual(SPAWNS["battle_ram"], frozenset({"barbarians", "battle_ram"}))

    def test_o15_r6_untested_addition_flagged_but_present(self):
        # goblin_gang: CardDB.spawner returns None (no measured engine spawn relationship) -- added per the
        # ticket anyway, distinguished in O15_v21.md as untested, not equivalent to the measured entries.
        self.assertEqual(SPAWNS["goblin_gang"], frozenset({"goblins", "spear_goblins", "goblin_gang"}))

    def test_o15_r6_goblin_cage_dropped_not_a_vocab_class(self):
        # "goblin_brawler" (goblin_cage's spawn output) is not a DETECTOR_CLASSES/ENGINE_ONLY_CLASSES member
        # -- the phoenix-egg situation again (O13). Dropped entirely, not guessed.
        self.assertNotIn("goblin_cage", SPAWNS)

    def test_o15_r6_goblin_drill_and_hut_unchanged(self):
        # ticket lists these as if new; both were already correct since O13 -- reconfirmed, not re-derived.
        self.assertEqual(SPAWNS["goblin_drill"], frozenset({"goblins", "goblin_drill"}))
        self.assertEqual(SPAWNS["goblin_hut"], frozenset({"spear_goblins", "goblin_hut"}))

    def test_o15_r7_r_spawn_raised(self):
        self.assertEqual(V2_PARAMS["r_spawn"], 0.12)

    def test_o15_wall_breakers_is_bodies_not_spawner(self):
        # ticket: "wall_breakers is a 2-body card (BODIES), not a spawner" -- reconfirmed unchanged.
        self.assertEqual(BODIES["wall_breakers"], 2)
        self.assertNotIn("wall_breakers", SPAWNS)


# ------------------------------------------------------------------------------------------------------
# V1 parity golden capture (BEFORE this ticket's edit) -- OpponentElixirEstimator itself must be untouched.
# Captured by loading the git-committed HEAD (64d7eca) copy of opponent_elixir.py as a separate module, so
# this test can never pass by coincidence if the live import were accidentally modified.
# ------------------------------------------------------------------------------------------------------
def _load_golden_v1():
    """O13 attempt 2 FIX 5 (verifier, LOW): the git-committed HEAD-64d7eca source is still captured with
    ``git show`` at test time (that part was right), but is now written under the OS temp dir (via
    ``tempfile``), never into the repo tree -- the previous version left a stray
    ``scratchpad/gauntlet/L67/opp_fix/_golden_v1_64d7eca.py`` file behind after every test run, which is not
    a backup or a progress artifact and does not belong in the write set."""
    import importlib.util
    import subprocess
    import tempfile
    from pathlib import Path

    repo = Path(__file__).resolve().parents[2]
    src = subprocess.check_output(
        ["git", "show", "64d7eca:icebow/src/clashrl/opponent_elixir.py"], cwd=str(repo)
    ).decode("utf-8")
    fd, tmp_path = tempfile.mkstemp(suffix=".py", prefix="golden_opponent_elixir_v1_64d7eca_")
    tmp = Path(tmp_path)
    try:
        with open(fd, "w", encoding="utf-8") as fh:
            fh.write(src)
        spec = importlib.util.spec_from_file_location("_golden_opponent_elixir_v1", tmp)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.OpponentElixirEstimator
    finally:
        try:
            tmp.unlink()
        except OSError:
            pass


# One-time cleanup: an earlier version of this test wrote its golden copy into the repo's scratchpad tree
# instead of a temp file (FIX 5 above) -- remove that stray artifact if a prior run left it behind.
def _remove_stray_golden_in_repo_tree() -> None:
    from pathlib import Path

    stray = (Path(__file__).resolve().parents[2] / "scratchpad" / "gauntlet" / "L67" / "opp_fix"
            / "_golden_v1_64d7eca.py")
    if stray.exists():
        stray.unlink()


_remove_stray_golden_in_repo_tree()


class TestV1ParityUnchanged(unittest.TestCase):
    """The live OpponentElixirEstimator must behave identically to the HEAD-64d7eca golden copy on 3
    synthetic sequences -- the class this ticket must not alter."""

    @classmethod
    def setUpClass(cls):
        cls.Golden = _load_golden_v1()

    def _run(self, cls, db, seq):
        est = cls(db)
        est.reset(my_elixir=5.0, now=0.0)
        out = []
        for my_elixir, dets, now, my_play in seq:
            if my_play:
                est.record_my_play(my_play)
            out.append(round(est.update(my_elixir, dets, now), 6))
        return out

    def test_sequence_1_simple_plays(self):
        db = _FakeDB({"ice_wizard": 3, "skeletons": 1, "knight": 3})
        seq = [
            (5.0, [], 0.0, "ice_wizard"),
            (5.0, [_Det("skeletons", 0.5, 0.5)], 1.0, None),
            (5.0, [_Det("skeletons", 0.51, 0.5)], 2.0, None),
            (6.0, [_Det("knight", 0.2, 0.2)], 3.0, None),
        ]
        self.assertEqual(self._run(OpponentElixirEstimator, db, seq), self._run(self.Golden, db, seq))

    def test_sequence_2_saturation(self):
        db = _FakeDB({"golem": 8, "pekka": 7})
        seq = [
            (10.0, [_Det("golem", 0.5, 0.5)], 0.0, None),
            (10.0, [_Det("pekka", 0.3, 0.3)], 0.5, None),
            (10.0, [], 1.0, None),
        ]
        self.assertEqual(self._run(OpponentElixirEstimator, db, seq), self._run(self.Golden, db, seq))

    def test_sequence_3_expiry_and_rebill(self):
        db = _FakeDB({"miner": 3})
        seq = [
            (5.0, [_Det("miner", 0.5, 0.5)], 0.0, None),
            (5.0, [], 7.0, None),                              # track expires (forget_s=6.0)
            (5.0, [_Det("miner", 0.5, 0.5)], 7.1, None),        # rebilled -- V1's own known bug, unchanged
        ]
        self.assertEqual(self._run(OpponentElixirEstimator, db, seq), self._run(self.Golden, db, seq))


# ------------------------------------------------------------------------------------------------------
# R1 -- suppress_spawns
# ------------------------------------------------------------------------------------------------------
class TestR1SuppressSpawns(unittest.TestCase):
    def test_live_form_skeletons_near_tombstone_not_charged(self):
        db = _FakeDB({"tombstone": 3, "skeletons": 1})
        est = OpponentElixirEstimatorV2(db)
        est.reset(my_elixir=5.0, now=0.0)
        est.update(5.0, [_Det("tombstone", 0.50, 0.50)], now=0.0)
        self.assertEqual(est._opp_spent, 3.0)
        est.update(5.0, [_Det("tombstone", 0.50, 0.50), _Det("skeletons", 0.55, 0.50)], now=1.0)
        self.assertEqual(est._opp_spent, 3.0, "live-form spawn (different class) near tombstone must not charge")

    def test_engine_form_second_tombstone_label_near_tombstone_not_charged(self):
        db = _FakeDB({"tombstone": 3, "skeletons": 1})
        est = OpponentElixirEstimatorV2(db)
        est.reset(my_elixir=5.0, now=0.0)
        est.update(5.0, [_Det("tombstone", 0.50, 0.50)], now=0.0)
        est.update(5.0, [_Det("tombstone", 0.50, 0.50), _Det("tombstone", 0.55, 0.50)], now=1.0)
        self.assertEqual(est._opp_spent, 3.0, "engine-form spawn (same class, self-mapped) must not charge")

    def test_skeletons_far_from_spawner_is_charged(self):
        db = _FakeDB({"tombstone": 3, "skeletons": 1})
        est = OpponentElixirEstimatorV2(db)
        est.reset(my_elixir=5.0, now=0.0)
        est.update(5.0, [_Det("tombstone", 0.50, 0.50)], now=0.0)
        est.update(5.0, [_Det("tombstone", 0.50, 0.50), _Det("skeletons", 1.00, 0.50)], now=1.0)
        self.assertEqual(est._opp_spent, 4.0, "a genuinely unrelated skeletons play, far away, must charge")

    def test_ablation_suppress_spawns_off_charges_the_spawn(self):
        db = _FakeDB({"tombstone": 3, "skeletons": 1})
        est = OpponentElixirEstimatorV2(db, suppress_spawns=False)
        est.reset(my_elixir=5.0, now=0.0)
        est.update(5.0, [_Det("tombstone", 0.50, 0.50)], now=0.0)
        est.update(5.0, [_Det("tombstone", 0.50, 0.50), _Det("skeletons", 0.55, 0.50)], now=1.0)
        self.assertEqual(est._opp_spent, 4.0, "rule OFF must reproduce V1's over-billing for this scenario")


# ------------------------------------------------------------------------------------------------------
# R2 -- body_count
# ------------------------------------------------------------------------------------------------------
class TestR2BodyCount(unittest.TestCase):
    def test_three_skeletons_one_update_spread_beyond_cluster_radius_one_charge(self):
        db = _FakeDB({"skeletons": 1})
        est = OpponentElixirEstimatorV2(db)
        est.reset(my_elixir=5.0, now=0.0)
        est.update(5.0, [_Det("skeletons", 0.30, 0.5), _Det("skeletons", 0.45, 0.5),
                        _Det("skeletons", 0.60, 0.5)], now=0.0)   # 0.15 apart, > cluster_radius (0.10)
        self.assertEqual(est._opp_spent, 1.0)
        self.assertEqual(len(est._tracks), 3, "all 3 bodies still become tracks for future matching")

    def test_fifteen_skeleton_army_over_two_updates_absorbed_one_charge(self):
        db = _FakeDB({"skeleton_army": 3})
        est = OpponentElixirEstimatorV2(db)
        est.reset(my_elixir=10.0, now=0.0)
        wave1 = [_Det("skeleton_army", 0.50 + 0.005 * i, 0.5) for i in range(8)]
        wave2 = [_Det("skeleton_army", 0.50 + 0.005 * i, 0.5) for i in range(8, 15)]
        est.update(10.0, wave1, now=0.0)
        self.assertEqual(est._opp_spent, 3.0)
        est.update(10.0, wave1 + wave2, now=0.25)          # +7 bodies, same spot, within W=1.0s
        self.assertEqual(est._opp_spent, 3.0, "second wave absorbed into the same deployment, no new charge")

    def test_two_plays_five_seconds_apart_different_spot_two_charges(self):
        """Body-group window (W=1.0s) isolated from track persistence: a DIFFERENT nearby spot so the
        lingering forget_s=6.0s track from play 1 cannot MATCH play 2's dets by proximity -- this is the
        scenario R2's body-group window (not V1's forget_s) is responsible for charging correctly."""
        db = _FakeDB({"skeletons": 1})
        est = OpponentElixirEstimatorV2(db)
        est.reset(my_elixir=10.0, now=0.0)
        est.update(10.0, [_Det("skeletons", 0.30, 0.5), _Det("skeletons", 0.32, 0.5),
                         _Det("skeletons", 0.34, 0.5)], now=0.0)
        self.assertEqual(est._opp_spent, 1.0)
        est.update(10.0, [_Det("skeletons", 0.70, 0.5), _Det("skeletons", 0.72, 0.5),
                         _Det("skeletons", 0.74, 0.5)], now=5.0)
        self.assertEqual(est._opp_spent, 2.0)

    def test_two_plays_same_spot_within_forget_s_absorbed_one_charge_KNOWN_LIMITATION(self):
        """KNOWN LIMITATION (O13 attempt 2 FIX 4, verifier LOW), inherited from V1 unmodified, NOT something
        R2 introduces or could fix without changing forget_s (out of scope, ticket: "do NOT change forget_s"):
        a second play of the SAME card at the literal SAME spot, within forget_s=6.0s of the first, is
        matched by ``_find_track`` to the still-live track from play 1 (V1's own track-matching, R3 off since
        neither is dashing) and REFRESHES it instead of creating new tracks -- so R2's body-group logic never
        even runs (there are no new tracks to group), and the second play is silently absorbed as if it were
        the same units still standing there. This is a pre-existing V1 behavior this ticket does not touch;
        it is the ORIGINAL scenario text ("two skeletons plays 5 s apart at the same spot -> TWO charges")
        that was wrong about V1-inherited track persistence, not a V2 R2 bug. See
        test_two_plays_five_seconds_apart_different_spot_two_charges above for R2's actual behavior, and
        test_two_plays_same_spot_after_forget_s_two_charges below for the literal same-spot case once the
        track has actually expired."""
        db = _FakeDB({"skeletons": 1})
        est = OpponentElixirEstimatorV2(db)
        est.reset(my_elixir=10.0, now=0.0)
        est.update(10.0, [_Det("skeletons", 0.30, 0.5), _Det("skeletons", 0.32, 0.5),
                         _Det("skeletons", 0.34, 0.5)], now=0.0)
        self.assertEqual(est._opp_spent, 1.0)
        est.update(10.0, [_Det("skeletons", 0.30, 0.5), _Det("skeletons", 0.32, 0.5),
                         _Det("skeletons", 0.34, 0.5)], now=5.0)   # same spot, 5s later (< forget_s=6.0)
        self.assertEqual(est._opp_spent, 1.0, "known limitation: absorbed by the still-live V1 track")
        # play 1's 3 dets are within cluster_radius (0.10) of each other, so they merge into ONE track
        # (n=3, centroid) even on the FIRST play -- play 2's dets all re-match that same single track, so
        # no NEW track is created either time.
        self.assertEqual(len(est._tracks), 1, "no NEW track was created -- all 3 dets matched/refreshed")

    def test_two_plays_same_spot_after_forget_s_two_charges(self):
        """Same spot as above, but 7s apart (> forget_s=6.0s): the first play's tracks have actually
        EXPIRED by the second play, so its dets are genuinely new -> TWO charges, as the original ticket
        scenario intended once the confound above is accounted for."""
        db = _FakeDB({"skeletons": 1})
        est = OpponentElixirEstimatorV2(db)
        est.reset(my_elixir=10.0, now=0.0)
        est.update(10.0, [_Det("skeletons", 0.30, 0.5), _Det("skeletons", 0.32, 0.5),
                         _Det("skeletons", 0.34, 0.5)], now=0.0)
        self.assertEqual(est._opp_spent, 1.0)
        est.update(10.0, [_Det("skeletons", 0.30, 0.5), _Det("skeletons", 0.32, 0.5),
                         _Det("skeletons", 0.34, 0.5)], now=7.0)   # same spot, 7s later (> forget_s=6.0)
        self.assertEqual(est._opp_spent, 2.0)

    def test_ablation_body_count_off_charges_once_per_cluster(self):
        db = _FakeDB({"skeletons": 1})
        est = OpponentElixirEstimatorV2(db, body_count=False)
        est.reset(my_elixir=5.0, now=0.0)
        est.update(5.0, [_Det("skeletons", 0.30, 0.5), _Det("skeletons", 0.45, 0.5),
                        _Det("skeletons", 0.60, 0.5)], now=0.0)
        self.assertEqual(est._opp_spent, 3.0, "rule OFF must reproduce V1's one-charge-per-cluster over-billing")


# ------------------------------------------------------------------------------------------------------
# R3 -- speed_aware_radius (bandit stub speed -- see module docstring for why real cards.yaml data can't
# demonstrate this; O13_v2.md has the measured gap)
# ------------------------------------------------------------------------------------------------------
class TestR3SpeedAwareRadius(unittest.TestCase):
    def test_bandit_dash_matched_no_charge(self):
        # stub speed chosen so speed_norm*dt*K covers the 0.12 move: 0.12/(0.25*1.5)=0.32/s -> speed_tiles
        # >= 0.32*18=5.76; 6.0 used with headroom. NOT bandit's real cards.yaml speed_tiles (1.5) -- see
        # module docstring / O13_v2.md.
        db = _FakeDB({"bandit": 3}, speeds={"bandit": 6.0})
        est = OpponentElixirEstimatorV2(db)
        est.reset(my_elixir=5.0, now=0.0)
        est.update(5.0, [_Det("bandit", 0.50, 0.5)], now=0.0)
        self.assertEqual(est._opp_spent, 3.0)
        est.update(5.0, [_Det("bandit", 0.62, 0.5)], now=0.25)     # moved 0.12 in 0.25s
        self.assertEqual(est._opp_spent, 3.0, "fast/dashing unit must match its track, not rebill")
        self.assertEqual(len(est._tracks), 1, "must be one continuing track, not two")

    def test_stationary_tombstone_radius_unchanged(self):
        db = _FakeDB({"tombstone": 3}, speeds={})       # no speed data for tombstone (a building)
        est = OpponentElixirEstimatorV2(db)
        est.reset(my_elixir=5.0, now=0.0)
        est.update(5.0, [_Det("tombstone", 0.50, 0.50)], now=0.0)
        est.update(5.0, [_Det("tombstone", 0.505, 0.50)], now=0.25)   # 0.005 move, well within match_radius
        self.assertEqual(est._opp_spent, 3.0)
        self.assertEqual(len(est._tracks), 1)

    def test_ablation_speed_aware_off_rebills_the_dash(self):
        # Charge-count check, not a raw opp_spent number: at my_elixir=5.0 a second 3-cost charge pushes the
        # books past the [0,10] cap, and the L67g saturation rebase (copied verbatim from V1) claws back the
        # overflow into opp_spent -- that correction is real V1 behaviour, not a defect in this ablation
        # check. `_body_groups`/track count is the unambiguous signal that a SECOND, separate charge event
        # fired (a real match would never hold my_elixir fixed at 5.0 across two live samples anyway).
        db = _FakeDB({"bandit": 3}, speeds={"bandit": 6.0})
        est = OpponentElixirEstimatorV2(db, speed_aware_radius=False)
        est.reset(my_elixir=5.0, now=0.0)
        est.update(5.0, [_Det("bandit", 0.50, 0.5)], now=0.0)
        self.assertEqual(est._opp_spent, 3.0)
        est.update(5.0, [_Det("bandit", 0.62, 0.5)], now=0.25)
        self.assertEqual(len(est._tracks), 2, "rule OFF must reproduce V1's fixed-radius rebill (2nd track)")
        self.assertGreater(est._opp_spent, 3.0, "a second charge must have been billed")


# ------------------------------------------------------------------------------------------------------
# R4 (O15) -- singleton_resight
# ------------------------------------------------------------------------------------------------------
class TestR4SingletonResight(unittest.TestCase):
    def test_miner_resight_within_window_not_charged(self):
        db = _FakeDB({"miner": 3})
        est = OpponentElixirEstimatorV2(db)
        est.reset(my_elixir=10.0, now=0.0)
        est.update(10.0, [_Det("miner", 0.5, 0.8)], now=0.0)
        self.assertEqual(est._opp_spent, 3.0)
        est.update(10.0, [_Det("miner", 0.5, 0.2)], now=3.0)   # resurfaced far away, 3.0s later (< 4.0s)
        self.assertEqual(est._opp_spent, 3.0, "re-sighting within singleton_window_s must not charge")

    def test_miner_reappears_after_window_charged(self):
        db = _FakeDB({"miner": 3})
        est = OpponentElixirEstimatorV2(db)
        est.reset(my_elixir=10.0, now=0.0)
        est.update(10.0, [_Det("miner", 0.5, 0.8)], now=0.0)
        self.assertEqual(est._opp_spent, 3.0)
        est.update(10.0, [_Det("miner", 0.5, 0.2)], now=5.0)   # beyond singleton_window_s=4.0 -> genuine play
        self.assertEqual(est._opp_spent, 6.0, "reappearance beyond singleton_window_s must charge")

    def test_two_miners_simultaneous_0_3s_apart_two_charges(self):
        db = _FakeDB({"miner": 3})
        est = OpponentElixirEstimatorV2(db)
        est.reset(my_elixir=10.0, now=0.0)
        est.update(10.0, [_Det("miner", 0.5, 0.5)], now=0.0)
        self.assertEqual(est._opp_spent, 3.0)
        est.update(10.0, [_Det("miner", 0.9, 0.9)], now=0.3)   # < singleton_double_window_s=0.5 -> genuine double
        self.assertEqual(est._opp_spent, 6.0, "two live singleton tracks this close together must both charge")

    def test_ablation_singleton_resight_off_rebills_the_resurface(self):
        db = _FakeDB({"miner": 3})
        est = OpponentElixirEstimatorV2(db, singleton_resight=False)
        est.reset(my_elixir=10.0, now=0.0)
        est.update(10.0, [_Det("miner", 0.5, 0.8)], now=0.0)
        est.update(10.0, [_Det("miner", 0.5, 0.2)], now=3.0)
        self.assertEqual(est._opp_spent, 6.0, "rule OFF must reproduce old V2's rebill for this scenario")


# ------------------------------------------------------------------------------------------------------
# R5 (O15) -- lifetime_absorb
# ------------------------------------------------------------------------------------------------------
class TestR5LifetimeAbsorb(unittest.TestCase):
    def test_drifted_body_absorbed_via_a_live_member_not_the_centroid(self):
        db = _FakeDB({"barbarians": 5})
        est = OpponentElixirEstimatorV2(db)
        est.reset(my_elixir=10.0, now=0.0)
        # 5 barbarians land as TWO track objects (3 @ 0.40, 2 @ 0.70 -- > cluster_radius=0.10 apart, so they
        # do not merge into one blob); weighted centroid = 0.58. ceil(5/5)=1 charge, cap=5.
        est.update(10.0, [_Det("barbarians", 0.40, 0.50)] * 3 + [_Det("barbarians", 0.70, 0.50)] * 2, now=0.0)
        self.assertEqual(est._opp_spent, 5.0)
        self.assertEqual(len(est._tracks), 2)
        # keep both members refreshed/alive across several ticks (< forget_s=6.0 between any two).
        for t in (2.0, 4.0, 6.0):
            est.update(10.0, [_Det("barbarians", 0.40, 0.50), _Det("barbarians", 0.70, 0.50)], now=t)
        self.assertEqual(est._opp_spent, 5.0)
        # O15.2 (verifier attempt 3): at t=8.0 one body of the 0.70 pair (n=2) has drifted to 0.85 (0.15 from
        # that member, within r_body=0.20; 0.27 from the stored weighted centroid 0.58, BEYOND r_body -- the
        # case the old centroid-only match would have missed). ALL THREE currently-live positions (0.40,
        # 0.70, AND the drifted 0.85) are fed together THIS tick -- what perfect detection actually reports
        # -- so the 0.70 track is matched by only 1 of its 2 original bodies (matched_n=1 < n=2) and
        # correctly spends only 1 of its budget, leaving room for the drifted one (attempt 2's version of
        # this test omitted the still-present 0.70 det and so never exercised this; flagged and fixed here).
        est.update(10.0, [_Det("barbarians", 0.40, 0.50), _Det("barbarians", 0.70, 0.50),
                          _Det("barbarians", 0.85, 0.50)], now=8.0)
        self.assertEqual(est._opp_spent, 5.0, "drift absorbed via proximity to a live member, no new charge")
        self.assertEqual(len(est._tracks), 3, "the drifted body still becomes its own new track")

    def test_a_one_of_five_walks_off_a_merged_blob_absorbed(self):
        # O15.2 verifier scenario (a): 5 barbarians land as ONE cluster track (n=5); later 4 of them are
        # still matched to it (matched_n=4 < n=5) while 1 walks 0.12 away (beyond match_radius=0.07, so it
        # cannot re-match the blob track and becomes a fresh point) -- absorbed (4+1<=5), total stays 5.
        db = _FakeDB({"barbarians": 5})
        est = OpponentElixirEstimatorV2(db, speed_aware_radius=False)
        est.reset(my_elixir=10.0, now=0.0)
        est.update(10.0, [_Det("barbarians", 0.50, 0.50)] * 5, now=0.0)
        self.assertEqual(est._opp_spent, 5.0)
        est.update(10.0, [_Det("barbarians", 0.50, 0.50)] * 4 + [_Det("barbarians", 0.62, 0.50)], now=2.0)
        self.assertEqual(est._opp_spent, 5.0, "one body walking off a still-4/5-matched blob must be absorbed")

    def test_b_a_second_body_then_walks_off_still_absorbed(self):
        # O15.2 verifier scenario (b): continuing from (a), 4s later a SECOND body also walks off (now only
        # 3 of the original blob's dets still match it) while both walkers are still visible -- still
        # absorbed (3+1+1<=5), total stays 5.
        db = _FakeDB({"barbarians": 5})
        est = OpponentElixirEstimatorV2(db, speed_aware_radius=False)
        est.reset(my_elixir=10.0, now=0.0)
        est.update(10.0, [_Det("barbarians", 0.50, 0.50)] * 5, now=0.0)
        est.update(10.0, [_Det("barbarians", 0.50, 0.50)] * 4 + [_Det("barbarians", 0.62, 0.50)], now=2.0)
        self.assertEqual(est._opp_spent, 5.0)
        est.update(10.0, [_Det("barbarians", 0.50, 0.50)] * 3 + [_Det("barbarians", 0.62, 0.50)]
                   + [_Det("barbarians", 0.38, 0.50)], now=6.0)
        self.assertEqual(est._opp_spent, 5.0, "a second walker, group still intact, must also be absorbed")

    def test_c_skeletons_blob_partially_matched_one_off_absorbed(self):
        # O15.2 verifier scenario (c): same mechanism as (a) but for a 3-cap card -- the blob track (n=3) is
        # matched by only 2 dets this tick while 1 body is 0.10 off (beyond match_radius) -- absorbed
        # (2+1<=3), total stays 1.
        db = _FakeDB({"skeletons": 1})
        est = OpponentElixirEstimatorV2(db, speed_aware_radius=False)
        est.reset(my_elixir=10.0, now=0.0)
        est.update(10.0, [_Det("skeletons", 0.50, 0.50)] * 3, now=0.0)
        self.assertEqual(est._opp_spent, 1.0)
        est.update(10.0, [_Det("skeletons", 0.50, 0.50)] * 2 + [_Det("skeletons", 0.60, 0.50)], now=2.0)
        self.assertEqual(est._opp_spent, 1.0, "one skeleton off a still-2/3-matched blob must be absorbed")

    def test_d_intact_group_plus_genuine_new_play_charged(self):
        # O15.2 verifier scenario (d): the original 5-blob is matched IN FULL this tick (matched_n=5=n) while
        # a genuinely separate new 5-body play lands 0.17 away (within r_body=0.20 of the blob) -- budget is
        # already fully spent by the intact original, so 5+5>5 -> the new play must charge in full, total 10.
        db = _FakeDB({"barbarians": 5})
        est = OpponentElixirEstimatorV2(db, speed_aware_radius=False)
        est.reset(my_elixir=10.0, now=0.0)
        blob = [_Det("barbarians", 0.50, 0.50)] * 5
        est.update(10.0, blob, now=0.0)
        self.assertEqual(est._opp_spent, 5.0)
        new_play = [_Det("barbarians", 0.67, 0.50)] * 5   # 0.17 away -- within r_body, a NEW full play
        est.update(10.0, blob + new_play, now=3.0)
        self.assertEqual(est._opp_spent, 10.0, "an intact group's full budget blocks a genuine new play")

    def test_e_partially_matched_group_plus_new_play_still_charged(self):
        # O15.2 verifier scenario (e): only 3 of the original 5 are matched this tick (matched_n=3, capped at
        # min(n=5,3)=3) while a genuinely new 5-body play arrives -- 3+5>5, still charged in full, total 10
        # (distinguishes this from scenario (a)/(b), where the "missing" bodies are the WALKER itself, not an
        # unrelated new play).
        db = _FakeDB({"barbarians": 5})
        est = OpponentElixirEstimatorV2(db, speed_aware_radius=False)
        est.reset(my_elixir=10.0, now=0.0)
        blob = [_Det("barbarians", 0.50, 0.50)] * 5
        est.update(10.0, blob, now=0.0)
        self.assertEqual(est._opp_spent, 5.0)
        three_only = [_Det("barbarians", 0.50, 0.50)] * 3
        new_play = [_Det("barbarians", 0.67, 0.50)] * 5
        est.update(10.0, three_only + new_play, now=3.0)
        self.assertEqual(est._opp_spent, 10.0, "3 of 5 matched still leaves no room for a genuine new play")

    def test_f_recall_miss_then_whole_group_relocates_absorbed(self):
        # O15.2 verifier scenario (f): one tick drops 2 of the 5 dets (a detector "recall miss" -- matched_n=3
        # that tick, but this has NO bearing on the NEXT tick, since matched_n resets every update()); the
        # tick after that, all 5 are back but the WHOLE group has displaced together by 0.09 (beyond
        # match_radius=0.07, so none of them re-match the original track at all -- matched_n=0 that tick) and
        # clusters into one new point of its own (n=5) -- since the original track's budget spend that tick
        # is min(5, 0)=0, the relocated group is absorbed in full: total stays 5.
        db = _FakeDB({"barbarians": 5})
        est = OpponentElixirEstimatorV2(db, speed_aware_radius=False)
        est.reset(my_elixir=10.0, now=0.0)
        est.update(10.0, [_Det("barbarians", 0.50, 0.50)] * 5, now=0.0)
        self.assertEqual(est._opp_spent, 5.0)
        est.update(10.0, [_Det("barbarians", 0.50, 0.50)] * 3, now=1.0)      # recall miss: 2 dropped
        self.assertEqual(est._opp_spent, 5.0)
        est.update(10.0, [_Det("barbarians", 0.59, 0.50)] * 5, now=2.0)      # all 5 back, displaced 0.09
        self.assertEqual(est._opp_spent, 5.0, "a whole-group relocation must still be absorbed, not rebilled")

    def test_g_sixth_body_while_five_alive_starts_new_deployment(self):
        # O15.2 verifier scenario (g).
        db = _FakeDB({"barbarians": 5})
        est = OpponentElixirEstimatorV2(db)
        est.reset(my_elixir=10.0, now=0.0)
        # 5 mutually-far track objects (0.15 apart, > cluster_radius) -> exactly 5 live members, at cap.
        original = [_Det("barbarians", 0.10 + 0.15 * i, 0.50) for i in range(5)]
        est.update(10.0, original, now=0.0)
        self.assertEqual(est._opp_spent, 5.0)
        self.assertEqual(len(est._tracks), 5)
        before = est._opp_spent
        # All 5 originals are still visible/refreshed (ACTIVE) this same tick, so the group's body budget
        # (5) is fully spent by them -- a 6th body, 0.15 from the nearest one (within r_body=0.20, so it
        # WOULD qualify by proximity alone), correctly cannot join: the budget, not distance, blocks it.
        est.update(10.0, original + [_Det("barbarians", 0.85, 0.50)], now=1.0)
        self.assertEqual(est._opp_spent - before, 5.0, "budget-full group -> new deployment, exactly one charge")
        self.assertEqual(len(est._tracks), 6)

    def test_i_all_five_die_then_five_new_charged_once(self):
        # O15.2 verifier scenario (i), part 1.
        db = _FakeDB({"barbarians": 5})
        est = OpponentElixirEstimatorV2(db)
        est.reset(my_elixir=10.0, now=0.0)
        est.update(10.0, [_Det("barbarians", 0.50, 0.50)] * 5, now=0.0)   # one merged blob, n=5, 1 charge
        self.assertEqual(est._opp_spent, 5.0)
        before = est._opp_spent
        # 7s later (> forget_s=6.0, no refresh in between) -- the old group is fully expired/dead.
        est.update(10.0, [_Det("barbarians", 0.50, 0.50)] * 5, now=7.0)
        self.assertEqual(est._opp_spent - before, 5.0, "a dead group's cap must not carry over -- one new charge")

    def test_i_two_independent_deployments_different_lanes_twenty_seconds_apart(self):
        # O15.2 verifier scenario (i), part 2: two full, independent 5-barbarian deployments in different
        # lanes, 20s apart -- both charge in full regardless of the first still being alive (different lane,
        # never within r_body of it), total 10.
        db = _FakeDB({"barbarians": 5})
        est = OpponentElixirEstimatorV2(db)
        est.reset(my_elixir=10.0, now=0.0)
        est.update(10.0, [_Det("barbarians", 0.20, 0.50)] * 5, now=0.0)
        self.assertEqual(est._opp_spent, 5.0)
        est.update(10.0, [_Det("barbarians", 0.80, 0.50)] * 5, now=20.0)
        self.assertEqual(est._opp_spent, 10.0, "two separate-lane deployments must both charge in full")

    def test_j_same_update_leftover_pooling_3_plus_2_skeletons_two_charges(self):
        # O15.2 verifier scenario (j). O15.1 FIX 2: BODIES[skeletons]=3, so a 3+2 split (5 bodies total, both points beyond
        # cluster_radius=0.10 of each other so they land as two separate cluster points) is
        # ceil(5/3)=2 charges -- NOT one; an earlier draft of the self-caught-pooling-fix docstring said
        # "one" for this exact example, which was arithmetically wrong (corrected in O15_v21.md attempt 2).
        # The pooling fix itself is still real: without it, this would wrongly split into 2 INDEPENDENT
        # per-point charges of ceil(3/3)=1 and ceil(2/3)=1, i.e. also 2 -- see the 2+1 case below for a split
        # where per-point-independent charging (2) and correct whole-batch pooling (1) actually differ.
        db = _FakeDB({"skeletons": 1})
        est = OpponentElixirEstimatorV2(db)
        est.reset(my_elixir=10.0, now=0.0)
        est.update(10.0, [_Det("skeletons", 0.30, 0.5)] * 3 + [_Det("skeletons", 0.60, 0.5)] * 2, now=0.0)
        self.assertEqual(est._opp_spent, 2.0, "ceil(5/3)=2, not the 1 an earlier draft wrongly claimed")

    def test_j_same_update_leftover_pooling_2_plus_1_skeletons_one_charge(self):
        # O15.2 verifier scenario (j). The case that actually demonstrates the self-caught pooling fix: per-point-independent charging
        # would give ceil(2/3)=1 + ceil(1/3)=1 = 2, but the two points are ONE play (5 -> wait, 3 total
        # bodies here) pooled as ONE batch -> ceil(3/3)=1.
        db = _FakeDB({"skeletons": 1})
        est = OpponentElixirEstimatorV2(db)
        est.reset(my_elixir=10.0, now=0.0)
        est.update(10.0, [_Det("skeletons", 0.30, 0.5)] * 2 + [_Det("skeletons", 0.60, 0.5)] * 1, now=0.0)
        self.assertEqual(est._opp_spent, 1.0, "3 bodies total, one play -> ceil(3/3)=1, not 2")


    def test_h_second_full_play_near_a_live_member_not_absorbed(self):
        # O15.2 verifier scenario (h), part 1. O15.1 FIX 1, verifier case 1: a SECOND, genuinely new 5-barbarian play landing near (0.15 from) a
        # live member of the first play's group must NOT be absorbed as if it were one drifted body --
        # V2.1's original (buggy) per-TRACK cap let this happen (5 billed instead of 10).
        db = _FakeDB({"barbarians": 5})
        est = OpponentElixirEstimatorV2(db)
        est.reset(my_elixir=10.0, now=0.0)
        original = [_Det("barbarians", 0.10 + 0.15 * i, 0.50) for i in range(5)]
        est.update(10.0, original, now=0.0)
        self.assertEqual(est._opp_spent, 5.0)
        # second play: 5 NEW bodies, spread among themselves; only the first (0.85) is within r_body (0.20)
        # of the first group's nearest live member (0.70) -- the other 4 are far from everything. The first
        # group's 5 originals are re-fed (still visible/alive) so their body budget reads as fully spent.
        second = [_Det("barbarians", 0.85 + 0.15 * i, 0.50) for i in range(5)]
        est.update(10.0, original + second, now=3.0)
        self.assertEqual(est._opp_spent, 10.0, "a genuinely new play must charge in full, not be absorbed")

    def test_h_three_separate_plays_five_seconds_apart_all_billed(self):
        # O15.2 verifier scenario (h), part 2. O15.1 FIX 1, verifier case 2: three separate 5-barbarian plays, each landing 0.15 from the
        # previous play's nearest live member, 5s apart -- V2.1's original bug billed only 5 of the true 15
        # (absorbing the 2nd and 3rd plays as if they were drifted bodies of the 1st). my_elixir=15.0
        # exactly (not 10.0, not 30.0): three 5-cost charges sum to 15, and this is the ONE fixed value that
        # keeps `est = my_elixir - opp_spent` inside [0, 10] after EVERY one of the three charges (10, 5, 0)
        # -- either lower (goes negative) or higher (goes over 10) would trigger the L67g saturation rebase,
        # which claws overflow/underflow into opp_spent itself and corrupts this raw-number check (a fixed,
        # non-regenerating my_elixir is unrealistic either way; see the R3 ablation test's own comment on
        # this same gotcha).
        db = _FakeDB({"barbarians": 5})
        est = OpponentElixirEstimatorV2(db)
        est.reset(my_elixir=15.0, now=0.0)
        play1 = [_Det("barbarians", 0.10 + 0.15 * i, 0.50) for i in range(5)]
        est.update(15.0, play1, now=0.0)
        self.assertEqual(est._opp_spent, 5.0)
        play2 = [_Det("barbarians", 0.85 + 0.15 * i, 0.50) for i in range(5)]   # 0.15 from play1's last member
        est.update(15.0, play1 + play2, now=5.0)
        self.assertEqual(est._opp_spent, 10.0)
        play3 = [_Det("barbarians", 1.60 + 0.15 * i, 0.50) for i in range(5)]   # 0.15 from play2's last member
        est.update(15.0, play1 + play2 + play3, now=10.0)
        self.assertEqual(est._opp_spent, 15.0, "three separate plays must bill 15, not 5")

    def test_h_skeletons_cycled_three_times_all_billed(self):
        # O15.2 verifier scenario (h), part 3. O15.1 FIX 1, verifier case 3: "skeletons" (BODIES=3) cycled 3x, 2s apart, each play's 3 bodies
        # landing 0.15 from the previous play's spot -- must bill 3, not 1.
        db = _FakeDB({"skeletons": 1})
        est = OpponentElixirEstimatorV2(db)
        est.reset(my_elixir=10.0, now=0.0)
        p1 = [_Det("skeletons", 0.10, 0.5)] * 3
        est.update(10.0, p1, now=0.0)
        self.assertEqual(est._opp_spent, 1.0)
        p2 = [_Det("skeletons", 0.25, 0.5)] * 3   # 0.15 from p1's spot
        est.update(10.0, p1 + p2, now=2.0)
        self.assertEqual(est._opp_spent, 2.0)
        p3 = [_Det("skeletons", 0.40, 0.5)] * 3   # 0.15 from p2's spot
        est.update(10.0, p1 + p2 + p3, now=4.0)
        self.assertEqual(est._opp_spent, 3.0, "three separate skeletons plays must bill 3, not 1")

    def test_ablation_lifetime_absorb_off_rebills_the_drift(self):
        # Same drift setup as the first test above (ALL live members fed every tick, including 0.70 at
        # t=8.0), but with the legacy time-window (body_group_window_s=1.0) + single-centroid match: by
        # t=8.0 the window has long expired, so the drifted body starts a NEW deployment regardless of
        # proximity to a live member -- reproducing V2.0's over-billing.
        db = _FakeDB({"barbarians": 5})
        est = OpponentElixirEstimatorV2(db, lifetime_absorb=False)
        est.reset(my_elixir=10.0, now=0.0)
        est.update(10.0, [_Det("barbarians", 0.40, 0.50)] * 3 + [_Det("barbarians", 0.70, 0.50)] * 2, now=0.0)
        self.assertEqual(est._opp_spent, 5.0)
        for t in (2.0, 4.0, 6.0):
            est.update(10.0, [_Det("barbarians", 0.40, 0.50), _Det("barbarians", 0.70, 0.50)], now=t)
        est.update(10.0, [_Det("barbarians", 0.40, 0.50), _Det("barbarians", 0.70, 0.50),
                          _Det("barbarians", 0.85, 0.50)], now=8.0)
        self.assertEqual(est._opp_spent, 10.0, "rule OFF must reproduce old V2's window-expiry rebill")


# ------------------------------------------------------------------------------------------------------
# O15.3 (attempt 4) -- within-one-update `pending` budget: two same-base points landing near ONE group in
# the SAME sample must not both be checked against that group's unchanged active_n (which only reflects
# `self._tracks`, not gaining a new entry for either point until AFTER the whole batch is resolved).
# Lettered A/B/C to match the verifier's own attempt-4 scenario list (a separate namespace from attempt 3's
# lower-case a-j, which this class's tests above already cover and which must still hold unmodified).
# ------------------------------------------------------------------------------------------------------
class TestR5WithinUpdatePendingBudget(unittest.TestCase):
    def test_A2_blob_of_five_three_matched_three_fan_outs_six_visible_charged(self):
        # 6 bodies visible this tick for a 5-cap card: the blob (n=5) is matched by only 3 dets, and 3 OTHER
        # dets fan out to separate spots (each >cluster_radius=0.10 from the blob and from each other, so
        # each is its own new point, n=1). Budget available this tick = cap(5) - active_n(3) = 2. Processed
        # in order, the first 2 fan-outs each fit (3+0+1<=5, then 3+1+1<=5) and join the blob's group for
        # free; the 3rd does not (3+2+1=6>5) and becomes its own new deployment, ceil(1/5)=1. Total: initial
        # 5 + this tick's 1 new charge = 10.
        db = _FakeDB({"barbarians": 5})
        est = OpponentElixirEstimatorV2(db, speed_aware_radius=False)
        est.reset(my_elixir=10.0, now=0.0)
        est.update(10.0, [_Det("barbarians", 0.50, 0.50)] * 5, now=0.0)
        self.assertEqual(est._opp_spent, 5.0)
        fan_outs = [_Det("barbarians", 0.62, 0.50), _Det("barbarians", 0.62, 0.65),
                    _Det("barbarians", 0.35, 0.50)]
        est.update(10.0, [_Det("barbarians", 0.50, 0.50)] * 3 + fan_outs, now=2.0)
        self.assertEqual(est._opp_spent, 10.0, "6 bodies visible for a 5-cap card must charge the excess")

    def test_A3_blob_of_five_three_matched_four_fan_outs_seven_visible_charged(self):
        # Same mechanism as A2 but with 4 fan-outs (7 visible): budget available = 2, so 2 fan-outs join for
        # free (pending fills 0->1->2) and the remaining 2 become leftover, POOLED together (existing R2/R5
        # batch-pooling, unaffected by this fix): total_n=1+1=2, ceil(2/5)=1 new charge (still just 5, since
        # 2 bodies fit within one deployment's cap). Total: 5 + 5 = 10 -- same total as A2 (ceil() rounds any
        # 1-5 excess up to one 5-cost charge either way), which is itself part of what this test confirms.
        db = _FakeDB({"barbarians": 5})
        est = OpponentElixirEstimatorV2(db, speed_aware_radius=False)
        est.reset(my_elixir=10.0, now=0.0)
        est.update(10.0, [_Det("barbarians", 0.50, 0.50)] * 5, now=0.0)
        self.assertEqual(est._opp_spent, 5.0)
        fan_outs = [_Det("barbarians", 0.62, 0.50), _Det("barbarians", 0.62, 0.65),
                    _Det("barbarians", 0.35, 0.50), _Det("barbarians", 0.35, 0.35)]
        est.update(10.0, [_Det("barbarians", 0.50, 0.50)] * 3 + fan_outs, now=2.0)
        self.assertEqual(est._opp_spent, 10.0, "7 bodies visible for a 5-cap card must charge the excess")

    def test_B1_group_returns_alone_absorbed(self):
        # Baseline (same mechanism as attempt-3 scenario f, restated under the B-numbering): the whole group
        # relocates together (matched_n=0 for the original track that tick) with no accompanying new play --
        # fully absorbed, total stays 5.
        db = _FakeDB({"barbarians": 5})
        est = OpponentElixirEstimatorV2(db, speed_aware_radius=False)
        est.reset(my_elixir=10.0, now=0.0)
        est.update(10.0, [_Det("barbarians", 0.50, 0.50)] * 5, now=0.0)
        est.update(10.0, [_Det("barbarians", 0.50, 0.50)] * 3, now=1.0)   # recall miss
        est.update(10.0, [_Det("barbarians", 0.59, 0.50)] * 5, now=2.0)   # whole group returns, displaced
        self.assertEqual(est._opp_spent, 5.0, "the group returning alone must still be fully absorbed")

    def _b2_setup(self, my_elixir=10.0):
        db = _FakeDB({"barbarians": 5})
        est = OpponentElixirEstimatorV2(db, speed_aware_radius=False)
        est.reset(my_elixir=my_elixir, now=0.0)
        est.update(my_elixir, [_Det("barbarians", 0.50, 0.50)] * 5, now=0.0)
        est.update(my_elixir, [_Det("barbarians", 0.50, 0.50)] * 3, now=1.0)   # recall miss (2 dropped)
        return est

    def test_B2_return_plus_new_play_charged_order_return_then_new(self):
        # The dropped group's 5 bodies return in ONE sample, displaced 0.09 (beyond match_radius=0.07, so
        # unmatched -> a fresh point R, n=5) TOGETHER WITH a genuinely new 5-body play N landing 0.16 from
        # the stale original track (within r_body=0.20). Processed in the order [R, N]: R is evaluated first
        # against the stale group (active_n=0, pending=0) -- 0+0+5=5<=5, JOINS (absorbed, "fills the
        # budget"). N is evaluated next -- 0+5(pending)+5=10>5, FAILS -> leftover -> new deployment,
        # ceil(5/5)=1 (5 elixir). Total: initial 5 + this tick's 5 = 10, regardless of which of R/N ends up
        # tagged into the original group (see the mirrored order test below).
        est = self._b2_setup()
        R = [_Det("barbarians", 0.59, 0.50)] * 5
        N = [_Det("barbarians", 0.66, 0.50)] * 5
        est.update(10.0, R + N, now=2.0)
        self.assertEqual(est._opp_spent, 10.0, "return + genuine new play must charge in full")

    def test_B2_return_plus_new_play_charged_order_new_then_return(self):
        # Same scenario, dets given in the OPPOSITE order (N before R) -- the `pending` fix makes the
        # RESULT order-independent even though N (not R) is the one that ends up absorbed for free this
        # time: 0+0+5=5<=5 joins first, then R sees 0+5+5=10>5 and becomes the new charge instead. Same
        # total either way: 10.
        est = self._b2_setup()
        R = [_Det("barbarians", 0.59, 0.50)] * 5
        N = [_Det("barbarians", 0.66, 0.50)] * 5
        est.update(10.0, N + R, now=2.0)
        self.assertEqual(est._opp_spent, 10.0, "order must not change the total: still charged in full")

    def test_B4_return_plus_two_new_plays_charged_fifteen(self):
        # Return (n=5) + TWO genuinely new 5-body plays, all in one sample. Whichever is processed first
        # claims the stale group's budget for free (0+0+5<=5); the other TWO both fail to join (pending now
        # 5) and are pooled together as leftover: total_n=5+5=10, ceil(10/5)=2 new charges (10 elixir).
        # Total: initial 5 + this tick's 10 = 15. my_elixir=15.0 (not 10.0) keeps `est` inside [0,10] after
        # every one of the three charges (10, 5, 0) -- see the R3 ablation test's own comment on why a fixed,
        # non-regenerating my_elixir must be sized to the total for a raw `_opp_spent` check to be valid.
        db = _FakeDB({"barbarians": 5})
        est = OpponentElixirEstimatorV2(db, speed_aware_radius=False)
        est.reset(my_elixir=15.0, now=0.0)
        est.update(15.0, [_Det("barbarians", 0.50, 0.50)] * 5, now=0.0)
        est.update(15.0, [_Det("barbarians", 0.50, 0.50)] * 3, now=1.0)
        R = [_Det("barbarians", 0.59, 0.50)] * 5
        N1 = [_Det("barbarians", 0.66, 0.50)] * 5
        N2 = [_Det("barbarians", 0.90, 0.50)] * 5
        est.update(15.0, R + N1 + N2, now=2.0)
        self.assertEqual(est._opp_spent, 15.0, "return + two new plays must charge both new plays in full")

    def test_C2_stale_group_plus_two_new_plays_pooled_charged_three(self):
        # A pre-existing ("stale") skeleton group (already charged once, cost 1) sits well outside r_body
        # (0.20) of two GENUINELY NEW skeleton plays that land in the SAME sample, 0.15 apart from each
        # other (> cluster_radius=0.10, so they remain two separate cluster points rather than merging into
        # one). Construction note (stated explicitly, since the ticket's prose geometry for this scenario
        # was ambiguous about which distances are measured from what): here the stale group does not
        # participate in absorption at all (it is placed beyond r_body of both new plays) -- neither new
        # play can join it, so both become "leftover" and are POOLED together per the existing, unmodified
        # R2/R5 batch-pooling rule (test j, above): total_n = 3 + 3 = 6, cap = 3, ceil(6/3) = 2 new charges
        # (2 elixir) -- numerically identical here to the two independent ceil(3/3)=1 contributions the
        # ticket's own hint describes, since 6 divides the cap evenly either way. Total: initial 1 + this
        # tick's 2 = 3.
        db = _FakeDB({"skeletons": 1})
        est = OpponentElixirEstimatorV2(db, speed_aware_radius=False)
        est.reset(my_elixir=10.0, now=0.0)
        est.update(10.0, [_Det("skeletons", 0.10, 0.50)] * 3, now=0.0)   # the stale group, charged once
        self.assertEqual(est._opp_spent, 1.0)
        play_a = [_Det("skeletons", 0.70, 0.50)] * 3
        play_b = [_Det("skeletons", 0.85, 0.50)] * 3   # 0.15 from play_a
        est.update(10.0, play_a + play_b, now=2.0)
        self.assertEqual(est._opp_spent, 3.0, "two new plays, neither near the stale group, both charge")



# ------------------------------------------------------------------------------------------------------
# R6 (O15) -- SPAWNS additions (skeleton_barrel)
# ------------------------------------------------------------------------------------------------------
class TestR6SpawnsAdditions(unittest.TestCase):
    def test_skeleton_barrel_self_label_not_charged(self):
        db = _FakeDB({"skeleton_barrel": 3, "skeletons": 1})
        est = OpponentElixirEstimatorV2(db)
        est.reset(my_elixir=10.0, now=0.0)
        est.update(10.0, [_Det("skeleton_barrel", 0.50, 0.50)], now=0.0)
        self.assertEqual(est._opp_spent, 3.0)
        est.update(10.0, [_Det("skeleton_barrel", 0.50, 0.50), _Det("skeleton_barrel", 0.55, 0.50)], now=1.0)
        self.assertEqual(est._opp_spent, 3.0, "second skeleton_barrel-labelled body near the track must not charge")

    def test_skeletons_near_skeleton_barrel_not_charged(self):
        db = _FakeDB({"skeleton_barrel": 3, "skeletons": 1})
        est = OpponentElixirEstimatorV2(db)
        est.reset(my_elixir=10.0, now=0.0)
        est.update(10.0, [_Det("skeleton_barrel", 0.50, 0.50)], now=0.0)
        self.assertEqual(est._opp_spent, 3.0)
        est.update(10.0, [_Det("skeleton_barrel", 0.50, 0.50), _Det("skeletons", 0.55, 0.50)], now=1.0)
        self.assertEqual(est._opp_spent, 3.0, "the barrel's own skeletons, 0.05 away, must not charge")


# ------------------------------------------------------------------------------------------------------
# R7 (O15) -- r_spawn 0.084 -> 0.12
# ------------------------------------------------------------------------------------------------------
class TestR7RSpawnRaised(unittest.TestCase):
    def test_witch_self_label_0_10_away_not_charged_at_new_r_spawn(self):
        db = _FakeDB({"witch": 4})
        est = OpponentElixirEstimatorV2(db)                 # default r_spawn = 0.12
        est.reset(my_elixir=10.0, now=0.0)
        est.update(10.0, [_Det("witch", 0.50, 0.50)], now=0.0)
        self.assertEqual(est._opp_spent, 4.0)
        est.update(10.0, [_Det("witch", 0.60, 0.50)], now=1.0)   # 0.10 away -- beyond old 0.084, within new 0.12
        self.assertEqual(est._opp_spent, 4.0, "must not charge at the raised r_spawn")

    def test_same_scenario_charged_at_old_r_spawn(self):
        # demonstrates the fix was necessary: at the OLD 0.084, 0.10 away is NOT suppressed by R1 -> charged.
        # singleton_resight (R4) is ALSO default-ON and, independently, would suppress this same scenario
        # (witch is itself a singleton base -- absent from BODIES -- and the two detections are only 1.0s
        # apart, inside singleton_window_s=4.0); disabled here to isolate R1/R7 alone, per this test's own
        # purpose. This R4/R7 overlap on the witch residual is noted in O15_v21.md.
        db = _FakeDB({"witch": 4})
        est = OpponentElixirEstimatorV2(db, r_spawn=0.084, singleton_resight=False)
        est.reset(my_elixir=10.0, now=0.0)
        est.update(10.0, [_Det("witch", 0.50, 0.50)], now=0.0)
        est.update(10.0, [_Det("witch", 0.60, 0.50)], now=1.0)
        self.assertEqual(est._opp_spent, 8.0, "at the old r_spawn this residual was charged -- O15_v21.md")


# ------------------------------------------------------------------------------------------------------
# All rules off => byte-for-byte same tracking/charging decisions as V1 (same match_radius,
# cluster_radius, forget_s, one-charge-per-cluster, no suppression).
# ------------------------------------------------------------------------------------------------------
class TestAblationAllOffMatchesV1(unittest.TestCase):
    def _run(self, cls, db, seq, **kwargs):
        est = cls(db, **kwargs) if kwargs else cls(db)
        est.reset(my_elixir=5.0, now=0.0)
        out = []
        for my_elixir, dets, now, my_play in seq:
            if my_play:
                est.record_my_play(my_play)
            out.append(round(est.update(my_elixir, dets, now), 6))
        return out, est._opp_spent, len(est._tracks)

    def test_matches_v1_on_a_mixed_scenario(self):
        db = _FakeDB({"tombstone": 3, "skeletons": 1, "bandit": 3, "skeleton_army": 3},
                     speeds={"bandit": 6.0})
        seq = [
            (5.0, [_Det("tombstone", 0.50, 0.50)], 0.0, None),
            (5.0, [_Det("tombstone", 0.50, 0.50), _Det("skeletons", 0.55, 0.50)], 1.0, None),
            (5.0, [_Det("bandit", 0.20, 0.20)], 2.0, None),
            (5.0, [_Det("bandit", 0.32, 0.20)], 2.25, None),
            (5.0, [_Det("skeleton_army", 0.10 + 0.15 * i, 0.10) for i in range(3)], 3.0, None),
        ]
        v1_out, v1_spent, v1_ntracks = self._run(OpponentElixirEstimator, db, seq)
        v2_out, v2_spent, v2_ntracks = self._run(
            OpponentElixirEstimatorV2, db, seq,
            suppress_spawns=False, body_count=False, speed_aware_radius=False,
        )
        self.assertEqual(v1_out, v2_out)
        self.assertEqual(v1_spent, v2_spent)
        self.assertEqual(v1_ntracks, v2_ntracks)

    def test_matches_v1_with_all_five_rules_off(self):
        # O15: a scenario where R4 (singleton re-sighting, 2.0s gap -- inside singleton_window_s=4.0) and R5
        # (body-count grouping) would BOTH change the outcome if left at their default-ON, so all 5 kwargs
        # must be explicitly False to reproduce V1's over-billing here.
        db = _FakeDB({"miner": 3, "skeletons": 1})
        seq = [
            (10.0, [_Det("miner", 0.5, 0.5)], 0.0, None),
            (10.0, [_Det("miner", 0.5, 0.9)], 2.0, None),      # far away, 2.0s gap: R4-on would suppress this
            (10.0, [_Det("skeletons", 0.10 + 0.15 * i, 0.10) for i in range(3)], 3.0, None),
        ]
        v1_out, v1_spent, v1_ntracks = self._run(OpponentElixirEstimator, db, seq)
        v2_out, v2_spent, v2_ntracks = self._run(
            OpponentElixirEstimatorV2, db, seq,
            suppress_spawns=False, body_count=False, speed_aware_radius=False,
            singleton_resight=False, lifetime_absorb=False,
        )
        self.assertEqual(v1_out, v2_out)
        self.assertEqual(v1_spent, v2_spent)
        self.assertEqual(v1_ntracks, v2_ntracks)
        self.assertEqual(v1_spent, 3.0 + 3.0 + 3.0, "sanity: both miner plays and all 3 skeletons charged")


# ------------------------------------------------------------------------------------------------------
# V2_PARAMS sanity -- every constant this class's DEFAULTS actually use must be logged (ticket 3).
# ------------------------------------------------------------------------------------------------------
class TestV2ParamsLogged(unittest.TestCase):
    def test_defaults_match_v2_params(self):
        db = _FakeDB({})
        est = OpponentElixirEstimatorV2(db)
        self.assertEqual(est.r_spawn, V2_PARAMS["r_spawn"])
        self.assertEqual(est.r_body, V2_PARAMS["r_body"])
        self.assertEqual(est.body_group_window_s, V2_PARAMS["body_group_window_s"])
        self.assertEqual(est.speed_k, V2_PARAMS["speed_k"])
        self.assertEqual(est.speed_radius_cap, V2_PARAMS["speed_radius_cap"])
        self.assertEqual(est.match_radius, V2_PARAMS["match_radius"])
        self.assertEqual(est.cluster_radius, V2_PARAMS["cluster_radius"])
        self.assertEqual(est.forget_s, V2_PARAMS["forget_s"])
        self.assertIs(est.spawns, SPAWNS)
        self.assertIs(est.bodies, BODIES)
        # O15
        self.assertEqual(est.singleton_window_s, V2_PARAMS["singleton_window_s"])
        self.assertEqual(est.singleton_double_window_s, V2_PARAMS["singleton_double_window_s"])
        self.assertTrue(est.singleton_resight)
        self.assertTrue(est.lifetime_absorb)


if __name__ == "__main__":
    unittest.main()
