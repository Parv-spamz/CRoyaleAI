# V8 blind verification of O8 (pipeline/opp_est_audit.py + tests) -- baseline 06dcc6d, uncommitted

VERDICT: FAIL (one goal-level defect in the ATTEMPT-3 over-charge ledger; everything else PASS or NOTE)

## Per-criterion

| # | criterion | result | evidence |
|---|---|---|---|
| 1 | tests | PASS | `icebow/.venv/Scripts/python.exe -m unittest pipeline.tests.test_opp_est_audit -v` -> Ran 20 tests, OK. Vacuity: `test_matches_phase_helper` (test:100-110) derives `expect` with the same if-chain as `phase_from_flags` -- self-referential, never asserts t->phase; no test for `overcharge_table`/`merge_base_ledgers` (my toy run: correct); attempt-3 loop code (run_match_audit:494-504) never ran against the engine (O8_harness.md:358-362). |
| 2 | scale | PASS | opp_est_audit.py:443,447,451 read `._est`; one-off reset(8.0)+update(4-cost musketeer): `update()`->0.4, `._est`->4.0, ledger {'musketeer':[1,4.0]}. |
| 3 | B seeding | PASS | :399 `np.random.default_rng(obs_seed(tag,k))` == e1_eval.py:241 (obs_seed = crc32(f"{tag}:eval:{k}"), e1_eval.py:74-75); `.bit_generator.state` equal for 3 (tag,k); b5_seed (:125-129, domain "oppest_b5") differs from obs_seed and random_seed; 293 held-out tags x k=0..2: 0 obs/b5 seed collisions. :427 routes rng_obs only on policy ticks. ctrl_live100 run.json noise_off=[] -> `Noise()` parity; threads default 2 both. |
| 4 | cadence | PASS (engine byte-state not directly checked) | :421 `is_policy_tick` gates the policy block :456; :489 `env._advance_to(min(env.tick+step, tail_cap))` -> PoolV1Mixin._advance_to (e1_pool.py:523-527) -> EngineMatchEnv._advance_to (engine_env.py:401-414, absolute target, stops on ghost/sched ticks). Extra 5-tick stops call `_fire_ghosts_at` (e1_pool.py:544-579) which only acts when `sched <= tick`, and every sched is itself a stop point -> identical act sequence. Smoke ticks.jsonl: all policy ticks %10==0, inter-policy gap 10 (359/156 gaps); plays_accepted 34/14, decisions 360/157, termination 3681/1656 identical to ctrl_live100 matches.jsonl. |
| 5 | dets | PASS code / NOTE docs | :153 `_TEAM_OF_SIDE` 1->enemy,0->mine,-1->unknown (one-off confirmed); :157-162 no whitelist; estimator filters team!="enemy" (opponent_elixir.py:94). A+ = units+spells (:441), A = units (:446), B = `view.units` (:450). Live = play.py:547 team=="enemy" AND base in detector_cards. Docstring :33-37 claims whitelist "100% troop/building, zero spell entries" and A = "structural live ceiling": CONTRADICTED -- `the_log` is in detector_cards (46 entries), and 4202/12205 (34%) held-out ghost plays are NON-spell bases absent from the whitelist (archer_queen, golem, mega_minion, ...). The module never states that A/B skip the troop whitelist. |
| 6 | metrics | PASS | 6-row toy errs [+1,-2,0,-1,+0.5,+3]: mae 1.25, bias 0.25, p90 2.5 (== np.percentile), share<=1 0.6667; summarize_condition identical. phase: `phase_of(bs)` <- from_engine `_phase(t)` (obs_contract.py:238,324); t=30 single, 150 double, 200 overtime. |
| 7 | ledger | PASS (TrackedEstimator) | one-off costs {a:3,b:5}: after update -> {'b':[1,5.0],'a':[1,3.0]}; repeat sighting within 0.07 -> unchanged; forced saturation (_rebase 2.0, _opp_spent 8->10) -> ledger unchanged. Rebase at opponent_elixir.py:122-129 never calls `db.elixir` -> not attributable, by construction. |
| 8 | per-match record | NOTE | run_match_audit:500-504 builds tag,k,n_ticks,decisions,plays_accepted,outcome,end_tick,unmapped,wall_s,charged_by_base,ghost_played_by_base,over_charge_at_end (crowns computed :493, discarded). Only `plays_accepted_by_match` and `over_charge_at_end_by_match` are PERSISTED (main:614-616); outcome/end_tick/decisions are never written. plays_accepted semantics == e1_eval (n_acc on `r["accepted"]`). |
| 9 | constraints | PASS | `git status --short pipeline/ icebow/ hogeq/`: only the 2 new files plus pre-existing untracked icebow/templates/*ice_wizard_hero*.png (present in the session-start snapshot, not this ticket); `git diff --stat 06dcc6d -- <listed files>`: empty. Imports: repo + numpy only. |

## Findings (ranked)

1. FAIL -- truth side of the over-charge ledger is the SCRIPT, not what the ghost played. `ghost_played_by_base` (:254-278) sums every `entry["ghost_commands"]` row. In ctrl_live100 (100 matches) the script has 3796 plays but only 2429 were delivered (68 refused, 1299 undelivered in 62/100 matches -- matches end before the script does). `over_charge_at_end`, `total_over_charge` and the per-base `over_charge` column (the OPP_EST_AUDIT_DONE headline `A_total_over_charge`) are therefore biased NEGATIVE by ~1/3 of ghost elixir on average, which directly confounds the diagnosis they exist for (attributing a negative bias to over-charging). The env already records the correct per-match truth: `env.ghost_cards_delivered` (Counter by slug, reset per match, e1_pool.py:519,562) -- unused by the harness. `over_charge_share_from_bases_never_played` is also understated (a base delivered 0 times but scripted counts as "played").
2. NOTE (medium) -- Condition A is labelled "structural live ceiling" but live's whitelist also drops 34% of held-out non-spell ghost plays; docstring claim "zero spell entries" is false (`the_log`). Interpretation of A vs live needs this caveat; no condition models the actual whitelist.
3. NOTE (medium) -- `is_opp_play_tick` (:436, threshold drop >= 1.0) misses EVERY 1-cost play: drop = 1 - regen(0.089/0.179/0.268 per 5 ticks) < 1.0. 1613/12205 (13%) of held-out ghost plays cost 1. The `opp_play_ticks` block is a biased subset.
4. NOTE (low) -- per-match outcome/end_tick/decisions/crowns not persisted (criterion 8); lead's fidelity gate can only use plays_accepted.
5. NOTE (low) -- `--max-ticks` help says "TOTAL across the run" but :486 also truncates each match at that many rows, then :493 computes `_outcome` on a non-terminal state. Smoke-only flag.
6. NOTE (low) -- `test_matches_phase_helper` is self-referential; `overcharge_table`/`merge_base_ledgers` untested; attempt-3 loop integration never ran against the engine.

## Not checked
- Engine byte-state equality at tick N via one `_advance_to(N)` vs two 5-tick calls (engine down); evidence is the code path + smoke plays_accepted/decisions/termination-tick equality only.
- Any end-to-end run of attempt-3 `main()` (summary.json/md assembly with `overcharge`), engine down.
- Torch numerical parity across machines/threads beyond the default-2 match.

STATUS: complete

## Attempt 2 (re-verification after worker attempt 4; same two uncommitted files; engine DOWN, not booted)

VERDICT: PASS_WITH_NOTES

| # | claim | result | evidence |
|---|---|---|---|
| 1 | truth ledger = delivered only | PASS | `overcharge_table` has ONE call site, main:788 `overcharge_table(charged_run, ghost_delivered_run)`; `ghost_delivered_run` = main:764 merge of `m["ghost_delivered_by_base"]` (run_match_audit:639 <- `dict(env.ghost_cards_delivered)`). `ghost_scripted_run` (main:765) flows only to `summary["ghost_scripted_by_base"]` (:782). `over_charge_at_end` (:643) uses `ghost_delivered_total` (:640). `merge_base_ledgers` call sites: :764, :765, :787 -- none mixes ledgers. One-off, scripted {knight:2, musketeer:1} / stub env delivered {knight:1}: scripted {'knight':[2,6.0],'musketeer':[1,4.0]}, delivered {'knight':[1,3.0]}; overcharge vs delivered total_over 0.0 (vs scripted would be -7.0). |
| 2 | opp_play_flags from ACCEPTED ghost_events | PASS | :391 filters `int(ok)==1`. e1_pool.py:561 appends `(g["tick"],1,"accepted")` only in the accepted, non-mine branch; :578 appends `(tick,0,name)` on final refusal; engine_env.py:334 resets `ghost_events=[]` inside `reset()`. One-off, samples 30..60 step 5: deliver@40 -> [40]; deliver@43 -> [45]; refused@40 -> []; @40+@43 -> [40,45]; @20 -> [30]; @70 (after last sample) -> no flag (no row exists). Cost-independent by construction (1-cost no longer matters). |
| 3 | per-match persistence | PASS | main:768-771 `matches` rows: tag,k,outcome,crowns_for,crowns_against,plays_accepted,decisions,end_tick,n_ticks -> summary.json (:777) and final JSON line (:832). `outcome`/`crowns_for`/`crowns_against` from `ep._outcome(env,state)` (:635,:646) == e1_eval.py:305,316; `plays_accepted` = n_acc incremented on `r["accepted"]` (:601-602) == e1_eval.py:290-291,324. |
| 4 | A_wl via play.py's Config path | PASS | :238-239 `Config.load(...).get("observation","detector_cards",default=[])` == play.py:376. One-off: `load_detector_cards(deck.config)` == frozenset of the play.py expression, n=46, `the_log` in it. Units [knight(enemy), golem(enemy), golem(mine), golem(unknown)]: A charges {golem:[1,8.0], knight:[1,3.0]} est 0.0; A_wl charges {knight:[1,3.0]} est 7.0 (golem dropped, non-enemy passed through). Four conditions in `conds` (:759-761), labels (:796-799), md loop, DONE line (:834-841). Docstring numbers re-derived from the pool: total 12205, spell 2591, non-spell 9614, out-of-whitelist 4202 -> 4202/12205=0.3443, 4202/9614=0.4371. Matches :123-126. |
| 5 | tests | PASS | `unittest -v` -> Ran 37 tests, OK. Phase test (test:112-118) uses hand-written {30:single,150:double,200:overtime} and an independent `t>=120 / t>=180` derivation. `TestOvercharge.test_overcharge_table_base_never_played_shows_full_charge_as_overcharge` (test:488-502): golemite charged [2,2.0], absent from ghost -> over_charge 2.0, share 0.4. `TestGhostDeliveredByBase` (test:376-388) covers the ticket's {a:2,b:1}/{a:1} case. |
| 6 | constraints | PASS | `git status --short pipeline/ icebow/ hogeq/` (templates excluded): only the two new files. `git diff --stat 06dcc6d -- <protected list>`: empty. HEAD 06dcc6d. New import `clashrl.config.Config` is repo code. |

Notes (none blocking):
- `ghost_events` tick is the SCRIPTED tick, not the accept tick (e1_pool.py:561 records `g["tick"]`; retry sets `sched`, :566, not `tick`). A play retried under elixir-slack flags a sample up to 40 ticks EARLY. Documented at :102-107 and :388-390; magnitude (how many accepted plays were retried) is unknown until the run.
- `PoolV1Env` is constructed without `drive_our_commands` (main:732; default False, e1_pool.py:603), and even when True, our-side commands go to `our_cmd_*`, never `ghost_events`/`ghost_cards_delivered` (e1_pool.py:557-562, 572-574).
- Attempt-4 loop code (run_match_audit:628-653, main:759-842) has not run against an engine; smoke/ directory is still attempt-2 output.

Unverified until the run (engine-facing, cannot be established offline):
- that `env.ghost_cards_delivered` / `env.ghost_events` on the live PoolV1Env hold exactly one match's entries (code says reset per match: e1_pool.py:519, engine_env.py:334) and that slugs there resolve through `_base_of_slug` for every delivered card.
- byte-state equality across 5- vs 10-tick chunking (unchanged from Attempt 1; smoke plays_accepted/decisions/termination-tick equality is the only evidence).
- end-to-end assembly of summary.json/summary.md with four conditions and the `matches` block.

STATUS: complete
