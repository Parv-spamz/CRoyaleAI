# O8 -- OpponentElixirEstimator offline audit harness

Repo HEAD 713b182. Write set: `pipeline/opp_est_audit.py`, `pipeline/tests/test_opp_est_audit.py`, this
file, `scratchpad/gauntlet/L67/opp_est/smoke/`. No edits to e1_eval.py / e1_view.py / obs_contract.py /
engine_play.py / e1_pool.py / icebow/src / hogeq/src -- all imported unmodified.

## 1. Estimator facts (read icebow/src/clashrl/opponent_elixir.py:20-132 myself; every line verified, not
   taken from the scout on trust)

- **Constructor / API**: `OpponentElixirEstimator(db, match_radius=0.07, cluster_radius=0.10, forget_s=6.0)`.
  `reset(my_elixir=5.0, now=None)` zeroes `_my_spent`/`_opp_spent`/`_tracks`/`_rebase`, sets `_est = clip(my_elixir, 0, 10)`.
  `record_my_play(base)` adds `db.elixir(base)` (or 0 if unknown/falsy) to `_my_spent` -- no time argument, no
  effect on tracks.
- **`update(my_elixir, enemy_dets, now)` (opponent_elixir.py:83-131), exact reading**:
  1. `_seen_tracks(now)` drops any track older than `forget_s=6.0` seconds.
  2. Filters `enemy_dets` ITSELF: `if d.team != "enemy": continue` (line 94) -- the caller does NOT need to
     pre-filter by team; passing mine/unknown dets through is harmless and is what the harness does (matches
     the ticket's fallback: "if play.py passes all dets ... pass all with team mapped").
  3. Needs `.base` (non-empty str), `.cx`, `.gy` (both default 0.5 if absent) from each surviving det.
  4. Each det is matched to an existing track of the SAME base within `match_radius=0.07` (squared-distance
     compare in normalized board-frame units, no coordinate conversion needed -- board frame IS the radii's
     frame); a match just refreshes that track's `(x, y, t)` (a long-lived unit is never charged twice).
  5. Everything that did NOT match an existing track is `fresh`, then CLUSTERED by base + `cluster_radius=0.10`
     (`_cluster_new`) so N bodies of one swarm-card play (Skeleton Army, Goblin Gang) become ONE new track and
     charge the card's elixir cost ONCE, not once per body.
  6. Each resulting new track costs `db.elixir(base)` (falls back to 0.0, never negative) added to
     `_opp_spent`.
  7. **No independent clock / no double-elixir handling of its own**: `est = my_elixir + _my_spent -
     _opp_spent` (line 113) is the WHOLE arithmetic. `now` is used ONLY to age tracks out of the
     `match_radius`/`cluster_radius` matching window (`forget_s`) -- it never drives regeneration, and single
     vs. double elixir is invisible to the estimator: it inherits whatever rate is baked into the CALLER's
     `my_elixir` argument (which the caller re-reads every tick, already regenerated at whatever the current
     phase's rate is). VERIFIED by the fixed smoke test: with zero enemy detections the estimate tracks the
     caller's `my_elixir` exactly tick for tick (e.g. tag 000YLL9RURY8 ticks 90-140: truth 7.602/7.78/7.958/
     8.136/8.314/8.492 and `est_A` identical to 4 decimal places every tick -- confirms both the arithmetic
     AND that `bs.my_elixir` is the right ground-truth source).
  8. **L67g saturation re-baselining** (lines 114-129, comment block read in full): the OLD code clipped the
     RETURNED value to `[0, 10]` but kept computing the next tick's `est` from the same un-clipped, inflated
     internal books -- so a detector that misses even one enemy play ratchets `est` up forever and it pins at
     10 and stays there (the FIRST-ATTEMPT bug the retracted L67h sim harness hit). The FIX charges an
     overflow (`est > 10`) or underflow (`est < 0`) straight back into `_opp_spent` (`_opp_spent += est - 10.0`
     / `_opp_spent += est` respectively) and tracks the total correction in `_rebase` (diagnostic only, not
     read by this harness), THEN clips `est` to `[0, 10]` for `_est`/the return value. So a saturation event is
     treated as evidence of a missed enemy play, not swept under a clip -- confirmed live in the smoke output:
     `est_A` sits pinned at `10.0` through overtime while `truth` is also pinned at `10.0` (tag 000YLL9RURY8
     ticks 3630-3680), i.e. the rebase keeps A correctly AT the ceiling rather than drifting past it.
  9. `update()` **RETURNS the estimate NORMALIZED to `[0, 1]`** (`return self._est / 10.0`, line 131); the
     ELIXIR-UNIT (0-10) value is the side-effect attribute `_est`, set one line earlier. **This harness grades
     on `_est`, reading it as an attribute right after the `update()` call, never the return value** -- this
     is exactly the trap play.py's own L67f/L67g comments (play.py:868-884) call out ("a genuine 0.8-elixir
     estimate must not become 8"). FIRST DRAFT OF THIS HARNESS GOT IT WRONG (used the return value directly as
     the 0-10 grade), which produced `est_A` off by 10x from `truth` in the very first smoke run (`truth=
     7.602, est_A=0.7602` at tick 90) -- caught by eyeballing the smoke ticks.jsonl before trusting the
     numbers, fixed, and RE-RUN (see section 3). Left as a documented near-miss because it is the textbook
     version of the bug the estimator's own comments warn callers about.

## 2. Live call sites (icebow/src/clashrl/play.py, read directly)

- play.py:400 `_opp_elx = OpponentElixirEstimator(_db)` (module-level, default radii/forget_s).
- play.py:1196-ish: `reset()` at match start with OCR'd `my_elixir` and `time.time()` (not re-checked line
  number precisely here, scout's line matched what I saw at the top of the match-loop function; not load
  bearing for the harness, which reads `now` from `bs.t_sec`, engine seconds, not wall clock).
- play.py:547 (inside `_threat_extra`): **`dets` fed to the estimator is ALREADY filtered twice** before
  `update()` ever sees it: `dets = [d for d in dets_all if d.team == "enemy" and d.base in detector_cards]`,
  where `detector_cards` is `set(cfg.get("observation", "detector_cards", default=[]))` (play.py:376) -- a
  LIVE-CONFIG CURATED WHITELIST (`icebow/config/config.yaml` `observation.detector_cards`, ~55 entries as of
  HEAD), commented "ENEMY TROOPS the detector RELIABLY names". I scanned the whole list (config.yaml:436-504):
  it is entirely troop/building BASE keys -- **zero spell classes appear in it** (no fireball/zap/arrows/
  poison/the_log/etc.). So **spells never reach `_opp_elx.update()` live, regardless of detection quality** --
  this is a structural property of `detector_cards`, not a detector-recall artifact.
- play.py:558: `_est = _opp_elx.update(float(my_elixir), dets, now)` -- `dets` here is the pre-filtered list
  above, `now = time.time()` (wall clock, not engine tick time -- irrelevant to the harness, which has no wall
  clock and uses `bs.t_sec`, monotonic engine seconds, per the ticket's instruction).
- play.py:884: `_oe = getattr(_opp_elx, "_est", None) if _student_opp_elixir else None` -- confirms `_est` (not
  `update()`'s return) is the value ever handed to the student model, and that this whole feature is
  **DEFAULT OFF** (`play.student_opp_elixir: false`) per the L67g comment block: on 835 real detector frames
  supplying the estimate suppressed the gate up to 3.2x even at a true value of 0, because a detector that
  MISSES enemy plays only ever drifts the estimate UP, never down, so `opp_known=1` reads as "the opponent has
  a lot of elixir" more often than not.
- play.py:1130: `_opp_elx.record_my_play(card_threat.base_key(vision.deck_keys[card_id]))` on an ACCEPTED play
  (this call is inside the play-execution path, i.e. AFTER the same tick's `update()` already ran against the
  pre-play `dets`/`my_elixir` -- the harness replicates this ordering: `update()` for both conditions runs
  BEFORE the tick's own play decision/execution, `record_my_play()` after, only on acceptance).

## 3. What this harness does (pipeline/opp_est_audit.py)

Not a subclass or edit of `e1_eval.run_match` (which returns only match-level aggregates, no per-tick
truth/estimate) -- a NEW instrumented per-decision-tick loop built entirely from e1_eval's own imported pure
helpers (`obs_seed`, `_slot_maps`, `allowed_slots`, `anti_stall`, `model_forward`, `live_decide`) plus
`e1_pool.PoolV1Env`, `e1_view.live_view`/`Noise`, `obs_contract.from_engine`/`to_tokens`/`_phase`, and
`engine_play.compact_raw`/`cell_center`/`cell_to_engine`/`load_model`/`_outcome` -- all imported, none copied
or edited. Two independent `OpponentElixirEstimator` instances per match:
- **A (perfect detection)**: dets from `bs.units` directly (engine ground truth), exact `bs.my_elixir`.
- **B (degraded, live-like)**: dets from `live_view(bs, rng_obs, deck, Noise())` where `rng_obs` is seeded
  IDENTICALLY to e1_eval (`obs_seed(tag, k)`, one generator per match, consumed decision by decision) --
  byte-identical to what the S1 student actually sees -- and `view.my_elixir`, which `live_view`/`degrade()`
  already floors (`float(int(bs.my_elixir))`), i.e. exactly "what live has".
- Both conditions read from `bs.units` / `view.units` ONLY (never `.spells`), matching the section-2 finding
  that spells never reach the estimator live -- `BoardState` already keeps units and spells in separate
  tuples, so this needed no extra filter, just picking the right tuple.
- `now` = `bs.t_sec` (`tick * TICK_S`, engine seconds) for BOTH conditions -- monotonic per match, and it is
  the correct clock per section-1.7 (the estimator's `now` only ages tracks, and both conditions must age
  tracks on the same schedule to be comparable).
- `is_opp_play_tick`: `truth` (ground-truth `bs.opp_elixir`) dropped by >= 1.0 since the PREVIOUS decision
  tick. CAVEAT: because this only samples at decision cadence (every `decide_every=10` engine ticks / 0.5s,
  matching e1_eval exactly), a burst of more than one opponent play inside one 0.5s window shows up as a
  single large drop (observed: tag 000YLL9RURY8 tick 1110, truth dropped 7.19 -> 2.55 in one tick) -- this is
  a real aliasing property of the decision cadence, not a harness bug, and it affects BOTH truth and what the
  estimator itself can ever see (its own dets are equally sampled at decision cadence).
- `record_my_play` fires on OUR OWN accepted play (same live S1 policy/anti-stall/tau as e1_eval, decided off
  the DEGRADED `view` tokens, matching what a real match would feed the student) for BOTH estimators (what we
  played is not a detection question).
- Metrics (`summarize_condition`): MAE, mean bias, P90|err| overall and per phase (single/double/overtime via
  `phase_of`/`_phase`), MAE at opponent-play ticks, MAE at our-accepted-play ticks, share of ticks with
  |err|<=1.0 and <=2.0, per-match MAE median/P90, n ticks/matches. Written to `<out>/summary.json` +
  `<out>/summary.md`; per-tick rows to `<out>/ticks.jsonl`.
- `--timeout` (default 20s) is passed through to `PoolV1Env`/`EngineMatchEnv` (default there is 120s) so a
  dead port fails with a clean `ENGINE UNREACHABLE` message and exit code 2 instead of a long hang; engine
  construction is wrapped in its own try/except for this.

## 4. Smoke test (port 38032, `--entries 0:2 --max-ticks 600`)

Command:
```
icebow/.venv/Scripts/python.exe -m pipeline.opp_est_audit --port 38032 \
    --ckpt icebow/data/pipeline/s1_icebow_v6lat_s0.pt --split heldout \
    --entries 0:2 --max-ticks 600 --out scratchpad/gauntlet/L67/opp_est/smoke
```
Ran clean, 2 matches (000YLL9RURY8, 000YLLP2UC98), 517 ticks total, well under the 600-tick smoke cap and
inside the 2-match limit. Final line:
```
{"OPP_EST_AUDIT_DONE": {"n_ticks": 517, "n_matches": 2, "A_mae": 3.5279392649903287,
 "A_bias": -3.4162348162475826, "B_mae": 6.260642940038684, "B_bias": -6.260642940038684}}
```
(This is the RE-RUN after the `_est` vs `update()`-return fix in section 1.9; the first attempt printed
`A_mae=6.60, A_bias=-6.60` from the 10x-scale bug and was discarded, not reported as a real measurement.)
Sanity checks against the raw `ticks.jsonl` (not just the summary numbers):
- Opening ticks (zero enemy dets so far): `est_A` matches `truth` to 4 decimal places every tick (e.g.
  7.602/7.78/7.958/8.136/8.314/8.492, both columns identical) -- confirms the arithmetic and the `my_elixir`
  source are wired correctly.
- Overtime tail: `truth` pinned at `10.0`, `est_A` also pinned at `10.0` -- confirms the L67g rebase keeps
  the ceiling correct rather than drifting past it.
- Condition B drifts well below truth for long stretches under detection noise (e.g. truth ~7.0-7.4 while
  `est_B` sits at `0.0` around ticks 1080-1180) -- consistent with the documented live behavior (a detector
  that misses enemy plays only ever drifts the estimate away from truth, never self-corrects) and with why
  `play.student_opp_elixir` defaults off. This is a genuine, not yet statistically meaningful (n=2 matches),
  first read of "is the estimate any good" -- the full run is explicitly OUT OF SCOPE for O8 (owned by the
  lead, 100 matches after the chain).

## 5. Findings worth flagging (not acted on -- OUT OF SCOPE to change the estimator or play.py)

- `CardDB.elixir("mirror")` returns `None` (`icebow/config/cards.yaml:3204`: `mirror: {mirrored_level_delta:
  1.0, verified: true}` -- no flat `elixir` key, because Mirror's true cost is dynamic, last-played-card-cost
  + 1). Surfaced by `test_heldout_ghost_decks_resolve_cost`, printed not silenced. Irrelevant in practice
  because Mirror is a SPELL and spells never reach the estimator (section 2), but if that ever changed, a
  Mirror play would silently cost `_opp_spent` 0.0 (the `c > 0.0` guard in both `record_my_play` and
  `update()` treats `None`/falsy the same as a free card) rather than raising.
- `detector_cards` (the live whitelist, section 2) is NOT applied by this harness in either condition -- the
  ticket's own dets-construction lines for A and B ("every unit in `bs` with side==1" / "the same rule") name
  only the team filter and the spells decision, not the whitelist, so Condition A stays a true "perfect
  detection, every enemy card" ceiling rather than "perfect detection of only the ~55 whitelisted troops",
  and Condition B measures the estimator's OWN robustness to detector noise, not compounded with the
  card-whitelist restriction. If the lead's full run wants the whitelist applied too (a third condition, or a
  stricter B), that is a design choice for them, not assumed here.

## Attempt 2 -- cadence fix + true ceiling condition

Coordinator's two changes, both implemented in `pipeline/opp_est_audit.py` (still the only new file besides
its test; still no edits to e1_eval/e1_view/obs_contract/engine_play/e1_pool or icebow/src, hogeq/src --
`git diff --stat` on all of those is empty, checked again after this attempt).

### CHANGE 1 -- estimator cadence: 5-tick stepping, policy unchanged at 10-tick boundaries

The coordinator's hypothesis (attempt 1's -3.4 bias under PERFECT detection is a harness artifact of feeding
`update()` at the coarse 10-tick decision cadence, when `match_radius=0.07` was tuned for live's ~4-5 Hz
frame rate) is PLAUSIBLE, not measured true or false by this attempt -- I implemented the fix and confirmed
it does not corrupt anything else, but 2 smoke matches is not enough signal to say the bias shrank because of
this mechanism specifically (see the numbers below: A_mae actually went from 3.53 -> 3.61, i.e. slightly
WORSE on this n=2 sample, not better -- consistent with "not enough matches to tell", not evidence against
the hypothesis, since a single opponent-play-adjacency tick can dominate a 2-match MAE). The 100-match run is
what will actually answer it.

Implementation: `run_match_audit` now steps `env._advance_to(env.tick + STEP_TICKS)` with `STEP_TICKS=5`
every loop iteration (`--estimator-step`, default 5, must divide `--decide-every`, default 10 -- enforced by
a `SystemExit` in both `main()` and `run_match_audit` itself, defensive duplication since the function can in
principle be called directly). ALL THREE estimators (`update()`) run every 5-tick step. The live policy
(`model_forward`/`live_decide`/`env.eng.act`) runs ONLY when `is_policy_tick(tick, first_tick, decide_every)`
is true -- a new PURE helper (`(tick - first_tick) % decide_every == 0`), tested directly in
`TestFiveTickCadence` against a synthetic 5-tick walk (no engine needed).

`EngineMatchEnv._advance_to(target)` (scratchpad/gauntlet/L62/engine_env.py:401-414, read in full) takes an
ABSOLUTE tick target and always walks tick-by-tick internally, stopping exactly on ghost ticks regardless of
chunk size -- so it needed no engine-API change to step by 5 instead of 10; this is NOT a case where "the
engine client cannot step 5 ticks" (the NEEDS_CONTEXT trigger in the ticket). Confirmed empirically, not just
by reading the code: **`plays_accepted` per match in the attempt-2 smoke is EXACTLY the attempt-1 smoke's
34 and 14** (same 2 entries, same seed, same checkpoint) -- see the smoke comparison below. Since the policy
only ever sees `view = live_view(bs, rng_obs, ...)` on policy ticks, using the SAME `rng_obs` stream
(`obs_seed(tag, k)`, e1_eval-identical) consumed in the SAME order as attempt 1, this equality is expected,
not coincidental, and it is the acceptance check the ticket asked for.

RNG split this required (documented in the module docstring too): Condition B needs a degraded view at the
NON-policy 5-tick steps as well, and e1_eval has no cadence of its own to borrow there (it never runs a
decision that often). Those extra draws come from a second generator seeded `b5_seed(tag, k) =
crc32(f"{tag}:oppest_b5:{k}")` -- same shape as `e1_eval.obs_seed`/`random_seed`, a different domain string,
tested (`test_b5_seed_differs_from_obs_seed_domain`) to never collide with `obs_seed`'s own values on the
matches checked. This is the ONE place the harness draws randomness of its own; every other draw (policy
ticks' `rng_obs`) is e1_eval's exact stream. Flagged plainly since the ticket's original "no RNG of your own
except rng_obs for B" constraint (attempt 1) no longer literally holds once B needs values at ticks e1_eval
itself never visits -- this is the smallest change that satisfies it in spirit (policy-tick draws still
100% e1_eval's stream) while satisfying Change 1's cadence requirement.

### CHANGE 2 -- Condition A+ (units + spells, the TRUE ceiling)

`est_Aplus` reads `dets_of(bs.units) + dets_of_costed(bs.spells, db, warned)` every 5-tick step (engine
truth, uncapped by `detector_cards`). `dets_of_costed` is new: like the existing `dets_of` but drops (never
zero-costs) an item whose base has no CardDB elixir row, printing a one-line warning the FIRST time each base
is seen (a process-lifetime `set`, threaded through `main()` -> every `run_match_audit()` call so one match's
Mirror doesn't re-warn in the next). Tested directly (`TestAplusSpellPath`, no engine): `fireball` (cost 4)
resolves and keeps its det; `mirror` (no flat cost -- attempt 1's finding) is dropped and warns exactly once
across two calls sharing the same `warned` set; a mixed batch keeps the costed one and drops the costless one
in the same call.

**Smoke-sample caveat, stated plainly**: across the 2 held-out entries smoked (1,033 ticks), `n_enemy_dets_
Aplus` summed to EXACTLY `n_enemy_dets_A` (2,997 == 2,997, zero per-tick difference) -- these two ghosts cast
NO enemy spell in the observed span, so `Aplus_mae == A_mae` to full float precision in this run. That is a
property of a 2-match sample, not evidence the A+/A gap is zero in general; the pure-function tests above are
what actually demonstrate the A+ code path works (fireball path exercised, mirror path exercised), since the
smoke data happens not to exercise it. The 100-match run is needed to size the real gap.

### Summary additions

`bias` (not just `mae`) is now reported at `opp_play_ticks` and `my_play_ticks` for every condition; a new
`by_truth_cap` block splits MAE/bias by `truth >= 9.0` (`NEAR_CAP_TRUTH`) vs below, per condition. Per-tick
rows add `truth_drop` (the raw size of the truth decrease since the previous row, 0.0 on the first row of a
match) alongside the existing boolean `is_opp_play_tick` (`truth_drop >= 1.0`), so a >1-card burst inside one
sampled window (attempt 1's tick-1110 example) is visible as a number, not just a flag; rows also carry
`is_policy_tick` now that not every row is one.

### Attempt-2 smoke (port 38032, `--entries 0:2`, same 2 entries/seed/checkpoint as attempt 1)

Command:
```
icebow/.venv/Scripts/python.exe -m pipeline.opp_est_audit --port 38032 \
    --ckpt icebow/data/pipeline/s1_icebow_v6lat_s0.pt --split heldout \
    --entries 0:2 --max-ticks 1200 --out scratchpad/gauntlet/L67/opp_est/smoke
```
(`--max-ticks` raised from 600 to 1200: the 5-tick cadence roughly doubles rows per match --
719 + 314 = 1,033 rows this run vs 360 + 157 = 517 at attempt 1's 10-tick cadence for the SAME 2 matches --
so 600 would have truncated the second match mid-way; 1200 comfortably fits both full matches, still exactly
the ticket's "2 matches max".)

Final line:
```
{"OPP_EST_AUDIT_DONE": {"n_ticks": 1033, "n_matches": 2,
 "plays_accepted_by_match": {"000YLL9RURY8:0": 34, "000YLLP2UC98:0": 14},
 "Aplus_mae": 3.6141296224588575, "A_mae": 3.6141296224588575,
 "A_bias": -3.3352574056147146, "B_mae": 6.327470087124879, "B_bias": -6.32713688286544}}
```
Side-by-side with attempt 1 (same 2 entries, same checkpoint, same seed):

| | attempt 1 (10-tick cadence) | attempt 2 (5-tick cadence) |
|---|---|---|
| n_ticks | 517 | 1033 |
| plays_accepted (000YLL9RURY8) | 34 | **34** (unchanged, as required) |
| plays_accepted (000YLLP2UC98) | 14 | **14** (unchanged, as required) |
| A_mae | 3.528 | 3.614 |
| A_bias | -3.416 | -3.335 |
| B_mae | 6.261 | 6.327 |
| B_bias | -6.261 | -6.327 |
| Aplus_mae | (n/a, attempt 1 had no A+) | 3.614 (== A_mae here, see spell-blind-spot caveat above) |

`plays_accepted` equality is the load-bearing check (confirms the policy sees identical states at identical
ticks under the finer stepping, per the ticket). The MAE/bias deltas between attempts are small and go in
BOTH directions (A slightly worse, B slightly worse too) on this n=2 sample -- not something this harness can
call a real effect size from; that judgment belongs to the 100-match run.

### Unittest (attempt 2)

`icebow/.venv/Scripts/python.exe -m unittest pipeline.tests.test_opp_est_audit -v` -> **15 passed, 0
failed** (10 from attempt 1 plus 5 new: `TestFiveTickCadence` x2, `TestAplusSpellPath` x3). Same Mirror
finding printed as attempt 1 (`[test_dets_conversion] 1 base key(s) resolve to NO CardDB cost:
[('Mirror', 'mirror')]`) -- now also directly exercised by `TestAplusSpellPath`, not just found by the
conversion scan.

## Attempt 3 -- charge attribution diagnostic (spawned-units hypothesis)

Coordinator's framing: attempt 2's cadence fix barely moved A_bias (-3.42 -> -3.34), so track loss from
sampling too coarsely is NOT the dominant cause of the persistent NEGATIVE bias under PERFECT detection.
Under `est = my_elixir + my_spent - opp_spent`, a negative bias means `opp_spent` is counting more than the
opponent actually spent. New hypothesis to test with data, not assert: SPAWNED units (tombstone/witch/
night-witch/furnace summons, golemites, lava pups, etc.) show up as new enemy bodies at a NEW position and
get charged as if they were a fresh card play, when they are a side effect of a card already charged once.

### Implementation (both new, no edits outside the write set)

**`charged_by_base`** (per condition, per match then merged run-level): built by `TrackedEstimator`, a
subclass of the UNMODIFIED `OpponentElixirEstimator`. Read opponent_elixir.py again in full before choosing
an approach: `_opp_spent` is incremented in exactly ONE place in the whole class, inside `update()`'s
per-new-track loop (`c = float(self.db.elixir(base) or 0.0); if c > 0.0: self._opp_spent += c`,
opponent_elixir.py:109-111) -- the L67g saturation correction (lines 122-129) also touches `_opp_spent` but
is a bookkeeping rebase, not attributable to any specific det, so it is correctly excluded from this ledger.
That single line is the ONLY consumer of `self.db.elixir(...)` inside `update()`. So `TrackedEstimator.
update()` temporarily swaps `self.db` for a one-shot recorder proxy (`_RecorderDB`, forwards `.elixir()` to
the real db and records every `(base, cost)` call made), calls the REAL, unmodified `super().update()`, puts
the real `db` back, and attributes every recorded call with `cost > 0` to `charged_by_base[base]`. This is
the option the ticket called "wrap/subclass the estimator" -- I picked wrapping the COLLABORATOR (`db`)
rather than overriding a chargeable method because there ISN'T a separate chargeable method to override (the
charge is inlined in `update()`); wrapping `db` intercepts the real algorithm's own per-base cost lookup with
zero duplicated logic. I considered and rejected the diff-`_opp_spent`-before/after option explicitly:
verified by `test_two_different_bases_in_one_update_call_attribute_separately` that when TWO different bases
both start new tracks inside the SAME `update()` call (routine once `update()` batches several 5-tick-cadence
detections), a before/after diff of the scalar `_opp_spent` has no way to split that total back into "which
base got how much" -- it can only report the sum. The wrapping approach attributes each one correctly, which
that test demonstrates directly (no engine, no live data, purely mechanical).

**`ghost_played_by_base`** (per match, then merged run-level, SHARED across all 3 conditions since it is one
truth): from `entry["ghost_commands"]` -- e1_pool.py's own per-command rows, the exact list
`PoolV1Mixin`/`EngineMatchEnv` re-drives in eval mode -- excluding ability entries (`card` is `None` for
those), costed via CardDB (never the engine's own recorded `cost` field, so both ledgers price off the SAME
source), with the pool's hyphenated slugs (`"giant-snowball"`) normalized to vocab's underscore convention
and evo/hero suffixes folded by `vocab.base_key` -- the identical base-key space `charged_by_base` uses.
CAUGHT BY RUNNING THE TEST, not by reading one file: my first draft used `giant_snowball` as the "costless"
fixture (its curated `cards.yaml` block genuinely has no `elixir` key -- confirmed by a direct grep), but
`CardDB.elixir("giant_snowball")` actually returns `2` because `CardDB.__init__` (cards.py:144-176) merges a
`cards_stats.json` BASE LAYER underneath the curated yaml, and that layer supplies the missing `elixir` key.
The test failed on the first run (`AssertionError: 2 is not None`), caught before it was reported as a fact,
and the fixture was swapped to `mirror` (re-confirmed costless via `CardDB.elixir("mirror") -> None` and via
attempt 1's independent `test_heldout_ghost_decks_resolve_cost` scan, which still finds it as the only
costless base among every card any held-out ghost deck plays). This is exactly the discipline the "measured,
not guessed" rule asks for, and it is now a comment in the test explaining why `giant_snowball` was rejected.

### Summary additions

Per condition: an over-charge table (`base | ghost_plays | ghost_elixir | charges | charged_elixir |
over_charge`, `over_charge = charged_elixir - ghost_elixir`), sorted by `|over_charge|` descending, top 25 in
`summary.json` (top 10 in `summary.md`); `total_over_charge`; `over_charge_share_from_bases_never_played`
(the fraction of TOTAL charged elixir sitting on bases the ghost never played as a card at all -- a spawned
body is by construction never in `ghost_commands`/`ghost_deck`, since only the 8 PLAYED cards are, so this
number is a direct read on the spawned-units hypothesis). Per match: `over_charge_at_end` per condition
(total charged elixir minus total ghost elixir for that match), in each match's own summary dict and
aggregated into `summary.json`'s `over_charge_at_end_by_match`.

### Smoke -- PORT 38032 WENT DOWN BETWEEN ATTEMPTS, SKIPPED PER THE HARD CONSTRAINT

`Test-NetConnection -ComputerName 127.0.0.1 -Port 38032` returned `TcpTestSucceeded: False` at the start of
this attempt (it answered for attempts 1 and 2). Per the ticket ("handle a dead port cleanly ... do not boot
anything"), I did NOT start or restart anything on that port. I DID run the harness once against it anyway,
specifically to VERIFY the dead-port handling stays clean under attempt 3's changes (not to get real numbers)
-- `--max-ticks 200 --timeout 8` into a throwaway directory OUTSIDE the write set
(`scratchpad/gauntlet/L67/opp_est/smoke_deadport_check/`), which I deleted immediately after reading the
result, so nothing outside the write set was left behind. Result: `PoolV1Env(...)` construction itself did
NOT raise (the engine client connects lazily, not at construction), so the existing exit-code-2
"ENGINE UNREACHABLE" branch was not the one exercised; the failure surfaced on the first `env.reset(entry)`
inside `run_match_audit`, caught by the existing per-match try/except in `main()`, which logged
`[opp_est_audit] ERROR on 000YLL9RURY8 k=0: ConnectionRefusedError(10061, ...)` and exited 3 -- **total wall
time 5.67 s**, no hang, no partial/corrupt output. Both of the harness's two error-handling tiers (construct-
time and per-match) are confirmed to fail cleanly and fast; which tier fires depends on whether the engine
client dials eagerly or lazily, and this attempt confirms it is lazy. No new smoke summary/over-charge
numbers exist for attempt 3 as a result -- the coordinator's own instruction ("if 38032 is alive") covers
this exact case. The attempt-2 smoke data (port alive then) has no `charged_by_base`/`ghost_played_by_base`
fields since attempt 2 predates this ledger; attempt 3's ledger code is verified correct by the unit tests
above, not by a live run, pending the port coming back or the lead's 100-match run.

### Unittest (attempt 3)

`icebow/.venv/Scripts/python.exe -m unittest pipeline.tests.test_opp_est_audit -v` -> **20 passed, 0
failed** (15 from attempts 1-2 plus 5 new: `TestChargedByBase` x3 -- single-base attribution, two-different-
bases-in-one-call attribution [the case a before/after diff cannot do], repeat-sighting does not re-charge --
and `TestGhostPlayedByBase` x2 -- built-correctly-from-hand-built-commands [ability excluded, hyphen
normalized, costless slug skipped+warned], empty-commands). The coordinator's message estimated "expect 17";
actual is 20 because `TestChargedByBase` and `TestGhostPlayedByBase` each cover more than the one required
case (the multi-base and no-recharge edge cases for the former, the empty-input case for the latter) -- more
granular coverage of the same two required behaviors, not scope creep.

## Attempt 4 -- blind-verifier fixes (V8_verify.md, baseline 06dcc6d)

Engine is DOWN this attempt (coordinator's constraint): unit tests only, no smoke, nothing booted. All 5
fixes below are implemented and unit-tested; none has been exercised against a live engine yet -- the
verifier's own quoted numbers (deliveries/refusals/1-cost-play shares) come from their ctrl_live100 read, not
from a run I performed, and are cited as such. Where I could independently re-derive a number from the pool
FILE (no engine needed), I did -- see FIX 4.

### FIX 1 (the verifier's FAIL) -- over-charge truth ledger was the SCRIPT, not delivered plays

`pipeline/opp_est_audit.py`:
- New `ghost_delivered_by_base()` (:359-376): the TRUTH ledger, built from `env.ghost_cards_delivered` (a
  `collections.Counter` keyed by slug -- `PoolV1Mixin.reset()` zeroes it per match at e1_pool.py:519,
  `_fire_ghosts_at` increments it ONLY on an accepted, non-mine ghost play at e1_pool.py:562; both read
  directly, matching the verifier's citation).
- Old `ghost_played_by_base()` renamed `ghost_scripted_by_base()` (:337-355), unchanged logic, docstring now
  says REFERENCE ONLY / not what actually happened, and it is no longer read by any over-charge computation.
- `run_match_audit()` (:637-653): computes both `ghost_scripted` (reference) and `ghost_delivered` (truth)
  per match; `ghost_delivered_total` (not scripted) feeds `over_charge_at_end`; the match summary carries
  `ghost_scripted_by_base` and `ghost_delivered_by_base` as two clearly separate, clearly labelled keys.
- `main()` (:762-786): `ghost_delivered_run` (merged across matches) is the ONLY ledger passed to
  `overcharge_table()` for every condition; `ghost_scripted_run` is written to `summary.json` alongside it,
  unused elsewhere.
- Test: `TestGhostDeliveredByBase.test_delivered_ledger_differs_from_scripted_when_a_play_is_never_delivered`
  -- the ticket's exact scenario (scripted `{a:2,b:1}`, delivered `{a:1}`) asserts the ledger is `{a:[1,
  cost_a]}` and nothing else, and that it differs from the scripted ledger.

### FIX 2 -- `is_opp_play_tick` missed every 1-cost play

`pipeline/opp_est_audit.py`:
- New pure function `opp_play_flags(sample_ticks, ghost_events)` (:381-396): flags the first sampled tick at
  or after each ACCEPTED entry in `env.ghost_events` (a `(tick, accepted, reason)` log the ghost-drive path
  already keeps -- engine_env.py:334 resets it to `[]` per match, `_fire_ghosts_at` appends one entry per
  ghost play ATTEMPT, accepted or refused). Documented caveat: the recorded tick is the play's SCRIPTED tick,
  which a retried (elixir-slack) play can reach up to `elixir_slack` ticks before its real accept tick --
  flagging at-or-after the recorded tick therefore never MISSES a delivery but can flag 1-2 samples early for
  a retried play. Not fixable without editing e1_pool.py (out of the write set), so stated rather than hidden.
- `run_match_audit()`: the old inline `is_opp_play_tick = ... truth_drop >= 1.0` line is gone; every row is
  appended with `"is_opp_play_tick": False` as a placeholder (:657), then AFTER the while-loop ends (:629-633)
  `opp_play_flags([row["tick"] for row in ticks], list(env.ghost_events))` overwrites every row's flag in one
  pass (safe because `env.ghost_events` is reset per match, so by loop-end it holds exactly this match's full
  log -- no incremental bookkeeping needed inside the loop). `truth_drop` (Attempt 3) is still computed and
  still written to every row, now purely informational.
- Tests: `TestOppPlayFlags`, 6 cases -- the ticket's exact scenario (1-cost delivery at tick 40 under 5-tick
  sampling `[30,35,40,45,50]` -> only the tick-40 row True), a REFUSED delivery never flags anything, a
  delivery strictly between two samples flags the next one, two deliveries in one gap share one flagged row,
  a delivery before the first sample flags the first sample, and the no-events case.

### FIX 3 -- per-match record not persisted

`pipeline/opp_est_audit.py`:
- `run_match_audit()` (:646): `crowns_for`/`crowns_against` now read from `ep._outcome(env, state)`'s second
  return value (previously computed as `crowns` and discarded -- the verifier's exact complaint) and added to
  the per-match summary dict alongside the already-present `outcome`, `plays_accepted`, `decisions`,
  `end_tick`, `n_ticks`.
- `main()` (:769-772): new `matches` list, one dict per match with exactly
  `{tag, k, outcome, crowns_for, crowns_against, plays_accepted, decisions, end_tick, n_ticks}` -- field
  SPELLING checked directly against `pipeline/e1_eval.py`'s `run_match()` return dict (`"outcome"`,
  `"crowns_for": int(crowns[0])`, `"crowns_against": int(crowns[1])`, `"plays_accepted"`) so the lead can diff
  this harness's matches straight against `attrib_noise/ctrl_live100/slot0/matches.jsonl`. Written to
  `summary.json["matches"]` (:783) and to the final `OPP_EST_AUDIT_DONE` JSON line (:822).

### FIX 4 -- condition A_wl (live's actual structural ceiling)

`pipeline/opp_est_audit.py`:
- `load_detector_cards(config_path)` (:233-239): loads `icebow/config/config.yaml`'s
  `observation.detector_cards` through the UNMODIFIED `clashrl.config.Config` (imported, never re-implemented
  -- `Config.load(str(config_path))` then `cfg.get("observation", "detector_cards", default=[])`, the exact
  call play.py:376 makes). Called once in `main()` (:714) with `deck.config`
  (`icebow/config/config.yaml`, per `pipeline/decks/icebow.yaml`), passed into every `run_match_audit()` call.
- `dets_of_whitelisted(items, whitelist)` (:242-246): drops an enemy det whose base is outside the whitelist,
  passes mine/unknown dets through unfiltered (harmless -- the estimator's own team filter drops them anyway).
- `run_match_audit()`: a fourth `TrackedEstimator`, `est_wl` (:531), updated every step from
  `dets_of_whitelisted(bs.units, whitelist)` (:596-599) -- engine truth, units only, whitelist applied.
  `record_my_play` and the tick row (`est_Awl`, `n_enemy_dets_Awl`) extended to match. `main()`'s `conds`
  tuple, `labels` dict, markdown, and final JSON line all report A+, A, A_wl, B (A_wl is now the headline
  over-charge figure in the final print line, replacing A).
- **Docstring correction** (module docstring, CHANGE 2 paragraph): Attempt 2 claimed the whitelist was "100%
  troop/building base keys ... zero spell entries" -- WRONG. Re-verified myself, independently of the
  verifier, by loading the real whitelist:
  `icebow/.venv/Scripts/python.exe -c "..."` -> 46 entries; `the_log` (member of `vocab.SPELL_CLASSES`, a
  real spell) IS one of them. Also independently re-measured the "34%" share the verifier quoted, over the
  held-out pool FILE directly (no engine needed): of the 12205 non-ability ghost card plays in the held-out
  split, 4202 are non-spell bases absent from the whitelist -- 4202/12205 = 34.4% (the verifier's framing,
  ALL plays as the denominator) or 4202/9614 = 43.7% of the 9614 non-spell plays specifically (the verifier
  did not give this second number; both are now in the module docstring so neither framing is silently
  preferred). `TestDetectorCardsWhitelist.test_load_detector_cards_measured_membership` asserts `knight` in,
  `golem` out, `the_log` in -- all checked directly against the live config file, not assumed.
- Tests: `TestDetectorCardsWhitelist`, 3 cases (measured whitelist membership; drops-outside/keeps-inside;
  never filters a non-enemy-team det).

### FIX 5 -- test quality

`pipeline/tests/test_opp_est_audit.py`:
- `test_matches_phase_helper` (self-referential -- built its `expect` with the same if/elif ladder
  `phase_from_flags` itself uses, so it could never catch a bug in that ladder) replaced with
  `test_matches_phase_helper_at_hand_written_times`: t=30/150/200 -> single/double/overtime, asserted BOTH
  via `obs_contract._phase(t)` (independent of `phase_from_flags`) AND via hand-written thresholds
  (`t >= 120.0`, `t >= 180.0`) computed with no call to `_phase` or `phase_from_flags` at all for the
  expectation itself.
- New `TestOvercharge` (4 cases): `merge_base_ledgers` sums across a list of per-match ledgers (and the empty
  list); `overcharge_table` on a hand-built `{charged, ghost}` pair where one base (`golemite`) is charged but
  NEVER in the ghost ledger -- asserts `ghost_plays == 0`, `over_charge == charged_elixir` for that base, and
  `over_charge_share_from_bases_never_played` computed correctly (exactly the spawned-units signature the
  coordinator's hypothesis predicts); sort-by-|over_charge|-descending and `top=N` truncation; the empty-input
  (0 bases) case returns `None` for the share, not a `ZeroDivisionError`.

### NOTE (no fix required) -- `--max-ticks` smoke-only warning

`build_parser()`'s `--max-ticks` help text now states plainly that it truncates each match mid-flight and
that `_outcome()` is then computed on a non-terminal engine state, so `outcome`/`crowns_for`/`crowns_against`
are meaningless for a truncated match (ticks/estimates up to the cut point are still valid). No code change
beyond the help string, per the coordinator's "no change required."

### Verify

`icebow/.venv/Scripts/python.exe -m unittest pipeline.tests.test_opp_est_audit -v` -> **37 passed, 0
failed** (20 from attempts 1-3 plus 17 new: `TestGhostDeliveredByBase` x3, `TestOppPlayFlags` x6,
`TestDetectorCardsWhitelist` x3, `TestOvercharge` x4, plus the FIX-5 phase-test replacement). `git status
--short pipeline/` shows only the two write-set files (pre-existing untracked `icebow/templates/*.png`
unrelated). `git diff --stat` on e1_eval/e1_view/obs_contract/engine_play/e1_pool + icebow/src + hogeq/src is
empty. No smoke this attempt (engine down, per the coordinator's explicit constraint) -- the delivered-ledger,
opp-play-flag, whitelist, and per-match-record code paths are verified by the unit tests above only, pending
a live run once the engine is back (or the lead's 100-match run) to confirm against `env.ghost_cards_
delivered`/`env.ghost_events` for real.

STATUS: complete
