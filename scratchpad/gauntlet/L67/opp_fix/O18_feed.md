# O18 -- feed the opponent-elixir ESTIMATE into the policy's observation, measure winrate

Repo `C:\Users\benpe\ClashBot`, HEAD `3d8ad52` at ticket start. Engine DOWN throughout -- unit tests only,
no commits, no engine runs performed by this worker. O19 is concurrently editing
`icebow/src/clashrl/play.py` + config; this ticket never opened either file for writing (confirmed below).

## 1. Read-first: `run_match_audit`'s existing loop and where the policy's observation is built

`pipeline/opp_est_audit.py::run_match_audit` (line 1141) mirrors `e1_eval.run_match`'s while-loop. Per
engine step (`STEP_TICKS`, default 5 ticks):

1. `bs = from_engine(...)` -- the tick's ENGINE-TRUTH BoardState (`bs.opp_elixir` exact).
2. `view = live_view(bs, rng_obs if pol_tick else rng_obs_b5, deck, Noise())` -- the STANDARD degraded
   view every mode computes identically. `Noise()` (all switches True, the default) degrades
   `opp_elixir` to `None` (`e1_view.py`'s `_degrade_switchable` line 168: `bs.opp_elixir if not
   noise.opp_elixir else None`) -- this is why the pre-O18 policy never sees opponent elixir.
3. Per active base condition (`Aplus/A/A_wl/B[/B_tt/B_tt_wl/B_corrS.../B_corrL...]`), per estimator
   variant: `est.update(my_e, dets, bs.t_sec)` (line 1347) -- EVERY estimator, including the
   tracker-input, whitelist-filtered `B_tt_wl`/`B_corrL_tt_wl` V2 estimators when `--tracker`/`--corr`
   are set, is updated with THIS sample's dets before anything else happens this iteration.
4. `if pol_tick:` (line 1366) -- only on the original 10-tick decision boundaries -- the policy is
   consulted: `tok, mask, sc = to_tokens(view, MAX_U)` (pre-O18) built the model's input tokens
   straight from `view`. This is the ONE place the policy's observation is constructed.
5. On an accepted play, `record_my_play` is called for every (base, variant) estimator (line 1391),
   from `d["play"]`/`r["accepted"]` alone -- see section 4 below, this is untouched by O18 and already
   ran in every mode before this ticket.

**Conclusion driving the design**: the only line that needs to change is #4's `to_tokens` input. Every
other line (dets computation, estimator updates, record_my_play, our own decision logic) is
untouched -- exactly what the ticket's causal-injection requirement needs.

## 2. What was added (write set: `pipeline/opp_est_audit.py`, `pipeline/tests/test_opp_est_audit.py`)

Two new pure functions, both unit-tested with no engine:

- `feed_condition_key(feed_noise)` -> `"B_tt_wl"` for `"live"`, `"B_corrL_tt_wl"` for `"corrL"`.
- `policy_view_for(view, bs, feed_opp_elixir, feed_noise, estimators)` -> the EXACT BoardState now
  handed to `to_tokens`:
  - `"off"` (default): returns `view` **unchanged, same object** (`is` identity, not just equal
    fields) -- zero behaviour change.
  - `"true"`: `replace(view, opp_elixir=float(bs.opp_elixir))` -- engine ground truth for this tick,
    equivalent to `e1_eval --noise-off opp_elixir`.
  - `"estimated"`: `replace(view, opp_elixir=float(estimators[(feed_condition_key(feed_noise), "v2")]
    ._est))` -- the live-reachable V2.1 tracker-input-whitelisted estimate.
- `validate_feed_config(feed_opp_elixir, feed_noise, tracker, corr, estimator)` (line 1062) -- the
  legality checks (estimated needs v2 + `--tracker`; `--feed-noise corrL` additionally needs `--corr`),
  called BOTH from `run_match_audit` (so a library caller can never skip it) and from `main()` right
  after argparse (line ~1387, before connecting to the engine or loading the checkpoint) -- a
  misconfigured invocation fails in milliseconds, not after burning a match.

**Injection site** (line 1371, immediately before line 1372's `to_tokens` call, inside `if pol_tick:`):

```python
policy_view = policy_view_for(view, bs, feed_opp_elixir, feed_noise, estimators)
tok, mask, sc = to_tokens(policy_view, MAX_U)
```

`estimators` is the SAME dict `run_match_audit` already builds and updates every sample (line ~1240);
no new estimator instances are created for O18 -- `"estimated"` mode reads the condition that was
already computing exactly this design (module docstring O16(a)/(b): `B_tt_wl`/`B_corrL_tt_wl`, V2.1
rules, TeamTracker-confirmed tracks filtered through `detector_cards`).

### Causality

The estimator-update loop (line 1333-1347, EVERY base including `B_tt_wl`/`B_corrL_tt_wl`) runs once
per engine step, unconditionally, BEFORE the `if pol_tick:` branch (line 1366) that calls
`policy_view_for`. Since `pol_tick` is itself one of those same steps, an `"estimated"` read at line
1371 reflects THIS SAMPLE's `update()` call and every earlier one -- never a later sample, because no
later sample has executed yet at that point in the loop. `policy_view_for` itself does no
caching/memoisation (it just reads `estimators[key]._est` at call time) -- the causality guarantee is a
property of WHERE `run_match_audit` calls it, not of the function hiding a stale value.

Verified by `TestFeedOppElixirCausality` (test file): a real (not mocked) `TrackedEstimatorV2` is
`update()`'d at tick T, `policy_view_for` is called immediately after (mirroring the loop's own
ordering) and its value captured, then the estimator is `update()`'d AGAIN with a later, different-base
det engineered to move `_est` -- the captured tick-T value is asserted unaffected, and the estimator's
new `_est` is asserted to have actually moved (so the test cannot pass vacuously). A second test
(`test_est_is_read_at_call_time_not_snapshotted_earlier`) confirms `policy_view_for` has no memo: called
again after a further update it picks up the new value -- proving the earlier test's causality result
comes from the CALL ORDER in `run_match_audit`, not from any freezing inside the helper.

### `--feed-noise` observation identity

`view` (the thing `policy_view_for` starts from) is built ONCE per sample by the SAME `live_view(bs,
rng_obs, deck, Noise())` call regardless of `feed_opp_elixir`/`feed_noise` (line ~1156, unchanged by
O18). `feed_noise` only selects which key `policy_view_for` reads `._est` from
(`feed_condition_key`) -- it never touches `view`. `policy_view_for("estimated", ...)` only ever calls
`replace(view, opp_elixir=X)`, a `dataclasses.replace` that changes exactly one field. So for a fixed
seed, `policy_view_for(view, bs, "estimated", "live", est)` and `policy_view_for(view, bs, "estimated",
"corrL", est)` are `replace(view, opp_elixir=None)`-equal on EVERY OTHER field, by construction (not
merely by not having found a counterexample).

Verified by `TestFeedNoiseObservationIdentity.test_live_and_corrl_share_every_field_but_opp_elixir`: two
estimator stubs with DELIBERATELY DIFFERENT `._est` values feed 'live' and 'corrL'; the test asserts (a)
`opp_elixir` genuinely differs between the two outputs (so the test isn't vacuously true), and (b) EVERY
other field is equal via full dataclass equality (`replace(out, opp_elixir=None) == ...`), including
nested `units`/`towers` tuples.

### `record_my_play` in all modes -- confirmed, cited

Line 1391 (`estimators[(base, variant)].record_my_play(base_key)`) sits inside the `if bool(r["accepted"
]):` branch that follows the model's decision, and is reached identically regardless of
`feed_opp_elixir`/`feed_noise` -- those flags only change what `to_tokens` (line 1372) is fed, never the
branching logic that leads to line 1391. This was already true before O18 (the loop's own play-acceptance
bookkeeping is independent of the observation build); O18 did not need to and did not touch it.

## 3. `chain_opp_feed.ps1`

`scratchpad/gauntlet/L67/e1/chain_opp_feed.ps1` (new) -- copied structurally from the reviewed
`chain_opp_est_v21.ps1` template (same `Note`/`Run-Worker`/`Run-Audit`/`Stop-Engine` functions, same
boot/liveness preamble, same traps: no `Start-Process -Wait`, no in-script scoring, boot only via
`L63/s0/_boot.ps1`). `$A = "$E1\opp_feed"`, `$Log = "$E1\opp_feed.log"`, pids file
`pids_feed.txt`, boot/status/liveness files suffixed `_feed`.

Arms (all `--estimator v2 --tracker`, port 38031):

| # | name | entries | flags | guarded? |
|---|---|---|---|---|
| 1 | gate_off10 | 0:10 | `--feed-opp-elixir off` | yes -- missing summary.json -> Note + Stop-Engine + exit 2 |
| 2 | gate_true10 | 0:10 | `--feed-opp-elixir true` | yes -- same guard |
| 3 | feed_est_s1 | 0:100 | `--feed-opp-elixir estimated --feed-noise live` | no |
| 4 | feed_estL_s1 | 0:100 | `--feed-opp-elixir estimated --feed-noise corrL --corr` | no |
| 5 | gate_off10_s2 | 100:110 | `--feed-opp-elixir off` | no |
| 6 | gate_true10_s2 | 100:110 | `--feed-opp-elixir true` | no |
| 7 | feed_est_s2 | 100:200 | `--feed-opp-elixir estimated --feed-noise live` | no |

Only arms 1 and 2 are guarded, per the ticket text ("After arm 1 AND arm 2 ..."); arms 3-7 run in
sequence regardless, each logging its own pass/fail via `Note` (matching the template's own pattern for
its non-smoke arm).

Parser check (evidence, this session):
```
$tokens=$null; $errors=$null
[System.Management.Automation.Language.Parser]::ParseFile('...\chain_opp_feed.ps1', [ref]$tokens, [ref]$errors)
# -> PARSE_OK (0 errors)
```
`grep -n -- '-Wait'` on the file: only the comment line (copied from the template) mentions `-Wait`; no
executable use. `grep -niE 'outcome|winrate|crowns_for'`: only comment lines describing what the module
itself reports -- no in-script scoring.

## 4. Reporting additions (`pipeline/opp_est_audit.py::main`)

`summary.json` gains:
- `"winrate"`: `{"n", "wins", "winrate", "winrate_entry_weighted"}` -- `winrate_entry_weighted` is
  `pipeline.e1_score.cluster_bootstrap` (imported, NEVER re-implemented) over each `matches[i]["tag"]`'s
  per-seed wins, the SAME entry-clustered percentile-bootstrap shape `e1_score.summarise` uses. Falls
  back to `{"n", "wins", "winrate", "note": "..."}` if `pipeline.e1_score` cannot be imported for any
  reason -- never fails the run over a reporting extra.
- `"feed_opp_elixir"` / `"feed_noise"`: which arm this run is, for the lead's own scoring/joins.

`OPP_EST_AUDIT_DONE`'s condensed line gains `feed_opp_elixir`, `feed_noise`, `winrate`, `wins`, `n`.
Every existing estimator-accuracy field (per-condition MAE/bias/overcharge, `matches`,
`plays_accepted_by_match`, etc.) is untouched.

## 5. Acceptance evidence

**(a) `--feed-opp-elixir off` + `--feed-noise live` byte-identical to HEAD, stub-driven.** Not testable as
a literal byte-diff of `summary.json` without the engine (this ticket ran no engine matches) -- the new
`"winrate"`/`"feed_opp_elixir"`/`"feed_noise"` summary keys are unconditional REQUIRED additions (ticket
section 2), so `summary.json` itself necessarily gains keys even in `"off"` mode. What IS proven,
stub-driven: `policy_view_for(view, bs, "off", "live", {})` returns `view` BY IDENTITY (`assertIs`), so
`to_tokens`'s input -- and therefore the policy's decision, `plays_accepted`, `outcome`, per-tick
`est_*` columns -- are unchanged from before O18 for every existing invocation
(`TestPolicyViewForOff.test_off_returns_view_object_unchanged`,
`test_off_ignores_feed_noise_and_empty_estimators`). CLI defaults confirmed directly off `build_parser()`
(`test_cli_defaults_are_off_and_live`: `feed_opp_elixir == "off"`, `feed_noise == "live"`). CONCERN: an
actual live-vs-HEAD `matches.jsonl`/`summary.json` diff needs the engine and is the lead's job per the
ticket's ACCEPTANCE section.

**(b) stub test proving injection reaches the policy.** `TestPolicyViewForTrue`/`TestPolicyViewForEstimated`:
`"true"` -> `out.opp_elixir == bs.opp_elixir` exactly, all other fields untouched; `"estimated"` ->
`out.opp_elixir == estimators[(key, "v2")]._est` exactly (both `feed_noise` keys tested,
`_FakeEst` stubs with distinct values so no accidental pass); `"off"` -> `None` (via the standard
degraded `view`). Missing-condition and bad-mode inputs raise `SystemExit`.

**(c) causality test.** `TestFeedOppElixirCausality` -- see section 2 above; a later sample provably
moves `_est` (test would fail vacuously otherwise) while the earlier captured value is unaffected.

**(d) `--feed-noise corrL` changes ONLY the estimator's input.** `TestFeedNoiseObservationIdentity` --
see section 2 above; every field but `opp_elixir` identical between the two `feed_noise` outputs for the
same `view`, while `opp_elixir` itself is proven to actually differ (non-vacuous).

**(e) unittest green; git status; protected files; parser check; no `-Wait`; no in-script scoring.**
- `icebow/.venv/Scripts/python.exe -m unittest pipeline.tests.test_opp_est_audit -v` -> **98 tests, OK**
  (0 failures, 0 errors; 26 of the 98 are new to O18: `TestPolicyViewForOff` x3,
  `TestPolicyViewForTrue` x2, `TestPolicyViewForEstimated` x5, `TestFeedNoiseObservationIdentity` x1,
  `TestValidateFeedConfig` x7, `TestFeedOppElixirCausality` x2; existing 72 pre-O18 tests still pass
  unmodified, confirming no regression).
- `git status --short pipeline/` -> `M pipeline/opp_est_audit.py`, `M pipeline/tests/test_opp_est_audit.py`
  only.
- `git diff --stat` on every protected file (`e1_eval.py`, `e1_view.py`, `obs_contract.py`,
  `engine_play.py`, `e1_pool.py`, `opponent_elixir.py`, `replay_mine.py`, `play.py`, `config.yaml`) ->
  ONLY `play.py` shows a diff, and it is O19's own concurrent, pre-existing change (this worker never
  opened `play.py` or `config.yaml` for writing -- confirmed by session history: neither file was ever
  passed to Read/Edit/Write in this session).
- Parser check on `chain_opp_feed.ps1`: `PARSE_OK`, 0 errors (section 3).
- No non-comment `-Wait`; no in-script scoring (section 3, grep evidence).

## 6. Deviations from a literal ticket reading (flagged, not silently taken)

- The ticket's acceptance (a) asks for "byte-identical to HEAD" summary keys/values; section 5(a) above
  explains why that is read as "the injection path changes nothing" rather than "summary.json gains zero
  new keys," since the ticket's own section 2 REQUIRES the new winrate keys unconditionally. Flagged
  rather than silently resolved either way.
- `validate_feed_config` is a new small factored-out function (not explicitly named in the ticket) so
  `main()` can fail fast before touching the engine, in addition to `run_match_audit`'s own check --
  a scope-preserving addition (still inside the two write-set files), not a new public surface the ticket
  didn't ask for elsewhere.

STATUS: complete
