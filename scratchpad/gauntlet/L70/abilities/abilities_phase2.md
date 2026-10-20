# Ability press policies, phase 2

Status: DONE_WITH_CONCERNS. These are press-intent policies learned against reconstructed board states, not observed pro board states or engine-accepted activations.

Timing calibration fails to match pro-context press shares: direct frame sampling over-presses by 6.8-25.2 percentage points. Cadence correction still leaves 3.7-20.1 points of over-pressing. These results do not establish pro-like simulated timing.

Audited 14,818 recording files; 14,661 unique replay tags; 40,421 recorded press intents. Held out 2,933 replay tags (20%, rounded up). Both sides of a replay and all recording duplicates stay together.

Neither icebow/.venv nor research/ext/Royale/.venv has scikit-learn or scipy. Fit uses icebow NumPy on CPU (one BLAS thread); inference imports only NumPy and the standard library.

Press counts below mean uniquely attributed, alive-context intents while proxy charges remained. Raw is the attributed log count before contextual filtering. Calibration uses the same held-out visible deployments for simulated and pro-context columns. Delays are FIRST-press medians; Boss Bandit all-press medians/repeat shares are in phase2_metrics.json.

| Ability | Raw / context presses | Model | AUC / log-loss | Three strongest features (+ raises press probability) | Pressed: sim / pro-context / phase 1 | Delay s: sim / pro-context / phase 1 |
|---|---:|---|---|---|---|---|
| archer-queen | 1,608 / 1,494 | logistic | 0.842 / 0.284 | - enemy crown tower farther away; - enemy unit farther away; + more enemy HP within 5 tiles | 88.7% / 79.3% / 79.6% | 7.0 / 11.0 / 10.7 |
| balloon-hero | 2,215 / 2,167 | logistic | 0.707 / 0.240 | - enemy building/tower farther away; + in the enemy half; + enemy crown tower farther away | 61.4% / 41.4% / 37.2% | 6.0 / 6.8 / 6.9 |
| barbarian-barrel-hero | 979 / 919 | logistic | 0.809 / 0.207 | - enemy building/tower farther away; - enemy crown tower farther away; - later after deployment | 39.3% / 21.0% / 19.8% | 4.0 / 4.3 / 5.0 |
| berserker-hero | 7,912 / 7,330 | logistic | 0.822 / 0.177 | - enemy building/tower farther away; + more enemy HP within 5 tiles; + more owner elixir | 42.0% / 25.2% / 28.6% | 4.8 / 5.4 / 5.0 |
| boss-bandit | 473 / 395 | logistic | 0.792 / 0.349 | - enemy crown tower farther away; + higher HP fraction; + in the enemy half | 89.1% / 76.1% / 61.8% | 7.8 / 9.2 / 9.8 |
| bowler-hero | 1,320 / 1,233 | logistic | 0.819 / 0.131 | - enemy crown tower farther away; - in the enemy half; - more enemy HP within 5 tiles | 55.3% / 35.0% / 32.6% | 10.4 / 12.2 / 12.4 |
| dark-prince-hero | 460 / 420 | logistic | 0.847 / 0.094 | + in the enemy half; - enemy building/tower farther away; - enemy crown tower farther away | 32.8% / 17.8% / 15.7% | 10.0 / 12.4 / 11.1 |
| giant-hero | 773 / 730 | logistic | 0.813 / 0.087 | - enemy unit farther away; - more enemies within 5 tiles; + higher HP fraction | 35.3% / 19.3% / 18.0% | 9.6 / 9.5 / 7.8 |
| goblins-hero | 687 / 611 | logistic | 0.655 / 0.275 | - enemy crown tower farther away; - later after deployment; - more owner elixir | 44.6% / 24.9% / 26.5% | 9.3 / 9.5 / 9.6 |
| goblinstein | 1,772 / 1,688 | GBT depth 3 | 0.772 / 0.153 | - enemy unit farther away; + more owner elixir; - enemy crown tower farther away | 55.6% / 32.1% / 37.8% | 7.6 / 7.6 / 7.5 |
| golden-knight | 3,356 / 3,189 | logistic | 0.717 / 0.360 | - enemy crown tower farther away; + more enemies within 5 tiles; - later after deployment | 90.2% / 70.6% / 71.4% | 3.8 / 5.8 / 4.8 |
| ice-golem-hero | 320 / 310 | logistic | 0.843 / 0.092 | - later after deployment; - enemy crown tower farther away; + in the enemy half | 18.6% / 10.8% / 11.4% | 4.0 / 3.4 / 3.5 |
| knight-hero | 1,501 / 1,392 | logistic | 0.701 / 0.085 | - enemy building/tower farther away; + in the enemy half; - later after deployment | 24.2% / 12.2% / 13.4% | 7.0 / 6.7 / 6.8 |
| little-prince | 255 / 229 | logistic | 0.713 / 0.131 | - enemy crown tower farther away; - later after deployment; + more owner elixir | 33.7% / 25.1% / 22.3% | 6.8 / 12.1 / 8.3 |
| magic-archer-hero | 232 / 211 | logistic | 0.827 / 0.079 | + more owner elixir; - enemy crown tower farther away; - later after deployment | 20.4% / 13.6% / 15.5% | 6.3 / 8.5 / 7.5 |
| mega-minion-hero | 717 / 657 | logistic | 0.636 / 0.104 | - enemy unit farther away; - more enemies within 3 tiles; - more enemies within 5 tiles | 35.9% / 16.8% / 19.8% | 7.9 / 7.7 / 8.0 |
| mighty-miner | 4,913 / 4,640 | logistic | 0.740 / 0.174 | - enemy crown tower farther away; + enemy building/tower farther away; + more enemies within 5 tiles | 56.5% / 34.5% / 40.5% | 7.9 / 9.6 / 8.9 |
| mini-pekka-hero | 1,212 / 1,069 | logistic | 0.820 / 0.160 | - enemy crown tower farther away; + enemy building/tower farther away; - higher HP fraction | 44.7% / 29.5% / 27.8% | 9.3 / 11.3 / 10.9 |
| monk | 467 / 442 | logistic | 0.750 / 0.340 | - enemy building/tower farther away; + enemy crown tower farther away; + in the enemy half | 88.1% / 72.9% / 59.2% | 4.8 / 6.5 / 6.8 |
| musketeer-hero | 674 / 624 | logistic | 0.782 / 0.100 | - enemy crown tower farther away; + enemy building/tower farther away; + more owner elixir | 31.9% / 19.3% / 16.7% | 12.2 / 13.6 / 12.2 |
| skeleton-king | 2,023 / 1,914 | logistic | 0.773 / 0.218 | + in the enemy half; - enemy crown tower farther away; + higher elixir multiplier | 73.1% / 49.0% / 51.3% | 7.8 / 10.4 / 10.3 |
| tombstone-hero | 490 / 192 | logistic | 0.833 / 0.220 | + more owner elixir; + higher HP fraction; + later after deployment | 18.7% / 10.2% / 20.1% | 12.8 / 10.1 / 10.6 |
| valkyrie-hero | 2,574 / 2,449 | GBT depth 3 | 0.806 / 0.189 | + more owner elixir; - enemy building/tower farther away; - enemy crown tower farther away | 61.7% / 36.5% / 33.0% | 5.2 / 6.4 / 5.7 |
| wizard-hero | 1,057 / 996 | logistic | 0.768 / 0.251 | - enemy crown tower farther away; - later after deployment; - enemy unit farther away | 69.2% / 47.9% / 51.3% | 4.0 / 3.8 / 4.8 |

## Recording evidence

- research/sandbox_tools/replay_drive.py:149-156 reads attr_ability, creates ability, and records no card/position for presses.
- research/sandbox_tools/replay_drive.py:333-334 preserves @hero/@evolution in final_decks.
- research/sandbox_tools/replay_drive.py:349-356 writes tick, elixir, entities and towers; column seven in full entity snapshots is kind, not id. Names map back to base cards (lines 58-65), so hero form at each spawn is not preserved.
- research/sandbox_tools/replay_drive.py:374-386 records periodic observations, splitting each advance into record_every chunks; cadence also shortens around play ticks.
- research/sandbox_tools/replay_drive.py:400-403 logs ability presses as card=_invalid, skipped="ability plays not driven by this version"; it does not call env.act for them.
- research/sandbox_tools/replay_drive.py:404-407 writes play_frames before ordinary card actions; there are no ability play_frames in this version.
- research/sandbox_tools/replay_drive.py:109 defines ability_exhausted=1014; lines 412-431 record ordinary card-action outcomes. That result name alone is NOT evidence of an ability-button press.

Fallback threshold: all 24 abilities have at least 150 retained contextual press intents; no phase-1 fallback activated.

## Dataset and evaluation contract

Every unique periodic frame with exactly one living matching controller is retained in the sequence NPZ. Training eligibility is a separate mask. Features use only that frame and an earlier accepted matching card deployment. No future frames, final scores, or future HP enter the features. Periodic snapshots at a press tick precede the skipped action; labels use inclusive [tick, tick+20]. A press can label multiple overlapping windows. The final second without a known positive is right-censored. Ambiguous ability-source deployments are excluded from training and calibration. Rejected card deployments never create a new deployment. Rejected explicit ability attempts, if present, are counted but not positive labels.

Composite-card controller matching uses level-scaled max HP from research/ext/Royale/RoyaleSim/data/derived/cards.json: Goblinstein doctor 282 base HP (721 at level 11), Hero Goblins flag 1000 (2560), and Tombstone passive controller 207 (529). Tombstone and its passive controller share max HP and name, so simultaneous matches remain excluded; lone skeletons never qualify. The Hero Goblins flag is untargetable and is excluded from enemy combatant counts. Building offspring are separated from their parent building by max HP. Recordings lacking unique controller identity remain unavailable rather than receiving invented features.

Single-use availability follows earlier historical intent, including intents that lack a matching frame. Golden Knight is single-use. Boss Bandit allows two intents, separated by the catalog 3s cooldown. Frames after actual intent remain in sequence files for counterfactual timing simulation. A unique deck candidate attributes the raw intent; with several deck candidates, exactly one must be alive in a frame no more than 20 ticks earlier. An ability press only counts as contextual when that same deployment has a unique living match within that second and proxy availability, and its deployment is not censored by another unresolved press. The 150-press threshold uses this retained count.

Coordinates are divided by 1000. Entity crown towers are excluded from enemy-unit aggregates and added once from towers. Catalog building names classify ordinary buildings; missing targets get 40 tiles. Crown difference is computed from current tower HP, with a fallen king worth three crowns. Enemy half uses y>16000 for side 0 and y<16000 for side 1. match_phase is 0/1/2/3 for 0-60/60-120/120-180/180+ seconds. elixir_multiplier uses the standard 1/2/3 schedule before 120/240/after 240 seconds; mode-specific schedules are not recorded.

Logistic regression standardizes features on training replays only, with L2 penalty 1 and no class weighting/downsampling. An optional 20-tree depth-3 NumPy GBT is chosen only if the inner replay-validation log-loss improves at least 5% AND AUC improves at least 0.01. Selection uses 64% train / 16% validation; the winner is refit on 80%. The final 20% is never used for model choice, scaling, or calibration tuning. Logistic feature signs are standardized coefficients. Tree signs are average +/-0.5-SD probability effects on validation frames; nonlinear effects may change sign locally.

For fewer than 150 contextual presses, the fallback estimates a smoothed one-second time-by-phase hazard from phase-1 compact deployments and attributed first presses. Held-out recording tags are excluded from that phase-1 fit. Exposure ends at next deployment, last event, or the phase-1 p95 lifetime proxy. Multi-candidate active deployments are conservatively omitted. Sparse phase-age cells shrink to the pooled age hazard; no board coefficients are claimed. The lifetime cap itself comes from the pre-existing phase-1 aggregate and is not independently refit.

Seeded simulation draws Bernoulli(p) at every recorded living frame, stops at first firing (and allows a second charge for Boss Bandit), with SHA256-derived per-deployment seeds. It runs over complete recorded visible sequences, not sequences stopped by the historical first press. No threshold/intercept was fitted to the test timing results. phase2_metrics.json also reports a cadence-corrected sensitivity simulation, using 1-(1-p)^dt for intervals below one second. A one-second forecast applied at subsecond frames over-presses; direct p is the requested primary check.

## Observed positive contexts

These are held-out positive-window medians, not causal rules or fitted cutoffs. Signs in the main table describe the actual model.
- archer-queen: positive frames typically have nearest enemy at 5.0 tiles, HP 78%, 0.0 enemies within 3 tiles, age 10.9s and elixir 6.0.
- balloon-hero: positive frames typically have nearest enemy at 4.5 tiles, HP 89%, 0.0 enemies within 3 tiles, age 6.5s and elixir 3.9.
- barbarian-barrel-hero: positive frames typically have nearest enemy at 2.8 tiles, HP 69%, 1.0 enemies within 3 tiles, age 4.0s and elixir 5.1.
- berserker-hero: positive frames typically have nearest enemy at 2.4 tiles, HP 64%, 1.0 enemies within 3 tiles, age 5.1s and elixir 6.4.
- boss-bandit: positive frames typically have nearest enemy at 2.4 tiles, HP 76%, 1.0 enemies within 3 tiles, age 10.7s and elixir 5.3.
- bowler-hero: positive frames typically have nearest enemy at 13.7 tiles, HP 96%, 0.0 enemies within 3 tiles, age 12.0s and elixir 6.9.
- dark-prince-hero: positive frames typically have nearest enemy at 2.7 tiles, HP 61%, 1.0 enemies within 3 tiles, age 12.0s and elixir 5.1.
- giant-hero: positive frames typically have nearest enemy at 2.4 tiles, HP 78%, 1.0 enemies within 3 tiles, age 8.9s and elixir 3.8.
- goblins-hero: positive frames typically have nearest enemy at 4.6 tiles, HP 98%, 0.0 enemies within 3 tiles, age 9.2s and elixir 4.9.
- goblinstein: positive frames typically have nearest enemy at 6.0 tiles, HP 100%, 0.0 enemies within 3 tiles, age 7.4s and elixir 5.2.
- golden-knight: positive frames typically have nearest enemy at 4.8 tiles, HP 85%, 0.0 enemies within 3 tiles, age 5.6s and elixir 4.4.
- ice-golem-hero: positive frames typically have nearest enemy at 2.2 tiles, HP 71%, 1.0 enemies within 3 tiles, age 3.0s and elixir 4.8.
- knight-hero: positive frames typically have nearest enemy at 3.1 tiles, HP 67%, 0.0 enemies within 3 tiles, age 6.4s and elixir 4.4.
- little-prince: positive frames typically have nearest enemy at 6.0 tiles, HP 100%, 0.0 enemies within 3 tiles, age 12.1s and elixir 6.0.
- magic-archer-hero: positive frames typically have nearest enemy at 3.7 tiles, HP 79%, 0.0 enemies within 3 tiles, age 8.5s and elixir 6.3.
- mega-minion-hero: positive frames typically have nearest enemy at 7.0 tiles, HP 100%, 0.0 enemies within 3 tiles, age 7.0s and elixir 5.5.
- mighty-miner: positive frames typically have nearest enemy at 2.8 tiles, HP 76%, 1.0 enemies within 3 tiles, age 9.4s and elixir 6.1.
- mini-pekka-hero: positive frames typically have nearest enemy at 5.9 tiles, HP 44%, 0.0 enemies within 3 tiles, age 11.1s and elixir 3.9.
- monk: positive frames typically have nearest enemy at 4.0 tiles, HP 80%, 0.0 enemies within 3 tiles, age 6.2s and elixir 4.1.
- musketeer-hero: positive frames typically have nearest enemy at 8.0 tiles, HP 86%, 0.0 enemies within 3 tiles, age 13.2s and elixir 5.7.
- skeleton-king: positive frames typically have nearest enemy at 4.2 tiles, HP 66%, 0.0 enemies within 3 tiles, age 10.2s and elixir 4.7.
- tombstone-hero: positive frames typically have nearest enemy at 7.4 tiles, HP 79%, 0.0 enemies within 3 tiles, age 9.8s and elixir 8.0.
- valkyrie-hero: positive frames typically have nearest enemy at 5.4 tiles, HP 88%, 0.0 enemies within 3 tiles, age 6.3s and elixir 5.3.
- wizard-hero: positive frames typically have nearest enemy at 5.9 tiles, HP 100%, 0.0 enemies within 3 tiles, age 3.5s and elixir 4.4.

## Concerns

All ability commands in these recorder versions are skipped: reconstruction omits ability effects and elixir costs, so later board states diverge from historical pro states.
Compact names strip hero form and no persistent unit IDs/readiness are recorded. A hero deck slot plus a unique alive base-name match is an eligibility proxy, not proof of the active hero form; ambiguous same-name units are excluded.
Raw card-action ability_exhausted results are not button activations. Press-intent counts must not be presented as successful engine presses.
Recorded matches can end early or drift after rejected/delayed card plays; context missing after those divergences is not recovered. A frame up to 1s before a press is an approximation.
Direct repeated Bernoulli(p_within_1s) sampling at shortened frame intervals can over-press. The reported timing differences are measured failures where present, not claims of calibrated human-like behavior.
Phase-1 lifetime and ability-source attribution are inferred; fallback hazard rates inherit that uncertainty, and phase-1 baseline press shares use broader deck-slot denominators.
The standard elixir schedule is assumed; mode-specific multipliers and authoritative readiness are unavailable.
Tombstone is marginal at 192 retained presses; its passive controller and building share name/max HP, and the retained lone-match subset is selective.
Anonymized membership does not independently prove every participant is a professional. Board correlations do not establish player intent.
157 repeated replay tags were kept in the first listed corpus only; 157 copies differ in raw bytes (which include run metadata). No duplicate tag crosses the split.
No engine/GPU/adb/live run or runtime integration was performed; all outputs are offline artifacts.

## Reproduce and consume

Run with icebow/.venv/Scripts/python.exe -B: phase2_build.py, then phase2_fit.py, then phase2_verify.py all (scripts in this directory). Source JSON is opened read-only; phase2_inventory.json records source SHA256, size and mtime, and original phase-1 file hashes. Per-ability phase2_data_*.npz contains X, y, eligible, replay, deployment, tick, split (0=train,1=validation,2=test). phase2_deployments.json and phase2_press_audit.jsonl preserve traceability. ability_models.json is plain JSON.

Import ability_policy.predict and pass an ability slug plus a feature mapping or array in feature_names order. Enforce alive/available/charges in the caller. predict is a one-second horizon probability; do not call it as a 20Hz Bernoulli probability.
