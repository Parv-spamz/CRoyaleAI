# Sampling and Rocket aim: CPU verdict, 2026-10-04

Both checkpoints pass the offline filter only at card ratio **0.7**. This is permission to measure candidates in the simulator, not gameplay acceptance. Code is available in SIM and the inactive `live_play_v2.py` entry point; the active anti-leak-off R1e run is unchanged.

Common comparison: all **11,934 held-out Icebow pro PLAY rows**, including **671 Rockets**, **179 tower Rockets**, **10 finishing Rockets**. Expected probabilities are calculated exactly, not estimated from a lucky random draw. R1e additionally evaluates 26,383 WAIT rows; old R1's supplementary WAIT statistic is unavailable. Old R1 requires card-vocabulary remapping; the first uncorrected old-R1 pass is invalid and superseded by `check_sampling_v2.py`.

| Model / ratio / temperature | Pro-card agreement | Change vs argmax (pp) | Rocket recall | Rocket false-fire | Confident override | Verdict |
|---|---:|---:|---:|---:|---:|---|
| R1e argmax | 64.589% | 0 | 14.158% | 0.808% | 0 | baseline |
| R1e / .5 / .7 | 63.236% | -1.352 | 15.022% | 0.948% | 1.663% | reject |
| R1e / .5 / 1 | 63.066% | -1.522 | 15.118% | 0.966% | 1.962% | reject |
| R1e / .7 / .7 | 64.134% | -.455 | 14.717% | .856% | 0 | offline pass |
| R1e / .7 / 1 | 64.110% | -.479 | 14.764% | .861% | 0 | offline pass |
| Old R1 argmax | 63.382% | 0 | 9.687% | .479% | 0 | baseline |
| Old R1 / .5 / .7 | 61.904% | -1.478 | 11.574% | .646% | 1.938% | reject |
| Old R1 / .5 / 1 | 61.734% | -1.648 | 11.761% | .668% | 2.281% | reject |
| Old R1 / .7 / .7 | 62.740% | -.642 | 10.673% | .528% | 0 | offline pass |
| Old R1 / .7 / 1 | 62.705% | -.677 | 10.712% | .531% | 0 | offline pass |

Recall is conditional card selection on pro Rocket rows. False-fire is selection on the 11,263 other pro PLAY rows. Neither includes the deterministic play gate; gate-adjusted metrics at tau .27/.35 are in `report.json`. Rank the two survivors by Rocket recall: T=1 first, T=.7 second, without further tuning.

Rocket-only area aim maximises learned location probability inside the catalog's two-tile radius:

| Checkpoint | All 671 pro Rocket coordinates covered | 179 pro tower coordinates covered | 10 finishing coordinates covered |
|---|---|---|---|
| R1e | 60.66% -> 68.55% | 48.60% -> 62.57% | 0 -> 3 |
| Old R1 | 59.02% -> 65.72% | 41.90% -> 55.87% | 0 -> 2 |

These are coordinate-coverage proxies with Rocket teacher-forced, not measured tower damage. **Both argmax models select Rocket in 0/10 finishing cases; both passing sampling settings also select it with zero probability there.** R1e's gate passes 9/10, but all ten Rockets fall below even the .5 filter. Aiming cannot fix a card the model never chooses. The finishing subset is small and is not a census of all possible one/two-Rocket opportunities.

CPU helper timing: median2.57ms/p953.07ms, one thread,200 calls, excluding model inference. No live or CUDA timing claim.

Verification: **58 tests pass** (geometry, affordability, deterministic defaults, seeded sampling, actual reactive/batched integration and existing regressions). Independent report reconciliation checks distributions, counts, vocabulary mapping, geometry and source hashes, and rejects a corrupted metric. Fixed a pre-existing reactive CLI omission that dropped `--behaviour-telemetry` before worker construction; defaults remain unchanged. Evidence and exact commands are in GATES.md/RUNBOOK.md.

Next: fresh same-code Q3 ghost/reactive/behaviour runs for both checkpoints. Current live occupies the GPU. Existing SIM anti-stall is recorded and unchanged in these comparison instruments; it differs from the owner's live anti-leak-off experiment, so an accepted simulator result is not proof of live improvement.
