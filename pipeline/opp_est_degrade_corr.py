"""TICKET O16(b) -- a TEMPORALLY CORRELATED live-view degrade, harness-local to opp_est_audit.py.

``pipeline/e1_view.live_view`` (and the ``degrade()`` it wraps) draws every noise component
INDEPENDENTLY per 5-tick sample: a unit's miss/hit, a false positive's presence, its position jitter,
and its team read are each a fresh i.i.d. roll every call. That is the BEST case for a tracker's
``min_hits`` corroboration gate -- a one-frame phantom is exactly what min_hits is built to catch, and
a real unit's one-in-seven (1 - 0.855) miss chance almost never strings two together. O16's V1-vs-V2
run measured both raw-detection estimators pinned at <=1.0 on 91% of ticks under that i.i.d. model
(scratchpad/gauntlet/L67/e1/opp_est/audit_v2_0_100/summary.md) -- but a REAL detector's errors are not
independent draws: a unit occluded behind a tower stays occluded for several frames in a row, a
misclassified decoration keeps re-appearing in the same spot, and a mis-read team assignment for one
sighting does not usually flip back and forth frame to frame. An i.i.d. model can only ever FLATTER a
tracker relative to a live one (a persistent phantom survives ``min_hits`` where an i.i.d. one does
not) and can only ever be pessimistic about a persistent miss (real occlusion strings misses together,
raising a raw estimator's error, where i.i.d. spreads the same total miss budget thinly and re-syncs
every sample). This module gives the SAME per-sample marginals as ``live_view`` -- so it is not a
different noise BUDGET, only a different noise SHAPE -- with the temporal structure carried in a
per-match ``state`` dict the caller threads through every call.

ANCHORS (the only measurements behind the persistence-length guesses; there is no direct measurement
of live detector run-lengths in this repo): AX (icebow/tools/live_reader_audit.py) measured track
SURVIVAL 89% over >= 0.5 s (a track that exists at all tends to persist at least 2 samples at this
harness's 0.25 s/sample cadence) and HEADING STABILITY 43.7 deg (a track's direction of travel does
not flip sample to sample) -- both consistent with "errors persist for more than one sample" but
neither pins down a specific miss-run or FP-run length in samples. ``L_miss``/``L_fp``/``rho`` below
are THEREFORE UNMEASURED JUDGMENT CALLS, not fits to data -- SHORT and LONG bracket a plausible range
so the live number can be read as "somewhere between these two", not as a point estimate. Flagged
again in the progress file and the hand-back; do not read either arm's numbers as calibrated.

DESIGN (derivations in the progress file, O16 section):

1. PER-UNIT DROPOUT -- a 2-state Markov chain per tracked unit, {VISIBLE, MISSED}. Closed form for
   the transition probabilities that gives an EXACT stationary miss probability ``1 - recall`` and an
   exact mean MISSED-run length ``L_miss`` samples, at every sample from the first one (the chain is
   INITIALISED from its own stationary distribution, not "warmed up"): with ``p_stay`` = P(stay missed
   | missed) and ``p_enter`` = P(become missed | visible),
       p_stay  = 1 - 1/L_miss
       p_enter = (1 - recall) / (L_miss * recall)
   (``markov_params(1 - recall, L_miss)`` below; the general form for target stationary probability
   ``p`` and mean run length ``L`` is ``p_stay = 1 - 1/L``, ``p_enter = p / (L * (1 - p))``.)

2. FALSE POSITIVES -- tied 1:1 to a currently-VISIBLE real unit (mirroring ``degrade()``'s own model:
   an FP is a duplicate box near a correctly-detected one, never a free-floating one), each such
   "slot" gets its OWN 2-state Markov chain {ACTIVE, INACTIVE} with the SAME closed form, target
   stationary probability ``fp_rate = (1 - precision) / precision`` and mean ACTIVE-run length
   ``L_fp``. The slot's chain only advances on samples the host unit is visible (an FP tied to an
   unseen host emits nothing and is not evidence of anything); this keeps
   E[FP count | unit visible] == fp_rate exactly, matching ``degrade()``'s own conditioning. A
   reactivation after a gap draws a FRESH class/position (a new phantom), not a resumption of the old
   one.

3. POSITION JITTER -- an AR(1) process per axis, in TILE units then converted to normalized
   coordinates the same way ``e1_view._degrade_switchable`` does (``dx_tiles / TILES_X``):
       x_t = rho * x_{t-1} + sqrt(1 - rho^2) * sigma_tiles * eps_t,   eps_t ~ N(0, 1)
   initialised ``x_0 ~ N(0, sigma_tiles^2)``. This is the standard stationarity-preserving AR(1)
   parameterisation: Var(x_t) = sigma_tiles^2 for EVERY t (not just asymptotically), so the marginal
   position error matches ``live_view``'s exactly at every sample while ``rho`` controls how much one
   sample's offset predicts the next.

4. TEAM CONFUSION -- drawn ONCE per track, at its first VISIBLE sample (not at track creation --
   a track created while its very first roll lands MISSED has not been "sighted" yet), from the SAME
   categorical ``obs_contract.degrade()`` uses (``UNKNOWN_TEAM_RATE`` / ``WRONG_TEAM_RATE`` by kind),
   then held for the rest of the track's life. Because every track's draw uses the identical
   probabilities, the CROSS-SECTIONAL marginal (the fraction of samples reading unknown/wrong at any
   fixed moment) equals those same probabilities regardless of how long any one track survives --
   sticky-per-entity does not bias a marginal built from i.i.d.-per-entity draws.

IDENTITY (no stable id exists on ``obs_contract.Unit`` / ``BoardState``, since the engine ground truth
carries none through ``from_engine``): tracks are matched sample-to-sample by GREEDY nearest neighbour
on the TRUE (engine) position, within the SAME (side, cls) group and a generous ``match_radius``
(default 0.20, board-normalized -- far more than a troop's true per-sample displacement at this
harness's 0.25 s cadence, so a genuine same-unit match is never missed; an ambiguous case, e.g. two
identical units passing near each other, can swap identities, which affects nothing this module
computes since every metric here is a CROSS-SECTIONAL marginal, never a per-track trajectory). This is
strictly easier than a real tracker's job (real trackers match on NOISY positions); it only has to be
right often enough that persistence lengths are not silently destroyed by spurious churn.

Everything random is drawn from the caller's ``rng`` -- this module owns no seed of its own. The
caller (opp_est_audit.py) is responsible for giving each corr setting (SHORT/LONG) its own
independent, harness-local RNG stream per match (see ``corrS_seed``/``corrL_seed`` there), the same
discipline ``b5_seed`` already established for condition B's own non-policy-tick draws.
"""
from __future__ import annotations

import math
import sys
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Optional

import numpy as np

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from pipeline import vocab as _vocab                                                # noqa: E402
from pipeline.obs_contract import (                                                 # noqa: E402
    BoardState, Deck, TILES_X, TILES_Y, DEGRADE_PRECISION, DEGRADE_RECALL, UNKNOWN_TEAM_RATE,
    WRONG_TEAM_RATE, Unit, _draw_conf, _FP_JITTER_TILES, _TP_SIGMA_TILES, mine_classes,
)
from pipeline.e1_view import KING_HP_LIVE as _KING_HP_LIVE, Noise as _Noise, _live_unit          # noqa: E402


# ------------------------------------------------------------------------------------------------------
# closed-form 2-state Markov chain constants (module docstring, item 1/2)
# ------------------------------------------------------------------------------------------------------
def markov_params(p_target: float, mean_run: float) -> tuple[float, float]:
    """(p_stay, p_enter) for a 2-state {False, True} chain with stationary P(True) == ``p_target`` and
    mean True-run length == ``mean_run`` samples. ``p_stay`` = P(True at t+1 | True at t); ``p_enter`` =
    P(True at t+1 | False at t). Derivation (progress file O16): a chain's True-run lengths are
    geometric with success probability ``1 - p_stay`` (probability of LEAVING True each step), so
    mean run length ``mean_run = 1 / (1 - p_stay)`` gives ``p_stay = 1 - 1/mean_run`` directly; the
    stationary balance equation ``pi_False * p_enter == pi_True * (1 - p_stay)`` (flow in == flow out)
    with ``pi_True = p_target`` then solves to ``p_enter = p_target / (mean_run * (1 - p_target))``.
    Both are clamped to [0, 1] (a ``p_target`` outside (0, 1) or a ``mean_run`` < 1 is a caller error,
    not clamped away silently -- callers here only ever pass measured/derived values in range)."""
    mean_run = float(mean_run)
    p_stay = 1.0 - 1.0 / mean_run
    denom = mean_run * (1.0 - float(p_target))
    p_enter = (float(p_target) / denom) if denom > 0 else 1.0
    return max(0.0, min(1.0, p_stay)), max(0.0, min(1.0, p_enter))


def _step_bool(is_true: bool, p_stay: float, p_enter: float, rng: np.random.Generator) -> bool:
    p = p_stay if is_true else p_enter
    return bool(rng.random() < p)


def _ar1_init(sigma: float, rng: np.random.Generator) -> float:
    return float(rng.normal(0.0, sigma))


def _ar1_step(prev: float, rho: float, sigma: float, rng: np.random.Generator) -> float:
    eps = rng.normal(0.0, 1.0)
    return float(rho * prev + math.sqrt(max(0.0, 1.0 - rho * rho)) * sigma * eps)


def _team_roll(kind: str, true_side: int, unknown_rate: float, wrong_rate: dict, rng: np.random.Generator) -> int:
    """The SAME categorical ``obs_contract.degrade()``/``e1_view._degrade_switchable`` use: unknown (-1)
    first, then a kind-dependent wrong-team flip, else the true side. One roll -> held sticky by the
    caller (module docstring item 4)."""
    r = rng.random()
    wrong = wrong_rate.get(kind, 0.0)
    if unknown_rate and r < unknown_rate:
        return -1
    if wrong and r < (unknown_rate or 0.0) + wrong and true_side in (0, 1):
        return 1 - true_side
    return true_side


def _build_kind_pools() -> dict[str, list[int]]:
    pools: dict[str, list[int]] = {"troop": [], "building": [], "spell": []}
    for i in range(_vocab.N_DETECTOR):
        pools[_vocab.kind_of(i)].append(i)
    return pools


_KIND_POOLS = _build_kind_pools()


# ------------------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class CorrParams:
    """One correlated-degrade setting. Every field is a per-sample MARGINAL that must equal
    ``live_view``'s (module docstring) except ``rho``/``L_miss``/``L_fp``/``match_radius``, which are
    pure temporal-structure / bookkeeping knobs with no marginal of their own."""
    recall: float = DEGRADE_RECALL
    precision: float = DEGRADE_PRECISION
    pos_sigma_tiles: float = _TP_SIGMA_TILES
    fp_jitter_tiles: float = _FP_JITTER_TILES
    unknown_team_rate: float = UNKNOWN_TEAM_RATE
    wrong_team_rate: dict = field(default_factory=lambda: dict(WRONG_TEAM_RATE))
    rho: float = 0.3
    L_miss: float = 1.5
    L_fp: float = 1.5
    match_radius: float = 0.20

    @property
    def fp_rate(self) -> float:
        return (1.0 - self.precision) / self.precision


#: UNMEASURED (module docstring "ANCHORS") -- both settings share every MARGINAL with live_view;
#: only the persistence lengths / rho differ, bracketing the live number from the pessimistic side.
CORR_SHORT = CorrParams(rho=0.3, L_miss=1.5, L_fp=1.5)
CORR_LONG = CorrParams(rho=0.8, L_miss=4.0, L_fp=8.0)


def new_state() -> dict:
    """A fresh per-match ``state`` dict for ``corr_live_view`` -- call once per match, thread the same
    dict through every sample of that match, never share it across matches or corr settings."""
    return {}


# ------------------------------------------------------------------------------------------------------
def _advance_group(true_units: "tuple[Unit, ...]", key: str, state: dict, rng: np.random.Generator,
                   params: CorrParams, with_fp: bool) -> list[Unit]:
    """One (units-or-spells) group's tracks, for one sample: match true units to existing tracks by
    nearest same-(side,cls) true position, create/drop tracks, advance every Markov/AR(1) process, and
    emit the noised ``Unit`` list (kept detections + any active false positives). Mutates ``state[key]``
    (and ``state[key + "_next_id"]``) in place."""
    tracks: dict[int, dict] = state.setdefault(key, {})
    p_stay_miss, p_enter_miss = markov_params(1.0 - params.recall, params.L_miss)
    p_stay_fp, p_enter_fp = markov_params(params.fp_rate, params.L_fp) if with_fp else (0.0, 0.0)

    # 1) match this sample's true units to existing tracks -- greedy nearest same-(side, cls) neighbour
    remaining = dict(tracks)
    assign: dict[int, int] = {}
    r2 = params.match_radius ** 2
    for i, u in enumerate(true_units):
        best_id, best_d2 = None, r2
        for tid, tr in remaining.items():
            if tr["side"] != u.side or tr["cls"] != u.cls:
                continue
            d2 = (tr["x"] - u.x) ** 2 + (tr["y"] - u.y) ** 2
            if d2 <= best_d2:
                best_id, best_d2 = tid, d2
        if best_id is not None:
            assign[i] = best_id
            del remaining[best_id]

    # 2) unmatched true units start fresh tracks, initialised from the STATIONARY distribution (module
    #    docstring item 1/3) so the marginal is exact from this very first sample, not just eventually
    next_id = int(state.get(key + "_next_id", 0))
    for i, u in enumerate(true_units):
        if i in assign:
            continue
        tid = next_id
        next_id += 1
        tr = {"side": int(u.side), "cls": int(u.cls), "x": float(u.x), "y": float(u.y),
             "missed": bool(rng.random() < (1.0 - params.recall)),
             "dx": _ar1_init(params.pos_sigma_tiles, rng), "dy": _ar1_init(params.pos_sigma_tiles, rng),
             "team": None}
        if with_fp:
            tr.update(fp_active=bool(rng.random() < params.fp_rate), fp_cls=None, fp_team=None,
                     fp_dx=0.0, fp_dy=0.0)
        tracks[tid] = tr
        assign[i] = tid
    state[key + "_next_id"] = next_id

    # 3) tracks whose true unit vanished this sample (died / left) are gone -- no continued bookkeeping
    for tid in (set(tracks) - set(assign.values())):
        del tracks[tid]

    # 4) advance every live track's processes and emit
    out: list[Unit] = []
    for i, u in enumerate(true_units):
        tr = tracks[assign[i]]
        tr["x"], tr["y"] = float(u.x), float(u.y)                    # refresh true position for next match
        tr["missed"] = _step_bool(tr["missed"], p_stay_miss, p_enter_miss, rng)
        tr["dx"] = _ar1_step(tr["dx"], params.rho, params.pos_sigma_tiles, rng)
        tr["dy"] = _ar1_step(tr["dy"], params.rho, params.pos_sigma_tiles, rng)
        visible = not tr["missed"]
        if with_fp:
            if visible:
                new_active = _step_bool(tr["fp_active"], p_stay_fp, p_enter_fp, rng)
                if tr["fp_active"] and not new_active:
                    tr["fp_cls"], tr["fp_team"] = None, None         # episode ended -- next one is fresh
                tr["fp_active"] = new_active
            # while missed: the slot's chain is FROZEN (module docstring item 2) -- no transition, no emission
        if visible and tr["team"] is None:
            tr["team"] = _team_roll(_vocab.kind_of(u.cls), int(u.side), params.unknown_team_rate,
                                    params.wrong_team_rate, rng)
        if not visible:
            continue
        nx = float(np.clip(u.x + tr["dx"] / TILES_X, 0.0, 1.0))
        ny = float(np.clip(u.y + tr["dy"] / TILES_Y, 0.0, 1.0))
        out.append(Unit(u.cls, tr["team"], nx, ny, None, None, None, _draw_conf(rng)))
        if with_fp and tr["fp_active"]:
            pool = _KIND_POOLS[_vocab.kind_of(u.cls)]
            jit = max(params.pos_sigma_tiles, params.fp_jitter_tiles)
            if tr["fp_cls"] is None:
                tr["fp_cls"] = int(pool[rng.integers(len(pool))])
                tr["fp_dx"] = _ar1_init(jit, rng)
                tr["fp_dy"] = _ar1_init(jit, rng)
            else:
                tr["fp_dx"] = _ar1_step(tr["fp_dx"], params.rho, jit, rng)
                tr["fp_dy"] = _ar1_step(tr["fp_dy"], params.rho, jit, rng)
            if tr["fp_team"] is None:
                tr["fp_team"] = _team_roll(_vocab.kind_of(tr["fp_cls"]), int(u.side),
                                           params.unknown_team_rate, params.wrong_team_rate, rng)
            fx = float(np.clip(u.x + tr["fp_dx"] / TILES_X, 0.0, 1.0))
            fy = float(np.clip(u.y + tr["fp_dy"] / TILES_Y, 0.0, 1.0))
            out.append(Unit(tr["fp_cls"], tr["fp_team"], fx, fy, None, None, None, _draw_conf(rng)))
    return out


def corr_live_view(bs: BoardState, state: dict, rng: np.random.Generator, deck: Deck,
                   params: Optional[CorrParams] = None) -> BoardState:
    """``live_view(bs, rng, deck)`` with the SAME per-sample marginals but temporally CORRELATED noise
    (module docstring): per-unit dropout as a 2-state Markov chain, false positives persisting for a
    geometric number of samples, AR(1) position jitter, and sticky-per-track team confusion. ``state``
    is this MATCH's ``new_state()`` dict, threaded through every sample in order (out-of-order or
    reused-across-matches calls silently produce nonsense tracks -- there is no way to detect misuse
    from inside this function, so this is the caller's contract to keep). ``rng`` must be a stream
    dedicated to this corr setting for this match (never shared with e1_eval's own streams or the
    other corr setting) so this module's draws never desync anything else. Everything downstream of the
    noise core (unit HP fill, king HP fill, the side -1 -> enemy resolution for a class this deck cannot
    produce) reuses ``e1_view``'s own private helpers UNCHANGED, so a corr view is "the live-fill rules
    applied to a correlated-noise core" exactly as ``live_view`` is "the live-fill rules applied to
    degrade()'s i.i.d. core"."""
    params = params or CORR_SHORT
    new_units = _advance_group(bs.units, "units", state, rng, params, with_fp=True)
    new_spells = _advance_group(bs.spells, "spells", state, rng, params, with_fp=False)
    towers = tuple((replace(t, hp_frac=None) if (t.kind == "king" and t.alive) else t) for t in bs.towers)
    d = replace(bs, source="degraded", t_source="clock", my_elixir=float(int(bs.my_elixir)),
               my_elixir_exact=False, opp_elixir=None, towers=towers,
               units=tuple(new_units), spells=tuple(new_spells))
    allowed = mine_classes(deck)
    noise_all_on = _Noise()
    units = tuple(_live_unit(u, allowed, noise_all_on) for u in d.units)
    spells = tuple(_live_unit(u, allowed, noise_all_on) for u in d.spells)
    towers2 = tuple((replace(t, hp_frac=_KING_HP_LIVE) if (t.kind == "king" and t.alive) else t)
                    for t in d.towers)
    return replace(d, units=units, spells=spells, towers=towers2)
