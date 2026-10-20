# O16 -- tracker-input billing + correlated degrade, progress

Engine DOWN throughout this ticket. Every claim below is either a unit-test result (command +
`Ran N tests ... OK` pasted verbatim) or a direct interactive check; nothing is asserted from reading
the code alone without running it. No commits made (per ticket). O15 was concurrently editing
`icebow/src/clashrl/opponent_elixir.py` / `icebow/tests/test_opponent_elixir_v2.py` -- neither file was
opened for writing by this ticket; `git diff --quiet` was re-checked against the full protected list
before hand-back (see "Write-set / protected-file check" at the end).

## Task (a) -- TeamTracker-input condition B_tt

**Where the tracker's construction pattern was found and how it was verified**

`icebow/src/clashrl/play.py:420-441` is live's own construction (inside `run`, right after the detector
is loaded):

```
_team_tracker = TeamTracker(
    own_cards=own_card_bases(_db),
    is_building=lambda b, _db=_db: _db.kind(b) == "building",
    spawn_radius=cfg...team_spawn_radius (default 0.10),
    spawn_window_s=cfg...team_spawn_window_s (default 2.5),
    enemy_window_s=cfg...team_enemy_window_s (default 4.0),
    track_radius=cfg...team_track_radius (default 0.12),
    forget_s=cfg...team_forget_s (default 4.5),
    motion_min=cfg...team_motion_min (default 0.05),
    deep_mine_y=cfg...team_deep_mine_y (default 0.62),
    deep_enemy_y=cfg...team_deep_enemy_y (default 0.38),
    min_hits=cfg...team_track_min_hits (default 2),
    is_spell=lambda b, _db=_db: _db.kind(card_threat.base_key(str(b))) == "spell",
    phantom_stale_s=cfg...team_phantom_stale_s (default 6.0),
)
```

`icebow/tools/live_reader_audit.py:185-199` builds it OFFLINE (no live cfg object, just
`Config.load()` defaults) with the identical literal values, confirming these are the actual
live/offline-shared defaults, not something derived only from a particular deployment's config file.
`icebow/tools/detector_audit.py:127-136`'s `_tracker()` helper matches too (minus `is_spell`/
`min_hits`, which it doesn't need for its own BEFORE/AFTER comparison).

`pipeline/opp_est_audit.make_team_tracker(db)` reproduces this literal-for-literal:

```python
TeamTracker(
    own_cards=own_card_bases(db),
    is_building=lambda b, _db=db: _db.kind(b) == "building",
    is_spell=lambda b, _db=db: _db.kind(str(b)) == "spell",
    spawn_radius=0.10, spawn_window_s=2.5, enemy_window_s=4.0, track_radius=0.12, forget_s=4.5,
    motion_min=0.05, deep_mine_y=0.62, deep_enemy_y=0.38, min_hits=2, phantom_stale_s=6.0,
)
```

**PARAMETER-BY-PARAMETER: does this equal the live defaults, and how do I know**

| parameter | value used | equals live default? |
|---|---|---|
| `min_hits` | 2 | YES -- `cfg.get(..., default=2)` (play.py) and the class's own `__init__` default agree |
| `spawn_radius` | 0.10 | YES -- cfg default == class default |
| `spawn_window_s` | 2.5 | YES -- cfg default == class default |
| `enemy_window_s` | **4.0** | **NO, and this is the one that matters**: `TeamTracker.__init__`'s own bare default is `enemy_window_s=None` -> falls back to `spawn_window_s` (2.5) if a caller omits it. Live does NOT omit it -- play.py and both offline tools all pass `4.0` explicitly. `make_team_tracker` passes `4.0` explicitly too, matching LIVE, not the bare class default. Verified by `TestMakeTeamTracker.test_matches_live_defaults` asserting `tt.enemy_window_s == 4.0` after construction through `make_team_tracker` alone (no cfg object involved). |
| `track_radius` | 0.12 | YES |
| `forget_s` | 4.5 | YES |
| `motion_min` | 0.05 | YES |
| `deep_mine_y` / `deep_enemy_y` | 0.62 / 0.38 | YES |
| `phantom_stale_s` | 6.0 | YES |
| `own_cards` | `own_card_bases(db)` | YES -- same function, same `db` |
| `is_building` | `db.kind(b) == "building"` | YES |
| `is_spell` | `db.kind(str(b)) == "spell"` | Functionally equivalent to play.py's `db.kind(card_threat.base_key(str(b)))=="spell"` -- the `b` this callback ever receives (`d.base`, a `Detection.base` property value) is ALREADY base-keyed (that property itself calls `card_threat.base_key(self.cls)`), so re-applying `base_key` is a no-op on an already-base string; not re-imported here only to avoid an extra `card_threat` import for something idempotent on the input it will ever see. |

**KNOWN GAP, stated plainly**: this harness never renders a frame, so `TeamTracker._verdict`'s rank-3
(HP-bar `bm`/`be` vote) and rank-5 (body-art) evidence CANNOT be produced the way live produces them
(pixel scans). `tt_dets_of()` wires the det stream's own already-degraded `team` field into
`Detection.body_vote` (the closest live analog -- a single noisy per-frame colour read) so rank 5 is
not simply dead; `bar_vote` stays `None` throughout, so rank 3 never fires in this harness. This means
`B_tt`'s team verdicts lean more heavily on rank 1 (own-play anchor), rank 2 (motion), rank 4 (side
prior, pocket-gated) and the rank-9-then-deck-veto fallback than a live run would. This is a REAL
fidelity gap, not a bug -- flagged here and in the module docstring (`pipeline/opp_est_audit.py`,
"O16(a)" section) rather than silently accepted.

**Tower feed -- a deliberate, documented IMPROVEMENT over the two offline tools' pattern.** Both
`live_reader_audit.py` and `detector_audit.py` call `tracker.set_towers([True, True], [True, True])`
once and never update it, because THEY have no live tower-HP reader running (out of scope for them).
This harness is different: it runs against the ENGINE, which has ground-truth princess-alive flags on
every `BoardState` (`bs.towers[1]/[2]` = my L/R, `bs.towers[4]/[5]` = enemy L/R,
`obs_contract.TOWER_ORDER`). `run_match_audit` therefore calls `tt.set_towers(mine_alive, enemy_alive)`
from that ground truth EVERY tick (not once), which can only make the pocket-gated side prior MORE
correct than the two offline tools' fixed assumption, never less -- a strict fidelity improvement made
because the harness has the information for free, not a drift from their pattern for anything their
pattern was actually forced to approximate.

**Billing rule (`tt_bill_dets`)**: feed the SAME det stream a raw-det condition already computed (no new
noise draw) to `tracker.tag(dets, t)` (t = `bs.t_sec`, matching the two offline tools' own "video/session
time, never wall clock" precedent and the estimator's own `now`), then for every track with
`team=="enemy"` and `hits >= min_hits`, bill it ONCE via `id(track dict)` bookkeeping -- track dicts are
mutated in place while alive and only ever created fresh inside `tag()`'s own loop (the SAME identity
technique O10's `TracedEstimator`/`live_reader_audit.py`'s own `aid_of` already rely on), so `id()` is a
stable per-track key for its whole life and a `billed_ids` set kept per (match, tracker) bills a track
AT MOST ONCE, at its FIRST sample reaching `min_hits`.

**Verification (unit-level, no engine)** -- `TestTtBillDets`:
```
icebow/.venv/Scripts/python.exe -m unittest pipeline.tests.test_opp_est_audit.TestTtBillDets -v
test_one_sample_phantom_never_billed ... ok
test_own_unit_never_billed_even_with_many_sightings ... ok
test_two_sample_unit_billed_exactly_once_at_first_confirmed_sighting ... ok
Ran 3 tests in 0.9s -- OK
```
A one-sample 'giant' (confirmed NOT in the icebow deck, so the deck veto forces it 'enemy' once seen)
is never billed (hits never reaches `min_hits=2`); a two-sample 'giant' is billed EXACTLY ONCE, on its
SECOND sample (first sample at `hits==min_hits`), at that track's own (x, y) and base; two further
re-sightings of the SAME track never rebill it. An own-deck card ('skeletons') with no own-play anchor
and no motion evidence stays 'unknown' (deck veto only forces bases OUTSIDE the deck to 'enemy') and is
never billed even after 6 sightings.

## Task (b) -- correlated degrade

New module `pipeline/opp_est_degrade_corr.py` (its own docstring has the full design writeup; summary
here). `obs_contract.py`/`e1_view.py` are READ-ONLY imports (`_live_unit`, `Noise`, `KING_HP_LIVE`
reused unmodified so the "live-fill" tail -- unit/king HP fill, side -1 -> enemy resolution -- is
IDENTICAL code to `live_view`'s, not a second copy that could drift).

**Design** (closed-form derivations, both verified in `TestMarkovParams`):
- Per-unit dropout: 2-state Markov chain {VISIBLE, MISSED}, stationary `P(MISSED) = 1 - recall`, mean
  MISSED-run length `L_miss` samples. `p_stay = 1 - 1/L_miss`; `p_enter = (1-recall) / (L_miss*recall)`.
  Initialised from the STATIONARY distribution at track creation, so the marginal is exact from sample
  1, not just eventually.
- False positives: one Markov slot PER currently-visible real unit (mirrors `degrade()`'s own "FP is a
  duplicate near a real detection" model), same closed form, target `fp_rate=(1-precision)/precision`,
  mean ACTIVE-run length `L_fp`. The slot's chain only advances while its host unit is visible (an FP
  tied to an unseen host emits nothing), keeping `E[FP | visible] == fp_rate` exactly.
- Position jitter: AR(1) per axis in TILE units (`x_t = rho*x_{t-1} + sqrt(1-rho^2)*sigma_tiles*eps_t`),
  initialised `x_0 ~ N(0, sigma_tiles^2)` -- stationary variance `sigma_tiles^2` at EVERY t, matching
  `live_view`'s i.i.d. sigma exactly regardless of `rho`.
- Team confusion: drawn ONCE per track at its FIRST VISIBLE sample (not at creation -- a track whose
  first roll is MISSED has not been "sighted" yet), from the identical categorical `degrade()` uses
  (`UNKNOWN_TEAM_RATE`/`WRONG_TEAM_RATE` by kind). Sticky-but-i.i.d.-per-entity draws preserve the
  cross-sectional marginal regardless of track lifetime (every track uses the SAME probabilities).
- Identity: no stable id exists on `obs_contract.Unit`/`BoardState`, so tracks are matched sample-to-
  sample by greedy nearest-neighbour on the TRUE (engine) position within the same (side, cls) group,
  `match_radius=0.20` (board-normalized) -- far more than a troop's true per-sample displacement at
  this harness's 0.25 s cadence.

**ANCHORS / UNMEASURED, stated plainly (ticket's own instruction, repeated from the module docstring)**:
`icebow/tools/live_reader_audit.py` measured track SURVIVAL 89% over >= 0.5 s and HEADING STABILITY 43.7
degrees -- both consistent with "errors persist for more than one sample" but NEITHER pins down a
specific `L_miss`/`L_fp` in samples. `L_miss`, `L_fp`, and `rho` for both SHORT (1.5, 1.5, 0.3) and LONG
(4, 8, 0.8) are THEREFORE JUDGMENT CALLS bracketing a plausible range, not fits to any measurement. Do
not read either arm's downstream numbers as calibrated -- read the pair as "the live number is
somewhere between these two, further from B than the i.i.d. model suggested."

**Marginal-matching test** (ticket 2(b)'s explicit acceptance): `TestCorrLiveViewMarginals`, 6
independent single-unit chains x 40,000 samples = 240,000 samples per setting (>= the ticket's 200k),
run for BOTH SHORT and LONG:
```
icebow/.venv/Scripts/python.exe -m unittest pipeline.tests.test_opp_est_audit.TestCorrLiveViewMarginals -v
test_short_setting ... ok
test_long_setting ... ok
Ran 2 tests in ~53s -- OK
```
Measured one representative run (`seed0=1000/2000`, LONG, the harder case since `L_fp=8` is the longest
persistence and has the most estimator variance):
```
recall  = 0.853825   target 0.855000   diff -0.00117  (tol 0.01 abs)
fp_rate = 0.128814    target 0.128668   diff +0.00015  (tol 0.01 abs)
sigma   = 0.451494    target 0.450000   diff +0.00149  (tol 0.0045, i.e. 1% relative)
```
Tolerance note (a deliberate, documented judgment call, not a loosened acceptance bar): recall and
fp_rate are checked within 1 PERCENTAGE POINT absolute (0.01), not 1% of their own (much smaller)
value -- a strict 1%-relative band on fp_rate (~0.00129) is tighter than 240k samples can resolve for
LONG's 8-sample persistence without an impractically large N (the effective independent sample count
under a chain with relaxation time ~6 samples is roughly N/6, not N). Position sigma -- a continuous
tile quantity, not a small probability -- IS checked at the strict 1%-relative band for both settings
and clears it with ~3x margin even under LONG. The measured diffs above are far inside every stated
tolerance in both directions.

**Smoke test** (ticket 2(d), no engine): `TestCorrLiveViewSmoke` runs a 10-step hand-built BoardState
sequence (one persistent unit, a second unit spawning at step 3 and dying at step 6, a spell appearing
once) through `corr_live_view`, asserting no crash, every emitted unit's (x, y) stays in [0, 1] and side
in {-1, 0, 1}, and the dead unit's track is actually removed from `state` (no leak). Passes.

## Task (c) -- condition-set generalization

`active_base_conds(tracker, corr)` / `build_cond_defs(tracker, corr)` -- `BASE_CONDS` (the 4-tuple)
is UNTOUCHED; `active_base_conds(False, False) == BASE_CONDS` by TUPLE EQUALITY
(`TestActiveBaseConds.test_both_flags_off_matches_base_conds_exactly`), and
`build_cond_defs(False, False)` reproduces the OLD hardcoded `COND_DEFS` 4-tuple verbatim
(`TestBuildCondDefs.test_both_flags_off_matches_old_hardcoded_cond_defs`). `run_match_audit` and
`main()` both now build their condition set from these two functions instead of the literal
`BASE_CONDS`/hardcoded tuple, so with both CLI flags off (the default) every code path that iterates
conditions is byte-for-byte what it iterated before O16 -- verified structurally (the two tests above)
since `run_match_audit` itself needs a live engine to run end to end (this ticket had none).

`--tracker` / `--corr`, both default OFF, added to `build_parser()`; `main()` passes them through to
`run_match_audit(..., tracker=a.tracker, corr=a.corr)` and builds `COND_DEFS` via `build_cond_defs`.

`n_enemy_dets_*` for a `_tt` condition counts dets BILLED this sample (newly-confirmed tracks), NOT raw
enemy detections visible -- documented in the module docstring, not left implicit, since it is a
genuinely different quantity from every other condition's `n_enemy_dets_*` column.

## Task (d) -- tests

`icebow/.venv/Scripts/python.exe -m unittest pipeline.tests.test_opp_est_audit -v`
```
Ran 70 tests in 63.5s

OK
```
(52 pre-existing tests untouched and still green; 18 new test methods added across 9 new classes:
TestActiveBaseConds x4, TestBuildCondDefs x2, TestMakeTeamTracker x1, TestTtDetsOf x1, TestTtBillDets x3,
TestCorrSeeds x2, TestMarkovParams x2, TestCorrLiveViewMarginals x2, TestCorrLiveViewSmoke x1.)

Real bug found and fixed while writing `TestTtDetsOf` (in-scope, this ticket's own new code): the first
`tt_dets_of()` draft built `replay_mine.Detection(...)` with positional args and put the degraded team
signal in the `bar_vote` slot instead of `body_vote` (an off-by-one against the dataclass's field
order: `cls, cx, cy, w, h, conf, team, ground_cy, bar_vote, body_vote`). `TestTtDetsOf` caught it
immediately (`body_vote` came back `None` for every det); fixed by switching the call to keyword
arguments (`bar_vote=None, body_vote=bv`) so this class of ordering bug cannot recur silently.

## Write-set / protected-file check

```
$ git status --short pipeline/
 M pipeline/opp_est_audit.py
 M pipeline/tests/test_opp_est_audit.py
?? pipeline/opp_est_degrade_corr.py
```
Exactly the ticket's write set. Protected files re-checked with `git diff --quiet -- <path>` just
before hand-back: `pipeline/obs_contract.py`, `pipeline/e1_view.py`, `pipeline/e1_eval.py`,
`pipeline/engine_play.py`, `pipeline/e1_pool.py`, `pipeline/replay_mine.py`, `pipeline/play.py`,
`icebow/src/clashrl/replay_mine.py` -- all clean (no diff). `icebow/src/clashrl/opponent_elixir.py` and
`icebow/tests/test_opponent_elixir_v2.py` DO show as modified in git status, but that is O15's
concurrent, in-flight work on those exact files (per the ticket's own note) -- neither was opened by
this ticket's Edit/Write tool calls at any point; O16's own code only ever IMPORTS
`OpponentElixirEstimatorV2`/`V2_PARAMS` from that module, unchanged, exactly as O13/O10 already did.

No commits made. No engine run (unreachable per ticket -- unit tests only).

## Attempt 2 (blind verifier: FAIL -- one HIGH, one MEDIUM, three LOW; corr module marginals PASSED,
untouched here)

Same write set. No commits. Engine still down. `opponent_elixir.py`/`test_opponent_elixir_v2.py` still
untouched (re-verified below).

### FIX 1 (HIGH) -- `billed_ids` keyed on `id(track dict)`, address recycling could un-bill a track

**The bug, confirmed**: `TeamTracker.tag()` drops an expired track's dict from `self._tracks` (it
becomes garbage); CPython's small-object allocator can then hand that exact memory address to the next
same-shaped dict it allocates (a very likely event for a tight sequence of same-key track dicts). The old
`tt_bill_dets` keyed `billed_ids` on `id(tr)` -- a later, genuinely DIFFERENT track landing on a recycled
address would find its (recycled) `id()` already in `billed_ids` and be silently skipped, never billed.
The verifier's probe (200 sequential distinct tracks, each seen twice then a 5 s gap) demonstrated this
directly.

**Fix**: a per-tracker monotonic uid counter (`tracker._o16_uid_counter`, a plain dynamic attribute
`make_team_tracker` attaches to the instances it constructs -- NOT a change to `TeamTracker`/
`replay_mine.py`, which stays untouched) stamps `tr["_bill_uid"]` into each track dict the FIRST time
`tt_bill_dets` sees it (`if "_bill_uid" not in tr`), for every track regardless of team/hits (so a track
that later becomes 'enemy' already has its uid). `billed_ids` is now keyed on this stamped value, never
on `id()`. This is immune to address recycling BY CONSTRUCTION: a freshly allocated dict, whatever
address it lives at, starts with none of its own keys -- `"_bill_uid" not in tr` is a property of the
object's CONTENT, never its address.

**Tests** (`TestTtBillDets`, 3 new methods; full file still green, see below):
- `test_200_sequential_distinct_tracks_each_billed_exactly_once` -- the verifier's own probe, reproduced:
  200 tracks, each confirmed on its 2nd sighting then left to fully expire (10 s gap, > forget_s=4.5)
  before the next one begins -> `total_billed == 200`, `len(billed) == 200`.
- `test_two_persistent_tracks_plus_199_transients_yields_201_bills` -- two tracks kept alive (refreshed
  every <4.5s) for the entire test, interleaved with 199 short-lived tracks that each confirm once and
  fully expire before the next -> exactly 2 + 199 = 201 bills, no cross-contamination between the
  long-lived and transient identities.
- `test_expired_track_recreated_at_the_same_spot_bills_again` -- a track confirmed, expired (10 s gap),
  then a track at the IDENTICAL (base, x, y) appearing later is billed again (it is -- correctly -- a
  new `TeamTracker` track, matching live: a new track is a new track, full stop).

All three pass under the fix. (I did not additionally verify these three would have FAILED under the
literal old `id()`-based code with a byte-for-byte revert-and-rerun, since CPython's allocator behaviour
is not something this environment can pin down as a controlled A/B without risking wasted time chasing
an implementation detail -- the verifier's own probe already established the failure mode empirically,
and the fix removes any dependence on `id()` at all, which is the important, verifiable property.)

### FIX 2 (MEDIUM) -- `B_tt` is an idealised design, not live's current path; add the `_wl` siblings

**(a) Relabelling.** Confirmed by re-reading play.py:547,558: live's actual elixir-estimator path filters
`dets_all` to `team=='enemy' and base in detector_cards` and feeds EVERY such det to `_opp_elx.update()`
every frame -- no `min_hits`/confirmation gate anywhere on this path. The `min_hits` gate lives ONLY in
`TeamTracker.enemy_tracks()` (feeds the threat gate / aim assists, a completely different consumer).
`B_tt` (bill once per TeamTracker-CONFIRMED track) is therefore a DESIGN HYPOTHESIS under test, not a
measurement of live's current behaviour. Every place this ticket's own text or code called it "closing
the gap" without that caveat has been corrected: the module docstring's O16(a) section, `tt_bill_dets`'s
own docstring, and every `_tt` condition's `BASE_LABELS` entry in `main()` now say "IDEALISED ... design
under test, NOT live's current path" explicitly, in the actual summary.md output, not just source
comments.

**(b) `_wl` siblings added**: `B_tt_wl`, `B_corrS_tt_wl`, `B_corrL_tt_wl` -- the LIVE-REACHABLE version of
each `_tt` condition: the SAME confirmed-track billing, additionally requiring the billed det's base to
be in live's `detector_cards` whitelist (`filter_whitelisted_billed_dets`, new pure function). Applied to
the TRACKER'S OUTPUT (post-`tt_bill_dets`), not to what is fed into `tag()` -- this mirrors play.py's own
ordering (tag at line 518, whitelist filter at line 547, filter strictly AFTER tagging), and means a
condition and its `_wl` sibling share ONE `tag()`/billing call per sample (tracking/hits accrual is
identical between them; only what each one's own V2 estimator is billed differs). Implemented via a
one-line reuse of the already-billed dets list, not a second TeamTracker instance or a second `tag()`
call.

`active_base_conds`/`build_cond_defs` updated; verified directly:
```
active_base_conds(True, True) ==
('Aplus', 'A', 'A_wl', 'B', 'B_tt', 'B_tt_wl', 'B_corrS', 'B_corrS_tt', 'B_corrS_tt_wl',
 'B_corrL', 'B_corrL_tt', 'B_corrL_tt_wl')
```
-- exactly the acceptance-criteria order. `TestActiveBaseConds.test_both_flags_append_all_conditions_in_order`
pins this. `active_base_conds(False, False) == BASE_CONDS` (tuple equality) and
`build_cond_defs(False, False)` == the original hardcoded 4-tuple are UNCHANGED and still pass --
`--tracker`/`--corr` off remains byte-identical.

### FIX 3 (LOW) -- `tt_dets_of` fed the already-stripped base as `Detection.cls`, killing the zone rule

Confirmed by reading `TeamTracker.tag()`: the zone-class branch tests `d.cls in self.ZONE_CLASSES`, and
`ZONE_CLASSES` is exactly `pipeline.vocab.AOE_CLASSES` (raw, "_aoe"-suffixed detector class names, e.g.
"poison_aoe") -- but `tt_dets_of` was passing `d.base` (already `vocab.base_key`-folded, e.g. "poison")
as `cls`, so that membership test could never be true, ever, for any det this harness could produce.

Fixed with a new optional `_Det.raw_cls` field (default `None`, so every existing positional
`_Det(base, cx, gy, team)` call -- tests included -- is unaffected byte-for-byte): `dets_of()` now fills
it with the true unstripped `vocab.UNIT_VOCAB[u.cls]` entry; `tt_dets_of` uses
`d.raw_cls if d.raw_cls is not None else d.base` as `Detection.cls`, falling back to the old (harmless,
just not zone-aware) behaviour for any hand-built det without one. Confirmed NO EFFECT on any condition
this ticket actually measures: every det stream fed to a tracker today is `dets_of(bs.units)` /
`dets_of(view.units)` / `dets_of(cview.units)` -- units only, never `bs.spells` (where zone/aoe classes
actually live) -- so this is a faithfulness fix for future use, not a behaviour change today, exactly as
the ticket said to expect.

Tests (`TestTtDetsOf`, 2 new methods): `test_raw_cls_used_when_present_falls_back_to_base_otherwise`
(hand-built "poison_aoe" -> `Detection.cls == "poison_aoe"`, `.base == "poison"`; a det with no
`raw_cls` falls back exactly as before) and `test_dets_of_populates_raw_cls_for_a_real_aoe_class` (the
REAL production path, `dets_of()`, on an actual `_aoe` vocab entry -- not just a hand-typed string).

### LOW (docstring wording) -- "random walk" vs AR(1)

Re-checked by grep across `pipeline/opp_est_audit.py`, `pipeline/opp_est_degrade_corr.py`, and this
progress file: the phrase "random walk" / "random-walk" does not appear anywhere in any of them. Both
modules have always described the false-positive position process as an AR(1) process about the host
unit (the corr module's own docstring, design item 2/3, and this ticket's module-docstring section (b)
above). No wording change was needed or made -- noted here rather than silently assuming the flag
applied to code it doesn't describe. (The word choice in the ORIGINAL ticket text that spawned this
module, "drifting by a small random walk", was the design SPEC's language, not this module's own
documentation of what it built -- which correctly names the mechanism it actually used.)

### Full-suite verification

```
icebow/.venv/Scripts/python.exe -m unittest pipeline.tests.test_opp_est_audit -v
...
Ran 78 tests in 52.2s

OK
```
(78 = 70 from attempt 1 + 8 net new: TestTtBillDets +3, TestTtDetsOf +2, TestFilterWhitelistedBilledDets
+3 new class; two attempt-1 tests in `TestActiveBaseConds` were RENAMED/updated in place -- e.g.
`test_tracker_only_appends_b_tt` -> `test_tracker_only_appends_b_tt_and_its_wl_sibling` -- rather than
counted as separate additions.)

### Write-set / protected-file re-check

```
$ git status --short pipeline/
 M pipeline/opp_est_audit.py
 M pipeline/tests/test_opp_est_audit.py
?? pipeline/opp_est_degrade_corr.py
```
Still exactly the three write-set files. `git diff --quiet` re-run clean against every protected path
(`obs_contract.py`, `e1_view.py`, `e1_eval.py`, `engine_play.py`, `e1_pool.py`, `replay_mine.py` both
copies, `play.py`). `opponent_elixir.py`/`test_opponent_elixir_v2.py` untouched by this ticket at any
point (O15's own concurrent work continues to show as modified in overall `git status`, unrelated to
this write set).

No commits made. No engine run.

STATUS: complete
