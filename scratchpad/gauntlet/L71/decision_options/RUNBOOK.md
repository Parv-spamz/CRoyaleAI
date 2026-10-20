# Sampling and Rocket aim candidates

These are Q1/Q2 implementation and teacher-forced checks. The running R1e anti-leak-off experiment is not reconfigured. No new checkpoint is trained, and no GPU acceptance job is started.

`pipeline/decision_options.py` supplies the shared rule. `pipeline/e1_eval.py` accepts optional decision arguments in its single and batched live-policy functions. `pipeline/search_s0.py --arms plain` applies options to the learner only. `run_screen_v2.py` is an isolated copy of the current ghost runner, including its existing telemetry support; the original runner had inherited edits and is untouched.

Live preparation uses `pipeline/live_gen_v2.py` and `scratchpad/gauntlet/L68/live_reader/live_play_v2.py`. The candidate defaults delegate to the original pilot. The running `live_play.py`, `live_gen.py`, supervisor and checkpoint override are preserved. The candidate start event records options and its per-match seed. The supervisor still starts the original entry point.

## Options

| Flag | Default | Experiment |
|---|---|---|
| `--card-choice` | `argmax` | `filtered` samples affordable cards whose probability is at least ratio times the top probability |
| `--card-ratio` | `0.7` | Frozen check: `0.5`, `0.7` |
| `--card-T` | `1.0` | Frozen check: `0.7`, `1.0`; applied after filtering |
| `--spell-aim` | `argmax` | `rocket_area` maximises learned cell probability within the catalog Rocket radius |
| `--decision-seed` | `0` | Separate per-match random stream; WAIT/singleton decisions consume no draw |

Sampling does not alter the gate or aim. Rocket aim does not alter card choice or the gate. No HP threshold, tower preference, card ban, new reward or forced finish-off is added. Non-Rocket cards keep their existing aim. The existing anti-stall configuration remains separate; the candidate live entry supports the already-existing `--no-anti-leak` option.

## Checks and interpretation

`verify_tests.py` runs CPU geometry, default parity, seeded decision, real reactive integration and existing E1/search regressions. `check_sampling.py` now evaluates R1e only; its historical old-R1 arm was removed after finding incompatible card vocabularies. **The historical old-R1 inference is invalid.** Follow it with `check_sampling_v2.py`, which remaps own hand/next/deck/label/past IDs by card name, recomputes old R1, and retains valid R1e results. Do not run the two scripts concurrently or use the original old-R1 figures.

`report.json` holds exact expected agreement and Rocket selection rates for every frozen setting. Conditional card-choice probabilities and gate-adjusted probabilities at tau0.27/0.35 are separate. A setting passes the offline filter only if agreement falls by at most1pp and confident-row override is zero (tolerance1e-12). This is not match-performance acceptance.

The finishing subset consists of actual held-out pro Rocket plays labelled as finishing a tower. It is not a census of all possible one- or two-Rocket opportunities. Area-aim coverage means the selected blast disk covers the pro's chosen coordinate; it is a target-agreement proxy, not measured damage or a win-rate result.

`verify_report.py` independently recomputes the statistics and disk objective from cached logits, checks source hashes and rejects a deliberately corrupted metric. Caches are under ignored `icebow/data/bench/decision_options_20261004/`; reports refer to their hashes.

Q3 remains a separate step: fresh same-code paired ghost baselines and reactive/behaviour checks for both checkpoints, with the precise anti-stall setting recorded. Only surviving candidates should be evaluated. The current live run occupies the GPU; do not start a competing GPU job. Live adoption is an owner decision after concrete acceptance results.

## CPU commands

```powershell
icebow/.venv/Scripts/python.exe scratchpad/gauntlet/L71/decision_options/verify_tests.py
icebow/.venv/Scripts/python.exe scratchpad/gauntlet/L71/decision_options/verify_report.py
research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L71/decision_options/run_screen_v2.py --help
icebow/.venv/Scripts/python.exe scratchpad/gauntlet/L68/live_reader/live_play_v2.py --help
```
