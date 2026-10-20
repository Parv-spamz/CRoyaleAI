# O19 -- LIVE wiring for the opponent-elixir V2 estimate (one-line-config-change prep)

Repo HEAD at start: 3d8ad52. Python: icebow/.venv/Scripts/python.exe. No engine/live run. No commits.

## Verified before editing

- `diff icebow/src/clashrl/play.py hogeq/src/clashrl/play.py` -> 385 lines differ. NOT byte-identical.
  Per ticket rule: **editing icebow only**; hogeq/src/clashrl/play.py is untouched.
- Live construct site: `icebow/src/clashrl/play.py:400` `_opp_elx = OpponentElixirEstimator(_db)`.
- `update()` call site: `:558` `_est = _opp_elx.update(float(my_elixir), dets, now)`, where `dets` (`:547`)
  is already whitelist-filtered (`d.team == "enemy" and d.base in detector_cards`).
- `record_my_play`: `:1130` `_opp_elx.record_my_play(...)`. `reset`: `:1196` `_opp_elx.reset(...)`.
- `_student_opp_elixir` flag: `:186`, gates `_oe` at `:884` -- confirmed a SEPARATE switch from the new one.
- TeamTracker instance already exists in play.py for its own tagging: `_team_tracker = TeamTracker(...)`
  constructed `:422-441`, `.tag()` called synchronously at `:518` (non-perception-thread path) and by
  `PerceptionLoop._tracker.tag(...)` (icebow/src/clashrl/perception.py:200) on the SAME instance when the
  perception thread is running (`_ploop = PerceptionLoop(cfg, _detector, _team_tracker, ...)` at `:496`).
  So `_team_tracker._tracks` is current by the time `_threat_extra()` reaches the estimator update, under
  BOTH perception modes, with no second tracker needed. Confirms item 6 of the ticket does NOT apply
  (a reusable tracker exists on this exact code path).
- Billing pattern mirrored from `pipeline/opp_est_audit.py` (`make_team_tracker` :892-914, `tt_bill_dets`
  :941-994) READ, NOT imported (pipeline/ never imported from the live path): stamp a per-tracker monotonic
  uid into each track dict on first sight (`tr["_bill_uid"]`), bill a track the first time it is
  `team == "enemy"` and `hits >= tracker.min_hits`, key the "already billed" set on the uid (not `id(dict)`,
  which the audit module's own O16 FIX 1 measured as unsafe under CPython address recycling).
- `TeamTracker` track dict fields confirmed in `icebow/src/clashrl/replay_mine.py`: `tr["team"]`,
  `tr["hits"]` (:452-453), `tr["base"]`, `tr["x"]`, `tr["y"]` (:436-452), `self.min_hits` (:311).
- Existing test home for play.py wiring: `icebow/tests/test_play_tracker_wiring.py` (source-parses play.py's
  `_team_tracker = TeamTracker(...)` construction, then exercises a reconstructed tracker for behaviour).
  No test file already covers `_opp_elx`'s wiring specifically (`test_opponent_elixir.py` /
  `test_opponent_elixir_v2.py` test the estimator CLASSES in isolation, not play.py's use of them).
  Added the new tests to `test_play_tracker_wiring.py`.

## Design (minimal diff)

- New code-default-OFF flag `play.opp_elixir_v2`, read exactly like `_student_opp_elixir` (`:186`):
  `bool(cfg.get("play", "opp_elixir_v2", default=False))`.
- `_opp_elx` construction (`:400`) becomes `OpponentElixirEstimatorV2(_db) if _opp_elixir_v2 else
  OpponentElixirEstimator(_db)` -- OFF path is the exact same call as before.
- New MODULE-LEVEL helpers (not nested inside `play()`, so they are directly importable/testable):
  `_BilledDet` (a `.base/.cx/.gy/.team` shim) and `_opp_elixir_v2_bill(tracker, bill_state)`, which mirrors
  `tt_bill_dets` but never calls `tracker.tag()` itself (play.py's own tag() call, sync or via the
  perception thread, already ran this tick for every other consumer of `_team_tracker`).
- `:558` update call becomes an if/else: OFF branch is byte-identical to today
  (`_opp_elx.update(float(my_elixir), dets, now)`); ON branch bills via `_opp_elixir_v2_bill(_team_tracker,
  _opp_bill)`, filters the billed dets through the SAME `detector_cards` whitelist (applied to the
  tracker's output, mirroring `filter_whitelisted_billed_dets`'s placement), then calls `.update()` with
  those.
- `_opp_bill = {"uid_counter": itertools.count(1), "billed": set()}` created once near `_opp_elx`
  construction (`:400`); `_opp_bill["billed"].clear()` added at the match-reset block (`:1196`) alongside
  `_opp_elx.reset(...)` -- the uid counter itself is never reset (matches `tt_bill_dets`'s own "kept one per
  (match, tracker)" billed-set semantics; a fresh match's tracks are fresh dicts either way).
- `_student_opp_elixir` (`:186`, `:884`) is UNTOUCHED -- stays its own independent switch.

## Edits made

- `icebow/src/clashrl/play.py`: `import itertools`; module-level `_BilledDet` + `_opp_elixir_v2_bill(tracker,
  bill_state)` (mirrors `tt_bill_dets`, does not call `.tag()` itself); `_opp_elixir_v2` flag read next to
  `_student_opp_elixir`; `_opp_elx` construction ternary; `_opp_bill` state dict; the `update()` call site
  if/else (OFF branch line is byte-for-byte what it was before this ticket); `_opp_bill["billed"].clear()`
  next to `_opp_elx.reset(...)` at the match-reset block. `record_my_play` (`:1130+diff`) and
  `_student_opp_elixir`/`_oe` (`:186`, `:884+diff`) are UNTOUCHED. `git diff --stat`:
  `icebow/src/clashrl/play.py | 74 ++++++++++++++++++++++++++++++++++++++++++++--` (71 insertions, 3
  deletions -- the 3 deletions are the single `_opp_elx = OpponentElixirEstimator(_db)` and
  `_est = _opp_elx.update(...)` lines each becoming multi-line, plus the reset-block line moving).
- `icebow/tests/test_play_tracker_wiring.py` (the existing home for play.py-wiring tests -- no test file
  already covered `_opp_elx`'s wiring; `test_opponent_elixir[_v2].py` test the estimator CLASSES only):
  added `import itertools`, `OpponentElixirEstimator`/`OpponentElixirEstimatorV2`/`clashrl.play` imports,
  and two new `TestCase` classes, `OppElixirV2Wiring` (source-parsed, same convention as `PlayTrackerWiring`)
  and `OppElixirV2Billing` (behavioural, against `play._opp_elixir_v2_bill`/`play._BilledDet` + a real
  `TeamTracker`) covering all six ticket items:
  (i) OFF path construction+update-call source-pinned byte-identical to before.
  (ii) `test_a_one_frame_phantom_is_never_billed` / `test_a_two_frame_unit_is_billed_exactly_once...`.
  (iii) `test_an_expired_then_recreated_track_is_billed_again`.
  (iv) `test_on_path_bills_via_the_shared_tracker_and_reapplies_the_whitelist` (source) +
  `test_the_whitelist_still_filters_billed_dets` (behavioural).
  (v) `test_record_my_play_is_unconditional_in_both_modes`.
  (vi) `test_student_opp_elixir_is_untouched_and_independent_of_the_new_flag`.
  hogeq/tests/test_play_tracker_wiring.py (currently byte-identical to icebow's pre-edit copy) is left
  UNCHANGED -- out of the write set; it still tests hogeq's own untouched play.py and is unaffected.

## Verification run

`cd icebow && PYTHONPATH=src ../icebow/.venv/Scripts/python.exe -m pytest tests/test_opponent_elixir.py
tests/test_opponent_elixir_v2.py tests/test_play_no_cnn.py tests/test_play_tracker_wiring.py
tests/test_live_opponent.py -q` -> **92 passed** (17 of those in `test_play_tracker_wiring.py`, 12 new).
`ast.parse` on the edited `play.py` -> syntax OK. `git diff --stat` limited to `icebow/src/clashrl/play.py`
and `icebow/tests/test_play_tracker_wiring.py`; `hogeq/**` and `pipeline/**` show no changes from this
session (pipeline's own working-tree diff, from the concurrent O18 worker, predates and is untouched by
this session).

## Exactly what changes on the live path, per flag combination

- `opp_elixir_v2=False, student_opp_elixir=False` (today's default): UNCHANGED. V1
  `OpponentElixirEstimator`, fed every raw whitelisted enemy det every frame; S1 never sees the estimate
  (`_oe=None`).
- `opp_elixir_v2=False, student_opp_elixir=True`: UNCHANGED from before this ticket (L67f/L67g behaviour).
  V1 as above; S1 receives `_opp_elx._est` (elixir units).
- `opp_elixir_v2=True, student_opp_elixir=False`: V2 `OpponentElixirEstimatorV2` replaces V1; its input is
  no longer every raw det but one `_BilledDet` per `_team_tracker` track the FIRST time it is confirmed
  (`hits >= _team_tracker.min_hits`, verdict `enemy`), whitelist-filtered the same way; `record_my_play`/
  `reset` unaffected; S1 still sees `_oe=None` (independent switch).
- `opp_elixir_v2=True, student_opp_elixir=True`: V2 + tracker-billing as above, AND S1 now receives THIS
  estimator's `_est` instead of V1's.
- In every combination, `_team_tracker` itself, its `.tag()` call site, the aim assists, threat/identity
  vectors and everything else reading `dets`/`dets_all` are untouched -- only `_opp_elx`'s construction and
  its `update()` input change.

## Exact revert

`git checkout -- icebow/src/clashrl/play.py icebow/tests/test_play_tracker_wiring.py` (repo HEAD 3d8ad52,
before this session's edits) -- or restore byte-for-byte from
`scratchpad/gauntlet/L67/opp_fix/backup/play.py.o19.orig` and
`scratchpad/gauntlet/L67/opp_fix/backup/test_play_tracker_wiring.py.o19.orig` (both verified `md5sum`-equal
to the pre-edit HEAD files before editing began). No config default was touched, so simply not setting
`play.opp_elixir_v2` in config.yaml is already a full behavioural revert without touching code at all.

## Attempt 2

Blind verifier returned PASS_WITH_NOTES on attempt 1 with one MEDIUM defect (FIX 1) and a design gap
(FIX 2), plus two LOW items (FIX 3 tests, FIX 4 docs). Coordinator relayed all four; addressed in this
order. Repo HEAD moved from 3d8ad52 to `ab76edb` between attempts (the concurrent O18 worker's own commit,
`pipeline/opp_est_audit.py` + `pipeline/tests/test_opp_est_audit.py` + this progress file, which its commit
picked up as an untracked file) -- **verified `play.py`/`perception.py` are byte-identical between the two
commits** (`git show 3d8ad52:...|md5sum` == `git show ab76edb:...|md5sum` for both files), so nothing about
this ticket's baseline changed.

**Restore step**: `cp scratchpad/gauntlet/L67/opp_fix/play_o19_wip.py icebow/src/clashrl/play.py` and the
test-file equivalent, restoring attempt 1's edits (the lead had reverted the working tree to HEAD so the
owner could run live on verified code). `git diff --stat` after the restore matched attempt 1's own
diffstat exactly (74/137 insertions) before any attempt-2 changes were made, and the 19 attempt-1 tests
still passed -- confirmed a clean restore before touching anything.

**Backup-verification note**: `git show HEAD:<file> | md5sum` does NOT match this session's `.o19.orig`
backups directly -- this repo's blobs are stored LF-only while Windows checkouts here are CRLF (confirmed
by git's own "LF will be replaced by CRLF" warnings on every commit-adjacent git call). Stripping `\r`
(`tr -d '\r'`) from both sides makes every backup match its HEAD blob exactly; `git status --porcelain`
being clean at the moment each backup was taken (the actually-authoritative check, since it is CRLF-aware)
was already confirmed for `play.py`/`test_play_tracker_wiring.py` at the start of attempt 1 and for
`perception.py` at the start of attempt 2, before any of them were first read or copied.

### FIX 1 (MEDIUM, verifier) -- perception-thread race on `_team_tracker`'s track dicts

**The defect, confirmed by reading**: `TeamTracker.tag()` (`replay_mine.py`) does
`trk["x"], trk["y"], trk["t"] = dx, dy, t` on an EXISTING track dict (not a fresh one), and
`PerceptionLoop._run()` calls `self._tracker.tag(dets, now)` on the SAME `_team_tracker` instance play.py
hands it, inside `with self._lock:`. Attempt 1's `_opp_elixir_v2_bill` read `tr["x"]`/`tr["y"]` from that
same tracker with NO lock at all when `_ploop` was running -- exactly the every-other-guarded-access
pattern play.py already follows for `record_play`/`set_towers`/`snapshot`/`enemy_tracks`, which attempt 1
missed for this one new read path.

**Fix**: moved `_BilledDet`/`_opp_elixir_v2_bill` from play.py into `icebow/src/clashrl/perception.py` (a
lightweight, stdlib-only module play.py already imports `PerceptionLoop` from -- no import cycle), and
added `PerceptionLoop.bill_confirmed(bill_state, whitelist=None)`, a lock-guarded passthrough matching
`record_play`/`set_towers`/`snapshot`/`enemy_tracks`. It runs `_opp_elixir_v2_bill` (the WHOLE scan) inside
`with self._lock:`, copying every field it needs into fresh, immutable `_BilledDet` objects before
releasing -- so nothing returned can be torn, and the lock is released BEFORE the caller's `_opp_elx
.update()` runs (never held across the estimator call). Whitelist filtering (plain string containment on
the already-copied dets) runs after release. play.py's call site now branches on the SAME
`if _ploop is not None and _ploop.running:` pattern used everywhere else in the file: locked
`_ploop.bill_confirmed(...)` when perception owns the tracker, or the direct unlocked call when this act
loop is the tracker's only reader/writer (no perception thread running -- no race possible by
construction).

**Backup**: `icebow/src/clashrl/perception.py` backed up to
`scratchpad/gauntlet/L67/opp_fix/backup/perception.py.o19.orig` BEFORE editing (md5 matches HEAD after
CRLF-stripping, see above) -- perception.py was not in ticket O19's original WRITE SET, but FIX 1 explicitly
instructs adding a locked passthrough there, so it was necessarily added to the write set for this ticket;
called out here rather than silently expanded.

**Tests** (new, `PerceptionBillConfirmedLockTests` in test_play_tracker_wiring.py): the scan runs while
`self._lock.locked()` is True (proven by monkeypatching `_opp_elixir_v2_bill` to record the lock state when
called), the lock is released before `bill_confirmed` returns, `bill_confirmed` agrees with the unlocked
helper on an identical tracker, a 1-hit track is still not billed through the passthrough, and the
whitelist is applied after the locked scan. A genuine two-thread race is not asserted directly (it would be
flaky by nature); the lock-state monkeypatch test instead proves the STRUCTURAL guarantee (the scan cannot
run while the lock is free) that makes the race impossible by construction, matching how `_run()`'s own
`tag()` call is documented and guarded.

### FIX 2 (design change) -- `play.opp_elixir_v2_shadow`, observe-only

**Confirmed the verifier's finding by reading**: `mem[5]` is written from `_est` unconditionally
(`play.py`, inside `_threat_extra`), `env.opp_mem_slot5` defaults to `"opp_estimate"` in `config.yaml`, and
the lead confirmed `icebow/data/policy_rl.pt` exists (`_no_cnn` is False, so the CNN's `PolicyNet` forward
pass consumes `threat_vec`, which `mem` folds into). So `play.opp_elixir_v2` alone was never
observe-only -- flipping it changes what the CNN (and, if `student_opp_elixir`, S1) actually decide on.
Attempt 1 never claimed otherwise, but the ticket's premise ("prepare... so enabling it later is a
one-line change" without a safe comparison mode first) needed this addition.

**Built**: `play.opp_elixir_v2_shadow` (code default False, read the same way as the other two flags).
`_opp_elx_shadow` is constructed ONLY when this flag is True, and is ALWAYS the class OTHER than whichever
`_opp_elx` is (`OpponentElixirEstimator` if `opp_elixir_v2` is True, else `OpponentElixirEstimatorV2`) --
so the shadow log is always a genuine V1-vs-V2 comparison, never V2-vs-itself when both flags happen to be
on. Both estimators are fed every tick the shadow flag is on: whichever one is NOT driving `mem[5]` gets
fed the SAME input its non-shadow counterpart would use (raw whitelisted `dets` for a V1 shadow, tracker-
billed dets for a V2 shadow) -- one billing scan (`_opp_elixir_v2_bill`/`bill_confirmed`, shared whenever
EITHER `opp_elixir_v2` or `opp_elixir_v2_shadow` is on) feeds both, never a second independent tracker
walk. Logged at the EXISTING per-frame `[play]` cadence (no new sink):
`[play] opp_elixir_v2_shadow V1=.. V2=.. diff=.. driving=V1|V2 wall=..`. `mem[5]` and the S1 `_oe` value
are read from `_opp_elx`/`_est` ONLY -- `_opp_elx_shadow`/`_shadow_est` never appear on either of those two
lines (asserted by test, see below). `_opp_elx_shadow.reset()` runs alongside `_opp_elx.reset()` at the
match boundary, guarded on `is not None`.

**CPU cost, measured offline** (synthetic in-process microbenchmark, `icebow/.venv/Scripts/python.exe`, an
8-confirmed-track `TeamTracker`, `pytest`/live capture NOT involved -- see the exact script in this
session's transcript, not saved to the repo since it is throwaway):
- The lock-held billing scan alone (`_opp_elixir_v2_bill`, what runs inside `PerceptionLoop.bill_confirmed`
  's lock): **~1.4 microseconds/call** on 8 live tracks.
- Shadow mode's full added cost per frame (billing scan + a second estimator's `.update()` call, V1's own
  `.update()` costs ~0.3 microseconds/call by comparison): **~2.0 microseconds/frame**.
This is a synthetic microbenchmark (no frame capture, no detector inference, no real perception-thread
contention) -- it measures the estimator/tracker-scan CPU cost in isolation, not any GIL/lock-contention
effect from a real ~10 Hz perception thread also holding the same lock; that combined effect is UNMEASURED
(would need an actual live or engine session, which this ticket must not run). Given the isolated cost is
~4 orders of magnitude below both the ~100 ms perception period and the 1.5 s default `act_period`, it is
not expected to be observable, but that expectation is stated as such, not measured end-to-end.

**Tests** (new, `OppElixirV2ShadowWiring`): flag defaults off (behavioural: `eval()` of the real
`_opp_elixir_v2_shadow = ...` expression against a real loaded `Config`); shadow construction is always the
class OTHER than `_opp_elx`, for both values of `opp_elixir_v2` (behavioural eval, and `None` when the
shadow flag itself is off); the `mem[5]` and `_oe` lines never mention the shadow estimator; the shadow
reset sits with the primary reset (text/ordering pin, documented why); the billing input is shared between
the two flags (text pin -- the shared `if _opp_elixir_v2 or _opp_elixir_v2_shadow:` guard).

### FIX 3 (LOW, tests)

- `test_v1_and_v2_estimators_both_accept_the_billed_det_shape` (a bare `0 <= norm <= 1` check, which both
  classes satisfy UNCONDITIONALLY via their own saturation clamp -- a `_BilledDet` missing `.base`/`.cx`
  would still pass) -> replaced with
  `test_v1_and_v2_estimators_charge_the_billed_dets_own_known_cost`, which asserts the EXACT charge: one
  confirmed `"giant"` det must move `est._opp_spent` by exactly `db.elixir("giant")` and `est._est` by
  exactly `5.0 - cost`, for BOTH classes (giant has no SPAWNS/BODIES entry and no sibling track, so none of
  V2's extra rules change this from V1's plain accounting -- a genuine agreement check, not just "some
  number in range").
- `test_record_my_play_is_unconditional_in_both_modes` (grepped 200 raw characters of source before the
  call site for the absence of `"if _opp_elixir_v2"`) -> replaced with an AST-based check
  (`_RecordMyPlayGuardVisitor`): walks play.py's real parse tree tracking the stack of enclosing `if` TESTS,
  finds the actual (sole) `_opp_elx.record_my_play(...)` call node, and asserts none of its enclosing `if`
  tests mention `_opp_elixir_v2` -- a structural claim about control flow, immune to comment text or
  reformatting around the call site (unlike a fixed-character-window grep).
- The other four `OppElixirV2Wiring` tests: converted two to genuine behaviour by extracting the REAL
  right-hand-side expression from source (a generalised `_rhs_of(name)` helper, same
  extract-then-reconstruct idea as this file's pre-existing `_construction()` for `TeamTracker`) and
  `eval()`-ing it against a controlled namespace: `test_off_path_construction_actually_builds_v1_not_v2` /
  `test_on_path_construction_actually_builds_v2` (real `isinstance` checks against the real classes, for
  both flag values) and `test_the_flag_reads_like_student_opp_elixir_and_really_defaults_to_False`
  (`eval()`s the real `cfg.get(...)` call against a real loaded `Config`, proving config.yaml really leaves
  it unset). `test_student_opp_elixir_is_untouched_and_independent_of_the_new_flag` converted similarly, but
  more pointedly: it `eval()`s the real `_oe = ...` expression in a namespace that DELIBERATELY OMITS
  `_opp_elixir_v2` -- if the code ever came to depend on that name, this raises `NameError` instead of
  silently passing a substring check. Two of the six stayed TEXT PINS, each labelled and justified in the
  test file itself: `test_off_path_update_call_is_unchanged` (no free-standing local variable exists to
  `eval()` the OFF branch's `update()` call against outside `play()` itself) and
  `test_match_reset_clears_the_billed_set_alongside_the_estimator_reset` (a source-ORDERING claim between
  two reset lines, only meaningful in the real per-match reset control flow). The seventh,
  `test_on_path_bills_via_the_shared_tracker_and_reapplies_the_whitelist`, is also left a text/structural
  pin (checks the exact call text plus, via a bounded slice, that no second `TeamTracker(` construction
  appears on the billing path) for the same reason -- documented in the class docstring rather than left
  unexplained.

### FIX 4 (LOW, docs)

Removed the two stale/fragile line-number citations attempt 1 introduced (`play.py:73 ... at :518` and
`~line 200` in the new `bill_confirmed` docstring) -- both replaced with citations by NAME (`_run()`'s own
`self._tracker.tag(...)` call, `TeamTracker.tag`'s assignment) rather than a line number that already drifted
once between attempts. Also corrected the substance the verifier flagged: `_opp_elixir_v2_bill`'s docstring
now states explicitly that on the perception-thread ("fresh") path, the act loop's snapshot of `_team_tracker`
may be UP TO the ~2.0 s staleness ceiling play.py already tolerates for every other perception-fed consumer
(`fresh = age <= 2.0` in `_threat_extra`) -- not a new gap this function opens, but real latency worth
stating rather than implying the tag is always current. Kept the (correct) cross-references to
`pipeline/opp_est_audit.py`'s `tt_bill_dets` (line range) and the `filter_whitelisted_billed_dets`
docstring, unchanged, since the ticket said to.

### Verification run (attempt 2)

`cd icebow && PYTHONPATH=src ../icebow/.venv/Scripts/python.exe -m pytest tests/test_play_tracker_wiring.py
-v` -> **29 passed** (19 from attempt 1 plus 10 new: 5 `PerceptionBillConfirmedLockTests`, 5
`OppElixirV2ShadowWiring`, replacing the 1 weakened test FIX 3 flagged and rewriting
`test_record_my_play_is_unconditional_in_both_modes`).

Wider run: `tests/test_opponent_elixir.py tests/test_opponent_elixir_v2.py tests/test_play_no_cnn.py
tests/test_play_tracker_wiring.py tests/test_live_opponent.py tests/test_perception_with_base_i9.py
tests/test_reaction_and_phantoms.py tests/test_spell_phantom_credit.py tests/test_env_init_attrs.py -q` ->
**163 passed** (covers every test file that imports `clashrl.perception` or `clashrl.opponent_elixir`, plus
this ticket's own two files).

`ast.parse` on both edited files -> syntax OK. `git diff --stat` (icebow/src/clashrl/play.py,
icebow/src/clashrl/perception.py, icebow/tests/test_play_tracker_wiring.py only): 71/92/336 insertions
respectively, 4/0/0 deletions -- no other file touched (`git status --porcelain` on config.yaml,
opponent_elixir.py, replay_mine.py, pipeline/**, hogeq/** all clean).

### Corrected live-path matrix (opp_elixir_v2, opp_elixir_v2_shadow, student_opp_elixir)

| opp_elixir_v2 | shadow | student_opp_elixir | estimator(s) run | -> mem[5] | -> S1 (`_oe`) |
|---|---|---|---|---|---|
| F | F | F | V1 only, raw dets | V1 | None |
| F | F | T | V1 only, raw dets | V1 | V1's `_est` |
| F | T | F | V1 (raw dets) + V2 (tracker-billed, shadow) | V1 | None |
| F | T | T | V1 (raw dets) + V2 (tracker-billed, shadow) | V1 | V1's `_est` |
| T | F | F | V2 only, tracker-billed | V2 | None |
| T | F | T | V2 only, tracker-billed | V2 | V2's `_est` |
| T | T | F | V2 (tracker-billed) + V1 (raw dets, shadow) | V2 | None |
| T | T | T | V2 (tracker-billed) + V1 (raw dets, shadow) | V2 | V2's `_est` |

In every row: `_team_tracker`'s own construction/tagging/aim-assists/threat-identity vectors are untouched;
`record_my_play`/the match-reset call pattern are unconditional (both estimators reset when both exist);
the `detector_cards` whitelist applies to whatever feeds EITHER estimator (raw dets already filtered at the
existing site; tracker-billed dets filtered again on the tracker's output, same relative placement as
`pipeline/opp_est_audit.filter_whitelisted_billed_dets`). Shadow rows add exactly one extra `[play]` log
line per tick and the measured (isolated) ~2 microsecond/frame cost above; they never change `mem[5]` or
`_oe`.

### Exact revert (attempt 2)

`git checkout -- icebow/src/clashrl/play.py icebow/src/clashrl/perception.py
icebow/tests/test_play_tracker_wiring.py` (repo HEAD `ab76edb`, confirmed byte-identical to 3d8ad52 for
both source files) -- or restore byte-for-byte from `scratchpad/gauntlet/L67/opp_fix/backup/play.py.o19.orig`,
`perception.py.o19.orig`, and `test_play_tracker_wiring.py.o19.orig` (all three verified content-identical to
HEAD, CRLF-normalisation aside, before editing began each file). No config default was touched, so simply
never setting `play.opp_elixir_v2` / `play.opp_elixir_v2_shadow` in config.yaml is already a full
behavioural revert without touching code at all.

## Attempt 3

Coordinator: attempt 2 verified and COMMITTED (`b814f5a`, both flags default False, behaviourally identical
to HEAD). Worked from the committed tree (confirmed `git status --porcelain` clean on the three write-set
files before touching anything). Backed up the NEW baseline (attempt-2-as-committed) under
`*.o19.a3.orig` in `scratchpad/gauntlet/L67/opp_fix/backup/` (md5 matches HEAD `b814f5a` exactly, before any
attempt-3 edit) -- the original `*.o19.orig` backups (pre-O19, HEAD `3d8ad52`) are left untouched as the
still-valid original-baseline revert point.

### Unplanned real fix found mid-attempt: three tests were coupled to the LIVE config.yaml

While re-verifying near the end of this attempt, `test_the_flag_reads_like_student_opp_elixir_and_really_
defaults_to_False` FAILED -- `icebow/config/config.yaml` had, mid-session, gained
`play.opp_elixir_v2: true` and `play.student_opp_elixir: true` (owner commit context: "L67bp/L67bo (owner
2026-09-17)... use OpponentElixirEstimatorV2... let the S1 student SEE the estimate" -- the owner turning
THIS EXACT feature on for a real experiment while this ticket's polish pass was still in flight, plus an
unrelated `preview.enabled: false -> true`). Three of this attempt's own "defaults to X" tests
(`test_the_flag_reads_like_student_opp_elixir_and_really_defaults_to_False`, `test_the_shadow_flag_defaults_
off`, `test_the_interval_constant_reads_like_a_neighbouring_cadence_and_defaults_to_10s`) had loaded the REAL
`Config.load()` and asserted against its CURRENT contents -- coupling a unit test to a live, owner-editable
file entirely outside this ticket's write set, something that had not yet been true at the moment each test
was written (config.yaml did not set any of these keys then) but predictably stopped being true the moment
someone else edited that file, unrelated to any defect in this ticket's own code. Fixed by adding `_StubCfg`
(returns the `default` kwarg regardless of section/key, i.e. simulates "key absent") and switching all three
tests to eval() the real expression against `_StubCfg()` instead of a loaded `Config` -- this proves the
CODE's own fallback value, decoupled from the file's current state, so it cannot break again the same way
regardless of what the owner sets in config.yaml next. `config.yaml` itself is untouched by this session (it
is not in the write set and its content is the owner's live decision, not this ticket's to make or revert).

### FIX 1 (the one that matters for a real session) -- rate-limit the shadow log

Confirmed the defect by reading: the shadow print sat directly inside `if _opp_elixir_v2_shadow:` with no
gate at all, so it fired every decision (every `act_period`, ~1.5s by default, or faster whenever a
perception "new enemy commitment" event fires one early, floor `_react_min_gap` 0.3s) -- worse than
"per act-loop frame" in the literal sense (the 6Hz poll loop), but still capable of multiple prints/second
on a busy board over a multi-minute match.

**Existing cadence pattern found and reused** (per the instruction, not invented): `trigger = now - last_act
>= act_period` / `last_act = now`, play()'s own act-loop cadence gate a few dozen lines below the shadow log
site. Added `_opp_elixir_v2_shadow_log_every_s` (code default 10.0s), read via the SAME `cfg.get("play",
<key>, default=...)` shape every neighbouring play() constant uses (e.g. `_react_min_gap` a few lines away)
-- there was no existing periodic-LOG throttle specifically to mirror (searched for `_wall`-based cadences,
count-based `% N == 0` rate limits, and elapsed-time gates throughout play.py; the closest true periodic-log
throttle is the count-based `_student.stats["log_n"] % 10 == 0`, the closest ELAPSED-TIME cadence is
`act_period`'s own gate -- reused the latter's exact `now - last >= period` shape since the ask was
specifically for a WALL-CLOCK-based cadence). `_shadow_log = {"last_t": 0.0, "sum_abs_diff": 0.0, "n": 0}`:
`sum_abs_diff`/`n` accumulate on EVERY decision (not just print ticks, so a 10s-apart pair of prints still
reports the true mean over everything in between); the print itself (both estimates, their diff, and
`mean_abs_diff` since match start) is gated on `now - last_t >= _opp_elixir_v2_shadow_log_every_s`.
`_shadow_log` resets alongside `_opp_bill["billed"].clear()` at the match boundary, so the mean is PER
MATCH, not since process start.

**Tests** (new, `OppElixirV2ShadowLogThrottle`, AST-based since this logic has no free-standing expression
or importable function -- same play()-cannot-be-called caveat as every other class in this file): the
interval constant reads like a neighbouring cadence and defaults to 10.0s (behavioural eval); the
accumulation statements are DIRECT children of the outer `if _opp_elixir_v2_shadow:` block (not nested
inside the throttle gate, i.e. they run every decision) while the `print()` call IS inside the throttle
gate, and there is exactly one of each (AST walk, not a text grep); `last_t` is only ever reassigned inside
the throttle gate (otherwise the throttle could never re-arm); the state reset sits beside the billed-set
reset (text/ordering pin, same reasoning as the file's other reset-ordering tests).

### FIX 2 (verifier-found weak tests)

- `test_mem5_and_s1_lines_never_mention_the_shadow_estimator` (grepped the word "shadow" out of ONE line of
  text) -> REMOVED, replaced with three PROVABLE AST checks: `test_est_is_assigned_only_from_opp_elx_never_
  the_shadow` (every assignment to the name `_est` anywhere in play.py -- there are exactly two, the OFF and
  ON branches -- must reference `_opp_elx` and must NOT reference `_opp_elx_shadow`/`_shadow_est` anywhere
  in its own expression tree), `test_mem5_is_assigned_only_from_est_never_the_shadow` (same style for
  `mem[5]`'s own assignment), `test_oe_is_derived_only_from_opp_elx_never_the_shadow` (same style, eval()-
  able expression, AST-checked). None of these three would pass if `_est`/`mem[5]`/`_oe` were EVER
  reassigned from the shadow estimator under any name or any condition -- unlike the old test, which checked
  one line's literal text and nothing else.
- `test_bill_confirmed_agrees_with_the_unlocked_helper_on_the_same_tracker` (one track, `(base, team)` only)
  -> REPLACED with `test_bill_confirmed_matches_the_unlocked_helper_in_full_order_on_three_tracks`: three
  distinct tracks, the full `(base, cx, gy, team)` tuple, and the exact sequence asserted both ways (locked
  == expected, unlocked == expected, locked == unlocked) -- matching the verifier's own probe. Order matters
  because `OpponentElixirEstimatorV2._cluster_new` consumes its input by popping from the end of whatever
  order it is handed, so a silently reordered billing output would change which points get clustered
  together.

### FIX 3 (accuracy)

**Text-pin count.** Recounted by hand: SIX literal `assertIn`/`assertNotIn` checks against raw `_src()`
text across the O19 test classes (not counting the pre-existing, pre-ticket `PlayTrackerWiring` test),
spread over five tests, not the three attempt 2's docstring named:
`test_off_path_update_call_is_unchanged` (1), `test_on_path_bills_via_the_shared_tracker_and_reapplies_the_
whitelist` (3 -- attempt 2 undercounted this one specifically, treating it as one fact instead of three),
`test_shadow_estimator_is_reset_alongside_the_primary_one` (1), `test_billing_input_is_shared_by_v2_and_
shadow_v2` (1, not previously labelled at all). All five are now individually labelled `TEXT PIN` at their
point of use, and both class docstrings (`OppElixirV2Wiring`, `OppElixirV2ShadowWiring`) state the count and
list every one, with the reason none of them has a free-standing expression to `eval()` (each is a fact
about a multi-statement control-flow block, not a single assignment). `test_match_reset_clears_the_billed_
set_alongside_the_estimator_reset` uses `src.index(...)` + `assertLess` rather than `assertIn`/`assertNotIn`
-- also source-text-dependent and also labelled TEXT PIN, but not counted in the "six" (that count tracks
literal-substring-presence checks specifically, matching how the verifier itself apparently counted).

**Test-count accuracy.** Reported "175 passed" in the attempt-2 handback for a NAMED 10-file subset (every
test file in `icebow/tests/` that imports `clashrl.perception` or `clashrl.opponent_elixir`, grep-confirmed,
plus this ticket's own two files) -- that command and file list were exact and reproduce (see "Verification
run" below: the same 10 files now total 183, +8 for this attempt's new wiring-file tests, exactly accounting
for the delta). It was never a claim about the FULL suite -- the verifier's "29 in the wiring file" matches
what I reported for attempt 2 exactly (my own handback said "19 → 29 tests, all passing"); the verifier's
"1524 in the full suite" is a number I never generated or reported, since I explicitly said in the attempt-2
handback that I started a full-suite background run and STOPPED it early (for an unrelated slow test) rather
than reporting its count. Any reader inferring "175" was meant to describe the full suite would be reading
past what was actually written; noted here so it is not repeated.

### FIX 4 (factual: `_BilledDet` "immutable")

Confirmed the defect: attempt 1/2's `_BilledDet` was a plain `__slots__` class, which does NOT prevent
attribute reassignment (`d.base = "x"` succeeds silently) -- the verifier demonstrated exactly that. Fixed
by making it a real `@dataclass(frozen=True, slots=True)`: reassignment now raises `FrozenInstanceError`,
so "immutable" is literally true rather than aspirational. The property that was ALREADY true and remains
the one `bill_confirmed`'s own correctness actually depends on -- NON-ALIASING (`str()`/`float()` copies at
construction, no shared dict/list with the tracker) -- is now documented explicitly as the load-bearing one,
with frozen-ness as an added, now-genuine guarantee on top. New test (`BilledDetImmutabilityTests`):
reassigning a field raises `dataclasses.FrozenInstanceError` and leaves the original value untouched;
positional construction with the default `team="enemy"` still works unchanged.

### INVESTIGATE -- the 1501 -> 1524 full-suite delta

Done cleanly (two full-suite runs, ~5.5-6 min each, `cd icebow && PYTHONPATH=src
../icebow/.venv/Scripts/python.exe -m pytest tests/ -q --ignore=tests/test_cr_web.py`):

- **With attempt 3's changes** (current working tree): `1 failed, 1504 passed, 21 skipped, 1 warning, 517
  subtests passed in 345.46s`. The one failure, `test_xbow_into_push.py::XbowIntoPushTests::test_the_
  clamped_frontmost_ROW_counts_as_forward`, is UNRELATED (X-Bow row-clamp vs `xbow_front`, nothing to do
  with opponent-elixir/perception) -- confirmed pre-existing by re-running just that file against HEAD
  (below), not something these changes touch or could plausibly cause.
- **Baseline, my three files reverted to HEAD `b814f5a`** (attempt-2-committed; via `git stash push --
  icebow/src/clashrl/play.py icebow/src/clashrl/perception.py icebow/tests/test_play_tracker_wiring.py`,
  confirmed clean with `git status --porcelain` before running, `git stash pop` immediately after to
  restore -- confirmed via `git diff --stat` matching pre-stash exactly and `git stash list` empty
  afterward; tree was never left dirty): `1 failed, 1496 passed, 21 skipped, 1 warning, 517 subtests passed
  in 338.49s`. Same lone `test_xbow_into_push.py` failure, confirmed pre-existing (`pytest tests/test_xbow_
  into_push.py -q` against this exact reverted tree: `1 failed, 18 passed, 15 subtests passed`).

**Delta explained, cleanly, for MY OWN two states**: 1504 - 1496 = **+8 passed**, which is EXACTLY the
wiring file's own growth this attempt (29 -> 37). Zero unattributed tests between "attempt 2 committed" and
"attempt 3" -- every new test in the full suite traces to `test_play_tracker_wiring.py`.

**The ORIGINAL "1501 -> 1524" / "~11 unattributed" question (attempt 1 -> attempt 2)**: NOT fully
reconciled, and said so rather than guessed. My own measured numbers (1496 baseline / 1504 with changes) do
not match either "1501" or "1524" -- expected, since these are DIFFERENT commits/scopes than whatever the
verifier ran (my attempt 1 was never committed to git at all per the attempt-2 kickoff message -- "the lead
reverted your play.py/test edits to HEAD" -- so there is no commit corresponding to a clean "attempt-1
full-suite" state for me to re-run). One CONCRETE, VERIFIED contributing factor, found cheaply (no test run
needed): the concurrent O18 worker's commit (`ab76edb`, landed between my attempt 1 and attempt 2) added
tests to `pipeline/tests/test_opp_est_audit.py` -- a file this ticket never touches, outside `icebow/tests/`
entirely -- `git show 3d8ad52:pipeline/tests/test_opp_est_audit.py | grep -c "def test_"` = 78 vs `git show
ab76edb:...` = 98, i.e. **+20 test functions**, matching that commit's own message ("Worker's '26 new tests'
was 20; total 98 is correct"). This would only appear in a "full suite" count whose SCOPE includes
`pipeline/tests/` alongside `icebow/tests/` -- my own runs (`cd icebow && pytest tests/`) do not, and there
is no repo-root `pytest.ini`/`conftest.py` that would sweep both automatically, so I cannot confirm the
verifier's command included it. +20 also does not equal "~11" on its own. Stopping here per the ticket's own
instruction (a bookkeeping question, not a defect) rather than chasing the exact reconciliation further;
flagging the O18 commit as the most concrete lead found, not a proven full explanation.

**Config.yaml side-observation (not caused by this session)**: after the two full-suite runs, `git status`
showed `icebow/config/config.yaml` modified (`preview.enabled: false -> true`, one line) -- NOT part of
either `git stash` operation (which only ever touched the three named files) and not written by any test or
by me. Given the coordinator's own note that "the engine is BUSY with an experiment" on this machine, this
is almost certainly that separate, concurrently-running process writing to the shared config file, not an
effect of this session's test runs. Left untouched (out of this ticket's write set); noted so it is not
mistaken for something this session did.

### Verification run (attempt 3)

`cd icebow && PYTHONPATH=src ../icebow/.venv/Scripts/python.exe -m pytest tests/test_play_tracker_wiring.py
-v` -> **37 passed** (33 carried from attempt 2 minus 1 removed/replaced weak test plus 5 new: 2
`BilledDetImmutabilityTests`, 3 net new in `OppElixirV2ShadowWiring` replacing the 1 removed weak test, 4
new `OppElixirV2ShadowLogThrottle` -- exact arithmetic: attempt 2 had 29; +2 from splitting the removed
mem5/shadow test into three AST tests (net +2, since 1 was removed and 3 added); +1 from splitting the
bill_confirmed order test (replaces 1, itself unchanged count -- net 0); +2 `BilledDetImmutabilityTests`;
+4 `OppElixirV2ShadowLogThrottle` = 29 + 2 + 0 + 2 + 4 = 37, matching pytest's own collected count).

Named 10-file subset (every test file under `icebow/tests/` importing `clashrl.perception` or
`clashrl.opponent_elixir`, grep-confirmed, plus this ticket's two files): `pytest tests/test_play_tracker_
wiring.py tests/test_opponent_elixir.py tests/test_opponent_elixir_v2.py tests/test_play_no_cnn.py tests/
test_live_opponent.py tests/test_perception_with_base_i9.py tests/test_reaction_and_phantoms.py tests/
test_spell_phantom_credit.py tests/test_env_init_attrs.py tests/test_zone_team_billing.py -q` -> **183
passed** (175 in attempt 2's report + 8 = matches the wiring file's 29->37 delta exactly).

Full suite (`tests/ --ignore=tests/test_cr_web.py`), WITH this attempt's changes: **1504 passed, 1 failed
(pre-existing, unrelated -- see INVESTIGATE above), 21 skipped, 517 subtests passed** in 345.46s.

`ast.parse` and `py_compile.compile` on all three edited files -> OK.

### ACCEPTANCE

- Tests green, exact commands/counts above (37 / 183 / 1504 of 1505 relevant -- see INVESTIGATE for the one
  pre-existing, unrelated failure). Re-confirmed AFTER the config.yaml-coupling fix above, final numbers
  unchanged (still 37 in the wiring file, still 183 in the named subset -- that fix corrected HOW three
  tests check a default, not how many tests exist).
- `git diff --stat` limited to the three write-set files (confirmed after the stash round-trip AND after
  the config.yaml-coupling fix): `icebow/src/clashrl/perception.py | 22 ++-`, `icebow/src/clashrl/play.py |
  38 ++-`, `icebow/tests/test_play_tracker_wiring.py | 247 +++++++++++++++++++++++++++----`. No other
  tracked file in this session's control shows a diff (config.yaml's changes are external -- see above).
- Both flags still default False: `_opp_elixir_v2 = bool(cfg.get("play", "opp_elixir_v2", default=False))`,
  `_opp_elixir_v2_shadow = bool(cfg.get("play", "opp_elixir_v2_shadow", default=False))`, both unchanged
  from attempt 2 (only the new `_opp_elixir_v2_shadow_log_every_s` constant was added, default 10.0, and it
  does nothing when the shadow flag itself is off).
- Shadow path still never drives mem[5]/S1: reproven this attempt with three PROVABLE AST checks
  (`test_est_is_assigned_only_from_opp_elx_never_the_shadow`, `test_mem5_is_assigned_only_from_est_never_
  the_shadow`, `test_oe_is_derived_only_from_opp_elx_never_the_shadow`), replacing the weak one-line grep
  FIX 2 flagged.

### Exact revert (attempt 3)

Note: HEAD moved twice more during this attempt, to `a797ca0` (commit-message-only fix, no code diff) then
`51b0574` (an unrelated experiment chain) -- confirmed all three write-set files are BYTE-IDENTICAL between
`b814f5a` and current HEAD (`git show <rev>:<file> | md5sum` matches for all three), so nothing below is
affected by that drift; `git checkout -- <path>` against current HEAD gives exactly the attempt-2-committed
content either way.

`git checkout -- icebow/src/clashrl/play.py icebow/src/clashrl/perception.py
icebow/tests/test_play_tracker_wiring.py` (current HEAD, content identical to `b814f5a`, attempt-2-
committed) -- or restore
byte-for-byte from `scratchpad/gauntlet/L67/opp_fix/backup/play.py.o19.a3.orig`,
`perception.py.o19.a3.orig`, and `test_play_tracker_wiring.py.o19.a3.orig` (all three md5-verified against
HEAD `b814f5a` before this attempt's edits began, CRLF-normalisation aside). Reverting further, to before
O19 existed at all, still works via the original `*.o19.orig` backups against HEAD `3d8ad52`. No config
default was touched by this session (config.yaml's observed diff is external, see above), so simply never
setting `play.opp_elixir_v2` / `play.opp_elixir_v2_shadow` in config.yaml remains a full behavioural revert
with no code change at all.

**Late update**: HEAD moved once more before this attempt finished, to `0ca20a5` ("enable opp_elixir_v2 and
student_opp_elixir in icebow config (owner request, live test)") -- the owner has now COMMITTED the
config.yaml change flagged above (`play.opp_elixir_v2: true`, `play.student_opp_elixir: true`) for an actual
live trial of this exact feature. Confirmed the three write-set files are STILL byte-identical to `b814f5a`
(unaffected by that commit, which touches only config.yaml), and `git status` on config.yaml is now clean
(the owner's change is committed, not a stray working-tree edit). Per the ticket: engine not booted, live
not run, unit tests only -- this session did neither, and the "revert" instructions above are unaffected by
who else is now using the feature this ticket built.

## STATUS: complete
