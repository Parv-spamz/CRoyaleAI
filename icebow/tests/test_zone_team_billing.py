"""O12: TeamTracker bills opponent SPELL ZONES ("_aoe" ground-effect classes) as 'enemy' by
default, so opponent_elixir.py (which only bills d.team == "enemy") can see them.

Effect-zone classes (poison_aoe, graveyard_aoe, rage_aoe, freeze_aoe, earthquake_aoe,
tornado_aoe, ...; pipeline.vocab.AOE_CLASSES) are stationary, unbodied VFX: no motion, no HP
bar, and no reliable body-art majority. Before this change, `_verdict`'s ladder abstained
("unknown") for a mid-board zone, and its generic side prior (rank 4) could actively MISREAD an
enemy zone landing deep in the player's own half as "mine" (measured pre-patch, see
scratchpad/gauntlet/L67/opp_fix/O12_spells.md section 2). The OWN-PLAY ANCHOR (rank 1) already
covered the "mine" case for zones with no code change, because Detection.base already strips
"_aoe" (base_key), so a recorded own play with base="poison" already matches a poison_aoe
detection. What was missing was the "no anchor" default, added here.

ATTEMPT 2 (F1, the blind verifier's live-risk note): the attempt-1 "no anchor -> enemy" default
also caught MY OWN zone whenever the anchor missed -- a zone's detected centroid drifts further
from the tap than a troop's (0.14 offset, just outside spawn_radius 0.10), or it can be first
recognised a beat later (3.0 s, just outside spawn_window_s 2.5) -- so it could get billed to the
opponent instead of resolving 'unknown' the way the pre-O12 ladder always did for an unrecognised
own zone. Two fixes, both covered below: (1) a DECK GUARD -- a zone whose base IS in
`self.own_cards` never gets the forced-enemy default, it falls through to the unchanged
`_verdict` ladder instead; (2) ZONE_ANCHOR_RADIUS (0.16) / ZONE_ANCHOR_WINDOW_S (3.5), a looser
anchor tolerance used ONLY for zone-class dets -- the troop/building anchor (sr2 / spawn_window_s
/ enemy_window_s) is untouched, checked here against a dynamically loaded copy of the pre-O12
module (the backup .orig) rather than a hand-computed expectation.
"""
from __future__ import annotations

import importlib.machinery
import importlib.util
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import clashrl  # noqa: E402  -- registers the package so the old module's relative imports resolve
from clashrl.replay_mine import (  # noqa: E402
    Detection, TeamTracker, ZONE_ANCHOR_RADIUS, ZONE_ANCHOR_WINDOW_S,
)

OWN = ["knight", "tesla", "x_bow", "skeletons", "the_log"]
OWN_WITH_TORNADO = OWN + ["tornado"]

#: The attempt-1 backup, i.e. the code as it stood BEFORE the F1 deck-guard/tolerance fix (attempt
#: 1's TeamTracker.tag), loaded as a real module so the "unchanged for troops" / "falls through to
#: the old ladder for a deck-owned zone" tests compare against its ACTUAL behaviour instead of a
#: hand-typed expectation that could itself be wrong.
_BACKUP_PATH = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", "..", "scratchpad", "gauntlet", "L67", "opp_fix",
    "backup", "replay_mine.py.orig"))


def _load_old_module():
    name = "clashrl._replay_mine_o12_attempt1"
    if name in sys.modules:
        return sys.modules[name]
    loader = importlib.machinery.SourceFileLoader(name, _BACKUP_PATH)
    spec = importlib.util.spec_from_file_location(name, _BACKUP_PATH, loader=loader)
    mod = importlib.util.module_from_spec(spec)
    mod.__package__ = "clashrl"          # so `from . import card_threat` resolves
    sys.modules[name] = mod              # dataclass's postponed-annotation lookup needs this first
    spec.loader.exec_module(mod)
    return mod


def _det(cls, cx=0.5, cy=0.5, bar=None, body=None, mod=None):
    """``mod`` picks which module's ``Detection`` to build (default: the current clashrl.replay_mine);
    pass the old module from :func:`_load_old_module` to build one usable with ITS ``TeamTracker``."""
    det_cls = mod.Detection if mod is not None else Detection
    return det_cls(cls, cx, cy, 0.05, 0.05, 0.9, "unknown", None, bar, body)


class TestZoneOwnPlayAnchor(unittest.TestCase):
    def test_a_zone_near_my_own_play_is_mine(self):
        """poison_aoe appearing 0.3s after my own poison play at the same spot -> mine. The
        anchor already matches (base strips "_aoe"); this locks the behaviour in."""
        tr = TeamTracker()
        tr.record_play(0.5, 0.5, 0.0, base="poison")
        d = _det("poison_aoe", cx=0.5, cy=0.5)
        tr.tag([d], 0.3)
        self.assertEqual("mine", d.team)


class TestZoneNoAnchorDefaultsToEnemy(unittest.TestCase):
    def test_a_zone_with_no_anchor_is_enemy(self):
        """Same det, no own-play anchor recorded -> enemy (mid-board: the ladder used to abstain
        with 'unknown', which the estimator never bills)."""
        tr = TeamTracker()
        d = _det("poison_aoe", cx=0.5, cy=0.5)
        tr.tag([d], 0.0)
        self.assertEqual("enemy", d.team)

    def test_a_zone_deep_in_my_half_with_no_anchor_is_still_enemy(self):
        """The bug this rule also fixes: an enemy zone landing deep in MY half used to be
        misread 'mine' by the generic side prior (rank 4) -- never billed, worst case."""
        tr = TeamTracker()
        d = _det("poison_aoe", cx=0.5, cy=0.73)
        tr.tag([d], 0.0)
        self.assertEqual("enemy", d.team)


class TestZoneStickiness(unittest.TestCase):
    def test_an_enemy_zone_verdict_survives_a_later_nearby_own_play(self):
        """A zone assigned 'enemy' (no anchor at first sighting) stays 'enemy' on later frames
        even if a later own play lands nearby -- once assigned, sticky for the track's life."""
        tr = TeamTracker()
        d0 = _det("poison_aoe", cx=0.5, cy=0.5)
        tr.tag([d0], 0.0)
        self.assertEqual("enemy", d0.team)
        tr.record_play(0.5, 0.5, 0.5, base="poison")   # a later own play lands right on top of it
        d1 = _det("poison_aoe", cx=0.5, cy=0.5)
        tr.tag([d1], 0.6)
        self.assertEqual("enemy", d1.team)


class TestNonZoneLadderUnchanged(unittest.TestCase):
    def test_a_troop_verdict_is_identical_to_before_this_change(self):
        """Fixture from test_team_veto.py's mirror-case test: a troop class never matches
        ZONE_CLASSES, so it must still go through the unmodified _verdict ladder."""
        d = _det("knight", cy=0.73)
        TeamTracker(own_cards=OWN).tag([d], 0.0)
        self.assertEqual("mine", d.team)      # unchanged: rank-4 side prior, deck veto passes it


class TestZoneDeckGuard(unittest.TestCase):
    """F1 fix 1: a zone whose card IS in my own deck must never be FORCED to 'enemy' just because
    the anchor missed -- it falls through to the unchanged `_verdict` ladder instead, exactly as
    the pre-O12 code (the attempt-1 backup) would resolve it."""

    def test_a_deck_owned_zone_with_no_anchor_matches_the_old_module_exactly(self):
        old = _load_old_module()
        old_tr = old.TeamTracker(own_cards=OWN_WITH_TORNADO)
        od = _det("tornado_aoe", cx=0.5, cy=0.5, mod=old)
        old_tr.tag([od], 0.0)

        new_tr = TeamTracker(own_cards=OWN_WITH_TORNADO)
        nd = _det("tornado_aoe", cx=0.5, cy=0.5)
        new_tr.tag([nd], 0.0)

        self.assertEqual(od.team, nd.team)          # both fall through to _verdict -> 'unknown'
        self.assertEqual("unknown", nd.team)

    def test_a_non_deck_zone_with_no_anchor_is_still_enemy(self):
        """Unchanged from attempt 1: 'poison' is not in this deck, so the default still applies."""
        tr = TeamTracker(own_cards=OWN)          # OWN holds no poison
        d = _det("poison_aoe", cx=0.5, cy=0.5)
        tr.tag([d], 0.0)
        self.assertEqual("enemy", d.team)

    def test_stickiness_still_holds_for_the_non_deck_case(self):
        tr = TeamTracker(own_cards=OWN)
        d0 = _det("poison_aoe", cx=0.5, cy=0.5)
        tr.tag([d0], 0.0)
        self.assertEqual("enemy", d0.team)
        tr.record_play(0.5, 0.5, 0.5, base="poison")
        d1 = _det("poison_aoe", cx=0.5, cy=0.5)
        tr.tag([d1], 0.6)
        self.assertEqual("enemy", d1.team)


class TestZoneAnchorTolerance(unittest.TestCase):
    """F1 fix 2: ZONE_ANCHOR_RADIUS/ZONE_ANCHOR_WINDOW_S widen the anchor ONLY for zone-class
    dets; a troop's anchor radius/window must stay exactly what the pre-O12 module used."""

    def test_a_zone_0_14_from_the_tap_is_mine_under_the_wider_radius(self):
        self.assertLess(0.10, 0.14)                 # > spawn_radius (troop radius)
        self.assertLessEqual(0.14, ZONE_ANCHOR_RADIUS)
        tr = TeamTracker()
        tr.record_play(0.5, 0.5, 0.0, base="tornado")
        d = _det("tornado_aoe", cx=0.5 + 0.14, cy=0.5)
        tr.tag([d], 0.3)
        self.assertEqual("mine", d.team)

    def test_a_knight_0_14_from_the_tap_matches_the_old_module_unchanged(self):
        """Same 0.14 offset, a TROOP class: 0.14 is outside spawn_radius (0.10) for both the old
        module and the new one, so both must fall through to `_verdict` identically."""
        old = _load_old_module()
        old_tr = old.TeamTracker(own_cards=OWN)
        old_tr.record_play(0.5, 0.5, 0.0, base="knight")
        od = _det("knight", cx=0.5 + 0.14, cy=0.5, mod=old)
        old_tr.tag([od], 0.3)

        new_tr = TeamTracker(own_cards=OWN)
        new_tr.record_play(0.5, 0.5, 0.0, base="knight")
        nd = _det("knight", cx=0.5 + 0.14, cy=0.5)
        new_tr.tag([nd], 0.3)

        self.assertEqual(od.team, nd.team)

    def test_a_zone_seen_3_2s_later_is_mine_under_the_wider_window(self):
        self.assertLess(2.5, 3.2)                    # > spawn_window_s (troop window)
        self.assertLessEqual(3.2, ZONE_ANCHOR_WINDOW_S)
        tr = TeamTracker(own_cards=OWN_WITH_TORNADO)
        tr.record_play(0.5, 0.5, 0.0, base="tornado")
        d = _det("tornado_aoe", cx=0.5, cy=0.5)
        tr.tag([d], 3.2)
        self.assertEqual("mine", d.team)

    def test_a_zone_seen_4_0s_later_is_past_even_the_wider_window(self):
        """4.0 s exceeds ZONE_ANCHOR_WINDOW_S (3.5) too: the anchor must miss, and (this deck owns
        tornado) the deck guard then routes to `_verdict`, matching the old module exactly."""
        self.assertGreater(4.0, ZONE_ANCHOR_WINDOW_S)
        old = _load_old_module()
        old_tr = old.TeamTracker(own_cards=OWN_WITH_TORNADO)
        old_tr.record_play(0.5, 0.5, 0.0, base="tornado")
        od = _det("tornado_aoe", cx=0.5, cy=0.5, mod=old)
        old_tr.tag([od], 4.0)

        new_tr = TeamTracker(own_cards=OWN_WITH_TORNADO)
        new_tr.record_play(0.5, 0.5, 0.0, base="tornado")
        nd = _det("tornado_aoe", cx=0.5, cy=0.5)
        new_tr.tag([nd], 4.0)

        self.assertEqual(od.team, nd.team)


if __name__ == "__main__":
    unittest.main()
