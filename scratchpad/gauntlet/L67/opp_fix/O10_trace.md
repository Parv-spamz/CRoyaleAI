# O10 -- charge-event trace for opp_est_audit

Ticket: instrument (do NOT fix) why continuously-visible units under condition A (perfect detection,
units, no whitelist) get re-billed. Engine is DOWN -- unit tests only, no boot.

## Plan

1. Read pipeline/opp_est_audit.py (O8, TrackedEstimator) and opponent_elixir.py:42-113 in full. DONE.
2. Add `TracedEstimator(TrackedEstimator)` in opp_est_audit.py: overrides `_seen_tracks` to diff
   `self._tracks` before/after the real `super()._seen_tracks(now)` call (captures track EXPIRIES --
   the ticket's two stated options were "override _seen_tracks to diff" or "replicate the filter";
   chose the diff, since it can never drift from the real forget_s filter). `update()` snapshots
   `self._tracks` BEFORE calling `super().update()` (which does the real `_seen_tracks` + matching +
   clustering + charging, unmodified), then identifies newly-appended track dicts by object identity
   (`id()` not in the pre-update snapshot's ids) and zips them against `TrackedEstimator`'s own
   `_RecorderDB` call list (order-preserved 1:1 with `_cluster_new`'s append-then-charge loop) to get
   (base, x, y, cost) per CHARGE with no re-implementation of match/cluster logic.
3. Add a pure `charge_diagnostics()` + `classify_charge_reason()` pair, and a `run_traced_update()`
   orchestrator that ties one `TracedEstimator.update()` call to the previous sample's dets (caller-
   tracked) to produce charge rows + track-event rows. All pure / offline-testable, no engine needed.
4. Wire `--charge-trace` into the CLI + `run_match_audit` (condition A's `est_a` only becomes a
   `TracedEstimator`; other conditions untouched), write `<out>/charges.jsonl` and
   `<out>/track_events.jsonl` only when the flag is set.
5. `chain_opp_trace.ps1`: copy of `chain_opp_est_audit.ps1` with only the specified names + arm changed.
6. Tests: the 3 ticket-specified scenarios (stationary/jump/expire-then-reappear) run `TracedEstimator`
   + `run_traced_update` directly against synthetic `_Det`s -- no engine.

## Reason-classification order (deviation from literal ticket text order, flagged)

The ticket lists reasons in this order: first_seen, split, rebill_after_expiry, rebill_out_of_radius,
other. Implemented evaluation order is **first_seen, rebill_after_expiry, split, rebill_out_of_radius,
other** -- checking expiry BEFORE split. Reasoning: the ticket's own acceptance scenario (c) is "a unit
absent for 7 s then present again" reappearing at (or very near) its OLD position -- which, being
stationary, is *also* <= cluster_radius (0.10) of its own previous-sample detection AND had a live
track before this update. Under the literal a/b/c/d order that scenario would hit "split" first and
never reach "rebill_after_expiry", contradicting the acceptance test's required label. Checking expiry
first resolves the conflict in the direction the acceptance test demands, and is the more causally
correct story (the track was provably just removed this exact update -- cross-checked against
track_events -- vs. a coincidental proximity match). All raw diagnostic fields are kept on every row
regardless, per the ticket's "keep the raw fields so the lead can re-classify."

## Status log

- Read opp_est_audit.py (848 lines) and opponent_elixir.py (132 lines) in full.
- Read existing chain_opp_est_audit.ps1 and test_opp_est_audit.py to match conventions.
- Implemented `TracedEstimator(TrackedEstimator)` (overrides `_seen_tracks` to diff before/after the real
  filter -- the ticket's "diff" option, not "replicate the filter"), plus `charge_diagnostics`,
  `classify_charge_reason`, `run_traced_update` -- all pure/offline, no engine dependency.
  `TrackedEstimator.update()` got one additive line (`self.last_calls = calls`) so TracedEstimator can pair
  new tracks with their (base, cost) 1:1 in `_cluster_new`'s own append order; no other line of
  TrackedEstimator or opponent_elixir.py changed.
- Wired `--charge-trace` into `build_parser`/`main` (opens `charges.jsonl`/`track_events.jsonl` ONLY when the
  flag is set) and into `run_match_audit` (new `charge_trace: bool = False` kwarg; only condition A's `est_a`
  becomes a `TracedEstimator`; A+/A_wl/B untouched either way). `run_match_audit`'s return signature changed
  from `(ticks, summary)` to `(ticks, summary, charge_rows, track_event_rows)` -- the trailing two are always
  `[]` when the flag is off. This is the only public-shape change; its one caller (main()) was updated in the
  same edit.
- Added 6 new tests (TestChargeTraceStationaryFirstSeen, TestChargeTraceJumpRebillOutOfRadius,
  TestChargeTraceExpiryRebillAfterExpiry, TestChargeTraceOffProducesNoTrace,
  TestTracedEstimatorParityWithTrackedEstimator) covering exactly the ticket's three scenarios plus the
  no-behavior-change constraint. Full suite: `python -m unittest pipeline.tests.test_opp_est_audit -v` ->
  **42 passed, 0 failed** (36 pre-existing + 6 new).
- Copied chain_opp_est_audit.ps1 -> chain_opp_trace.ps1, changed only: header comment, `$Log`
  (opp_trace.log), the pids.txt tags (`opp_trace`/`boot_trace`), `status_trace_pre`/`status_stop_trace`,
  `boot_trace.log`/`boot_trace.stderr.log`, `liveness\p38031_trace`, the start `Note` string, and the arm
  (`audit_0_100` -> `trace_0_5`, `--entries 0:100` -> `--entries 0:5 --charge-trace`). `diff -u` against the
  original confirms no other line changed. PowerShell AST parser: 0 errors. `grep -n -- -Wait` on the new
  file: only hit is inside the carried-over comment on line 15 (the trap description itself), zero
  non-comment `Start-Process -Wait`.
- `git status --short pipeline/` -> only `pipeline/opp_est_audit.py` and
  `pipeline/tests/test_opp_est_audit.py`. `git diff --stat` on every protected path
  (icebow/src, hogeq/src, pipeline/e1_eval.py, e1_view.py, obs_contract.py, engine_play.py, e1_pool.py,
  and opponent_elixir.py specifically) -> empty, EXCEPT a pre-existing, unrelated diff in
  `icebow/src/clashrl/replay_mine.py` (17 insertions) that predates this session -- never opened, read, or
  edited by this ticket's work; flagged for the lead's awareness, not caused here.

STATUS: complete
