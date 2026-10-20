"""Opponent elixir inference from observable card-play events.

Live play cannot read the enemy elixir bar directly. This tracker follows the deterministic
relationship

    enemy_elixir ~= my_elixir + my_spend - enemy_spend

where my_elixir is read from OCR, my_spend is known from our own plays, and enemy_spend is inferred
from newly observed enemy card appearances.

The event detector is intentionally simple and robust: enemy detections are matched to short-lived
tracks by (base card, proximity) so one long-lived unit is not charged repeatedly, and clustered on
spawn so swarm cards are charged once per play rather than once per body.
"""
from __future__ import annotations

from typing import Iterable, List


class OpponentElixirEstimator:
    def __init__(self, db, match_radius: float = 0.07, cluster_radius: float = 0.10,
                 forget_s: float = 6.0):
        self.db = db
        self.match_radius = float(match_radius)
        self.cluster_radius = float(cluster_radius)
        self.forget_s = float(forget_s)
        self.reset()

    def reset(self, my_elixir: float = 5.0, now: float | None = None) -> None:
        self._my_spent = 0.0
        self._opp_spent = 0.0
        self._tracks: list[dict] = []      # {base, x, y, t}
        self._est = float(max(0.0, min(10.0, my_elixir)))
        self._rebase = 0.0                 # cumulative saturation correction, for grading the estimator
        self._last_t = float(now) if now is not None else None

    def record_my_play(self, base: str) -> None:
        c = float(self.db.elixir(base) or 0.0)
        if c > 0.0:
            self._my_spent += c

    def _seen_tracks(self, now: float) -> None:
        self._tracks = [tr for tr in self._tracks if now - tr["t"] <= self.forget_s]

    def _find_track(self, base: str, x: float, y: float):
        best = None
        best_d2 = self.match_radius * self.match_radius
        for tr in self._tracks:
            if tr["base"] != base:
                continue
            dx = x - tr["x"]
            dy = y - tr["y"]
            d2 = dx * dx + dy * dy
            if d2 <= best_d2:
                best, best_d2 = tr, d2
        return best

    def _cluster_new(self, fresh: List[tuple[str, float, float]]) -> List[tuple[str, float, float]]:
        """Cluster new detections by base + proximity so swarms cost one card play, not N bodies."""
        out = []
        rem = list(fresh)
        r2 = self.cluster_radius * self.cluster_radius
        while rem:
            base, x, y = rem.pop()
            xs, ys, n = x, y, 1
            keep = []
            for b2, x2, y2 in rem:
                if b2 != base:
                    keep.append((b2, x2, y2))
                    continue
                dx = x2 - x
                dy = y2 - y
                if dx * dx + dy * dy <= r2:
                    xs += x2
                    ys += y2
                    n += 1
                else:
                    keep.append((b2, x2, y2))
            rem = keep
            out.append((base, xs / n, ys / n))
        return out

    def update(self, my_elixir: float, enemy_dets: Iterable, now: float) -> float:
        """Return normalized estimated enemy elixir in [0, 1].

        enemy_dets should contain detections with `.base`, `.cx`, `.gy`, and `.team` where team is
        already resolved to "enemy"/"mine".
        """
        now = float(now)
        self._seen_tracks(now)

        fresh = []
        for d in enemy_dets:
            if getattr(d, "team", None) != "enemy":
                continue
            base = str(getattr(d, "base", "") or "")
            if not base:
                continue
            x = float(getattr(d, "cx", 0.5))
            y = float(getattr(d, "gy", 0.5))
            tr = self._find_track(base, x, y)
            if tr is not None:
                tr["x"], tr["y"], tr["t"] = x, y, now
            else:
                fresh.append((base, x, y))

        for base, x, y in self._cluster_new(fresh):
            self._tracks.append({"base": base, "x": x, "y": y, "t": now})
            c = float(self.db.elixir(base) or 0.0)
            if c > 0.0:
                self._opp_spent += c

        est = float(my_elixir) + self._my_spent - self._opp_spent
        # L67g -- RE-BASELINE ON SATURATION, instead of clipping the output and keeping the bad books.
        # The accounting is exact only if EVERY enemy play is seen: both players regenerate at the same
        # rate, so opp = my_elixir + (what I spent) - (what they spent). Live, the detector misses enemy
        # plays, `_opp_spent` runs low, and `est` drifts UP for the rest of the match -- the clip below used
        # to hide that in the returned value while the next update recomputed from the same inflated base,
        # so the estimate RATCHETED to a pinned 10 and stayed there. Nobody can hold more than 10 elixir, so
        # an overflow IS the evidence of a missed play: charge it to `_opp_spent` and the books recover.
        # Symmetrically, going below 0 means a play was double-counted, so give it back.
        if est > 10.0:
            self._opp_spent += est - 10.0
            self._rebase += est - 10.0                 # diagnostic: total correction charged to the books
            est = 10.0
        elif est < 0.0:
            self._opp_spent += est                     # est < 0 -> reduces _opp_spent
            self._rebase += est
            est = 0.0
        self._est = est
        self._last_t = now
        return self._est / 10.0


# ==========================================================================================================
# TICKET O13 -- OpponentElixirEstimatorV2: a NEW class beside the one above, which stays byte-for-byte
# unchanged (the audit harness's baseline numbers for it must not move). Fixes the over-billing measured in
# O10's charge trace (scratchpad/gauntlet/L67/e1/opp_est/trace_0_5/charges.jsonl, 195 charges over 5 matches
# vs. 70 first_seen): 92 "split" (spawner output sharing/naming the parent's class, or a multi-body card
# scattering past cluster_radius), 25 "rebill_out_of_radius" (fast units outrunning match_radius between
# samples), 6 "rebill_after_expiry". All three ablatable rules default ON; see O13_v2's progress file
# (scratchpad/gauntlet/L67/opp_fix/O13_v2.md) for the data-derived constants and the SPAWNS/BODIES
# verification against pipeline.vocab / CardDB (spawner counts, class names) -- every entry below was cross-
# checked there, not guessed; unverifiable ticket entries (phoenix egg-form, "fire_spirits", "cursed_hog",
# singular "lava_pup") were corrected or dropped, never silently kept wrong.
# ==========================================================================================================

# R1 (suppress_spawns): parent card -> the set of vocab base-keys its spawn output can appear as, PLUS the
# parent's own key (the engine names many spawned bodies after the PARENT card, not the spawned unit --
# pipeline/vocab.py:157-198 documents this; the trace's own `split` reason for tombstone/witch/night_witch is
# entirely SAME-base splits, i.e. exactly this self-naming collision). Verified against
# pipeline.vocab.UNIT_VOCAB and, where available, CardDB.spawner(parent)["unit"] (a measured engine value,
# not a guess) -- see O13_v2.md "SPAWNS / BODIES verification" for the row-by-row source of every entry and
# every correction made to the ticket's own list.
SPAWNS: dict[str, frozenset[str]] = {
    "tombstone": frozenset({"skeletons", "tombstone"}),
    "witch": frozenset({"skeletons", "witch"}),
    "night_witch": frozenset({"bats", "night_witch"}),
    "goblin_hut": frozenset({"spear_goblins", "goblin_hut"}),
    "barbarian_hut": frozenset({"barbarians", "barbarian_hut"}),
    "furnace": frozenset({"fire_spirit", "furnace"}),          # NOT "fire_spirits" -- not a vocab class (O13_v2.md)
    "graveyard": frozenset({"skeletons", "graveyard"}),
    "goblin_drill": frozenset({"goblins", "goblin_drill"}),
    "mother_witch": frozenset({"mother_witch_hog", "mother_witch"}),  # NOT "cursed_hog"/"hog" (not vocab classes)
    "golem": frozenset({"golemite", "golem"}),
    "lava_hound": frozenset({"lava_pups", "lava_hound"}),       # NOT singular "lava_pup" -- not a vocab class
    "elixir_golem": frozenset({"elixir_golemite", "elixir_blob", "elixir_golem"}),
    "skeleton_king": frozenset({"skeletons", "skeleton_king"}),
    # "phoenix" DROPPED -- no egg-form vocab class exists at all (neither "phoenix_egg" nor "egg"); see
    # O13_v2.md UNVERIFIED #1.
    # -- O15 (V2.1) additions/re-checks -- see O15_v21.md for the row-by-row source of each --
    # MEASURED via CardDB.spawner(parent)["unit"] (icebow/config/cards.yaml), both new:
    "skeleton_barrel": frozenset({"skeletons", "skeleton_barrel"}),   # spawner: unit=skeletons, on_death=7
    "battle_ram": frozenset({"barbarians", "battle_ram"}),            # spawner: unit=barbarians, on_death=2
    # PLAUSIBLE BUT UNTESTED (O15_v21.md) -- CardDB.spawner('goblin_gang') is None (a one-shot swarm card,
    # not an engine spawner-building like goblin_drill/goblin_hut above), so there is no measured engine
    # spawn relationship backing this entry the way the other O15 additions have; all three names ARE valid
    # DETECTOR_CLASSES, so this instead models a possible DETECTOR-level class collision (a trained
    # "goblin_gang" visual class distinct from the individual "goblins"/"spear_goblins" classes). Added per
    # the ticket's explicit instruction; flagged as untested against any trace evidence, unlike the two
    # entries directly above.
    "goblin_gang": frozenset({"goblins", "spear_goblins", "goblin_gang"}),
    # "goblin_cage" DROPPED (O15_v21.md): CardDB.spawner('goblin_cage')['unit'] == 'goblin_brawler', but
    # "goblin_brawler" is NOT a vocab class (absent from both DETECTOR_CLASSES and ENGINE_ONLY_CLASSES) --
    # the exact phoenix-egg situation from O13: a body with no detector class can never appear as a spurious
    # track, so there is nothing here for a detector-class suppression rule to suppress.
}

# R2 (body_count): base -> bodies deployed by one play (or one death-spawn burst). Cross-checked against
# CardDB.get(base)["count"] (icebow/config/cards_stats.json, level-11 wiki import) for every entry, EXCEPT
# lava_pups, sourced instead from CardDB.spawner("lava_hound")["on_death"] == 6 (the card's own `count` field
# describes one pup's stats, not how many spawn on death -- O13_v2.md). "fire_spirits" (ticket: 3) and
# "cursed_hog" (ticket: 1) dropped -- neither is a real vocab class (see SPAWNS comment above); furnace's
# actual (measured) spawn count is 1 fire_spirit at a time, not 3.
BODIES: dict[str, int] = {
    "skeletons": 3, "skeleton_army": 15, "wall_breakers": 2, "barbarians": 5, "elite_barbarians": 2,
    "royal_hogs": 4, "goblin_gang": 6, "goblins": 4, "spear_goblins": 3, "minions": 3, "minion_horde": 6,
    "guards": 3, "three_musketeers": 3, "royal_recruits": 6, "rascals": 3, "bats": 5, "zappies": 3,
    "lava_pups": 6, "goblin_giant": 1, "archers": 2, "dart_goblin": 1, "firecracker": 1, "ice_spirit": 1,
    "fire_spirit": 1, "heal_spirit": 1, "electro_spirit": 1, "mini_pekka": 1,
}

# Every module constant the V2 estimator's default behaviour depends on, logged here so the audit harness can
# dump it verbatim into summary.json (ticket 3) -- see O13_v2.md for the derivation/source of each.
V2_PARAMS: dict[str, object] = {
    "match_radius": 0.07,
    "cluster_radius": 0.10,
    "forget_s": 6.0,
    # R1 / R7 -- r_spawn RAISED 0.084 -> 0.12 by O15 (V2.1 ticket): 0.084 was the p90 of only 49
    # tombstone/witch/night_witch split rows (O10_trace / charges.jsonl) and left ~10% of exactly those
    # rows uncaught by design -- the witch residual (16 delivered -> 84 charged, audit_v2_0_100/summary.md)
    # is that same p90 floor's own tail. Ticket-specified value, not re-derived from a fresh trace this
    # session (see O15_v21.md). ACCEPTED TRADEOFF (attempt 2 NOTE, no code change): the wider zone also frees
    # a genuine SECOND, deliberate play of the same spawner card adjacent to a still-live first one (e.g. a
    # second witch placed 0.10 from a live witch track) -- indistinguishable, at the detector-class level
    # alone, from that same witch's own self-labelled spawn output. Accepted per the ticket's own instruction
    # to raise this value; not something R1/R7 can resolve without more information than a base+position pair.
    "r_spawn": 0.12,
    "death_spawn_window_s": 1.0,         # ticket's floor; satisfied for free by forget_s=6.0 (>= 1.0) -- no
                                          # separate timer needed or implemented (O13_v2.md).
    "spawns": SPAWNS,
    # R2 (legacy, used verbatim when lifetime_absorb=False -- O15_v21.md)
    "body_group_window_s": 1.0,          # W, per ticket ("choose W ~1.0s, state it")
    "r_body": 0.20,                      # NOT data-derived -- a judgment call (O13_v2.md), ~2x cluster_radius
    "bodies": BODIES,
    # R3
    "speed_k": 1.5,
    "speed_radius_cap": 0.25,
    "speed_axis": "x:/18 (larger of x:/18, y:/32 per-axis normalized speed)",
    # R4 (O15) -- singleton_resight: a base with BODIES.get(base) absent or <= 1 cannot legitimately
    # reappear (at any distance) within one card cycle -- ticket-specified, not data-derived.
    "singleton_window_s": 4.0,           # per ticket: "4-card cycle" floor for a re-sighting vs. a new play.
    "singleton_double_window_s": 0.5,    # hardcoded, not a constructor kwarg (ticket's kwarg list omits it):
                                          # two same-base singleton tracks both live and seen this close
                                          # together are a genuine double (mirror/clone), not a re-sighting.
    # R5 (O15) -- lifetime_absorb: no new numeric constant (reuses r_body/forget_s/bodies above); replaces
    # the R2 time-window + single-centroid matching with per-deployment-group, any-live-member matching --
    # see the OpponentElixirEstimatorV2 docstring and O15_v21.md.
}


class OpponentElixirEstimatorV2:
    """Same public API as OpponentElixirEstimator (reset/record_my_play/update/._est), same exact-books
    saturation re-baselining (copied verbatim from L67g below), plus three independently-ablatable fixes for
    the over-billing O10's trace measured. Each defaults ON; set any to False to reproduce
    OpponentElixirEstimator's exact behaviour for that rule (with all three False, this class is behaviourally
    identical to OpponentElixirEstimator -- same tracks, same matches, same one-charge-per-cluster, verified
    by TestAblationMatchesV1 in the new test file).

    R1 suppress_spawns: a new same/related-base track within `r_spawn` of an existing LIVE track of a base in
        SPAWNS is created WITHOUT a charge (it still becomes a track, so it stops re-triggering next frame).
    R2 body_count: new same-base tracks from one update() call are grouped and charged
        ceil(n_new / BODIES[base]) times (not once per cluster); further same-base arrivals within
        `body_group_window_s` seconds and `r_body` of the group's centroid are absorbed free, up to
        BODIES[base] bodies total.
    R3 speed_aware_radius: match radius per det is widened by the card's own `db.speed_tiles(base)`
        (icebow/config/cards_stats.json), `max(match_radius, speed_norm*dt*speed_k)` capped at
        `speed_radius_cap` -- see O13_v2.md for a measured gap (bandit) this does not close.

    O15 (V2.1) additions, each independently ablatable and default ON, closing the four gaps measured in
    audit_v2_0_100/summary.md (miner, barbarians/royal_hogs/skeletons, skeleton_barrel/goblins, witch --
    see O15_v21.md for the full residual-to-rule mapping):

    R4 singleton_resight: for a base with `bodies.get(base)` absent or <= 1 ("singleton" -- one body per
        play, e.g. miner, a burrow/teleport/dash unit), a NEW track (unmatched by the normal proximity
        rule) is a RE-SIGHTING -- created, not charged -- if any existing same-base track was last seen
        within `singleton_window_s` (regardless of distance: a singleton card cannot be redeployed within
        one card cycle). EXCEPTION: if that existing track was seen within `singleton_double_window_s`
        (hardcoded 0.5s, not a kwarg) of now, the two are read as a genuine simultaneous double (mirror/
        clone) and the charge is kept. NOTE (attempt 2, no code change): this exception means R4 only ever
        fires when the prior sighting is MORE than 0.5s old -- at live sampling cadence <= `singleton_double_
        window_s` (i.e. two CONSECUTIVE samples), R4 never suppresses at all, so a fast mover (e.g. a knight)
        that outruns the match radius between one frame and the next is NOT what R4 closes; that gap is R3's
        (speed_aware_radius) job. Do not read R4 as a general fast-mover fix.
    R5 lifetime_absorb: replaces R2's `body_group_window_s` + single-centroid-per-base matching with
        persistent multi-group state: a deployment group for base X keeps a BODY BUDGET (`bodies[X]`) that
        its currently ACTIVE members (tracks refreshed in the SAME `update()` call, `tr["t"] == now`) spend;
        a member not refreshed this tick is excluded from that sum (its body may be the very one that moved
        and produced the new point under evaluation), so a drift/re-detection can still be absorbed once the
        group's active members alone would allow it, while a genuinely new body arriving alongside every one
        of the group's still-visible original members correctly cannot (O15.1 FIX 1 -- the O15 original
        counted LIVE TRACKS, not bodies, so an entire second play could be silently absorbed as if it were
        one drifted unit; see O15_v21.md attempt 2). A new same-base track joins the first EXISTING group
        with ANY live member (active or stale) within `r_body` of it (not just a stored centroid) AND room in
        that group's active-body budget; beyond that, it starts a new deployment, charged `ceil(n/cap)`
        exactly as R2 did. Ignored (falls back to R2's original logic verbatim) when False.
    """

    def __init__(self, db, match_radius: float = 0.07, cluster_radius: float = 0.10,
                 forget_s: float = 6.0, suppress_spawns: bool = True, body_count: bool = True,
                 speed_aware_radius: bool = True, spawns: dict | None = None, bodies: dict | None = None,
                 r_spawn: float = V2_PARAMS["r_spawn"], r_body: float = V2_PARAMS["r_body"],
                 body_group_window_s: float = V2_PARAMS["body_group_window_s"],
                 speed_k: float = V2_PARAMS["speed_k"], speed_radius_cap: float = V2_PARAMS["speed_radius_cap"],
                 singleton_resight: bool = True, lifetime_absorb: bool = True,
                 singleton_window_s: float = V2_PARAMS["singleton_window_s"]):
        self.db = db
        self.match_radius = float(match_radius)
        self.cluster_radius = float(cluster_radius)
        self.forget_s = float(forget_s)
        self.suppress_spawns = bool(suppress_spawns)
        self.body_count = bool(body_count)
        self.speed_aware_radius = bool(speed_aware_radius)
        self.spawns = dict(spawns) if spawns is not None else SPAWNS
        self.bodies = dict(bodies) if bodies is not None else BODIES
        self.r_spawn = float(r_spawn)
        self.r_body = float(r_body)
        self.body_group_window_s = float(body_group_window_s)
        self.speed_k = float(speed_k)
        self.speed_radius_cap = float(speed_radius_cap)
        # O15 (V2.1)
        self.singleton_resight = bool(singleton_resight)
        self.lifetime_absorb = bool(lifetime_absorb)
        self.singleton_window_s = float(singleton_window_s)
        self.singleton_double_window_s = float(V2_PARAMS["singleton_double_window_s"])
        self.reset()

    def reset(self, my_elixir: float = 5.0, now: float | None = None) -> None:
        self._my_spent = 0.0
        self._opp_spent = 0.0
        self._tracks: list[dict] = []      # {base, x, y, t[, group_id]}
        self._body_groups: dict[str, dict] = {}   # base -> {cx, cy, n, t_start}  (R2 legacy, lifetime_absorb=False)
        self._deploy_groups: dict[str, list[dict]] = {}   # base -> [{id, cap}, ...]  (R5, lifetime_absorb=True)
        self._group_seq = 0                # next R5 group id
        self._est = float(max(0.0, min(10.0, my_elixir)))
        self._rebase = 0.0
        self._last_t = float(now) if now is not None else None
        # O13 attempt 2 FIX 3: per-NEW-TRACK (base, x, y, charged, cost) ledger for this update() call, in
        # creation order -- see the comment in update() for why this exists (unambiguous charge attribution
        # for a downstream trace, kept OUT of V1 which has no such ambiguity).
        self.last_new_tracks: list[tuple[str, float, float, bool, float]] = []

    def record_my_play(self, base: str) -> None:
        c = float(self.db.elixir(base) or 0.0)
        if c > 0.0:
            self._my_spent += c

    def _seen_tracks(self, now: float) -> None:
        # forget_s (unchanged, 6.0 by default) keeps a dead spawner's track live well past R1's requested
        # >=1.0s "still counts as live" floor -- see O13_v2.md; no separate death-spawn timer is needed.
        self._tracks = [tr for tr in self._tracks if now - tr["t"] <= self.forget_s]

    def _speed_radius(self, base: str, dt: float) -> float:
        if not self.speed_aware_radius:
            return self.match_radius
        speed_tiles = None
        get_speed = getattr(self.db, "speed_tiles", None)
        if callable(get_speed):
            speed_tiles = get_speed(base)
        if speed_tiles is None or dt <= 0.0:
            return self.match_radius
        speed_norm = float(speed_tiles) / 18.0     # the larger of x:/18, y:/32 (O13_v2.md)
        eff = speed_norm * float(dt) * self.speed_k
        eff = min(eff, self.speed_radius_cap)
        return max(self.match_radius, eff)

    def _find_track(self, base: str, x: float, y: float, now: float):
        best = None
        best_d2 = None
        for tr in self._tracks:
            if tr["base"] != base:
                continue
            r = self._speed_radius(base, now - tr["t"])
            dx = x - tr["x"]
            dy = y - tr["y"]
            d2 = dx * dx + dy * dy
            if d2 <= r * r and (best_d2 is None or d2 <= best_d2):
                best, best_d2 = tr, d2
        return best

    def _cluster_new(self, fresh: List[tuple[str, float, float]]) -> List[tuple[str, float, float, int]]:
        """Same clustering as V1 (base + cluster_radius proximity), but also returns each cluster's member
        count `n` -- R2 needs body counts, not just centroids."""
        out = []
        rem = list(fresh)
        r2 = self.cluster_radius * self.cluster_radius
        while rem:
            base, x, y = rem.pop()
            xs, ys, n = x, y, 1
            keep = []
            for b2, x2, y2 in rem:
                if b2 != base:
                    keep.append((b2, x2, y2))
                    continue
                dx = x2 - x
                dy = y2 - y
                if dx * dx + dy * dy <= r2:
                    xs += x2
                    ys += y2
                    n += 1
                else:
                    keep.append((b2, x2, y2))
            rem = keep
            out.append((base, xs / n, ys / n, n))
        return out

    def _spawn_suppressed(self, base: str, x: float, y: float) -> bool:
        """R1: is (base, x, y) within r_spawn of a LIVE track whose base P has `base` in SPAWNS[P]
        (P's own key included, per the self-naming collision -- see SPAWNS comment)?"""
        if not self.suppress_spawns:
            return False
        r2 = self.r_spawn * self.r_spawn
        for tr in self._tracks:
            spawn_set = self.spawns.get(tr["base"])
            if not spawn_set or base not in spawn_set:
                continue
            dx = x - tr["x"]
            dy = y - tr["y"]
            if dx * dx + dy * dy <= r2:
                return True
        return False

    def _singleton_resighted(self, base: str, now: float) -> bool:
        """R4 (O15): is a NEW track of a singleton base (bodies.get(base) absent or <= 1) a re-sighting of
        the same card, not a genuine new play? True (suppress the charge) iff some existing same-base track
        was last seen more than `singleton_double_window_s` ago but within `singleton_window_s` -- distance
        is deliberately ignored (a burrow/teleport/dash unit resurfaces far from where it was last seen).
        The <= singleton_double_window_s case (both alive, seen almost simultaneously) is read as a genuine
        double (mirror/clone) instead and returns False (charge kept)."""
        if not self.singleton_resight:
            return False
        cap = self.bodies.get(base)
        if cap and cap > 1:
            return False                 # not a singleton base -- governed by R2/R5 instead
        gaps = [now - tr["t"] for tr in self._tracks if tr["base"] == base]
        if not gaps:
            return False
        min_gap = min(gaps)
        if min_gap <= self.singleton_double_window_s:
            return False                 # genuine double -- keep the charge
        return min_gap <= self.singleton_window_s

    def _group_live_members(self, gid: int) -> list[dict]:
        """R5: the track objects currently in `self._tracks` tagged with deployment-group id `gid`. Purely
        derived from `self._tracks` (already forget_s-expired by `_seen_tracks`), so a group's liveness needs
        no separate timer or cleanup -- it is empty exactly when every one of its tracks has aged out."""
        return [tr for tr in self._tracks if tr.get("group_id") == gid]

    def _charge_groups(self, base: str, points: list[tuple[float, float, int]],
                        now: float) -> tuple[int, list[int | None]]:
        """R2/R5 dispatcher: `points` are this update's non-suppressed (base, x, y, n) cluster points for one
        base. Returns (charges, group_ids) where `group_ids` has one entry per point in `points`' order --
        the R5 deployment-group id to tag that point's new track with (None when R5 is inactive for this
        base/call, e.g. `lifetime_absorb=False` or `body_count` disabled the grouping entirely)."""
        cap = self.bodies.get(base)
        if not self.body_count or not cap or cap <= 1:
            return len(points), [None] * len(points)     # V1 parity: one charge per cluster point
        if self.lifetime_absorb:
            return self._charge_groups_lifetime(base, points, now, cap)
        return self._charge_groups_legacy(base, points, now, cap), [None] * len(points)

    def _charge_groups_lifetime(self, base: str, points: list[tuple[float, float, int]], now: float,
                                 cap: int) -> tuple[int, list[int | None]]:
        """R5 (O15/O15.1/O15.2): persistent multi-group state, replacing the R2 time-window + single-centroid
        match. A group's BODY BUDGET is `bodies[base]` (the card's own body count); what a live member
        currently SPENDS of that budget is `min(tr["n"], tr["matched_n"])` -- `tr["n"]` is the body count the
        track was CREATED with (a merged cluster point can represent several bodies at once) and never
        changes, while `tr["matched_n"]` is how many dets `update()` matched to that exact track THIS call,
        reset to 0 at the top of every `update()` (see there) -- so a track matched by FEWER dets than its
        own `n` this tick (some of its bodies were not re-seen, e.g. one walked far enough to fail the normal
        proximity match) spends only that reduced amount, not its full creation size. This is what lets a
        body that visibly drifted off a group's original blob still be absorbed by that SAME group (the
        blob's remaining, still-matched bodies free up exactly the budget the drifted one needs), while a
        genuinely NEW body or play arriving alongside a group whose EVERY original member is still being
        matched in full cannot (O15.1 FIX 1 found the first version of this: `len(live) >= cap` counted
        TRACK OBJECTS, not bodies, so an entire second N-body play could be absorbed as if it were one
        drifted unit; O15.2 FIX found the regression in FIX 1's own remedy: it summed each live member's
        CREATION size unconditionally whenever the member was refreshed at all this tick, which still over-
        counts a partially-rematched blob as fully present and wrongly BLOCKS the very drift it needs to
        allow -- see O15_v21.md attempt 3 for the measured cases both fixes get wrong that this one does
        not). O15.3 FIX (attempt 4): `active_n` alone only reflects `self._tracks`, which does not gain a
        new entry for a point until AFTER this whole function returns -- so two same-base points landing
        near the SAME group in one sample were both checked against the group's unchanged active_n and
        could both fit a budget sized for only one of them. A `pending` counter, local to this call, now
        accumulates the body count already committed to each group by an earlier point in the SAME points
        list, so a later point sees that claim; this makes the outcome independent of which point happens
        to be evaluated first. A new point joins the first EXISTING (i.e. from a prior `update()` call)
        group with any LIVE member (active or stale, matched or not, this tick) within `r_body` of it AND
        room in the group's active-plus-pending budget for the point's own body count; beyond that, it
        starts a new deployment, charged
        `ceil(n/cap)` exactly as before. Points that join no existing group are themselves pooled together
        and charged as ONE new deployment, `ceil(total_n/cap)` -- same aggregate-the-whole-batch behaviour
        the legacy path used for a fresh play (e.g. barbarians landing as a 3+2 split in one update, both
        beyond cluster_radius of each other, is ceil(5/5)=1 charge; the same split for a 3-cap card like
        skeletons is ceil(5/3)=2 -- NOT one, a mistake in an earlier draft of this comment, corrected in
        O15.1). Points join no group WITHIN one update() call to each other either (only pre-existing, prior-
        call groups are checked): a new group created earlier in the SAME call has no track appended to
        `self._tracks` yet, so a sibling point could never see it as a candidate anyway; pooling every
        leftover of this call into one shared new deployment afterwards sidesteps that ordering issue without
        needing to special-case it."""
        groups = self._deploy_groups.setdefault(base, [])
        groups[:] = [g for g in groups if self._group_live_members(g["id"])]   # drop fully-dead groups
        r2 = self.r_body * self.r_body
        group_ids: list[int | None] = [None] * len(points)
        leftover: list[int] = []
        # O15.3 FIX (MEDIUM): `pending` tracks, PER GROUP, the body count already committed to it by an
        # EARLIER point in this SAME points list -- `_group_live_members`/`matched_n` only reflect
        # `self._tracks`, which does not gain a new entry until the caller appends one AFTER this whole
        # function returns, so two same-base points landing near one group in a single sample would
        # otherwise both be checked against the SAME (stale) active_n and could both fit under a budget only
        # big enough for one of them. Order-independent: whichever point is evaluated first claims the
        # budget via `pending`; a later point sees that claim and is correctly blocked if there is no room
        # left, regardless of which point that "later" one is.
        pending: dict[int, int] = {}
        for i, (x, y, n) in enumerate(points):
            joined: int | None = None
            for g in groups:
                live = self._group_live_members(g["id"])
                if not any((x - m["x"]) ** 2 + (y - m["y"]) ** 2 <= r2 for m in live):
                    continue
                active_n = sum(min(m.get("n", 1), m.get("matched_n", 0)) for m in live)
                if active_n + pending.get(g["id"], 0) + n <= cap:
                    joined = g["id"]
                    break
            if joined is not None:
                group_ids[i] = joined
                pending[joined] = pending.get(joined, 0) + n
            else:
                leftover.append(i)
        charges_total = 0
        if leftover:
            total_n = sum(points[i][2] for i in leftover)
            charges = -(-total_n // cap)      # ceil
            self._group_seq += 1
            gid = self._group_seq
            groups.append({"id": gid})
            charges_total += charges
            for i in leftover:
                group_ids[i] = gid
        return charges_total, group_ids

    def _charge_groups_legacy(self, base: str, points: list[tuple[float, float, int]], now: float,
                               cap: int) -> int:
        """R2 (unchanged since O13): time-window (`body_group_window_s`) + single stored centroid per base.
        Used verbatim when `lifetime_absorb=False`, for ablation parity with pre-O15 V2."""
        total_n = sum(p[2] for p in points)
        if total_n <= 0:
            return 0
        wx = sum(p[0] * p[2] for p in points) / total_n
        wy = sum(p[1] * p[2] for p in points) / total_n
        grp = self._body_groups.get(base)
        if (grp is not None and (now - grp["t_start"]) <= self.body_group_window_s
                and grp["n"] < grp["cap"]):
            dx, dy = wx - grp["cx"], wy - grp["cy"]
            if dx * dx + dy * dy <= self.r_body * self.r_body:
                grp["n"] = min(grp["n"] + total_n, grp["cap"])
                return 0                # absorbed into the active deployment, no new charge
        # start a new deployment
        charges = -(-total_n // cap)    # ceil
        self._body_groups[base] = {"cx": wx, "cy": wy, "n": min(total_n, charges * cap),
                                   "cap": charges * cap, "t_start": now}
        return charges

    def update(self, my_elixir: float, enemy_dets: Iterable, now: float) -> float:
        """Return normalized estimated enemy elixir in [0, 1]. Same det shape as V1
        (`.base`, `.cx`, `.gy`, `.team`)."""
        now = float(now)
        self._seen_tracks(now)
        # O15.2 FIX (R5): reset THIS update's occupancy counter on every surviving track before matching --
        # `matched_n` must reflect only dets matched to it in the CURRENT call (0 if none), never a stale
        # value from a previous update, so a track that goes unmatched this tick (its body may have moved)
        # correctly stops contributing to its group's active body budget below.
        for tr in self._tracks:
            tr["matched_n"] = 0

        fresh = []
        for d in enemy_dets:
            if getattr(d, "team", None) != "enemy":
                continue
            base = str(getattr(d, "base", "") or "")
            if not base:
                continue
            x = float(getattr(d, "cx", 0.5))
            y = float(getattr(d, "gy", 0.5))
            tr = self._find_track(base, x, y, now)
            if tr is not None:
                tr["x"], tr["y"], tr["t"] = x, y, now
                tr["matched_n"] = tr.get("matched_n", 0) + 1   # O15.2: how many dets matched THIS track now
            else:
                fresh.append((base, x, y))

        clusters = self._cluster_new(fresh)          # [(base, x, y, n)]
        by_base: dict[str, list[tuple[float, float, int]]] = {}
        suppressed: list[bool] = []
        for base, x, y, n in clusters:
            # R1 (spawn proximity) OR R4 (O15, singleton re-sighting -- distance-independent) suppress the
            # charge; R4 is only even checked when R1 did not already suppress this point.
            supp = self._spawn_suppressed(base, x, y)
            if not supp:
                supp = self._singleton_resighted(base, now)
            suppressed.append(supp)
            if not supp:
                by_base.setdefault(base, []).append((x, y, n))

        charge_info: dict[str, tuple[int, list[int | None]]] = {
            base: self._charge_groups(base, pts, now) for base, pts in by_base.items()
        }
        n_charges_for_base: dict[str, int] = {base: v[0] for base, v in charge_info.items()}
        group_ids_for_base: dict[str, list[int | None]] = {base: v[1] for base, v in charge_info.items()}
        remaining: dict[str, int] = dict(n_charges_for_base)
        base_cursor: dict[str, int] = {}     # R5: index into group_ids_for_base[base], non-suppressed order

        # O13 attempt 2 FIX 3 (verifier, MEDIUM): record, per NEW TRACK created this call, whether it was
        # actually charged and for how much -- in creation order, 1:1 with the tracks appended below. A
        # positional zip of "new tracks this update" against "db.elixir() calls this update" (which is how
        # the harness's TracedEstimator attributes a charge to a track) is only valid when EVERY new track
        # makes EXACTLY one call, which is true for V1 but false for V2: a spawn-suppressed (R1) or body-
        # count-absorbed (R2) track makes NO call at all, so a no-charge track ahead of a charged one in the
        # SAME update would shift every later (base, x, y) attribution off by one. Exposing this explicit,
        # unambiguous per-track ledger (kept OUT of V1, which has no such ambiguity) lets the harness
        # attribute correctly with no re-implementation of R1/R2's own logic.
        self.last_new_tracks: list[tuple[str, float, float, bool, float]] = []
        for (base, x, y, n), supp in zip(clusters, suppressed):
            tr = {"base": base, "x": x, "y": y, "t": now, "n": n}   # O15.1: n = bodies this track represents
            if not supp:
                idx = base_cursor.get(base, 0)
                base_cursor[base] = idx + 1
                gid_list = group_ids_for_base.get(base)
                if gid_list is not None and idx < len(gid_list) and gid_list[idx] is not None:
                    tr["group_id"] = gid_list[idx]      # R5 (O15): tag for future _group_live_members lookups
            self._tracks.append(tr)
            charged, cost = False, 0.0
            if not supp and remaining.get(base, 0) > 0:
                remaining[base] -= 1
                c = float(self.db.elixir(base) or 0.0)
                if c > 0.0:
                    self._opp_spent += c
                    charged, cost = True, c
            self.last_new_tracks.append((base, x, y, charged, cost))

        est = float(my_elixir) + self._my_spent - self._opp_spent
        # L67g -- RE-BASELINE ON SATURATION (copied verbatim from OpponentElixirEstimator.update above).
        if est > 10.0:
            self._opp_spent += est - 10.0
            self._rebase += est - 10.0
            est = 10.0
        elif est < 0.0:
            self._opp_spent += est
            self._rebase += est
            est = 0.0
        self._est = est
        self._last_t = now
        return self._est / 10.0