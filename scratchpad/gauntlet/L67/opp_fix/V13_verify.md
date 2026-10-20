# V13 — blind verification of O13 (OpponentElixirEstimatorV2 + side-by-side harness) — LEAD TRANSCRIPTION

Verifier role writes nothing to the tree; transcribed by the lead 2026-09-16.

## Attempt 1 — FAIL
- **HIGH:** `summary["v2_params"] = V2_PARAMS` then `json.dumps` — frozensets in `SPAWNS` -> TypeError at the END of a run (all matches run, summary.json/.md/DONE line lost). No test covered serialization.
- **HIGH:** `_RecorderDB` forwarded only `elixir`, so V2's `getattr(db, "speed_tiles")` returned None -> R3 silently OFF inside the harness (the audit would measure a different estimator than the tests).
- MEDIUM: `_TracedMixin` zipped new tracks with cost calls positionally; V2 creates no-charge tracks -> trace rows mis-attributed.
- LOW: same-spot replay within forget_s=6 s = one charge (V1-inherited); golden written into the repo tree; hogeq had no V2 test; v1 ticks.jsonl key order changed.
- PASS: V1 lines 1-132 byte-identical to 64d7eca (both decks); 66 tests, golden captured at test time from `git show`; R1 engine/live/death-spawn forms; R2 body counts (3 skel -> 1, 15 skarmy -> 1, 5 barb -> 1, 6 barb -> 2); all-off == V1 on a 30-update sequence; both variants read the same dets (B's rng drawn once).
- Note (useful): R3 is NOT dead for real speeds — `dt` is time since the track was last seen (up to 6 s), so a bandit unseen 1 s gets radius 0.125. Max DB speed is bats 2.0 tiles/s -> 0.042 at dt=0.25 (floor 0.07 holds for fresh tracks).

## Attempt 2 — PASS_WITH_NOTES
- FIX 1: `_jsonable(V2_PARAMS)` dumps; live dict unmutated; full both-mode summary rebuilt through the real summarize/overcharge/merge functions and dumped; recursive leaf walk clean; every other component is the pre-O13 shape that serialized in the real 100-match run.
- FIX 2: `_RecorderDB.__getattr__` delegation; stub speed 8 through `TrackedEstimatorV2` == bare V2 (1 charge); V1 ledger still records; db restored after update.
- FIX 3: [tombstone live, skeletons far, tombstone dup @0.08] -> one row `skeletons (0.5,0.2) cost 1.0 first_seen`; 3 skeletons in one update -> ONE row. Via V2 `last_new_tracks` (opponent_elixir.py:416-426).
- FIX 4/5/6: 5 s same spot -> 1, 7 s -> 2, honestly named; golden via tempfile, no stray file; hogeq mirror present; v1 ticks key order identical to the 64d7eca writer.
- V1 untouched in both decks; decks identical; protected files unchanged vs 8084aad. Suites 74 + 22.
- Notes (LOW): test module deletes a stray path on import; `_jsonable` doesn't handle numpy scalars (none reach summary); `_RecorderDB.__getattr__` recursion if `_real` unset (not on any harness path).
- Unverifiable until the run: both-mode summary on the engine; trace `estimator` field; real effect sizes of R1/R2/R3.

STATUS: complete (lead transcription)
