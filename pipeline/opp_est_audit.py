"""O8: offline harness measuring play.py's OpponentElixirEstimator against ENGINE ground truth, under THREE
input conditions, driven through the SAME engine match loop e1_eval uses (held-out ghost pool v1, live S1
policy). Does not modify pipeline/e1_eval.py, pipeline/e1_view.py, pipeline/obs_contract.py,
pipeline/engine_play.py, pipeline/e1_pool.py, or anything under icebow/src or hogeq/src -- every one of
those is IMPORTED unmodified. The per-tick loop below is a NEW instrumented copy of e1_eval.run_match's
while-loop (not a subclass -- run_match returns only match-level aggregates, no per-tick truth/estimate),
built entirely out of e1_eval's own pure helpers (obs_seed, _slot_maps, allowed_slots, anti_stall,
model_forward, live_decide) plus e1_pool.PoolV1Env, e1_view.live_view, obs_contract.from_engine/to_tokens,
and engine_play.compact_raw/cell_center/cell_to_engine/load_model -- all imported, none copied.

ATTEMPT 2 changes (progress file "## Attempt 2" has the full writeup):

CHANGE 1 -- estimator cadence. Live feeds ``_opp_elx.update()`` every detector/perception frame (~4-5 Hz),
NOT once per policy decision (0.5 s / 10 engine ticks) -- attempt 1 fed it at the (too coarse) decision
cadence, which the estimator's ``match_radius=0.07`` (~1.3 tiles) was never tuned to tolerate: a unit that
moves more than that between SAMPLES (not between real detector frames) loses its track and is double-charged
as a new play. Fix: step the engine in ``STEP_TICKS=5``-tick increments; call ``update()`` on every estimator
at EVERY 5-tick step; run the live policy only every ``decide_every`` (still 10) ticks, i.e. every OTHER step,
at the identical ticks attempt 1 (and e1_eval itself) decided on. The engine is a deterministic function of
history, so ``EngineMatchEnv._advance_to(target)`` (an absolute tick, stepping tick-by-tick and stopping
exactly on ghost ticks regardless of chunk size -- scratchpad/gauntlet/L62/engine_env.py:401-414) produces a
BIT-IDENTICAL state at tick 100 whether reached via one ``_advance_to(100)`` call or two 5-tick calls; the
smoke re-run confirms ``plays_accepted`` per match is unchanged from attempt 1 (see progress file).
RNG split this forces: e1_eval's own ``rng_obs`` (seeded ``obs_seed(tag, k)``) is consumed ONLY at policy
ticks, exactly as attempt 1 / e1_eval -- so the POLICY's decisions (and thus ``plays_accepted``) stay
byte-identical. Condition B needs a degraded view at the NON-policy 5-tick steps too, for which e1_eval has
no cadence of its own to borrow -- those extra draws come from a second, harness-local generator seeded
``b5_seed(tag, k)`` (module-level, same crc32 style as ``e1_eval.obs_seed``/``random_seed``, deliberately a
different domain string so it can never collide with e1_eval's own stream). This is the one place this
harness draws its own randomness; every other draw is e1_eval's.

CHANGE 2 -- condition A+ (``est_Aplus``): perfect detection INCLUDING spells (``bs.spells``, not just
``bs.units``). Quantifies part of the blind spot attempt 1 found: play.py:547 pre-filters ``dets`` to
``team == "enemy" and base in observation.detector_cards`` before ``update()`` ever sees them. A (units only,
NO whitelist applied -- see ATTEMPT 4's correction below, this claim was wrong in earlier attempts) is kept
as an upper-bound ceiling; A+ (units + spells, also no whitelist) is the strictly-better ceiling if spells
were ever priced in at all. A spell whose CardDB cost is None (measured in attempt 1: Mirror -- dynamic
pricing, no flat ``elixir`` key) is skipped from A+'s dets (not charged as a free play) and logged ONCE per
base name per process, per the ticket.

Per-tick rows now carry ``truth_drop`` (attempt 1 folded this into a boolean; the raw size makes multi-play
aliasing inside one decision window visible instead of hidden -- see progress file). Summaries add
``bias`` (not just MAE) at opponent-play ticks, and an MAE split by ``truth >= 9.0`` (near the [0,10] cap,
where the counting identity is expected to strain) vs below.

ATTEMPT 3 (progress file "## Attempt 3" has the full writeup): diagnostic for the coordinator's
spawned-units hypothesis (attempt 2's A_bias moved -3.42 -> -3.34 under the cadence fix, i.e. barely, so
track loss from a too-coarse sample rate is not the dominant cause of the persistent NEGATIVE bias; a
negative bias under ``est = my_elixir + my_spent - opp_spent`` with PERFECT detection means ``opp_spent`` is
counting more than the opponent actually spent -- something is being charged that should not be). Two new
per-condition ledgers:
  ``charged_by_base`` -- every base the estimator's own ``_opp_spent`` accounting actually charged, and how
    much. Built by ``TrackedEstimator``, a subclass that does NOT reimplement or duplicate any of
    ``OpponentElixirEstimator``'s tracking/clustering logic (which would risk drifting from the real
    algorithm): ``update()`` is the ONLY place ``_opp_spent`` is ever incremented from a detection (the
    saturation rebase at lines 122-129 is a bookkeeping correction, not attributable to a specific card), and
    the ONLY thing that method reads to price a new track is exactly one call, ``self.db.elixir(base)``
    (opponent_elixir.py:109). ``TrackedEstimator.update()`` temporarily swaps ``self.db`` for a one-shot
    recorder proxy for the duration of the (unmodified) ``super().update()`` call, restores the real ``db``
    immediately after, and attributes every call the REAL charging code made (base, cost) with cost > 0 to
    ``charged_by_base``. This is the faithful option over diffing ``_opp_spent`` before/after: a diff cannot
    tell two different bases apart when both become new tracks inside the SAME ``update()`` call (a common
    case once ``update()`` batches several 5-tick-cadence detections), while wrapping the collaborator
    captures the real per-base charge event with no re-implementation and no ambiguity.
  ``ghost_played_by_base`` -- the TRUTH ledger: the opponent's actual card plays, from ``entry["ghost_commands"]``
    (the exact list ``PoolV1Mixin``/``EngineMatchEnv`` re-drives in eval mode -- e1_pool.py's own ``_cmd()``
    rows), excluding ability entries (``card`` is ``None``), costed via the SAME ``CardDB`` (never the
    engine's own recorded ``cost`` field, so both ledgers price off one source) after normalizing the pool's
    hyphenated slugs (``"giant-snowball"``) to vocab's underscore convention and folding evo/hero suffixes
    with ``vocab.base_key`` -- the SAME base-key space ``charged_by_base`` uses, so the two ledgers are
    directly comparable base-for-base.
Summary adds, per condition: an over-charge table (base | ghost_plays | ghost_elixir | charges |
charged_elixir | over_charge, top 25 by |over_charge| absolute value), ``total_over_charge``, and
``over_charge_share_from_bases_never_played`` (the fraction of charged elixir landing on bases the ghost
NEVER played at all -- a spawned body, e.g. tombstone's skeletons or a witch's summons, is BY DEFINITION not
in ``ghost_deck``/``ghost_commands`` since only the 8 played cards are, so this number directly tests the
spawned-units hypothesis). Per-match: ``over_charge_at_end`` (total charged elixir minus total ghost elixir
for that match) per condition, in each match's summary and in ``summary.json``'s
``over_charge_at_end_by_match``.

ATTEMPT 4 (progress file "## Attempt 4" has line numbers for every fix; blind verifier report
scratchpad/gauntlet/L67/opp_est/V8_verify.md, baseline 06dcc6d):

FIX 1 (the verifier's FAIL) -- the over-charge truth ledger was built from ``entry["ghost_commands"]``, the
SCRIPT, but the verifier measured (ctrl_live100, 100 matches) only 2429 of 3796 scripted ghost plays were
ever DELIVERED (68 refused, 1299 undelivered because 62/100 matches end before the script does) -- biasing
every over-charge figure NEGATIVE by about a third of ghost elixir, directly confounding the diagnosis. Fixed
by reading ``env.ghost_cards_delivered`` (a ``collections.Counter`` keyed by slug; ``PoolV1Mixin.reset()``
zeroes it per match at e1_pool.py:519, ``_fire_ghosts_at`` increments it ONLY on an accepted, non-mine ghost
play at e1_pool.py:562) at the end of each match and costing THAT via CardDB -- ``ghost_delivered_by_base``.
The old function is kept as ``ghost_scripted_by_base`` (same source, same costing) for reference ONLY,
clearly labelled in the summary and NEVER fed into ``over_charge``/``total_over_charge``/
``over_charge_share_from_bases_never_played``/``over_charge_at_end``, all of which now read exclusively from
``ghost_delivered_by_base``.

FIX 2 -- ``is_opp_play_tick`` (truth-drop >= 1.0) silently misses every 1-cost ghost play (regen offsets a
1-elixir drop below the threshold; the verifier measured 1613/12205 = 13% of held-out ghost plays cost 1).
Replaced with ``opp_play_flags``, a pure function over (a) the ascending list of this match's sampled ticks
and (b) ``env.ghost_events`` (a ``(tick, accepted 0/1, reason)`` log the SAME ghost-drive path already keeps,
engine_env.py:334 initializes it empty per match, PoolV1Mixin._fire_ghosts_at appends to it on every ghost
play attempt whether accepted or refused): the FIRST sampled tick at or after each ACCEPTED delivery's
recorded tick is flagged. CAVEAT, stated plainly: the recorded tick is the play's ORIGINAL SCRIPTED tick
(``g["tick"]``), not necessarily the engine tick it was actually accepted at -- a `not_enough_elixir` refusal
retries up to ``elixir_slack`` (40 ticks / 2s) later before either succeeding or being counted as refused
(e1_pool.py's ``_fire_ghosts_at``). Since the real accept tick is always >= the recorded one, flagging the
first sample at-or-after the recorded tick never MISSES a delivery, but for a retried play it can flag one or
two samples slightly EARLY (before the unit is actually visible on board). ``truth_drop`` (attempt 3) is kept
as an informational column, no longer used to set the flag.

FIX 3 -- per-match ``outcome``/``crowns_for``/``crowns_against`` (``ep._outcome(env, state)``'s second return
value was being discarded), ``plays_accepted``, ``decisions``, ``end_tick``, ``n_ticks`` are now persisted in
``summary.json``'s ``matches: [...]`` and in the final JSON line, field-for-field the same spelling
``e1_eval.run_match`` writes to ``matches.jsonl`` (``outcome`` a "win"/"draw"/"loss" string, ``crowns_for``/
``crowns_against`` ints, ``plays_accepted`` the accepted-play count) -- so the lead can diff this harness's
matches directly against ``attrib_noise/ctrl_live100/slot0/matches.jsonl`` as a fidelity gate.

FIX 4 -- condition ``A_wl``: perfect detection, enemy units only, WITH live's ``observation.detector_cards``
whitelist applied (``load_detector_cards``, loads ``icebow/config/config.yaml`` through the SAME unmodified
``clashrl.config.Config`` play.py itself uses -- ``cfg.get("observation", "detector_cards", default=[])``,
play.py:376). This is live's ACTUAL structural ceiling (A, kept unchanged, is a looser upper bound with no
whitelist at all -- the earlier "100% troop/building, zero spell entries" claim in CHANGE 2 above was WRONG
and is corrected here). MEASURED, independently re-derived from the pool file (not just taken from the
verifier): the whitelist has 46 entries; ``the_log`` (a spell -- ``vocab.SPELL_CLASSES`` -- config.yaml:494)
IS one of them, so "zero spell entries" was false. Across the held-out split's 12205 non-ability ghost card
plays, 4202 (34.4%) are non-spell bases the whitelist excludes (e.g. archer_queen, golem, mega_minion); of
the 9614 non-spell plays specifically, that is 4202/9614 = 43.7% -- both framings are given here since the
verifier's "34%" used the ALL-plays denominator, not the non-spell one. Summaries now report A+, A, A_wl, B.

NOTE (no fix needed, flagged by the verifier): ``--max-ticks`` truncates each match at that row count, and
``ep._outcome`` is then computed on a NON-TERMINAL engine state -- the CLI help now says this is smoke-only.

    icebow/.venv/Scripts/python.exe -m pipeline.opp_est_audit --port 38032 --ckpt <pt> --split heldout ^
        --entries 0:2 --max-ticks 600 --out scratchpad/gauntlet/L67/opp_est/smoke

TICKET O10 -- charge-event TRACE (no fix; instrumentation only). ATTEMPT 4's over-charge tables (real audit,
condition A) found continuously-visible SINGLE units re-billed many times over (tombstone: 58 delivered plays
-> 442 charges; miner 28 -> 201; witch 16 -> 142) despite ``_find_track`` (opponent_elixir.py:101-105)
appearing, by reading, to refresh a matched track's timestamp every update rather than re-charging it. This
adds ``--charge-trace``: for condition A ONLY, ``<out>/charges.jsonl`` (one row per actual ``_opp_spent``
increment, with the diagnostics needed to tell WHY the charge happened) and ``<out>/track_events.jsonl`` (one
row per track EXPIRY, i.e. every base ``_seen_tracks`` -- opponent_elixir.py:42-43 -- actually removes).

``TracedEstimator(TrackedEstimator)`` gets both WITHOUT re-implementing any tracking/matching/clustering
logic and WITHOUT touching opponent_elixir.py: it overrides ``_seen_tracks`` to diff ``self._tracks``
before/after the real (unmodified) ``super()._seen_tracks(now)`` call -- the ticket's own "diff before/after"
option, chosen over "replicate the same filter" because a diff can never drift from the real ``forget_s``
comparison if that constant or the comparison operator ever changes. ``update()`` snapshots ``self._tracks``
by object identity BEFORE calling ``super().update()`` (which runs the real, unmodified expiry -> match ->
cluster -> charge pipeline), then reads off which tracks in the POST-update list are new objects (never
mutated in place, only ever created fresh inside ``_cluster_new``'s loop, opponent_elixir.py:107-108) and
zips them 1:1, in order, against ``TrackedEstimator``'s own ``_RecorderDB`` call list (order-preserved because
both the ``self._tracks.append(...)`` and the ``self.db.elixir(base)`` call sit in the SAME loop iteration,
opponent_elixir.py:107-111) to recover (base, x, y, cost) for every actual charge, cost > 0 only, mirroring
``charged_by_base``'s own gate exactly.

Per-charge diagnostics are computed by the harness (``charge_diagnostics``), never inside the estimator, from
two things the estimator itself does not remember past one call: the PREVIOUS sample's det list (caller-
tracked, one match at a time) and the pre-update track snapshot ``TracedEstimator.update`` already captured
for its own bookkeeping. ``classify_charge_reason`` turns those into a best-effort ``reason`` string; see the
module's inline comment on that function for the one place its evaluation order deliberately departs from the
ticket text's literal listing order (and why -- the "rebill_after_expiry" acceptance scenario forces it).
Full writeup: scratchpad/gauntlet/L67/opp_fix/O10_trace.md.

TICKET O16 -- two new measurement conditions, both OFF by default (``--tracker``, ``--corr``; existing
runs byte-identical). Full writeup: scratchpad/gauntlet/L67/opp_fix/O16_tracker.md.

(a) TRACKER-INPUT (``--tracker``): condition B's raw dets feed billing directly (module docstring
above, "the estimator is fed raw dets instead" -- play.py:558). Live never does this: play.py:518
runs ``TeamTracker.tag()`` first and only THEN filters to ``d.team == "enemy"`` (play.py:547) before
``_opp_elx.update()`` ever sees a det. ``B_tt`` closes that gap: a ``TeamTracker`` (constructed with
live's own defaults -- ``make_team_tracker()`` below, cited against play.py:420-441 /
live_reader_audit.py:185-199) is fed the SAME per-sample det stream condition B already draws (no new
noise), and the V2 estimator is billed ONE synthetic det per track's FIRST sample at ``hits >=
min_hits`` ("first confirmed sighting"), at that track's position/base, team forced "enemy" (only
enemy-verdict tracks are ever billed) -- never the same track twice (``id(track)`` is a stable
per-track identity for its life, the SAME technique O10's ``TracedEstimator`` already uses for
track-expiry diffing; see ``tt_bill_dets``). ``B_corrS_tt``/``B_corrL_tt`` are the same billing scheme
over the correlated det streams (b) below, one independent ``TeamTracker`` per stream. KNOWN GAP: this
harness never renders pixels, so the HP-bar (rank 3) and body-art (rank 5) evidence ranks in
``TeamTracker._verdict`` cannot be simulated; the noisy per-sample team already baked into a detection
by ``degrade()``/``corr_live_view`` (UNKNOWN_TEAM_RATE / WRONG_TEAM_RATE) is wired into ``body_vote``
instead (the closest live analog: a noisy single-frame colour read) so the ladder's last-resort rank
still gets SOME evidence rather than none; ``bar_vote`` stays ``None`` throughout (rank 3 never fires).
Every det (mine + enemy + unknown side) is fed to the tracker, exactly as live's ``dets_all`` is,
so the deck veto / own-play anchor / motion prior see the same population a real run would.

(b) CORRELATED DEGRADE (``--corr``): ``pipeline/opp_est_degrade_corr.corr_live_view`` -- a NEW,
harness-local module (obs_contract.py / e1_view.py untouched, imported read-only). Full design
rationale, the closed-form Markov/AR(1) derivations, and the UNMEASURED-persistence-length caveat are
in that module's own docstring (read it before touching any constant here) and repeated in the
progress file. Two settings, both always run when ``--corr`` is set: ``CORR_SHORT`` (L_miss=1.5,
L_fp=1.5, rho=0.3) and ``CORR_LONG`` (L_miss=4, L_fp=8, rho=0.8) -- conditions ``B_corrS``/``B_corrL``
(raw-det estimator) and, additionally under ``--tracker``, ``B_corrS_tt``/``B_corrL_tt``. Each corr
setting gets its OWN per-match ``new_state()`` track dict and its OWN harness-local RNG stream
(``corrS_seed``/``corrL_seed``, same crc32-domain discipline as ``b5_seed``) -- never e1_eval's own
streams, never shared between settings, never re-used across matches.

(c) CONDITION-SET GENERALIZATION: ``BASE_CONDS`` (the 4-tuple ``Aplus/A/A_wl/B``) is UNCHANGED --
existing imports/tests that pin its exact shape keep working. ``active_base_conds(tracker, corr)``
returns the FULL set actually run this invocation (``BASE_CONDS`` plus whichever of
``B_tt``/``B_corrS``/``B_corrL``/``B_corrS_tt``/``B_corrL_tt`` are enabled), and every per-tick/
per-match data structure that used to iterate ``BASE_CONDS`` directly (the estimator dict, the dets/
my_elixir/n_enemy_dets maps, the row-building loops) now iterates ``active_base_conds(...)`` instead --
with both flags off this is BYTE-IDENTICAL to ``BASE_CONDS``, so ticks.jsonl/summary.json/summary.md
are unchanged for every existing invocation. ``_HIST_FIELD``/``tick_field`` gained entries for the five
new conditions (their OWN name, no historical spelling to preserve) so ticks.jsonl's new columns are
``est_B_tt``, ``n_enemy_dets_B_tt``, etc. -- for a ``_tt`` condition, ``n_enemy_dets_*`` counts dets
BILLED this sample (tracks newly confirmed), not raw enemy detections visible, since that is what is
actually fed to ``update()``; documented here and in the progress file, not just left to be inferred.

TICKET O16 ATTEMPT 2 -- blind verifier fixes (progress file "## Attempt 2" has the full writeup; the
corr module's marginals PASSED cleanly and were NOT touched).

FIX 1 (HIGH) -- ``billed_ids`` no longer keys on ``id(track dict)``. A track dict is freed the instant
``TeamTracker.tag()`` drops it from ``self._tracks``, and CPython's small-object allocator can (and, per
the verifier's 200-sequential-track probe, DOES) hand that exact address to the next same-shaped dict it
allocates -- a later, genuinely different track landing on a recycled address used to look
"already billed" under the old key and was silently never charged. Fixed by stamping a per-tracker
MONOTONIC uid into each track dict on first sight (``tr["_bill_uid"]``, from a counter
``make_team_tracker`` attaches to the instance as ``tracker._o16_uid_counter`` -- a dynamic attribute,
not a change to ``TeamTracker``/replay_mine.py itself) and keying ``billed_ids`` on THAT. Immune to
address recycling by construction: a freshly allocated dict starts with none of its own keys regardless
of which address it occupies. See ``tt_bill_dets``'s docstring for the full before/after reasoning.

FIX 2 (MEDIUM) -- ``B_tt`` (and its corr-setting siblings) is an IDEALISED DESIGN UNDER TEST, not a
measurement of what live's estimator path actually does today: live bills every enemy-tagged,
whitelisted det EVERY FRAME with no confirmation gate at all (play.py:547,558 -- ``min_hits`` lives only
in ``enemy_tracks()``, which feeds threat/aim logic, never ``_opp_elx.update()``). Every "_tt" label
(module docstring, ``BASE_LABELS`` in ``main()``) now says so explicitly. (b) Added the LIVE-REACHABLE
sibling of every "_tt" condition -- ``B_tt_wl``, ``B_corrS_tt_wl``, ``B_corrL_tt_wl``: the SAME
confirmed-track billing, additionally requiring the billed det's base to clear live's
``detector_cards`` whitelist (``filter_whitelisted_billed_dets``, applied to the tracker's OUTPUT, the
same place play.py:547's own filter sits relative to play.py:518's ``tag()`` call -- so a condition and
its "_wl" sibling share ONE ``tag()``/billing call per sample; tracking never forks between them, only
what is ultimately billed to each one's own estimator does). ``active_base_conds``/``build_cond_defs``
updated so ``--tracker --corr`` now yields (in order): ``Aplus, A, A_wl, B, B_tt, B_tt_wl, B_corrS,
B_corrS_tt, B_corrS_tt_wl, B_corrL, B_corrL_tt, B_corrL_tt_wl``.

FIX 3 (LOW) -- ``tt_dets_of`` now passes the RAW (unstripped) detector class name as ``Detection.cls``
when the pipeline det carries one (``_Det.raw_cls``, new optional field ``dets_of`` now fills in,
defaulting to None so every existing ``_Det(base, cx, gy, team)`` positional call is unaffected), falling
back to the already-stripped ``.base`` otherwise. Before this fix ``cls`` was always the stripped base
(e.g. "poison" instead of "poison_aoe"), so ``TeamTracker``'s zone-class rule (``d.cls in
ZONE_CLASSES``, where ``ZONE_CLASSES`` IS ``vocab.AOE_CLASSES`` -- raw "_aoe"-suffixed names) could never
fire. No effect on any measurement produced so far (every det stream billed through a tracker today is
units-only, per ``dets_of(bs.units)``/``dets_of(view.units)``/``dets_of(cview.units)`` -- no spells/zones
in the mix yet), kept faithful for whenever that changes.

LOW (docstring accuracy, verifier-flagged) -- re-checked: this module and ``opp_est_degrade_corr.py``
never described the false-positive process as a "random walk" anywhere (grepped both files plus the
progress file to confirm) -- both have always called it what it is, an AR(1) process about the host
unit's position (module docstring (b) above, and ``opp_est_degrade_corr.py``'s own docstring, design
item 2/3). No wording change was needed; noted here rather than silently assuming the flag applied.
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
import statistics
import sys
import time
import zlib
from dataclasses import replace
from pathlib import Path
from typing import Any, Optional

import numpy as np

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
_ICEBOW_SRC = REPO / "icebow" / "src"
if str(_ICEBOW_SRC) not in sys.path:
    sys.path.insert(0, str(_ICEBOW_SRC))

from pipeline import vocab                                                         # noqa: E402
from pipeline.dataset import _past                                                 # noqa: E402
from pipeline.e1_eval import (                                                     # noqa: E402
    DECIDE_EVERY, MAX_U, SLOT_OF_PORT, STALL_ELIXIR_LIVE, STALL_SECONDS_LIVE, TAU_LIVE,
    _slot_maps, allowed_slots, anti_stall, live_decide, make_tasks, model_forward, obs_seed,
    parse_entries, parse_seeds, parse_shard, refuse_existing_out,
)
from pipeline.e1_pool import POOL_V1, PoolV1Env, load_pool_v1, select_split, sha256_file  # noqa: E402
from pipeline.e1_view import Noise, live_view                                      # noqa: E402
from pipeline.obs_contract import _phase, from_engine, load_deck, to_tokens        # noqa: E402
from pipeline import engine_play as ep                                             # noqa: E402

from clashrl.cards import CardDB                                                   # noqa: E402
from clashrl.config import Config                                                  # noqa: E402
from clashrl.opponent_elixir import (                                              # noqa: E402
    OpponentElixirEstimator, OpponentElixirEstimatorV2, V2_PARAMS,
)
from clashrl.replay_mine import Detection as TTDetection, TeamTracker, own_card_bases  # noqa: E402

from pipeline.opp_est_degrade_corr import CORR_LONG, CORR_SHORT, CorrParams, corr_live_view, new_state  # noqa: E402


STEP_TICKS = 5              # CHANGE 1: estimator update cadence (engine ticks); must divide --decide-every
NEAR_CAP_TRUTH = 9.0         # CHANGE 2 (summary split): truth >= this is "near the [0, 10] saturation cap"


def b5_seed(tag: str, k: int) -> int:
    """Harness-local RNG domain for Condition B's estimator updates at the NON-policy 5-tick steps (module
    docstring CHANGE 1). Same crc32(f"{tag}:<domain>:{k}") shape as e1_eval.obs_seed/random_seed, a different
    domain string so it can never collide with either of those."""
    return zlib.crc32(f"{tag}:oppest_b5:{k}".encode())


def corrS_seed(tag: str, k: int) -> int:
    """O16(b): harness-local RNG domain for the SHORT correlated-degrade stream -- same crc32 discipline as
    ``b5_seed``, a distinct domain string so it never collides with e1_eval's streams, ``b5_seed``, or the
    LONG corr stream."""
    return zlib.crc32(f"{tag}:oppest_corrS:{k}".encode())


def corrL_seed(tag: str, k: int) -> int:
    """O16(b): the LONG correlated-degrade stream's own RNG domain -- see ``corrS_seed``."""
    return zlib.crc32(f"{tag}:oppest_corrL:{k}".encode())


def is_policy_tick(tick: int, first_tick: int, decide_every: int) -> bool:
    """True on the ticks the live policy actually decides on: the first decision tick and every
    ``decide_every`` engine ticks after it -- e1_eval's own cadence, unchanged by the finer 5-tick stepping."""
    return (int(tick) - int(first_tick)) % int(decide_every) == 0


# ------------------------------------------------------------------------------------------------------
# detection shim -- the shape OpponentElixirEstimator.update() reads (.base, .cx, .gy, .team); mirrors
# scratchpad/gauntlet/L67/opp_estimator_sim.py's ``_Det`` (that harness is the SIM, not the engine -- copied
# for its shape only, per the ticket).
# ------------------------------------------------------------------------------------------------------
class _Det:
    __slots__ = ("base", "cx", "gy", "team", "raw_cls")

    def __init__(self, base: str, cx: float, gy: float, team: str, raw_cls: Optional[str] = None):
        self.base = str(base)
        self.cx = float(cx)
        self.gy = float(gy)
        self.team = str(team)
        # O16 attempt 2 FIX 3 (verifier, LOW): the UNSTRIPPED detector class name (e.g. "poison_aoe"),
        # when known -- ``base`` is already ``vocab.base_key``-folded (e.g. "poison"), which is what every
        # OTHER consumer of ``_Det`` wants, but ``tt_dets_of`` needs the raw name so TeamTracker's own
        # zone-class check (``d.cls in ZONE_CLASSES``, replay_mine.py -- ``ZONE_CLASSES`` is exactly
        # ``vocab.AOE_CLASSES``, RAW "_aoe"-suffixed names) can ever fire. Optional and defaults to None
        # (falls back to ``base``) so every existing positional ``_Det(base, cx, gy, team)`` call --
        # tests included -- is unaffected.
        self.raw_cls = str(raw_cls) if raw_cls is not None else None


_TEAM_OF_SIDE = {0: "mine", 1: "enemy", -1: "unknown"}
PHASES = ("single", "double", "overtime")


def dets_of(items) -> list[_Det]:
    """Any ``BoardState`` unit sequence (``.units`` OR ``.spells``) -> ``_Det`` list, every side kept (the
    estimator's own ``update()`` filters to ``team == "enemy"`` at opponent_elixir.py:94, so passing all
    three and letting it filter is equivalent to pre-filtering, and matches e1_eval's own dets shape).
    Carries the RAW (unstripped) detector class name too (``_Det.raw_cls`` -- FIX 3 above); today only
    ``tt_dets_of`` reads it, everyone else keeps using ``.base``."""
    out = []
    for u in items:
        raw = vocab.UNIT_VOCAB[u.cls]
        out.append(_Det(vocab.base_key(raw), u.x, u.y, _TEAM_OF_SIDE.get(u.side, "unknown"), raw_cls=raw))
    return out


def dets_of_costed(items, db: CardDB, warned: set) -> list[_Det]:
    """Like ``dets_of`` but drops (never zero-costs) any item whose base has no CardDB elixir row, logging
    the base ONCE per process into ``warned`` -- CHANGE 2's A+ spell path (e.g. Mirror: dynamic pricing, no
    flat ``elixir`` key, found in attempt 1's dets-conversion test)."""
    out = []
    for u in items:
        base = vocab.base_key(vocab.UNIT_VOCAB[u.cls])
        if db.elixir(base) is None:
            if base not in warned:
                warned.add(base)
                print(f"[opp_est_audit] A+: {base!r} has no CardDB elixir cost -- skipped from dets "
                     f"(not charged as free)", flush=True)
            continue
        out.append(_Det(base, u.x, u.y, _TEAM_OF_SIDE.get(u.side, "unknown")))
    return out


def load_detector_cards(config_path) -> frozenset[str]:
    """FIX 4: live's ``observation.detector_cards`` whitelist, loaded the SAME way play.py:376 does
    (``cfg.get("observation", "detector_cards", default=[])``) through the UNMODIFIED ``clashrl.config.
    Config`` -- never a re-parse of the yaml by hand. ``config_path`` is ``deck.config``
    (``icebow/config/config.yaml``, per pipeline/decks/icebow.yaml)."""
    cfg = Config.load(str(config_path))
    return frozenset(str(c) for c in (cfg.get("observation", "detector_cards", default=[]) or []))


def dets_of_whitelisted(items, whitelist: frozenset) -> list[_Det]:
    """Like ``dets_of`` but drops an ENEMY det whose base is outside live's ``detector_cards`` whitelist
    (FIX 4's Condition A_wl, live's actual structural ceiling) -- mine/unknown dets pass through unfiltered
    since the estimator's own ``update()`` drops them by team regardless (opponent_elixir.py:94)."""
    return [d for d in dets_of(items) if d.team != "enemy" or d.base in whitelist]


def n_enemy(items) -> int:
    return sum(1 for u in items if u.side == 1)


def phase_from_flags(double_elixir: bool, overtime: bool) -> str:
    if overtime:
        return "overtime"
    if double_elixir:
        return "double"
    return "single"


def phase_of(bs) -> str:
    return phase_from_flags(bs.double_elixir, bs.overtime)


def card_cost(db: CardDB, cls_id: int) -> Optional[int]:
    """Vocab id -> elixir cost via the same base-key fold the estimator's own ``db.elixir(d.base)`` call uses."""
    return db.elixir(vocab.base_key(vocab.UNIT_VOCAB[cls_id]))


# ------------------------------------------------------------------------------------------------------
# ATTEMPT 3: charge attribution -- see the module docstring for why db-wrapping (not a diff of _opp_spent,
# not a reimplementation of update()) is the faithful way to get this without touching opponent_elixir.py.
# ------------------------------------------------------------------------------------------------------
class _RecorderDB:
    """Transparent proxy: forwards ``.elixir(base)`` to the REAL db and records every (base, cost) call made
    while it is installed, and forwards EVERY OTHER attribute (e.g. V2's ``.speed_tiles(base)``) straight
    through via ``__getattr__`` -- unrecorded, but never dropped. FIX 2 (O13 attempt 2 verifier, HIGH):
    before this, only ``elixir`` was forwarded, so ``OpponentElixirEstimatorV2._speed_radius``'s
    ``getattr(self.db, "speed_tiles", None)`` saw None while wrapped by ``TrackedEstimator[V2]``/
    ``TracedEstimator[V2]`` -- R3 (speed_aware_radius) silently went inert INSIDE the harness even though the
    bare estimator (as exercised directly in icebow/tests/test_opponent_elixir_v2.py) has it fully working,
    so the audit would have measured a different estimator than the one the unit tests cover."""

    def __init__(self, real_db, calls: list):
        self._real = real_db
        self._calls = calls

    def elixir(self, base):
        c = self._real.elixir(base)
        self._calls.append((base, c))
        return c

    def __getattr__(self, name):
        # only reached for attributes NOT found on this proxy itself (i.e. anything but elixir/_real/_calls)
        return getattr(self._real, name)


class _TrackedMixin:
    """``**kwargs`` forwarded to the underlying estimator's ``__init__`` -- with none, byte-identical to the
    original ``TrackedEstimator(db)`` shape (O10); ``TrackedEstimatorV2`` (O13) reuses this same mixin to
    wrap ``OpponentElixirEstimatorV2`` instead, forwarding its ablation kwargs (suppress_spawns=, etc.)
    through the SAME db-wrapping instrumentation -- no charging/tracking logic is duplicated either way."""

    def __init__(self, db, **kwargs):
        super().__init__(db, **kwargs)
        self.charged_by_base: dict[str, list] = {}   # base -> [n_charges, total_elixir_charged]
        self.last_calls: list[tuple[str, Optional[float]]] = []   # O10: this update() call's raw db.elixir()
                                                                    # calls (base, cost), in _cluster_new order --
                                                                    # read-only bookkeeping, no behavior change.

    def update(self, my_elixir, enemy_dets, now):
        real_db = self.db
        calls: list[tuple[str, Optional[float]]] = []
        self.db = _RecorderDB(real_db, calls)
        try:
            result = super().update(my_elixir, enemy_dets, now)
        finally:
            self.db = real_db
        for base, c in calls:
            cf = float(c or 0.0)
            if cf > 0.0:                              # mirrors update()'s own ``if c > 0.0`` charge gate exactly
                row = self.charged_by_base.setdefault(base, [0, 0.0])
                row[0] += 1
                row[1] += cf
        self.last_calls = calls        # O10: exposed so TracedEstimator can pair (base, cost) with new tracks
        return result


class TrackedEstimator(_TrackedMixin, OpponentElixirEstimator):
    """``OpponentElixirEstimator`` (V1) with a per-instance ``charged_by_base`` ledger -- UNCHANGED from
    before O13 (same name, same behavior; existing tests/callers construct it as ``TrackedEstimator(db)``)."""


class TrackedEstimatorV2(_TrackedMixin, OpponentElixirEstimatorV2):
    """O13: the same db-wrapping charge ledger, wrapping ``OpponentElixirEstimatorV2`` instead -- lets the
    harness measure V2's ``charged_by_base``/over-charge ledger side by side with V1's, from the SAME
    instrumentation, with NO duplicated tracking/matching/clustering/suppression logic. Extra kwargs
    (``suppress_spawns=``, ``body_count=``, ``speed_aware_radius=``, ...) pass straight through to
    ``OpponentElixirEstimatorV2.__init__``."""


# ------------------------------------------------------------------------------------------------------
# TICKET O10: charge-event / track-expiry trace -- see module docstring for the full design rationale.
# ------------------------------------------------------------------------------------------------------
class _TracedMixin:
    """``TrackedEstimator``/``TrackedEstimatorV2`` plus two mechanical, read-only observations of the SAME
    unmodified super() calls: ``last_charges`` (this update() call's newly-tracked, cost > 0 bases with (x,
    y, cost, n_tracks_before, n_tracks_after)) and ``last_expired`` (this update() call's track EXPIRIES,
    i.e. every track ``_seen_tracks`` actually dropped). Neither re-implements matching/clustering/
    forgetting -- both are diffs of ``self._tracks`` around the real, unmodified super() calls, by object
    identity (track dicts are mutated in place when refreshed, and are only ever created fresh inside the
    estimator's own clustering loop, so identity alone tells 'refreshed' from 'new' or 'gone' correctly, for
    EITHER estimator version)."""

    def __init__(self, db, **kwargs):
        super().__init__(db, **kwargs)
        self.last_charges: list[dict] = []
        self.last_expired: list[dict] = []

    def _seen_tracks(self, now: float) -> None:
        before = list(self._tracks)
        super()._seen_tracks(now)                      # the REAL, unmodified forget_s filter
        kept_ids = {id(tr) for tr in self._tracks}
        self.last_expired = [
            {"base": tr["base"], "x": tr["x"], "y": tr["y"], "age_s": float(now) - float(tr["t"]),
             "last_seen_t": float(tr["t"])}
            for tr in before if id(tr) not in kept_ids
        ]

    def update(self, my_elixir, enemy_dets, now):
        tracks_before = list(self._tracks)             # BEFORE this call's _seen_tracks/match/cluster/charge
        before_ids = {id(tr) for tr in tracks_before}
        n_before = len(tracks_before)
        result = super().update(my_elixir, enemy_dets, now)   # real _seen_tracks (via our override above) +
                                                                 # real match/cluster/charge (via the Tracked mixin)
        new_tracks = [tr for tr in self._tracks if id(tr) not in before_ids]   # cluster-append order
        n_after = len(self._tracks)
        charges = []
        v2_ledger = getattr(self, "last_new_tracks", None)   # O13 attempt 2 FIX 3 -- V2 only (None for V1)
        if v2_ledger is not None:
            # V2: attribute EXACTLY via its own per-track (base, x, y, charged, cost) ledger, in the SAME
            # creation order as new_tracks -- never a positional zip against db.elixir() CALLS, which breaks
            # as soon as any new track is spawn-suppressed (R1) or body-count-absorbed (R2) without a call.
            for tr, (_base, _x, _y, charged, cost) in zip(new_tracks, v2_ledger):
                if charged:
                    charges.append({"base": tr["base"], "x": tr["x"], "y": tr["y"], "cost": float(cost),
                                    "n_tracks_before": n_before, "n_tracks_after": n_after})
        else:
            # V1: every new track makes EXACTLY one db.elixir() call (one charge per cluster, unconditionally
            # -- opponent_elixir.py's original update()), so this positional zip is exact. UNCHANGED from
            # before O13 attempt 2.
            for tr, (base, cost) in zip(new_tracks, self.last_calls):
                cf = float(cost or 0.0)
                if cf > 0.0:                            # same charge gate as charged_by_base
                    charges.append({"base": tr["base"], "x": tr["x"], "y": tr["y"], "cost": cf,
                                    "n_tracks_before": n_before, "n_tracks_after": n_after})
        self.last_charges = charges
        return result


class TracedEstimator(_TracedMixin, TrackedEstimator):
    """UNCHANGED from before O13 (same name, same behavior; constructed as ``TracedEstimator(db)``)."""


class TracedEstimatorV2(_TracedMixin, TrackedEstimatorV2):
    """O13: the same charge/expiry trace, over ``OpponentElixirEstimatorV2``. Constructed as
    ``TracedEstimatorV2(db, **v2_kwargs)``."""


def _dist(ax: float, ay: float, bx: float, by: float) -> float:
    return math.hypot(ax - bx, ay - by)


def charge_diagnostics(base: str, x: float, y: float, prev_dets: Optional[list], tracks_before: list[dict],
                       match_radius: float, cluster_radius: float) -> dict:
    """O10 (b): the diagnostic fields computed by the HARNESS (never inside the estimator) from the PREVIOUS
    sample's dets and the pre-update track snapshot ``TracedEstimator.update`` already took."""
    prev_same = [d for d in (prev_dets or [])
                if str(getattr(d, "team", None)) == "enemy" and str(getattr(d, "base", "")) == base]
    prev_dists = [_dist(float(d.cx), float(d.gy), x, y) for d in prev_same]
    prev_min = min(prev_dists) if prev_dists else None
    track_same = [tr for tr in tracks_before if tr["base"] == base]
    track_dists = [_dist(float(tr["x"]), float(tr["y"]), x, y) for tr in track_same]
    track_min = min(track_dists) if track_dists else None
    return {
        "prev_same_base_within_match_radius": bool(prev_min is not None and prev_min <= match_radius),
        "prev_same_base_min_dist": (round(prev_min, 4) if prev_min is not None else None),
        "prev_n_same_base": len(prev_same),
        "same_base_track_existed_before": bool(track_same),
        "nearest_track_same_base_dist": (round(track_min, 4) if track_min is not None else None),
    }


def classify_charge_reason(base: str, diag: dict, expired_bases_this_update: set, match_radius: float,
                           cluster_radius: float) -> str:
    """O10 (c): best-effort classification from ``charge_diagnostics`` + this SAME update() call's
    track_events (``expired_bases_this_update``, from ``TracedEstimator.last_expired``).

    DEVIATION FROM THE TICKET TEXT'S LITERAL LISTING ORDER (first_seen, split, rebill_after_expiry,
    rebill_out_of_radius, other), flagged in the progress file and hand-back: this checks
    rebill_after_expiry BEFORE split. The ticket's own acceptance scenario -- a unit absent 7s then
    reappearing at (or near) its old, stationary position -- is simultaneously <= cluster_radius of its own
    previous-sample detection (it never moved) AND had a live track before this update, so under the literal
    a/b/c/d order it would hit 'split' first and never reach 'rebill_after_expiry', contradicting that same
    acceptance test. Checking the expiry cross-reference first resolves this in the direction the acceptance
    test requires, and is the more causally direct story (the track was PROVABLY just removed this exact
    update) versus a merely coincidental positional match. All raw diagnostic fields are kept on every row
    regardless, so the lead can re-derive any other ordering they prefer."""
    if diag["prev_n_same_base"] == 0 and not diag["same_base_track_existed_before"]:
        return "first_seen"
    if diag["same_base_track_existed_before"] and base in expired_bases_this_update:
        return "rebill_after_expiry"
    if (diag["prev_same_base_min_dist"] is not None and diag["prev_same_base_min_dist"] <= cluster_radius
            and diag["same_base_track_existed_before"]):
        return "split"
    if diag["prev_n_same_base"] > 0 and (diag["prev_same_base_min_dist"] is None
                                         or diag["prev_same_base_min_dist"] > match_radius):
        return "rebill_out_of_radius"
    return "other"


def run_traced_update(est: TracedEstimator, my_elixir: float, dets: list, now: float, tick: int, tag: str,
                      k: int, prev_dets: Optional[list], prev_t: Optional[float], t_to_tick: dict
                      ) -> tuple[list[dict], list[dict]]:
    """One condition-A ``TracedEstimator.update()`` cycle with tracing: calls the real (unmodified) update(),
    then builds this call's charge rows (module docstring O10 (a)/(b)/(c)) and track-event rows from
    ``est.last_charges``/``est.last_expired`` plus ``prev_dets`` (the PREVIOUS sample's det list for this
    match, caller-tracked) and ``t_to_tick`` (this match's t_sec -> tick map, caller-updated every sample so
    a track's stored ``t`` -- always some earlier call's ``now`` -- can be resolved back to a tick)."""
    tracks_before = [dict(tr) for tr in est._tracks]        # value snapshot, immune to later in-place mutation
    t_to_tick[float(now)] = int(tick)
    est.update(my_elixir, dets, now)
    expired_bases = {ex["base"] for ex in est.last_expired}
    match_radius, cluster_radius = est.match_radius, est.cluster_radius
    charge_rows = []
    for ch in est.last_charges:
        diag = charge_diagnostics(ch["base"], ch["x"], ch["y"], prev_dets, tracks_before,
                                  match_radius, cluster_radius)
        reason = classify_charge_reason(ch["base"], diag, expired_bases, match_radius, cluster_radius)
        dt = (round(float(now) - float(prev_t), 4) if prev_t is not None else None)
        charge_rows.append({"tag": tag, "k": int(k), "tick": int(tick), "t_sec": round(float(now), 3),
                            "base": ch["base"], "cost": ch["cost"], "x": ch["x"], "y": ch["y"],
                            "n_tracks_before": ch["n_tracks_before"], "n_tracks_after": ch["n_tracks_after"],
                            "reason": reason, "dt_since_prev_sample_s": dt, **diag})
    track_rows = []
    for ex in est.last_expired:
        track_rows.append({"tag": tag, "k": int(k), "tick": int(tick), "base": ex["base"], "x": ex["x"],
                           "y": ex["y"], "age_s": round(float(ex["age_s"]), 4),
                           "last_seen_tick": t_to_tick.get(ex["last_seen_t"])})
    return charge_rows, track_rows


def _base_of_slug(slug: str) -> str:
    """The pool's hyphenated slugs (e.g. ``"giant-snowball"``) normalized to vocab's underscore convention,
    then evo/hero suffix-folded -- the SAME base-key space ``charged_by_base`` uses."""
    return vocab.base_key(str(slug).replace("-", "_"))


def _cost_ledger_add(out: dict[str, list], base: str, n: int, cost: float) -> None:
    row = out.setdefault(base, [0, 0.0])
    row[0] += n
    row[1] += n * cost


def _warn_costless_once(base: str, warned: set, where: str) -> None:
    if base not in warned:
        warned.add(base)
        print(f"[opp_est_audit] {where}: {base!r} has no CardDB elixir cost -- excluded from the ledger "
             f"(not charged as free)", flush=True)


def ghost_scripted_by_base(entry: dict, db: CardDB, warned: Optional[set] = None) -> dict[str, list]:
    """REFERENCE ONLY (FIX 1 -- see module docstring): the opponent's SCRIPTED card plays for one
    pool entry, from ``entry["ghost_commands"]`` (ability entries excluded -- ``card`` is ``None`` for those,
    e1_pool.py's ``_cmd()``), costed via CardDB. NOT what actually happened in the match -- a scripted play
    can be refused, or the match can end before the script does (verifier: ~1/3 of scripted plays, ctrl_
    live100). Use ``ghost_delivered_by_base`` for anything measuring the estimator against truth; this
    function exists only so the SCRIPT is visible for reference, clearly labelled as such in the summary."""
    if warned is None:
        warned = set()
    out: dict[str, list] = {}
    for c in entry.get("ghost_commands") or []:
        if c.get("ability") or not c.get("card"):
            continue
        base = _base_of_slug(c["card"])
        cost = db.elixir(base)
        if cost is None:
            _warn_costless_once(base, warned, "ghost_scripted_by_base")
            continue
        _cost_ledger_add(out, base, 1, float(cost))
    return out


def ghost_delivered_by_base(delivered: dict, db: CardDB, warned: Optional[set] = None) -> dict[str, list]:
    """FIX 1 -- the TRUTH ledger every over-charge figure uses: the opponent's ACTUALLY DELIVERED card plays
    for one match, from ``env.ghost_cards_delivered`` (a ``collections.Counter`` keyed by slug; PoolV1Mixin.
    reset() zeroes it per match at e1_pool.py:519, ``_fire_ghosts_at`` increments it ONLY on an accepted,
    non-mine ghost play at e1_pool.py:562 -- refused and never-reached plays are never counted), costed via
    the SAME CardDB / base-key folding ``ghost_scripted_by_base``/``charged_by_base`` use. ``delivered`` is
    ``dict(env.ghost_cards_delivered)`` (or any ``{slug: count}`` mapping -- a hand-built stub for tests)."""
    if warned is None:
        warned = set()
    out: dict[str, list] = {}
    for slug, n in (delivered or {}).items():
        if not slug or not n:
            continue
        base = _base_of_slug(slug)
        cost = db.elixir(base)
        if cost is None:
            _warn_costless_once(base, warned, "ghost_delivered_by_base")
            continue
        _cost_ledger_add(out, base, int(n), float(cost))
    return out


def opp_play_flags(sample_ticks: list, ghost_events: list) -> list:
    """FIX 2 -- one bool per ``sample_ticks`` entry (ascending engine ticks, this match's per-row ticks):
    True on the FIRST sample tick at or after each ACCEPTED ghost delivery's recorded tick. ``ghost_events``
    is ``env.ghost_events`` for this match, ``(tick, accepted 0/1, reason)`` tuples -- engine_env.py:334
    initializes it to ``[]`` per match reset, PoolV1Mixin._fire_ghosts_at appends one entry per ghost play
    ATTEMPT (accepted or refused); only ``accepted == 1`` entries count as a delivery here. Multiple
    deliveries landing between the same two sample ticks all flag the one next sample tick they share.
    CAVEAT (module docstring FIX 2): the recorded tick is the play's ORIGINAL SCRIPTED tick, which for a
    retried play (elixir-slack) can be up to ``elixir_slack`` ticks before the real accept tick -- this can
    flag a sample slightly EARLY but never misses a delivery, since the real accept tick is always >= it."""
    delivered = sorted(int(t) for t, ok, _r in ghost_events if int(ok) == 1)
    out = [False] * len(sample_ticks)
    di = 0
    for i, t in enumerate(sample_ticks):
        while di < len(delivered) and delivered[di] <= int(t):
            out[i] = True
            di += 1
    return out


def merge_base_ledgers(ledgers: list[dict]) -> dict[str, list]:
    """Sum a list of {base: [n, total]} dicts (one per match) into one run-level ledger."""
    out: dict[str, list] = {}
    for d in ledgers:
        for base, (n, tot) in d.items():
            row = out.setdefault(base, [0, 0.0])
            row[0] += n
            row[1] += tot
    return out


def overcharge_table(charged: dict[str, list], ghost: dict[str, list], top: int = 25) -> dict:
    """Per-condition base | ghost_plays | ghost_elixir | charges | charged_elixir | over_charge table (module
    docstring, ATTEMPT 3), sorted by |over_charge| descending, plus the two run-level diagnostics."""
    bases = set(charged) | set(ghost)
    rows = []
    for b in sorted(bases):
        gp, ge = ghost.get(b, [0, 0.0])
        cp, ce = charged.get(b, [0, 0.0])
        rows.append({"base": b, "ghost_plays": int(gp), "ghost_elixir": round(float(ge), 2),
                    "charges": int(cp), "charged_elixir": round(float(ce), 2),
                    "over_charge": round(float(ce) - float(ge), 2)})
    rows.sort(key=lambda r: -abs(r["over_charge"]))
    total_charged = sum(r["charged_elixir"] for r in rows)
    total_ghost = sum(r["ghost_elixir"] for r in rows)
    never_played_charged = sum(r["charged_elixir"] for r in rows if r["ghost_plays"] == 0)
    share = (never_played_charged / total_charged) if total_charged > 0 else None
    return {"top": rows[:top], "n_bases": len(rows),
           "total_charged_elixir": round(total_charged, 2), "total_ghost_elixir": round(total_ghost, 2),
           "total_over_charge": round(total_charged - total_ghost, 2),
           "over_charge_share_from_bases_never_played": (round(share, 4) if share is not None else None)}


# ------------------------------------------------------------------------------------------------------
# pure metric helpers (tested offline; no numpy percentile surprises -- linear interpolation, matches
# numpy.percentile's default so results are reproducible without importing it in the hot path)
# ------------------------------------------------------------------------------------------------------
def mae(errs: list[float]) -> Optional[float]:
    return sum(abs(e) for e in errs) / len(errs) if errs else None


def mean_bias(errs: list[float]) -> Optional[float]:
    return sum(errs) / len(errs) if errs else None


def percentile(vals: list[float], q: float) -> Optional[float]:
    """Linear-interpolation percentile (numpy.percentile's default method), q in [0, 100]."""
    if not vals:
        return None
    s = sorted(vals)
    if len(s) == 1:
        return float(s[0])
    rank = (q / 100.0) * (len(s) - 1)
    lo = int(rank)
    hi = min(lo + 1, len(s) - 1)
    frac = rank - lo
    return float(s[lo] + (s[hi] - s[lo]) * frac)


def share_within(abs_errs: list[float], bound: float) -> Optional[float]:
    return sum(1 for e in abs_errs if e <= bound) / len(abs_errs) if abs_errs else None


def summarize_condition(rows: list[dict], est_key: str) -> dict:
    """One condition's ("Aplus"/"A"/"B") full metric block over ``rows`` (dicts with truth/est*/phase/tag/k/
    is_opp_play_tick/is_my_play_tick)."""
    errs = [r[est_key] - r["truth"] for r in rows]
    abs_errs = [abs(e) for e in errs]
    out: dict[str, Any] = {
        "n_ticks": len(rows),
        "mae": mae(errs), "mean_bias": mean_bias(errs), "p90_abs_err": percentile(abs_errs, 90),
        "share_abs_err_le_1_0": share_within(abs_errs, 1.0), "share_abs_err_le_2_0": share_within(abs_errs, 2.0),
        "by_phase": {}, "opp_play_ticks": {}, "my_play_ticks": {}, "by_match": {}, "by_truth_cap": {},
    }
    for ph in PHASES:
        sub = [r[est_key] - r["truth"] for r in rows if r["phase"] == ph]
        out["by_phase"][ph] = {"n": len(sub), "mae": mae(sub), "mean_bias": mean_bias(sub),
                               "p90_abs_err": percentile([abs(e) for e in sub], 90)}
    opp_sub = [r[est_key] - r["truth"] for r in rows if r.get("is_opp_play_tick")]
    out["opp_play_ticks"] = {"n": len(opp_sub), "mae": mae(opp_sub), "bias": mean_bias(opp_sub)}
    my_sub = [r[est_key] - r["truth"] for r in rows if r.get("is_my_play_tick")]
    out["my_play_ticks"] = {"n": len(my_sub), "mae": mae(my_sub), "bias": mean_bias(my_sub)}
    near_sub = [r[est_key] - r["truth"] for r in rows if r["truth"] >= NEAR_CAP_TRUTH]
    below_sub = [r[est_key] - r["truth"] for r in rows if r["truth"] < NEAR_CAP_TRUTH]
    out["by_truth_cap"] = {
        "near_cap_ge_9": {"n": len(near_sub), "mae": mae(near_sub), "mean_bias": mean_bias(near_sub)},
        "below_cap": {"n": len(below_sub), "mae": mae(below_sub), "mean_bias": mean_bias(below_sub)},
    }
    by_match: dict[tuple, list[float]] = {}
    for r in rows:
        by_match.setdefault((r["tag"], r["k"]), []).append(abs(r[est_key] - r["truth"]))
    match_maes = [sum(v) / len(v) for v in by_match.values() if v]
    out["by_match"] = {"n_matches": len(by_match), "mae_median": (statistics.median(match_maes)
                        if match_maes else None), "mae_p90": percentile(match_maes, 90)}
    return out


# ------------------------------------------------------------------------------------------------------
# O13: BASE_CONDS x estimator variant -- run_match_audit builds one TrackedEstimator[V2] per (base
# condition, variant) pair. Field/condition-key naming is UNCHANGED (Aplus/A/A_wl/B, est_Aplus/est_A/
# est_Awl/est_B) whenever only ONE variant is active (the default ``--estimator v1`` reproduces the exact
# pre-O13 shape; ``--estimator v2`` reuses the same names, just backed by V2 instances) -- keys only grow a
# ``_v1``/``_v2`` suffix under ``--estimator both``, per the ticket's "A_v1, A_v2, A_wl_v1, A_wl_v2, ..."
# ------------------------------------------------------------------------------------------------------
BASE_CONDS: tuple[str, ...] = ("Aplus", "A", "A_wl", "B")
_HIST_FIELD = {"Aplus": "Aplus", "A": "A", "A_wl": "Awl", "B": "B"}   # historical (pre-O13) field spelling
# O16: the new conditions have no pre-existing spelling to preserve -- their ticks.jsonl column is just
# their own name (est_B_tt, n_enemy_dets_B_corrS_tt_wl, ...). tick_field() falls back to the base name
# itself for any key not in this dict, so this update is additive only -- BASE_CONDS's four historical
# entries above are untouched. Attempt 2 FIX 2(b) adds the three "_wl" (live-reachable) siblings.
_HIST_FIELD.update({"B_tt": "B_tt", "B_tt_wl": "B_tt_wl", "B_corrS": "B_corrS", "B_corrL": "B_corrL",
                    "B_corrS_tt": "B_corrS_tt", "B_corrS_tt_wl": "B_corrS_tt_wl",
                    "B_corrL_tt": "B_corrL_tt", "B_corrL_tt_wl": "B_corrL_tt_wl"})

#: O16: every condition this module knows how to run, base-condition-agnostic, in the fixed order
#: active_base_conds() ever emits them (BASE_CONDS first, then B's tracker-input pair, then each corr
#: setting's raw-det condition followed by its own tracker-input pair) -- long summary-key name -> short
#: base name.
_LONG_NAME = {
    "Aplus": "Aplus_perfect_detection_with_spells", "A": "A_perfect_detection",
    "A_wl": "A_wl_live_whitelist", "B": "B_degraded_live",
    "B_tt": "B_tt_tracker_input_idealised", "B_tt_wl": "B_tt_wl_tracker_input_live_whitelist",
    "B_corrS": "B_corrS_short_correlated",
    "B_corrS_tt": "B_corrS_tt_short_correlated_tracker_input_idealised",
    "B_corrS_tt_wl": "B_corrS_tt_wl_short_correlated_tracker_input_live_whitelist",
    "B_corrL": "B_corrL_long_correlated",
    "B_corrL_tt": "B_corrL_tt_long_correlated_tracker_input_idealised",
    "B_corrL_tt_wl": "B_corrL_tt_wl_long_correlated_tracker_input_live_whitelist",
}


def active_base_conds(tracker: bool, corr: bool) -> tuple[str, ...]:
    """O16(c): the full set of base conditions THIS invocation runs. Both flags False (the default)
    reproduces ``BASE_CONDS`` exactly (tuple equality, not just same elements) -- every existing
    invocation's ticks.jsonl/summary keys are therefore byte-identical to before O16. ``--tracker`` alone
    adds ``B_tt`` + ``B_tt_wl`` (billed from condition B's own det stream via a TeamTracker, module
    docstring (a); ``_wl`` is the live-reachable, whitelist-filtered sibling -- attempt 2 FIX 2(b));
    ``--corr`` alone adds the two raw-det correlated conditions ``B_corrS``/``B_corrL``; both together
    additionally add, for EACH corr setting, its own tracker-input pair (``B_corrS_tt``/``B_corrS_tt_wl``,
    ``B_corrL_tt``/``B_corrL_tt_wl``) right after that setting's raw-det condition. With both flags on:
    ``Aplus, A, A_wl, B, B_tt, B_tt_wl, B_corrS, B_corrS_tt, B_corrS_tt_wl, B_corrL, B_corrL_tt,
    B_corrL_tt_wl``."""
    conds = list(BASE_CONDS)
    if tracker:
        conds += ["B_tt", "B_tt_wl"]
    if corr:
        for name in ("B_corrS", "B_corrL"):
            conds.append(name)
            if tracker:
                conds += [f"{name}_tt", f"{name}_tt_wl"]
    return tuple(conds)


def build_cond_defs(tracker: bool, corr: bool) -> tuple[tuple[str, str], ...]:
    """(long_summary_key, base_condition) pairs for exactly the conditions ``active_base_conds`` returns,
    in the same order -- replaces main()'s old hardcoded ``COND_DEFS`` 4-tuple, which is now this
    function's ``tracker=False, corr=False`` case (byte-identical output, per O16(c))."""
    return tuple((_LONG_NAME[b], b) for b in active_base_conds(tracker, corr))


# ------------------------------------------------------------------------------------------------------
# O16(a): TeamTracker-input billing. See the module docstring's O16(a) section for the full design and
# the KNOWN GAP (no bar_vote/body_vote pixel evidence available offline).
# ------------------------------------------------------------------------------------------------------
def make_team_tracker(db: CardDB) -> TeamTracker:
    """A ``TeamTracker`` built with LIVE's OWN construction defaults -- literal-for-literal the values
    play.py:420-441 passes (``icebow/tools/live_reader_audit.py:185-199`` builds it identically offline,
    modulo ``is_spell``, confirming these are the shared live/offline defaults, not a one-off). The only
    parameter live derives from ``cfg.get(...)`` that is NOT simply the class's own ``__init__`` default
    is ``enemy_window_s`` (4.0 live vs 2.5 if left to default to ``spawn_window_s``) -- every other value
    below equals both the live cfg default AND the bare class default; they are still spelled out
    explicitly so this construction can never silently drift from live if either default ever changes.

    O16 attempt 2 FIX 1 (verifier, HIGH): also stamps a per-tracker monotonic uid COUNTER onto the
    returned instance (``tt._o16_uid_counter``) -- a plain dynamic attribute, not a change to
    ``TeamTracker`` itself (``replay_mine.py`` is O15's protected territory this ticket never opens for
    writing). ``tt_bill_dets`` uses it to stamp a content-based id into each track dict on first sight;
    see that function's docstring for why ``id(track dict)`` alone was wrong."""
    tt = TeamTracker(
        own_cards=own_card_bases(db),                                # DECK VETO (play.py:422)
        is_building=lambda b, _db=db: _db.kind(b) == "building",      # building side prior (play.py:424)
        is_spell=lambda b, _db=db: _db.kind(str(b)) == "spell",       # play.py:441 (base already base-keyed here)
        spawn_radius=0.10, spawn_window_s=2.5, enemy_window_s=4.0, track_radius=0.12, forget_s=4.5,
        motion_min=0.05, deep_mine_y=0.62, deep_enemy_y=0.38, min_hits=2, phantom_stale_s=6.0,
    )
    tt._o16_uid_counter = itertools.count(1)
    return tt


def tt_dets_of(pipeline_dets: list) -> list:
    """Pipeline ``_Det``s (this sample's condition-B/corr det stream, ALL sides -- mine + enemy +
    unknown, exactly the population ``TeamTracker.tag()`` sees live via ``dets_all``) -> real
    ``clashrl.replay_mine.Detection`` objects ``TeamTracker.tag()`` can mutate. ``cls`` is the RAW
    (unstripped) detector class name when the pipeline det carries one (``_Det.raw_cls`` -- O16 attempt 2
    FIX 3, verifier LOW) so ``TeamTracker``'s own zone-class check (``d.cls in ZONE_CLASSES``) can fire
    exactly as it would live, falling back to the already-stripped ``.base`` for any det built without
    one (``Detection.base`` re-applies ``card_threat.base_key``, idempotent on an already-base string, so
    the fallback is harmless, just not zone-aware -- true today only for det streams built by hand in a
    test). ``cx``/``cy`` are the pipeline det's ``cx``/``gy`` with no separate ground offset (pipeline's
    ``Unit.y`` is already the ground position -- ``_Det.gy`` module docstring above), so ``Detection.gy``
    (``cy`` when ``ground_cy`` is None) equals it directly. ``body_vote`` carries the SAME degraded team
    this det already has (module docstring KNOWN GAP: the closest live analog to a noisy single-frame
    colour read, since no pixels exist to vote from); ``bar_vote`` stays None -- rank 3 of
    ``TeamTracker._verdict`` never fires in this harness."""
    out = []
    for d in pipeline_dets:
        bv = "mine" if d.team == "mine" else "enemy" if d.team == "enemy" else None
        cls = d.raw_cls if d.raw_cls is not None else d.base
        out.append(TTDetection(cls, d.cx, d.gy, 0.05, 0.05, 1.0, team="unknown", ground_cy=None,
                               bar_vote=None, body_vote=bv))
    return out


def tt_bill_dets(tracker: TeamTracker, pipeline_dets: list, t: float, billed_ids: set) -> list:
    """O16(a): IDEALISED billing design under test, NOT live's current estimator path -- live feeds
    EVERY enemy-tagged, whitelisted det to the estimator every frame with NO confirmation gate at all
    (play.py:547,558; the ``min_hits`` gate lives only in ``enemy_tracks()``, which feeds threat/aim
    logic, never the elixir estimator). This function is the hypothesis "bill once per
    TeamTracker-CONFIRMED track instead" -- see ``B_tt``'s condition label in ``main()`` for the same
    caveat surfaced in summary.md.

    Feeds ``pipeline_dets`` (condition B/corr's own det stream for this sample, unmodified -- via
    ``tt_dets_of`` above) to ``tracker.tag()``, then returns one ``_Det`` per track that just reached
    ``tracker.min_hits`` for the FIRST time ("first confirmed sighting") -- team 'enemy' only (a track
    the tracker calls 'mine'/'unknown' is never billed), never a track already in ``billed_ids``.

    O16 attempt 2 FIX 1 (verifier, HIGH -- the previous version of this docstring's own justification
    was WRONG): ``billed_ids`` no longer holds ``id(track dict)``. A track dict is freed the moment
    ``TeamTracker.tag()`` drops it from ``self._tracks`` (module docstring -- CPython's small-object
    allocator then happily hands that exact address to the NEXT same-shaped dict it allocates), so two
    DIFFERENT tracks over a match's lifetime can share the same ``id()`` in sequence -- a later track
    landing on a recycled address would silently look "already billed" and never get charged. Verified
    live by the blind verifier's own probe (200 sequential distinct tracks, each seen twice then a 5 s
    gap between them, produced fewer than 200 bills under the old ``id()`` key).

    FIXED by stamping a per-tracker MONOTONIC uid INTO the track dict itself, on first sight
    (``tr["_bill_uid"]``, from the counter ``make_team_tracker`` attaches as ``tracker._o16_uid_counter``)
    and keying ``billed_ids`` on THAT instead. This is immune to address recycling by construction: a
    freshly allocated dict -- REGARDLESS of what memory it occupies -- starts with none of its own keys,
    so ``"_bill_uid" not in tr`` is true for every genuinely new track and false for every track that
    already has one, with no dependence on the object's address. Extra keys on a ``TeamTracker`` track
    dict do not confuse ``TeamTracker`` itself (it only ever reads specific keys it wrote, never
    inspects a track's full key set or length).

    ``billed_ids`` (uids, not addresses) is kept one per (match, tracker) and never reset mid-match, so a
    track is billed AT MOST ONCE for its life; a track that later EXPIRES and a brand-new track created
    at the same spot afterward is -- correctly -- a different dict with no ``_bill_uid`` yet, so it CAN
    be billed again (matches live: a new ``TeamTracker`` track is a new track, full stop). Mutates
    ``tracker`` (via ``tag()``, plus the ``_bill_uid`` stamp) and ``billed_ids`` in place."""
    tt_dets = tt_dets_of(pipeline_dets)
    tracker.tag(tt_dets, float(t))
    counter = getattr(tracker, "_o16_uid_counter", None)
    if counter is None:                    # defensive: a TeamTracker built without make_team_tracker
        counter = itertools.count(1)
        tracker._o16_uid_counter = counter
    out: list[_Det] = []
    for tr in tracker._tracks:
        if "_bill_uid" not in tr:
            tr["_bill_uid"] = next(counter)          # stamped on EVERY track, not just billed ones, so a
        if tr["team"] != "enemy" or int(tr.get("hits", 0)) < tracker.min_hits:  # later verdict flip to
            continue                                                            # 'enemy' still finds its uid
        uid = tr["_bill_uid"]
        if uid in billed_ids:
            continue
        billed_ids.add(uid)
        out.append(_Det(str(tr["base"]), float(tr["x"]), float(tr["y"]), "enemy"))
    return out


def filter_whitelisted_billed_dets(dets: list, whitelist: frozenset) -> list:
    """O16 attempt 2 FIX 2(b): the live-reachable sibling of a ``_tt`` condition -- keep only billed dets
    whose base is in live's ``detector_cards`` whitelist. Mirrors ``dets_of_whitelisted``'s own
    'keep iff base in whitelist' semantics (every det here is already team=='enemy' by construction --
    ``tt_bill_dets`` only ever emits enemy-verdict tracks -- so there is no 'never filter non-enemy'
    passthrough branch to reuse from that function, unlike its raw-Unit-list callers). Applied to the
    TRACKER'S OUTPUT, not to what is fed into ``tag()`` -- this mirrors play.py's own order, where the
    whitelist filter (line 547) sits AFTER tagging (line 518), not before it, so tracking/hits accrual is
    identical between a ``_tt`` condition and its ``_tt_wl`` sibling; only which confirmed sightings are
    actually billed to the estimator differs."""
    return [d for d in dets if d.base in whitelist]


def cond_key(base: str, variant: str, both: bool) -> str:
    """Condition key for summary.json / charged_by_base (e.g. 'A', or 'A_v2' under --estimator both)."""
    return f"{base}_{variant}" if both else base


def tick_field(base: str, variant: str, both: bool, prefix: str) -> str:
    """Per-tick column name (e.g. 'est_Awl', or 'est_Awl_v2' under --estimator both) -- historical spelling
    preserved so ``--estimator v1`` (default) never changes ticks.jsonl's shape."""
    name = f"{prefix}_{_HIST_FIELD[base]}"
    return f"{name}_{variant}" if both else name


def make_estimator(variant: str, db: CardDB, traced: bool, v2_kwargs: Optional[dict]):
    """One (base-condition-agnostic) estimator instance for ``variant`` ('v1'/'v2'), traced iff this is
    condition A with --charge-trace set."""
    if variant == "v2":
        return (TracedEstimatorV2 if traced else TrackedEstimatorV2)(db, **(v2_kwargs or {}))
    return (TracedEstimator if traced else TrackedEstimator)(db)


def _jsonable(obj):
    """O13 attempt 2 FIX 1 (verifier, HIGH): recursively convert ``set``/``frozenset`` values to sorted lists
    so the result can pass through ``json.dumps`` -- used ONLY at the point ``V2_PARAMS`` is logged into
    summary.json (``V2_PARAMS["spawns"]`` is ``dict[str, frozenset[str]]``; the un-converted dict raised
    ``TypeError: Object of type frozenset is not JSON serializable`` at the very END of a full run, after
    every match had already completed, losing summary.json/summary.md and the OPP_EST_AUDIT_DONE line).
    Returns a NEW structure; never mutates the live module's own SPAWNS/BODIES/V2_PARAMS objects (which stay
    frozensets/dicts, exactly as opponent_elixir.py defines them, for O(1) membership at runtime)."""
    if isinstance(obj, (set, frozenset)):
        return sorted(obj)
    if isinstance(obj, dict):
        return {k: _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonable(v) for v in obj]
    return obj


# ------------------------------------------------------------------------------------------------------
# TICKET O18: feed the opponent-elixir OBSERVATION -- true engine value or the live-reachable estimate --
# into the BoardState the policy actually consumes (``to_tokens``), so a full match can be re-driven with
# the student SEEING opp_elixir instead of the always-None degraded default, and its effect on winrate
# measured. Pure helpers (unit-testable with no engine): ``feed_condition_key`` picks which already-running
# tracker-input estimator backs 'estimated' mode per ``--feed-noise``; ``policy_view_for`` builds the
# EXACT BoardState ``run_match_audit`` hands to ``to_tokens`` -- ``view`` (the standard, always-computed
# live_view) with ONLY its ``opp_elixir`` field replaced, never any other field. 'off' (the default) returns
# ``view`` completely unchanged -- byte-identical to every pre-O18 invocation.
# ------------------------------------------------------------------------------------------------------
FEED_OPP_ELIXIR_MODES = ("off", "true", "estimated")
FEED_NOISE_MODES = ("live", "corrL")


def validate_feed_config(feed_opp_elixir: str, feed_noise: str, tracker: bool, corr: bool,
                         estimator: str) -> None:
    """O18: the --feed-opp-elixir/--feed-noise/--tracker/--corr/--estimator combination is legal --
    factored out of ``run_match_audit`` (which still calls this, so a library caller can never skip it) so
    ``main()`` can ALSO call it right after argparse, before connecting to the engine or loading the
    checkpoint -- a misconfigured run fails in milliseconds instead of after the first match."""
    if feed_opp_elixir not in FEED_OPP_ELIXIR_MODES:
        raise SystemExit(f"--feed-opp-elixir must be one of {FEED_OPP_ELIXIR_MODES}, got {feed_opp_elixir!r}")
    if feed_noise not in FEED_NOISE_MODES:
        raise SystemExit(f"--feed-noise must be one of {FEED_NOISE_MODES}, got {feed_noise!r}")
    if feed_opp_elixir != "estimated":
        return
    variants = ("v1", "v2") if estimator == "both" else (estimator,)
    if "v2" not in variants:
        raise SystemExit("--feed-opp-elixir estimated requires --estimator v2 (or both) -- V2.1 rules")
    if not tracker:
        raise SystemExit("--feed-opp-elixir estimated requires --tracker (condition B_tt_wl)")
    if feed_noise == "corrL" and not corr:
        raise SystemExit("--feed-opp-elixir estimated --feed-noise corrL requires --corr (B_corrL_tt_wl)")


def feed_condition_key(feed_noise: str) -> str:
    """--feed-noise -> the (tracker-input, live-whitelist) condition key already computed every sample
    (module docstring O16(a)/(b)) whose V2 estimator backs 'estimated' mode: 'live' reads the SAME degraded
    view / det stream the policy itself sees (``B_tt_wl``, MAE 2.68 in the measured range); 'corrL' reads
    the long-persistence correlated stream (``B_corrL_tt_wl``, MAE 3.46) -- a sensitivity arm. Either way
    only the ESTIMATOR's input stream differs; see ``policy_view_for``'s docstring for why the policy's own
    observation never changes with this flag."""
    if feed_noise == "live":
        return "B_tt_wl"
    if feed_noise == "corrL":
        return "B_corrL_tt_wl"
    raise SystemExit(f"--feed-noise must be one of {FEED_NOISE_MODES}, got {feed_noise!r}")


def policy_view_for(view, bs, feed_opp_elixir: str, feed_noise: str, estimators: dict):
    """O18: the BoardState ``run_match_audit`` actually hands to ``to_tokens`` for the policy's decision --
    ``view`` (the SAME standard live_view every mode computes identically; module docstring) with ONLY its
    ``opp_elixir`` field overridden, never any other field:

      'off'       (default) -- ``view`` returned UNCHANGED (``opp_elixir`` stays whatever live_view set,
                  i.e. None under the default Noise() -- obs_contract's ``opp_known`` flag is 0, exactly as
                  every pre-O18 invocation). Byte-identical to before this ticket.
      'true'      -- ``bs.opp_elixir`` (engine ground truth for THIS tick), equivalent to e1_eval's
                  ``--noise-off opp_elixir`` (e1_view.py's ``_degrade_switchable`` line 168: the same
                  ``bs.opp_elixir if not noise.opp_elixir else None`` value).
      'estimated' -- ``estimators[(feed_condition_key(feed_noise), "v2")]._est`` -- the V2.1 estimator
                  already running for the live-reachable tracker-input condition (module docstring O16),
                  read AFTER its update() call for this exact sample (caller contract below).

    CAUSALITY (by construction, not by anything this function checks): ``run_match_audit`` calls this only
    from inside the per-tick loop, AFTER the loop's per-base ``estimators[...].update(...)`` calls for this
    same sample and BEFORE ``to_tokens`` -- so an 'estimated' read reflects every sample up to and including
    the current tick and NOTHING later. This function itself does no time-travel: it only ever reads
    ``estimators``' CURRENT ``._est``, whatever that happens to be when called.

    OBSERVATION IDENTITY ACROSS --feed-noise (ticket requirement): for a fixed ``feed_opp_elixir`` and seed,
    'live' and 'corrL' pass the IDENTICAL ``view`` in (feed_noise only selects which condition's estimator
    ``estimated`` reads ``._est`` from -- it never touches ``view`` itself, which every mode computes from
    the same ``live_view(bs, rng_obs, deck, Noise())`` call regardless of these flags). ``replace(view,
    opp_elixir=...)`` therefore changes at most one field: every other field of the returned BoardState is
    ``view``'s own object, unchanged -- proven field-by-field in TestFeedNoiseObservationIdentity."""
    if feed_opp_elixir == "off":
        return view
    if feed_opp_elixir == "true":
        return replace(view, opp_elixir=float(bs.opp_elixir))
    if feed_opp_elixir == "estimated":
        key = feed_condition_key(feed_noise)
        est = estimators.get((key, "v2"))
        if est is None:
            raise SystemExit(f"--feed-opp-elixir estimated requires condition {key!r} (v2) to be active -- "
                             f"pass --estimator v2 (or both), --tracker, and (for --feed-noise corrL) --corr")
        return replace(view, opp_elixir=float(est._est))
    raise SystemExit(f"--feed-opp-elixir must be one of {FEED_OPP_ELIXIR_MODES}, got {feed_opp_elixir!r}")


# ------------------------------------------------------------------------------------------------------
# one match, four conditions, per-tick rows at STEP_TICKS cadence -- one or two estimator variants each
# ------------------------------------------------------------------------------------------------------
def run_match_audit(env, model, deck, db: CardDB, entry: dict, k: int, cfg: dict,
                    warned_costless: Optional[set] = None, whitelist: Optional[frozenset] = None,
                    charge_trace: bool = False, estimator: str = "v1",
                    v2_kwargs: Optional[dict] = None, tracker: bool = False,
                    corr: bool = False, feed_opp_elixir: str = "off",
                    feed_noise: str = "live") -> tuple[list[dict], dict, list[dict], list[dict]]:
    """Mirrors e1_eval.run_match's while-loop (same live policy, same accepted-play bookkeeping, IDENTICAL
    decisions at IDENTICAL ticks) but steps the engine STEP_TICKS at a time, updates every active
    estimator every step from the SAME det stream per condition, and records a per-tick truth/estimate row
    instead of only a match summary. ``estimator``: 'v1' (default -- byte-identical shape to before O13),
    'v2', or 'both' (every condition run for BOTH estimators from the same dets, condition keys suffixed
    '_v1'/'_v2' -- O13 ticket 3). Returns (ticks, match_summary, charge_rows, track_event_rows) -- the last
    two are always [] unless ``charge_trace`` is set, in which case condition A's active variant(s) become
    Traced* estimators (module docstring O10/O13) and rows carry an ``estimator`` field; every other
    condition (A+, A_wl, B) is untouched regardless of this flag. ``whitelist``: FIX 4's
    ``load_detector_cards()`` result, required for A_wl. ``tracker``/``corr``: O16(c) -- both default
    False, in which case every condition below iterates ``active_base_conds(False, False) == BASE_CONDS``
    and this function's behaviour is BYTE-IDENTICAL to before O16. ``tracker`` adds ``B_tt`` (module
    docstring O16(a)); ``corr`` adds ``B_corrS``/``B_corrL`` (O16(b)); both together additionally add
    ``B_corrS_tt``/``B_corrL_tt``.

    O18: ``feed_opp_elixir`` ('off' default/'true'/'estimated') and ``feed_noise`` ('live' default/'corrL')
    -- see ``policy_view_for``'s docstring for the exact BoardState this builds and the causality contract.
    'off' leaves every line above and the policy's decision byte-identical to before O18. 'estimated'
    requires condition ``B_tt_wl`` (v2) active (``--tracker``, ``--estimator v2``/``both``); with
    ``feed_noise='corrL'`` it additionally requires ``B_corrL_tt_wl`` active (``--corr`` too) -- both
    checked up front, before the match loop runs."""
    if warned_costless is None:
        warned_costless = set()
    if whitelist is None:
        whitelist = frozenset()
    step = int(cfg.get("estimator_step") or STEP_TICKS)
    decide_every = int(cfg["decide_every"])
    if decide_every % step != 0:
        raise SystemExit(f"--decide-every {decide_every} must be a multiple of --estimator-step {step}")
    if estimator not in ("v1", "v2", "both"):
        raise SystemExit(f"--estimator must be v1/v2/both, got {estimator!r}")
    # O18: 'estimated' reads condition B_tt_wl / B_corrL_tt_wl's V2 estimator -- validated up front (never
    # mid-match) so a misconfigured run fails fast instead of KeyError-ing on the first policy tick.
    validate_feed_config(feed_opp_elixir, feed_noise, tracker, corr, estimator)
    variants = ("v1", "v2") if estimator == "both" else (estimator,)
    both_mode = len(variants) > 1
    bases = active_base_conds(tracker, corr)      # O16(c): BASE_CONDS unchanged when both flags are off

    t0 = time.perf_counter()
    state = env.reset(entry)
    side, mirror = env.side, env._mirror
    engine_deck, deck_index_of_slot, costs = _slot_maps(env, deck, entry)
    tag = str(entry["tag"])
    rng_obs = np.random.default_rng(obs_seed(tag, k))          # e1_eval-identical stream -- POLICY ticks only
    rng_obs_b5 = np.random.default_rng(b5_seed(tag, k))        # harness-local -- NON-policy 5-tick steps only
    # O16(b): each corr setting gets its OWN per-match track-state dict and its OWN RNG stream -- never
    # shared with e1_eval's streams, b5's, or each other. Unused (None) unless --corr.
    corrS_state = new_state() if corr else None
    corrL_state = new_state() if corr else None
    rng_corrS = np.random.default_rng(corrS_seed(tag, k)) if corr else None
    rng_corrL = np.random.default_rng(corrL_seed(tag, k)) if corr else None
    corr_view_of: dict[str, Any] = {}    # this tick's {"B_corrS": BoardState, "B_corrL": BoardState}
    # O16(a): one TeamTracker (+ its own "already billed" track-id set) per stream that needs tracker-input
    # billing this run. Live's own construction defaults (make_team_tracker) -- see module docstring O16(a).
    team_trackers: dict[str, TeamTracker] = {}
    billed_ids: dict[str, set] = {}
    if tracker:
        team_trackers["B_tt"] = make_team_tracker(db)
        billed_ids["B_tt"] = set()
        if corr:
            team_trackers["B_corrS_tt"] = make_team_tracker(db)
            billed_ids["B_corrS_tt"] = set()
            team_trackers["B_corrL_tt"] = make_team_tracker(db)
            billed_ids["B_corrL_tt"] = set()
    policy, grid, device = cfg["policy"], cfg["grid"], cfg["device"]
    unmapped: set = set()
    done_plays: list[tuple[int, int, float, float]] = []
    last_play_tick: Optional[int] = None
    first_tick: Optional[int] = None
    # O13: one estimator per (base condition, variant). Condition A's active variant(s) become Traced*
    # when --charge-trace is set -- byte-identical to before O13 for the default v1-only, untraced-elsewhere
    # case (TracedEstimator IS-A TrackedEstimator, so ._est/.charged_by_base are unaffected either way).
    estimators = {(base, variant): make_estimator(variant, db, charge_trace and base == "A", v2_kwargs)
                  for base in bases for variant in variants}

    def my_elixir_of(base: str) -> float:
        """O16(c): which degraded/perfect my_elixir a base condition reads. B_tt/B_tt_wl/B_corr* and
        their _tt/_tt_wl siblings all read the SAME my_elixir as their parent raw-det condition --
        tracker-input billing (and whitelist-filtering its output) changes only which ENEMY dets the
        estimator sees, never how it reads its own hand's elixir."""
        if base in ("B", "B_tt", "B_tt_wl"):
            return view.my_elixir
        if base in ("B_corrS", "B_corrS_tt", "B_corrS_tt_wl"):
            return corr_view_of["B_corrS"].my_elixir
        if base in ("B_corrL", "B_corrL_tt", "B_corrL_tt_wl"):
            return corr_view_of["B_corrL"].my_elixir
        return bs.my_elixir

    inited = False
    prev_truth: Optional[float] = None
    ticks: list[dict] = []
    charge_rows: list[dict] = []       # O10/O13: condition A's charge trace (only populated if charge_trace)
    track_event_rows: list[dict] = []  # O10/O13: condition A's track-expiry trace (ditto)
    prev_a_dets: Optional[list] = None # O10: PREVIOUS sample's condition-A det list (same for every variant,
    prev_a_t: Optional[float] = None   # since all variants see the identical det stream), for charge_diagnostics
    t_to_tick: dict = {}                # O10: this match's t_sec -> tick map, for track_events' last_seen_tick
    n_dec = n_acc = 0
    max_ticks = int(cfg.get("max_ticks") or 0)
    done = False
    while not done:
        tick = int(env.tick)
        if first_tick is None:
            first_tick = tick
        if last_play_tick is None:
            last_play_tick = tick
        pol_tick = is_policy_tick(tick, first_tick, decide_every)

        bs = from_engine(ep.compact_raw(state), side, deck, engine_deck=engine_deck, unmapped=unmapped)
        # Condition B's view: the REAL e1_eval stream on policy ticks (so the policy decision below is
        # byte-identical to attempt 1 / e1_eval), the harness-local stream on the 5-tick-only steps in
        # between (CHANGE 1 -- e1_eval has no cadence of its own for those).
        view = live_view(bs, rng_obs if pol_tick else rng_obs_b5, deck, Noise())
        if corr:
            corr_view_of["B_corrS"] = corr_live_view(bs, corrS_state, rng_corrS, deck, CORR_SHORT)
            corr_view_of["B_corrL"] = corr_live_view(bs, corrL_state, rng_corrL, deck, CORR_LONG)
        if tracker:
            # ground-truth princess alive flags feed the tracker's pocket gating (module docstring
            # O16(a) construction cite: MORE faithful than the two offline audit tools' fixed "assume
            # towers alive" simplification, since this harness -- unlike them -- HAS engine ground
            # truth available at zero extra cost; a deliberate, documented improvement, not a drift
            # from their pattern for anything that pattern was actually forced to approximate).
            mine_alive = (bs.towers[1].alive, bs.towers[2].alive)
            enemy_alive = (bs.towers[4].alive, bs.towers[5].alive)
            for tt in team_trackers.values():
                tt.set_towers(mine_alive, enemy_alive)
        if not inited:
            for base in bases:
                for variant in variants:
                    estimators[(base, variant)].reset(my_elixir=my_elixir_of(base), now=bs.t_sec)
            inited = True

        truth = float(bs.opp_elixir)
        # FIX 2: is_opp_play_tick is filled in AFTER the loop (opp_play_flags, from env.ghost_events) --
        # truth_drop stays as an informational column only, it no longer decides the flag.
        truth_drop = 0.0 if prev_truth is None else (prev_truth - truth)

        # update() RETURNS the estimate normalized to [0, 1] (opponent_elixir.py:131); the 0-10 elixir-unit
        # value this harness grades is ``._est`` (set as a side effect of the same call, opponent_elixir.py
        # :130) -- attempt 1's section-1.9 near-miss. Call update() for its side effect, then read ``._est``.
        ap_dets = dets_of(bs.units) + dets_of_costed(bs.spells, db, warned_costless)
        a_dets = dets_of(bs.units)
        wl_dets = dets_of_whitelisted(bs.units, whitelist)      # FIX 4
        b_dets = dets_of(view.units)
        dets_by_base = {"Aplus": (ap_dets, bs.my_elixir), "A": (a_dets, bs.my_elixir),
                        "A_wl": (wl_dets, bs.my_elixir), "B": (b_dets, view.my_elixir)}
        n_by_base = {"Aplus": n_enemy(bs.units) + n_enemy(bs.spells), "A": n_enemy(bs.units),
                    "A_wl": sum(1 for d in wl_dets if d.team == "enemy"), "B": n_enemy(view.units)}
        # O16(a): B_tt is billed from B's OWN det stream (b_dets, drawn above -- no new noise). O16(b):
        # each corr setting's raw-det condition uses its own corr_live_view output; O16(a)+(b) together
        # bill it through that same setting's own TeamTracker. n_enemy_dets_* for a _tt/_tt_wl condition
        # counts dets BILLED this sample (tracks newly confirmed), NOT raw enemy dets visible -- module
        # docstring. Attempt 2 FIX 2(b): each _tt condition's "_wl" sibling is the SAME billed-dets list
        # (one tag()/billing call feeds both -- tracking/hits accrual must not fork), filtered to live's
        # detector_cards whitelist AFTER billing (mirrors play.py:547's filter sitting after tag() at
        # play.py:518, not before it).
        if "B_tt" in team_trackers:
            tt_b = tt_bill_dets(team_trackers["B_tt"], b_dets, bs.t_sec, billed_ids["B_tt"])
            tt_b_wl = filter_whitelisted_billed_dets(tt_b, whitelist)
            dets_by_base["B_tt"] = (tt_b, view.my_elixir)
            dets_by_base["B_tt_wl"] = (tt_b_wl, view.my_elixir)
            n_by_base["B_tt"] = len(tt_b)
            n_by_base["B_tt_wl"] = len(tt_b_wl)
        if corr:
            for name in ("B_corrS", "B_corrL"):
                cview = corr_view_of[name]
                cdets = dets_of(cview.units)
                dets_by_base[name] = (cdets, cview.my_elixir)
                n_by_base[name] = n_enemy(cview.units)
                tt_name = name + "_tt"
                if tt_name in team_trackers:
                    ttd = tt_bill_dets(team_trackers[tt_name], cdets, bs.t_sec, billed_ids[tt_name])
                    ttd_wl = filter_whitelisted_billed_dets(ttd, whitelist)
                    dets_by_base[tt_name] = (ttd, cview.my_elixir)
                    dets_by_base[f"{tt_name}_wl"] = (ttd_wl, cview.my_elixir)
                    n_by_base[tt_name] = len(ttd)
                    n_by_base[f"{tt_name}_wl"] = len(ttd_wl)

        # O13 attempt 2 FIX 6b (verifier, LOW): compute every estimate FIRST, into a plain dict, then build
        # `row` in two separate passes (all est_* fields, THEN all n_enemy_dets_* fields, THEN the three
        # flags) -- this reproduces the PRE-O13 key ORDER exactly for --estimator v1 (the historical dict
        # literal put every est_* field before every n_enemy_dets_* field, with the three flags last; a
        # single combined per-condition loop, tried first, interleaved est_X/n_enemy_dets_X instead and
        # moved the flags earlier, changing ticks.jsonl's line-for-line bytes even though the values were
        # unchanged). Verified by TestTicksRowKeyOrder below: a stub v1-only row's ``list(row)`` matches the
        # exact historical key sequence.
        est_vals: dict[tuple[str, str], float] = {}
        for base in bases:
            dets, my_e = dets_by_base[base]
            for variant in variants:
                est = estimators[(base, variant)]
                if base == "A" and charge_trace:
                    ch_rows, tr_rows = run_traced_update(est, my_e, dets, bs.t_sec, tick, tag, k,
                                                         prev_a_dets, prev_a_t, t_to_tick)
                    for r in ch_rows:
                        r["estimator"] = variant
                    for r in tr_rows:
                        r["estimator"] = variant
                    charge_rows.extend(ch_rows)
                    track_event_rows.extend(tr_rows)
                else:
                    est.update(my_e, dets, bs.t_sec)
                est_vals[(base, variant)] = round(float(est._est), 4)
        if charge_trace:
            prev_a_dets, prev_a_t = a_dets, bs.t_sec

        row = {"tag": tag, "k": int(k), "tick": tick, "t_sec": round(bs.t_sec, 3), "phase": phase_of(bs),
              "truth": truth, "truth_drop": round(truth_drop, 4)}
        for base in bases:
            for variant in variants:
                row[tick_field(base, variant, both_mode, "est")] = est_vals[(base, variant)]
        for base in bases:
            for variant in (variants if both_mode else variants[:1]):
                row[tick_field(base, variant, both_mode, "n_enemy_dets")] = n_by_base[base]
        row["is_opp_play_tick"] = False   # FIX 2: filled in below from env.ghost_events, not here
        row["is_my_play_tick"] = False
        row["is_policy_tick"] = bool(pol_tick)

        # --- our own decision (same live rule as e1_eval.run_match), POLICY ticks only, unchanged cadence ---
        is_my_play_tick = False
        if pol_tick:
            # O18: the estimator update() loop above (this exact sample) has already run for every base,
            # so an 'estimated' read here is causal -- through this tick and nothing later. 'off' returns
            # ``view`` unchanged (byte-identical to before O18); every other field of the BoardState
            # ``to_tokens`` reads is ``view``'s own, regardless of feed_opp_elixir/feed_noise.
            policy_view = policy_view_for(view, bs, feed_opp_elixir, feed_noise, estimators)
            tok, mask, sc = to_tokens(policy_view, MAX_U)
            past = _past(done_plays, tick)
            enc, heads, p, hand = model_forward(model, tok, mask, sc, past, device)
            n_dec += 1
            el_int = float(int(view.my_elixir))
            allowed = allowed_slots(hand, costs, el_int, afford_mask=cfg["afford_mask"])
            st = anti_stall(el_int, tick, last_play_tick, cfg["stall_elixir"], cfg["stall_seconds"])
            d = live_decide(model, enc, heads, p, allowed, tau=cfg["tau"], stalled=st, device=device)
            if d["play"]:
                x, y = ep.cell_center(d["cell"], grid)
                X, Y = ep.cell_to_engine(d["cell"], mirror, grid)
                r = env.eng.act(side=side, deck_index=deck_index_of_slot[d["slot"]], x=X, y=Y)
                if bool(r["accepted"]):
                    n_acc += 1
                    done_plays.append((tick, d["slot"], x, y))
                    last_play_tick = tick
                    base_key = vocab.base_key(deck.cards[d["slot"]])
                    for base in bases:
                        for variant in variants:
                            estimators[(base, variant)].record_my_play(base_key)
                    for tt in team_trackers.values():                # O16(a): own-play anchor, every tracker
                        tt.record_play(x, y, bs.t_sec, base=base_key)
                    is_my_play_tick = True

        row["is_my_play_tick"] = bool(is_my_play_tick)
        ticks.append(row)
        prev_truth = truth
        if max_ticks and len(ticks) >= max_ticks:
            break

        env._advance_to(min(env.tick + step, env.tail_cap))
        state = env.eng.observe()
        done = bool(env.terminated) or env.tick >= env.tail_cap

    # FIX 2: is_opp_play_tick from the ghost-drive path's own delivery log, not the truth-drop threshold
    # (which silently misses every 1-cost play -- module docstring). env.ghost_events is reset to [] per
    # match by engine_env.py's reset(), so by here it holds exactly THIS match's (tick, accepted, reason) log.
    flags = opp_play_flags([row["tick"] for row in ticks], list(env.ghost_events))
    for row, flag in zip(ticks, flags):
        row["is_opp_play_tick"] = bool(flag)

    outcome, crowns = ep._outcome(env, state)
    # FIX 1: the over-charge TRUTH ledger is what was actually DELIVERED (env.ghost_cards_delivered), never
    # the script (ghost_scripted_by_base is kept below for reference only, clearly labelled, unused in math).
    ghost_scripted = ghost_scripted_by_base(entry, db, warned_costless)
    ghost_delivered = ghost_delivered_by_base(dict(env.ghost_cards_delivered), db, warned_costless)
    ghost_delivered_total = sum(v[1] for v in ghost_delivered.values())
    charged_by_base = {cond_key(base, variant, both_mode): dict(estimators[(base, variant)].charged_by_base)
                       for base in bases for variant in variants}
    over_charge_at_end = {cond: round(sum(v[1] for v in d.values()) - ghost_delivered_total, 2)
                          for cond, d in charged_by_base.items()}
    summary = {"tag": tag, "k": int(k), "n_ticks": len(ticks), "decisions": n_dec, "plays_accepted": n_acc,
              "outcome": outcome, "crowns_for": int(crowns[0]), "crowns_against": int(crowns[1]),
              "end_tick": int(env.tick), "unmapped": sorted(unmapped),
              "wall_s": round(time.perf_counter() - t0, 1),
              "charged_by_base": charged_by_base,
              "ghost_scripted_by_base": ghost_scripted,           # reference only -- NOT used for over-charge
              "ghost_delivered_by_base": ghost_delivered,         # the truth ledger over-charge actually uses
              "over_charge_at_end": over_charge_at_end}
    return ticks, summary, charge_rows, track_event_rows


# ------------------------------------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--port", type=int, required=True)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--ckpt", type=Path, required=True, help="S1 checkpoint the 'live' policy drives")
    ap.add_argument("--pool", type=Path, default=POOL_V1)
    ap.add_argument("--split-file", type=Path, default=None)
    ap.add_argument("--split", choices=("heldout", "train"), default="heldout")
    ap.add_argument("--entries", default="all", help="a:b over the split's entries in pool order, or 'all'")
    ap.add_argument("--seeds", default="0")
    ap.add_argument("--shard", default="0/1")
    ap.add_argument("--tau", type=float, default=TAU_LIVE)
    ap.add_argument("--no-afford-mask", action="store_true")
    ap.add_argument("--stall-elixir", default=str(STALL_ELIXIR_LIVE), help="'none' disables anti-stall")
    ap.add_argument("--stall-seconds", type=float, default=STALL_SECONDS_LIVE)
    ap.add_argument("--decide-every", type=int, default=DECIDE_EVERY, help="policy decision cadence, ticks")
    ap.add_argument("--estimator-step", type=int, default=STEP_TICKS,
                    help="CHANGE 1: estimator update() cadence, ticks; must divide --decide-every")
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--threads", type=int, default=2)
    ap.add_argument("--timeout", type=float, default=20.0, help="engine socket timeout (s) -- kept short so a "
                    "dead port fails cleanly instead of hanging on the 120s EngineMatchEnv default")
    ap.add_argument("--max-ticks", type=int, default=0, help="stop after this many TOTAL per-tick rows across "
                    "the run (smoke); 0 = unlimited. SMOKE ONLY: truncates each match mid-flight, then "
                    "_outcome() is computed on a NON-terminal engine state (outcome/crowns are meaningless "
                    "for a truncated match; ticks/estimates up to the cut are still valid)")
    ap.add_argument("--charge-trace", action="store_true", help="O10: for condition A ONLY, write "
                    "<out>/charges.jsonl (one row per _opp_spent charge, with diagnostics + a best-effort "
                    "reason) and <out>/track_events.jsonl (one row per track expiry). No fix -- "
                    "instrumentation only; off by default and produces no new files / no summary change. "
                    "O13: with --estimator v2/both, this also traces the v2 A condition (rows carry an "
                    "'estimator' field).")
    ap.add_argument("--estimator", choices=("v1", "v2", "both"), default="v1", help="O13: which "
                    "OpponentElixirEstimator[V2] backs every condition (A+/A/A_wl/B). 'v1' (default) is "
                    "byte-identical in shape to before O13. 'both' runs every condition for BOTH "
                    "estimators from the same det stream, condition keys suffixed _v1/_v2.")
    ap.add_argument("--tracker", action="store_true", help="O16(a): add conditions B_tt/B_tt_wl -- bill "
                    "from a live-default TeamTracker's first-confirmed-sighting (>= min_hits) tracks over "
                    "condition B's own det stream, instead of raw per-frame dets. IDEALISED design under "
                    "test, not live's current path (live has no such gate on the estimator path); _wl is "
                    "the live-reachable sibling (billed det's base must clear detector_cards too). With "
                    "--corr, also adds B_corrS_tt/B_corrS_tt_wl/B_corrL_tt/B_corrL_tt_wl over the "
                    "correlated streams. OFF by default -- no effect on existing runs.")
    ap.add_argument("--corr", action="store_true", help="O16(b): add conditions B_corrS/B_corrL -- the same "
                    "per-sample marginals as condition B's live_view, but temporally CORRELATED noise "
                    "(pipeline/opp_est_degrade_corr.py; SHORT/LONG persistence settings, both always run). "
                    "OFF by default -- no effect on existing runs.")
    ap.add_argument("--feed-opp-elixir", choices=FEED_OPP_ELIXIR_MODES, default="off", help="O18: what the "
                    "POLICY sees as opp_elixir. 'off' (default): unchanged, the degraded view's None -- "
                    "byte-identical to before O18. 'true': bs.opp_elixir (engine ground truth), equivalent "
                    "to e1_eval --noise-off opp_elixir. 'estimated': the live-reachable V2.1 estimate "
                    "(condition B_tt_wl/B_corrL_tt_wl's ._est, per --feed-noise), requires --tracker "
                    "(and --estimator v2/both; --corr too for --feed-noise corrL).")
    ap.add_argument("--feed-noise", choices=FEED_NOISE_MODES, default="live", help="O18: with "
                    "--feed-opp-elixir estimated, which det stream feeds the ESTIMATOR -- 'live' (default, "
                    "condition B_tt_wl, MAE 2.68) or 'corrL' (condition B_corrL_tt_wl, long-persistence "
                    "correlated degrade, MAE 3.46; requires --corr). The policy's own OBSERVATION (the "
                    "board it sees) is the SAME standard live_view either way -- only the estimator's "
                    "input, and so the injected elixir number, differs. Ignored for --feed-opp-elixir "
                    "off/true.")
    ap.add_argument("--out", type=Path, required=True)
    return ap


def main(argv=None) -> int:
    a = build_parser().parse_args(argv)
    refuse_existing_out(a.out, resume=False)
    shard = parse_shard(a.shard)
    seeds = parse_seeds(a.seeds)
    stall_elixir = None if str(a.stall_elixir).lower() == "none" else float(a.stall_elixir)
    if int(a.decide_every) % int(a.estimator_step) != 0:
        raise SystemExit(f"--decide-every {a.decide_every} must be a multiple of --estimator-step {a.estimator_step}")
    validate_feed_config(a.feed_opp_elixir, a.feed_noise, bool(a.tracker), bool(a.corr), a.estimator)
    import torch
    torch.set_num_threads(max(1, int(a.threads)))

    pool_path = Path(a.pool)
    split_path = Path(a.split_file) if a.split_file else pool_path.with_name(pool_path.stem + "_split.json")
    frozen = json.loads(split_path.read_text(encoding="utf-8"))
    pool_sha = sha256_file(pool_path)
    if pool_sha != frozen["pool_sha256"]:
        raise SystemExit(f"REFUSING: pool sha256 {pool_sha} != frozen split's {frozen['pool_sha256']}")
    rows = load_pool_v1(pool_path)
    entries = select_split(rows, a.split)
    del rows
    idx = parse_entries(a.entries, entries)
    tasks = make_tasks(idx, seeds, shard)

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    deck = load_deck("icebow")
    db = CardDB(path=deck.config.parent / "cards.yaml")
    whitelist = load_detector_cards(deck.config)          # FIX 4: A_wl's live detector_cards whitelist
    model, minfo = ep.load_model(a.ckpt, a.device)
    slot = SLOT_OF_PORT.get(int(a.port), int(a.port))
    cfg = {"policy": "live", "tau": float(a.tau), "afford_mask": not a.no_afford_mask, "stall_elixir": stall_elixir,
          "stall_seconds": float(a.stall_seconds), "grid": minfo.get("grid", "floor"), "device": a.device,
          "decide_every": int(a.decide_every), "estimator_step": int(a.estimator_step), "max_ticks": int(a.max_ticks)}
    print(json.dumps({"opp_est_audit": True, "port": a.port, "tasks": len(tasks), "grid": cfg["grid"],
                      "tau": cfg["tau"], "decide_every": cfg["decide_every"],
                      "estimator_step": cfg["estimator_step"], "n_detector_cards": len(whitelist)}), flush=True)

    tick_path = out / "ticks.jsonl"
    charge_trace = bool(a.charge_trace)
    # O10: charges.jsonl / track_events.jsonl are ONLY ever created when --charge-trace is passed -- off by
    # default means no new files at all, per the ticket.
    charges_fh = (out / "charges.jsonl").open("a", encoding="utf-8") if charge_trace else None
    track_events_fh = (out / "track_events.jsonl").open("a", encoding="utf-8") if charge_trace else None
    all_rows: list[dict] = []
    match_summaries: list[dict] = []
    warned_costless: set = set()
    env = None
    total_ticks = 0
    try:
        try:
            env = PoolV1Env(port=int(a.port), host=a.host, decision_ticks=int(a.decide_every), timeout=float(a.timeout))
        except Exception as exc:
            print(f"[opp_est_audit] ENGINE UNREACHABLE on {a.host}:{a.port}: {exc!r}", flush=True)
            return 2
        with tick_path.open("a", encoding="utf-8") as fh:
            for (i, k) in tasks:
                entry = entries[i]
                try:
                    match_rows, msummary, ch_rows, tr_rows = run_match_audit(
                        env, model, deck, db, entry, k, cfg, warned_costless, whitelist,
                        charge_trace=charge_trace, estimator=a.estimator,
                        tracker=bool(a.tracker), corr=bool(a.corr),
                        feed_opp_elixir=a.feed_opp_elixir, feed_noise=a.feed_noise)
                except Exception as exc:
                    print(f"[opp_est_audit] ERROR on {entry['tag']} k={k}: {exc!r}", flush=True)
                    return 3
                for row in match_rows:
                    fh.write(json.dumps(row) + "\n")
                fh.flush()
                if charge_trace:
                    for row in ch_rows:
                        charges_fh.write(json.dumps(row) + "\n")
                    for row in tr_rows:
                        track_events_fh.write(json.dumps(row) + "\n")
                    charges_fh.flush()
                    track_events_fh.flush()
                all_rows.extend(match_rows)
                match_summaries.append(msummary)
                total_ticks += len(match_rows)
                print(f"[opp_est_audit] {entry['tag']} k={k} ticks={len(match_rows)} "
                     f"accepted={msummary['plays_accepted']} {msummary['wall_s']}s", flush=True)
                if a.max_ticks and total_ticks >= a.max_ticks:
                    break
    finally:
        if env is not None:
            env.close()
        if charges_fh is not None:
            charges_fh.close()
        if track_events_fh is not None:
            track_events_fh.close()

    # O13: which estimator variant(s) back every condition -- 'v1' (default) keeps every key below
    # UNSUFFIXED, byte-identical to before O13; 'both' suffixes every key '_v1'/'_v2' (ticket 3).
    variants = ("v1", "v2") if a.estimator == "both" else (a.estimator,)
    both_mode = len(variants) > 1
    # O16(c): build_cond_defs(False, False) == the old hardcoded 4-tuple exactly (tuple equality, see
    # TestActiveBaseConds/TestBuildCondDefs) -- --tracker/--corr off leaves this byte-identical to before.
    COND_DEFS = build_cond_defs(bool(a.tracker), bool(a.corr))

    def long_key(long_name: str, variant: str) -> str:
        return f"{long_name}_{variant}" if both_mode else long_name

    conds = [(long_key(long_name, variant), tick_field(base, variant, both_mode, "est"),
             cond_key(base, variant, both_mode))
            for long_name, base in COND_DEFS for variant in variants]
    # FIX 1: ghost_delivered_run is THE truth ledger fed to every overcharge_table below; ghost_scripted_run
    # is carried in summary.json for reference only and is never used in an over-charge computation.
    ghost_delivered_run = merge_base_ledgers([m["ghost_delivered_by_base"] for m in match_summaries])
    ghost_scripted_run = merge_base_ledgers([m["ghost_scripted_by_base"] for m in match_summaries])
    # FIX 3: per-match record, field-for-field the same spelling e1_eval.run_match writes to matches.jsonl
    # (outcome, crowns_for, crowns_against, plays_accepted) -- the lead's fidelity gate against ctrl_live100.
    matches = [{"tag": m["tag"], "k": m["k"], "outcome": m["outcome"], "crowns_for": m["crowns_for"],
               "crowns_against": m["crowns_against"], "plays_accepted": m["plays_accepted"],
               "decisions": m["decisions"], "end_tick": m["end_tick"], "n_ticks": m["n_ticks"]}
              for m in match_summaries]
    # O18: run-level winrate -- wins/n plus, when importable, the SAME entry-clustered bootstrap CI shape
    # pipeline/e1_score.summarise/cluster_bootstrap uses (never re-implemented here, so it can never drift
    # from the lead's own scoring). Falls back to wins/n + a note if e1_score can't be imported for any
    # reason (e.g. run standalone outside the repo) -- never fails the run over a reporting extra.
    n_matches_wr = len(matches)
    wins_wr = sum(1 for m in matches if m["outcome"] == "win")
    winrate_summary: dict[str, Any] = {
        "n": n_matches_wr, "wins": wins_wr,
        "winrate": (wins_wr / n_matches_wr) if n_matches_wr else None,
    }
    try:
        from pipeline.e1_score import cluster_bootstrap as _cluster_bootstrap
        by_entry_wr: dict[str, list] = {}
        for m in matches:
            by_entry_wr.setdefault(m["tag"], []).append(1.0 if m["outcome"] == "win" else 0.0)
        winrate_summary["winrate_entry_weighted"] = _cluster_bootstrap(by_entry_wr)
    except Exception as exc:
        winrate_summary["note"] = f"pipeline.e1_score bootstrap unavailable ({exc!r}) -- wins/n only"
    summary = {
        "n_ticks": len(all_rows), "n_matches": len(match_summaries), "port": a.port, "split": a.split,
        "entries": a.entries, "seeds": a.seeds, "ckpt": str(a.ckpt),
        "decide_every": cfg["decide_every"], "estimator_step": cfg["estimator_step"],
        "n_detector_cards": len(whitelist),
        "matches": matches,
        "winrate": winrate_summary,                       # O18: run-level wins/n (+ bootstrap CI if available)
        "feed_opp_elixir": a.feed_opp_elixir, "feed_noise": a.feed_noise,   # O18: which arm this run is
        "plays_accepted_by_match": {f"{m['tag']}:{m['k']}": m["plays_accepted"] for m in match_summaries},
        "over_charge_at_end_by_match": [{"tag": m["tag"], "k": m["k"], **m["over_charge_at_end"]}
                                        for m in match_summaries],
        "ghost_delivered_by_base": ghost_delivered_run,             # the truth ledger over-charge uses
        "ghost_scripted_by_base": ghost_scripted_run,                # REFERENCE ONLY -- not used for over-charge
        "estimator": a.estimator,
        "finished": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    if "v2" in variants:
        # FIX 1: _jsonable() converts V2_PARAMS["spawns"]'s frozensets to sorted lists for THIS logged copy
        # only -- the live opponent_elixir.V2_PARAMS/SPAWNS/BODIES objects are never touched.
        summary["v2_params"] = _jsonable(V2_PARAMS)    # O13 ticket 3: every V2 default constant, for the record
    for key, est_key, cond in conds:
        summary[key] = summarize_condition(all_rows, est_key)
        charged_run = merge_base_ledgers([m["charged_by_base"][cond] for m in match_summaries])
        summary[key]["overcharge"] = overcharge_table(charged_run, ghost_delivered_run)
    (out / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")

    md = ["# opp_est_audit summary", "", f"n_ticks={summary['n_ticks']} n_matches={summary['n_matches']} "
         f"port={a.port} split={a.split} entries={a.entries} decide_every={cfg['decide_every']} "
         f"estimator_step={cfg['estimator_step']}", "",
         "| condition | MAE | bias | P90\\|err\\| | share<=1.0 | share<=2.0 |",
         "|---|---|---|---|---|---|"]
    # O16 attempt 2 FIX 2(a) (verifier, MEDIUM): every "_tt" label says plainly that confirmed-track
    # billing is an IDEALISED DESIGN UNDER TEST, not live's actual estimator path -- live bills every
    # enemy-tagged, whitelisted det every frame with NO min_hits gate at all (play.py:547,558; that gate
    # lives only in enemy_tracks(), which feeds threat/aim logic, never the elixir estimator). The "_wl"
    # siblings (FIX 2(b)) are the LIVE-REACHABLE version: same confirmed-track billing, but the billed
    # det's base must also clear live's detector_cards whitelist, exactly as play.py:547 would gate it.
    BASE_LABELS = {"Aplus_perfect_detection_with_spells": "A+ perfect detection (+spells, no whitelist)",
                  "A_perfect_detection": "A perfect detection (units only, NO whitelist -- loose upper bound)",
                  "A_wl_live_whitelist": "A_wl perfect detection (units only, live's detector_cards whitelist)",
                  "B_degraded_live": "B degraded (live)",
                  "B_tt_tracker_input_idealised": "B_tt IDEALISED: bill once per TeamTracker-confirmed "
                      "track (min_hits), no whitelist -- a design under test, NOT live's current path",
                  "B_tt_wl_tracker_input_live_whitelist": "B_tt_wl live-reachable: B_tt's billing, "
                      "restricted to live's detector_cards whitelist",
                  "B_corrS_short_correlated": "B_corrS correlated-degrade, SHORT persistence",
                  "B_corrS_tt_short_correlated_tracker_input_idealised": "B_corrS_tt IDEALISED "
                      "tracker-input on SHORT correlated -- design under test, NOT live's current path",
                  "B_corrS_tt_wl_short_correlated_tracker_input_live_whitelist": "B_corrS_tt_wl "
                      "live-reachable tracker-input on SHORT correlated",
                  "B_corrL_long_correlated": "B_corrL correlated-degrade, LONG persistence",
                  "B_corrL_tt_long_correlated_tracker_input_idealised": "B_corrL_tt IDEALISED "
                      "tracker-input on LONG correlated -- design under test, NOT live's current path",
                  "B_corrL_tt_wl_long_correlated_tracker_input_live_whitelist": "B_corrL_tt_wl "
                      "live-reachable tracker-input on LONG correlated"}
    labels = {long_key(long_name, variant): BASE_LABELS[long_name] + (f" [{variant}]" if both_mode else "")
             for long_name, _base in COND_DEFS for variant in variants}
    for key, _, _cond in conds:
        m = summary[key]
        md.append(f"| {labels[key]} | {m['mae']} | {m['mean_bias']} | {m['p90_abs_err']} | "
                 f"{m['share_abs_err_le_1_0']} | {m['share_abs_err_le_2_0']} |")
    md.append("")
    for key, _, _cond in conds:
        md.append(f"## Condition {labels[key]}")
        for ph in PHASES:
            p = summary[key]["by_phase"][ph]
            md.append(f"- {ph}: n={p['n']} MAE={p['mae']} bias={p['mean_bias']} P90={p['p90_abs_err']}")
        op, mp = summary[key]["opp_play_ticks"], summary[key]["my_play_ticks"]
        md.append(f"- opponent-play ticks: n={op['n']} MAE={op['mae']} bias={op['bias']}")
        md.append(f"- our accepted-play ticks: n={mp['n']} MAE={mp['mae']} bias={mp['bias']}")
        nc, bc = summary[key]["by_truth_cap"]["near_cap_ge_9"], summary[key]["by_truth_cap"]["below_cap"]
        md.append(f"- truth>=9.0 (near cap): n={nc['n']} MAE={nc['mae']} bias={nc['mean_bias']}")
        md.append(f"- truth<9.0: n={bc['n']} MAE={bc['mae']} bias={bc['mean_bias']}")
        bm = summary[key]["by_match"]
        md.append(f"- per-match MAE: n_matches={bm['n_matches']} median={bm['mae_median']} p90={bm['mae_p90']}")
        oc = summary[key]["overcharge"]
        md.append(f"- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged={oc['total_charged_elixir']} "
                 f"total_ghost_delivered={oc['total_ghost_elixir']} total_over_charge={oc['total_over_charge']} "
                 f"share_from_never_played_bases={oc['over_charge_share_from_bases_never_played']}")
        md.append("  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |")
        md.append("  |---|---|---|---|---|---|")
        for row in oc["top"][:10]:
            md.append(f"  | {row['base']} | {row['ghost_plays']} | {row['ghost_elixir']} | "
                     f"{row['charges']} | {row['charged_elixir']} | {row['over_charge']} |")
        md.append("  (top 10 shown here; top 25 in summary.json)")
        md.append("")
    (out / "summary.md").write_text("\n".join(md), encoding="utf-8")
    # O13: generalized over every active (base condition, variant) pair -- for solo v1/v2 mode this produces
    # the EXACT SAME flat keys as before O13 (Aplus_mae, A_mae, A_wl_mae, A_wl_total_over_charge, ...); under
    # --estimator both each key grows a _v1/_v2 suffix (Aplus_v1_mae, A_wl_v2_total_over_charge, ...).
    done_metrics: dict[str, Any] = {
        "n_ticks": summary["n_ticks"], "n_matches": summary["n_matches"],
        "matches": summary["matches"],                            # FIX 3: fidelity gate vs ctrl_live100
        "plays_accepted_by_match": summary["plays_accepted_by_match"],
        "feed_opp_elixir": a.feed_opp_elixir, "feed_noise": a.feed_noise,           # O18
        "winrate": winrate_summary["winrate"], "wins": winrate_summary["wins"], "n": winrate_summary["n"],
    }
    for long_name, base in COND_DEFS:
        for variant in variants:
            m = summary[long_key(long_name, variant)]
            tag = f"{base}_{variant}" if both_mode else base
            done_metrics[f"{tag}_mae"] = m["mae"]
            done_metrics[f"{tag}_bias"] = m["mean_bias"]
            if base in ("A_wl", "B_tt", "B_tt_wl", "B_corrS", "B_corrL", "B_corrS_tt", "B_corrS_tt_wl",
                       "B_corrL_tt", "B_corrL_tt_wl"):
                # O16: the new conditions' whole point is over-charge behaviour -- surface it in the
                # condensed OPP_EST_AUDIT_DONE line too, not just summary.json (A_wl unchanged).
                done_metrics[f"{tag}_total_over_charge"] = m["overcharge"]["total_over_charge"]
                done_metrics[f"{tag}_over_charge_share_never_played"] = m["overcharge"][
                    "over_charge_share_from_bases_never_played"]
                done_metrics[f"{tag}_over_charge_top3"] = m["overcharge"]["top"][:3]
    print(json.dumps({"OPP_EST_AUDIT_DONE": done_metrics}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
