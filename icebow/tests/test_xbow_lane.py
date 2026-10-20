"""Put the offensive X-Bow in the lane that still has a tower.

Reported from live overtime (user, 2026-08-16), one tower down on each side: the model placed a
technically perfect offensive bow several times, and every one was in the lane whose enemy
princess was ALREADY DESTROYED. Six elixir, a good spot, nothing to chip -- the bow can then only
fall through to the king, which is far tankier and further away.

Nothing existing caught it. `xbow_lock_cell` snaps to the NEARER tower's lane, which is exactly
wrong when the nearer one is the dead one, and the depth assist only sets the row. Neither ever
asked whether the target was alive.
"""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from clashrl.actions import ActionSpace                  # noqa: E402
from clashrl.config import Config                        # noqa: E402
from clashrl.reward import xbow_target_lane_cell, xbow_lock_cell  # noqa: E402

# left / right enemy princess anchors, mirroring reward._anchors' layout
LEFT, RIGHT = (0.25, 0.205), (0.745, 0.205)
ANCHORS = [LEFT, RIGHT]
DEFENSE_Y = 0.52                     # below this row a bow is OFFENSIVE
FULL = 2500.0


class XbowLaneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.acts = ActionSpace(Config.load())

    def _lane_of(self, cell):
        gw = int(self.acts.gw)
        cx, _ = self.acts.cell_center(cell % gw, cell // gw)
        return "left" if abs(cx - LEFT[0]) < abs(cx - RIGHT[0]) else "right"

    def _call(self, cx, cy=0.50, hp=(FULL, FULL), alive=(True, True)):
        return xbow_target_lane_cell(cx, cy, ANCHORS, list(hp) if hp else None,
                                     list(alive), DEFENSE_Y, self.acts)

    # -- rule 1: never bow a dead lane ------------------------------------------------
    def test_a_bow_aimed_at_a_DEAD_left_tower_moves_right(self):
        got = self._call(cx=0.25, alive=(False, True))
        self.assertIsNotNone(got, "a bow in the dead lane must be moved")
        self.assertEqual(self._lane_of(got), "right")

    def test_a_bow_aimed_at_a_DEAD_right_tower_moves_left(self):
        got = self._call(cx=0.745, alive=(True, False))
        self.assertIsNotNone(got)
        self.assertEqual(self._lane_of(got), "left")

    def test_a_bow_already_on_the_live_tower_is_left_alone(self):
        self.assertIsNone(self._call(cx=0.745, alive=(False, True)))

    def test_both_towers_down_leaves_the_placement_alone(self):
        """Only the king is left; this rule has no opinion and must not thrash the placement."""
        self.assertIsNone(self._call(cx=0.25, alive=(False, False)))

    def test_the_dead_lane_rule_ignores_hp_entirely(self):
        """A destroyed tower cannot be chipped at any margin, so no HP gap can justify staying."""
        got = self._call(cx=0.25, hp=(0.0, FULL), alive=(False, True))
        self.assertEqual(self._lane_of(got), "right")

    # -- rule 2: concentrate on the weaker tower --------------------------------------
    def test_it_moves_to_the_clearly_weaker_tower(self):
        got = self._call(cx=0.25, hp=(FULL, FULL * 0.5))
        self.assertIsNotNone(got, "should concentrate on the weaker (right) tower")
        self.assertEqual(self._lane_of(got), "right")

    def test_a_near_tie_does_NOT_move_the_bow(self):
        """Without a margin the lane would flap between placements on ordinary chip damage."""
        self.assertIsNone(self._call(cx=0.25, hp=(FULL, FULL * 0.96)))

    def test_it_stays_when_already_on_the_weaker_tower(self):
        self.assertIsNone(self._call(cx=0.25, hp=(FULL * 0.4, FULL)))

    # -- scope --------------------------------------------------------------------
    def test_a_DEFENSIVE_bow_is_never_touched(self):
        """Deep in our half the bow is a second pull building, not a tower aim."""
        self.assertIsNone(self._call(cx=0.25, cy=0.60, alive=(False, True)))

    def test_missing_hp_readings_disable_only_the_weaker_rule(self):
        """The live digit read can fail; the dead-lane rule must still work without HP."""
        self.assertIsNone(self._call(cx=0.25, hp=None))
        got = xbow_target_lane_cell(0.25, 0.50, ANCHORS, None, [False, True], DEFENSE_Y, self.acts)
        self.assertEqual(self._lane_of(got), "right")

    def test_the_depth_row_is_preserved(self):
        """Depth belongs to xbow_offense_depth_cell; this rule only changes the lane."""
        gw = int(self.acts.gw)
        for cy in (0.47, 0.50):
            with self.subTest(cy=cy):
                got = self._call(cx=0.25, cy=cy, alive=(False, True))
                self.assertEqual(got // gw, self.acts.cell_at(0.745, cy) // gw)


class XbowDeadLaneAnyDepthTests(unittest.TestCase):
    """L67bz: the owner reported dead-lane bows a THIRD time (2026-08-16, then twice on 2026-09-18),
    after two rounds of "fixes" that changed nothing. Cause: rule 1 ("never bow a dead lane") sat
    behind `cy >= defense_y`, and every bow the model actually plays sits at board y 0.61 -- BEHIND
    that cut. So the rule returned None before it could ever run. `dead_lane_any_depth=True` runs
    rule 1 at any depth; rule 2 (weaker tower) stays offensive-only on purpose.
    """

    @classmethod
    def setUpClass(cls):
        cls.acts = ActionSpace(Config.load())

    def _lane_of(self, cell):
        gw = int(self.acts.gw)
        cx, _ = self.acts.cell_center(cell % gw, cell // gw)
        return "left" if abs(cx - LEFT[0]) < abs(cx - RIGHT[0]) else "right"

    def _call(self, cx, cy, alive, hp=(FULL, FULL), any_depth=True):
        return xbow_target_lane_cell(cx, cy, ANCHORS, list(hp) if hp else None, list(alive),
                                     DEFENSE_Y, self.acts, dead_lane_any_depth=any_depth)

    # -- the precondition: this is exactly what was broken -----------------------------
    def test_PRECONDITION_the_old_default_leaves_a_defensive_dead_lane_bow_alone(self):
        """Without the flag the bug reproduces: a DEFENSIVE bow in the dead left lane is untouched.
        If this ever starts returning a cell, the fix below is no longer testing anything."""
        self.assertIsNone(self._call(cx=0.25, cy=0.60, alive=(False, True), any_depth=False))

    def test_a_DEFENSIVE_bow_in_the_dead_lane_now_moves_to_the_live_lane(self):
        got = self._call(cx=0.25, cy=0.60, alive=(False, True))
        self.assertIsNotNone(got, "the owner's exact complaint: bows kept going to the dead lane")
        self.assertEqual(self._lane_of(got), "right")

    def test_the_mirror_case_dead_right_moves_left(self):
        got = self._call(cx=0.745, cy=0.60, alive=(True, False))
        self.assertIsNotNone(got)
        self.assertEqual(self._lane_of(got), "left")

    def test_a_defensive_bow_already_on_the_live_lane_is_left_alone(self):
        self.assertIsNone(self._call(cx=0.745, cy=0.60, alive=(False, True)))

    def test_both_towers_down_leaves_it_alone_and_never_aims_at_the_king(self):
        self.assertIsNone(self._call(cx=0.25, cy=0.60, alive=(False, False)))

    def test_it_works_without_any_hp_reading(self):
        """The live HP digit read fails often; a correctness rule must not depend on it."""
        got = self._call(cx=0.25, cy=0.60, alive=(False, True), hp=None)
        self.assertEqual(self._lane_of(got), "right")

    def test_the_depth_row_is_still_preserved(self):
        gw = int(self.acts.gw)
        for cy in (0.55, 0.60, 0.65):
            with self.subTest(cy=cy):
                got = self._call(cx=0.25, cy=cy, alive=(False, True))
                self.assertEqual(got // gw, self.acts.cell_at(0.745, cy) // gw)

    # -- scope: rule 2 must NOT leak to defensive bows ---------------------------------
    def test_the_weaker_tower_rule_does_NOT_apply_to_a_defensive_bow(self):
        """Rule 2 is an attacking preference. Chasing HP could drag a defensive bow off the lane
        it was placed to defend, so the flag must not enable it."""
        self.assertIsNone(self._call(cx=0.25, cy=0.60, alive=(True, True), hp=(FULL, FULL * 0.4)))

    # -- regression: offensive behaviour is unchanged ----------------------------------
    def test_offensive_behaviour_is_identical_with_and_without_the_flag(self):
        for cx, cy, alive, hp in ((0.25, 0.50, (False, True), (FULL, FULL)),
                                  (0.745, 0.50, (False, True), (FULL, FULL)),
                                  (0.25, 0.50, (True, True), (FULL, FULL * 0.5)),
                                  (0.25, 0.50, (True, True), (FULL, FULL * 0.96)),
                                  (0.25, 0.50, (False, False), (FULL, FULL))):
            with self.subTest(cx=cx, alive=alive, hp=hp):
                self.assertEqual(self._call(cx, cy, alive, hp, any_depth=True),
                                 self._call(cx, cy, alive, hp, any_depth=False))


class XbowLockDeadLaneTests(unittest.TestCase):
    """O22: play.py:1101-1109 runs xbow_target_lane_cell (moves off a dead lane) and THEN
    xbow_lock_cell (snaps to the NEARER princess, no aliveness check at all) unconditionally.
    Two lines later the lock could undo the lane fix by re-snapping onto the nearer-but-dead
    tower. ``enemy_alive`` on xbow_lock_cell closes that: filter the candidate princesses by
    aliveness BEFORE picking the nearer one, so a dead lane is never a candidate again.
    """

    @classmethod
    def setUpClass(cls):
        cls.acts = ActionSpace(Config.load())

    def _lane_of(self, cell):
        gw = int(self.acts.gw)
        cx, _ = self.acts.cell_center(cell % gw, cell // gw)
        return "left" if abs(cx - LEFT[0]) < abs(cx - RIGHT[0]) else "right"

    def _lock(self, cx, cy=0.50, xbow_range=0.36, alive=None):
        if alive is None:
            return xbow_lock_cell(cx, cy, ANCHORS, xbow_range, DEFENSE_Y, self.acts)
        return xbow_lock_cell(cx, cy, ANCHORS, xbow_range, DEFENSE_Y, self.acts, enemy_alive=alive)

    # -- 1. both alive: the new keyword must not change anything -----------------------
    def test_both_alive_matches_the_default_None_path_already_in_range(self):
        """cx on the RIGHT anchor, cy=0.50: distance to RIGHT is hypot(0, 0.295)=0.295 <= 0.36,
        so both the untouched default path and an explicit alive=(True, True) must leave it (None)."""
        cx, cy, rng = RIGHT[0], 0.50, 0.36
        old = self._lock(cx, cy, rng)
        new = self._lock(cx, cy, rng, alive=(True, True))
        self.assertIsNone(old)
        self.assertEqual(old, new)

    def test_both_alive_matches_the_default_None_path_out_of_range(self):
        """cx=0.50 (midway): RIGHT is hypot(0.245,0.295)=0.3835 away, LEFT is hypot(0.25,0.295)=0.3867
        -- RIGHT is nearer and both are > 0.36, so both paths must snap to the RIGHT lane."""
        cx, cy, rng = 0.50, 0.50, 0.36
        old = self._lock(cx, cy, rng)
        new = self._lock(cx, cy, rng, alive=(True, True))
        self.assertIsNotNone(old)
        self.assertEqual(old, new)
        self.assertEqual(self._lane_of(old), "right")

    # -- 2. nearer DEAD, farther alive, out of range: must snap to the farther (alive) lane --
    def test_nearer_dead_farther_alive_snaps_to_the_farther_lane(self):
        """cx=0.40 (nearer to LEFT): LEFT is hypot(0.15,0.295)=0.331 away, RIGHT is
        hypot(0.345,0.295)=0.454 away. At range=0.30 BOTH are out of range, so the unfiltered
        (buggy) default snaps to the nearer one -- LEFT, which is dead. Filtered by
        alive=(False, True), LEFT is not a candidate at all, so it must snap to RIGHT instead."""
        cx, cy, rng = 0.40, 0.50, 0.30
        buggy = self._lock(cx, cy, rng)                       # today's behaviour: ignores aliveness
        self.assertIsNotNone(buggy)
        self.assertEqual(self._lane_of(buggy), "left", "precondition: the unfiltered lock picks the dead lane")
        fixed = self._lock(cx, cy, rng, alive=(False, True))
        self.assertIsNotNone(fixed)
        self.assertEqual(self._lane_of(fixed), "right")

    # -- 3. both dead: never redirect toward the king -----------------------------------
    def test_both_dead_returns_None_never_aims_at_the_king(self):
        got = self._lock(0.40, 0.50, 0.30, alive=(False, False))
        self.assertIsNone(got, "no live princess left: leave the model's own cell, never aim at the king")

    # -- 4. the full play.py sequence: lane fix, then lock, must land in the LIVE lane ---
    def test_the_play_sequence_lane_fix_then_lock_stays_in_the_live_lane(self):
        """Reproduces play.py:1101-1109 in order: the model aimed at the DEAD left tower,
        xbow_target_lane_cell moves it to the live right lane, and the (filtered) lock -- forced
        to re-snap by a deliberately tiny range -- must not undo that move back onto the left lane."""
        alive = [False, True]
        gw = int(self.acts.gw)
        cx, cy = LEFT[0], 0.50                     # model's own placement: dead (left) lane
        lane = xbow_target_lane_cell(cx, cy, ANCHORS, None, alive, DEFENSE_Y, self.acts)
        self.assertIsNotNone(lane, "precondition: the dead-lane rule must fire")
        cell = lane
        cx, cy = self.acts.cell_center(cell % gw, cell // gw)
        snapped = xbow_lock_cell(cx, cy, ANCHORS, 0.05, DEFENSE_Y, self.acts, enemy_alive=alive)
        if snapped is not None:
            cell = snapped
        self.assertEqual(self._lane_of(cell), "right", "the lock must not re-snap back onto the dead lane")

    # -- 5. a deep/defensive bow is untouched, exactly as today --------------------------
    def test_a_DEFENSIVE_bow_still_returns_None_with_alive_passed(self):
        got = self._lock(LEFT[0], cy=0.60, xbow_range=0.30, alive=(False, True))
        self.assertIsNone(got)


if __name__ == "__main__":
    unittest.main()
