# October 3 continuation: public inputs and Rocket behaviour

Status: **partial, not training-ready or live-approved**. The old versions 1/2/3 paths retain byte-identical tested
arrays, seeded weights, losses, simulation actions/trajectories/RNG and real u0155/gen_v3 live inputs. Version 4
has a repaired development path, explicit unknown timing, and training preflight rejection of missing sources.

## Required source data is missing

The re-driver's full native frames save projectile side, position, target and card, but omit time-to-impact.
More seriously, its `effects` field saves the bridge's generic nonunit objects. Actual spell areas are separately
exported as `area_effects` and discarded by the recorder. In three completed diagnostic native recordings,
**865/865 frames** had identical generic-effect/projectile projections; **766 projectile observations** were
duplicated as generic effects; **0 frames** carried the actual area field. Version 4 now ignores those aliases
and records missing area coverage rather than treating the missing observations as a verified empty arena.

`native_source_audit.json` and the receipt under `.foreman/codex_autopilot/runs/rocket_native_samples_1510/`
pin the samples. `native_timing_evidence.json` is an earlier, superseded audit: its effect counts were aliases.
The bridge labels its area extension unverified, so copying its timer into training is not validation.
Reader v2's real area `remaining_ms` is separately validated; projectile impact time is absent there too.
SIM's flight delay is a pre-flight delay, not time-to-impact. No live sampler or ongoing VM recorder was changed.

An offline radial-speed feasibility probe (`timing_feasibility.json`) found 9 Goblin Barrel tracks with 25 estimates
and 9 Rocket tracks with 14 estimates on 6 tracks. All scored predictions fell in the observed disappearance
intervals, whose median width was1 second. This is **not** an impact-time error measurement and is too coarse
to validate the 0.5-second Log metric. No Skeleton Barrel track was observed. No estimate was deployed.

## Rocket mining

The legacy audit covers all six existing corpora in dataset order: 14818 files, 14661 unique replay tags,
157 duplicate-tag variants excluded/listed. It enumerates **9176 accepted Rockets  / 928165 accepted plays**.
These are mixed-deck replay-engine observations; their 0.989% overall Rocket share is not comparable to the
Icebow-only pro 5.8% figure. `legacy_mining_1510/manifest.json` pins every selected input.

A 3.5-tile tower-center envelope finds 5557 tower-target candidates. The envelope is deliberately labelled
geometric, not a verified hitbox or causal damage attribution. 2369 are within 2 tiles and 3188 are in the
unvalidated edge band. Their pre-cast tower HP median is 1956 (10th/90th 572/3052), own elixir median 8.6732,
and 5091/5557 have tower HP above 497. There are 1349 multi-Rocket candidate sequences on one tower:
600 sequences of 2, 327 of 3, 213 of 4, 128 of 5, 51 of 6, 18 of 7, 10 of 8 and 2 of 9. Median gap is 33.55 seconds.
These measurements support examining Rocket cycling broadly rather than defining it as a one-shot finish.

2314 tower-target candidates occur in recordings explicitly labelled `native_tiebreak_hp_drain`;
203 have unknown tiebreak status. An end-of-match outcome does not establish that an earlier Rocket was
intended to win a tiebreak. Row-level contexts retain phase/time left, crowns, tower-HP margin, own elixir,
previous same-tower candidates/gaps and outcome labels. Outcome labels never enter the model features.

Three selected completed native re-drives contain 8 Rockets, 6 near-tower candidates and one 3-Rocket same-tower
sequence. All 6 candidate flights are visible and their disappearance intervals align with 342-HP tower drops.
This is compatible damage evidence, not independent causal attribution.342 also illustrates why the live
497-HP observation must not be treated as universal across levels/instruments. The requested <=497HP metric
remains a separate specified diagnostic, not the new loss definition.

The loss now supports continuous `1 + (maximum_weight - 1) * P(pro tower-Rocket context)` row weights.
It contains no scripted Rocket action or HP threshold. **No classifier or maximum weight has been selected**.
The CLI refuses missing probability annotations, disjoint fit/tune/test identifiers and held-out selection
evidence. Verified labels and the complete native corpus are still needed before fitting or a weight sweep.

## Paired ghost-screen baseline

All rows use the same 299 pinned replay keys and matching recorded policy/observation settings. CIs are paired
replay-cluster bootstrap intervals, 10000 resamples, seed 20261003. Historical run dates remain a limitation.

| Model | Rocket / accepted plays | Rocket share, 95% CI | Accepted plays/min, 95% CI | Median elixir at Rocket |
|---|---:|---:|---:|---:|
| gen_v1 |72/9466|0.761% [0.592,0.942]|10.322 [10.173,10.476]|7.695|
| u0155 |50/9001|0.555% [0.405,0.713]|10.036 [9.925,10.155]|7.624|
| gen_v3 |83/9299|0.893% [0.696,1.106]|10.327 [10.141,10.511]|7.570|

Paired Rocket-share delta vs gen_v1: u0155 **-0.205pp [-0.392,-0.018]**; gen_v3 **+0.132pp [-0.090,+0.363]**.
Rates above pool plays and duration; older HANDOFF rates average match-specific rates and differ accordingly.
These are ghost-screen metrics, not reactive or ladder results. `behavior_baselines.json` pins inputs and CIs.

Denominator check (October3 17:28): the owner's5.8% reference is1267/21687 accepted PLAY rows from493 S1
Icebow replays (`L70/audit/audit.md`, sectionC). It is not the mixed-deck corpus rate9176/928165=0.989%.
The pinned ghost screen uses the fixed Icebow deck (all299 gen_v3 rows contain only its eight card keys);
the three model comparisons above are paired with each other. The S1 human-replay reference is a separate
historical replay-engine sample, not a paired policy comparison. No acceptance rule or weighting was changed.

The saved logs omit the opportunity/context denominators for Rocket-on-tower pro contexts, multi-Rocket hits,
tiebreak tower-HP margin, one-Rocket finish conversion and preemptive Log. These remain null/UNMEASURED, never
zero. Full behaviour acceptance requires new passive telemetry and instrumented baseline runs when resources
permit. The already-running R1t's recipe and acceptance commands remain unchanged; its historical acceptance
must not be relabelled as passing the updated behaviour suite.

## Verification and remaining work

38 focused tests passed after the source-alias correction. A separate 34-test regression batch plus 4 subtests
passed, overlapping 8 legacy tests; five audit tests passed after adding the timing probe. The persisted audit
verifier checks replay/row/sequence counts, source hashes for the three baseline logs, and unavailable fields.
Exact logs are under `.foreman/codex_autopilot/runs/1510_*`.

Full native fetch/shutdown and R1t final acceptance are still running dependencies. Ability calibration/R1e
remains blocked by the documented share/delay mismatch and IPC permissions. Live selection remains owner-only.
Publication was attempted and denied at `.git/index.lock`; no files were staged and no commit/push occurred.
The reviewable patch and explicit 77-file manifest are under `.foreman/codex_autopilot/` (regenerate after later
document updates). No `icebow/data` path is included.
