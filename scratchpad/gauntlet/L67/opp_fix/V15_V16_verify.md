# V15 (O15, V2.1 rules) and V16 (O16, tracker condition + correlated degrade) — LEAD TRANSCRIPTIONS

Verifier role writes nothing to the tree; transcribed by the lead 2026-09-17.

## V15 — OpponentElixirEstimatorV2 rules R4-R7
- **Attempt 1 — FAIL.** HIGH: R5 budgeted TRACKS not bodies (a 5-body cluster point took one slot) -> a second
  same-base play near a live group absorbed free (skeletons cycled x3 -> 1 billed of 3; barbarians x3 -> 5 of 15).
  MEDIUM: the lead's ticket criterion "3+2 skeletons -> ONE charge" is arithmetically 2 (ceil(5/3)); the worker's
  docstring inherited it. LOW: R4 fires only when the previous sighting is > 0.5 s old (consecutive-frame fast
  movers rely on R3); R7 frees a genuine adjacent second spawner play at 0.10; test count 40 not 41.
- **Attempt 2 — FAIL.** Under-billing closed, fan-out over-billing re-opened: `tr.n` = creation size, never
  decremented -> 4 stayers refreshing an n=5 track + 1 walker = 6 > 5 -> the walker charged (first drift billed
  like V1; skeletons 2 vs 1). Worker's drift test passed only by omitting a member's det.
- **Attempt 3 — PASS_WITH_NOTES.** Occupancy = min(n, dets matched THIS update). Cases (a)-(j) on spec:
  5/5/1/10/10/5/10/10-15-3/5-10/2-1. Fan-out closed; recall-miss return absorbed; new 5-body play beside an
  intact group charged. MEDIUM: same-sample joins did not accumulate (A2/A3/B2/B4 under-billed).
- **Attempt 4 — PASS.** Per-call `pending[group]` counter (opponent_elixir.py:504-517). A2/A3 -> 10, B2 both
  orders -> 10, B4 -> 15, B1 -> 5, C1/C3 -> 2/3, D (R1 catches a witch-labelled spawn) -> 5, E (min cap) -> 10.
  C2 = 2 under the "stale group within r_body absorbs" reading -- by design; spec cannot distinguish an
  all-dropped return from a new play beside it (accepted). All-off == V1 (30 and 300 updates); ablations ==
  V2.0; V1 lines 1-132 == 64d7eca in both decks; decks identical; 59+1 tests per deck.
- Design notes carried (b): R4 is a dropout/burrow fix, not the consecutive-frame fast-mover fix (R3); R7's
  wider free zone; a same-base det inside match_radius of a live track is never charged in any version.

## V16 — harness: B_tt (TeamTracker-confirmed billing) + corr_live_view
- **Attempt 1 — FAIL.** HIGH: `billed_ids` keyed on `id(track_dict)`; freed dicts' addresses recycled ->
  200 sequential tracks billed ONCE (every _tt condition would have reported a spurious under-charge).
  MEDIUM: B_tt is the idealised confirmed-track design, not live's path (play.py:547,558 has no min_hits
  gate on the estimator path and applies detector_cards). LOW: Detection.cls was the stripped base (zone
  rule could never fire); "random walk" wording (FP drift is AR(1)); team marginal thin in the worker test.
  PASS: tracker params literal-equal to play.py:422-441 (own_cards, is_building, spawn_radius .10,
  spawn_window 2.5, enemy_window 4.0, track_radius .12, forget 4.5, motion_min .05, deep_mine .62,
  deep_enemy .38, min_hits 2, phantom_stale 6.0); same det stream for B/B_tt and per corr setting; seeds
  domain-separated (eval/random/oppest_b5/oppest_corrS/oppest_corrL).
  **Corr marginals (verifier's own 200k-sample sim):** SHORT recall .857 fp .130 sigma .448/.450 L_miss 1.49
  L_fp 1.51 rho1 .293; LONG .856/.126/.448/.451, L_miss 4.00, L_fp 8.02, rho1 .798; team unknown .25 / wrong
  .15; team never changes within a track; non-temporal fields identical to live_view; an i.i.d.-equivalent
  config reproduces i.i.d. statistics. Targets met within 0.5% absolute.
- **Attempt 2 — PASS_WITH_NOTES.** `_bill_uid` stamped per track (itertools counter on the tracker; no
  copy/rebuild path in TeamTracker, replay_mine.py:436-510): 200/200, 201/201, expired -> re-billed,
  carried-through-misses -> once. `_wl` siblings filter the same billing event. 12-condition set with both
  flags; flags off == BASE_CONDS / cc4a774 COND_DEFS. raw_cls -> Detection.cls 'poison_aoe', base 'poison'.
  78 tests. Notes: whitelist=None defaults to empty (main() always passes it); uid counter per tracker instance.
- **Unverifiable until the engine run:** the integrated loop under --tracker --corr (hence the smoke arm);
  `ep.cell_center` frame vs Unit.x/y for record_play anchors; hogeq deck path.

STATUS: complete (lead transcription)
