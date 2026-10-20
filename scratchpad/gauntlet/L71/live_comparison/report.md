# Q0 live comparison

Snapshot: 2026-10-05T01:27:54.495675+00:00

| Checkpoint | W / L | Unknown / unread | Win rate (Wilson 95%) | Confirmed Rockets / plays |
|---|---:|---:|---:|---:|
| old_r1_u0155 | 152 / 146 | 5 / 0 | 51.0% [45.4, 56.6] | 96 / 9935 |
| r1e_u0155 | 6 / 3 | 0 / 0 | 66.7% [35.4, 87.9] | 1 / 350 |

The descriptive Wilson intervals overlap; these data do not establish a winner. Sequential ladder runs also differ in opponents and conditions.

Checkpoint identity comes from each match start.ckpt; outcomes come from a unique subsequent navigation event within 30 seconds of the recorded end, before the next match.

Pre-emptive Log and trophy progression are unavailable from these saved event schemas. Missing values are null, not zero.

## old_r1_u0155

Ended logs 303; incomplete logs 0; frames in 38 ended matches.
Ability attempts / confirmed: 1053 / 1049.
Confirmed X-Bow intended coordinates: `{"0.1389,0.6094": 671, "0.2500,0.6094": 13, "0.4167,0.7031": 6, "0.4722,0.7031": 21, "0.5278,0.7031": 22, "0.5833,0.5781": 1, "0.5833,0.7031": 4, "0.6944,0.7031": 1, "0.7500,0.6094": 4, "0.8611,0.6094": 504, "0.9167,0.3906": 1}`.

## r1e_u0155

Ended logs 9; incomplete logs 1; frames in 2 ended matches.
Ability attempts / confirmed: 14 / 14.
Confirmed X-Bow intended coordinates: `{"0.1389,0.6094": 11, "0.4722,0.7031": 3, "0.8611,0.6094": 16}`.

## Limits

- Observational time-separated cohorts; trophy range, opponents, reader and ability-rule changes are confounders.
- Wilson intervals are descriptive binomial intervals, not a causal or sequential significance test.
- Behaviour uses ended logs, including unknown outcomes; unfinished matches are excluded from behaviour totals.
- X-Bow coordinates are intended placements attached to confirmed plays, not independently measured landings.
- Draw/unread is not counted as a loss. Frame logging is a selected subset, typically clip matches.
- No trophy values or preemptive-Log rate are inferred from wins, troop spawns, or absence of logged fields.

Reproduce with `icebow/.venv/Scripts/python.exe scratchpad/gauntlet/L71/live_comparison/compare.py`.
Verify this exact snapshot with `icebow/.venv/Scripts/python.exe scratchpad/gauntlet/L71/live_comparison/verify_report.py`.
