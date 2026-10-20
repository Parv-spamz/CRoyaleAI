# noise attrib gate: repro (live view, no change)

Run dirs: `scratchpad\gauntlet\L67\e1\attrib_noise\gate_live10\slot0`. Duplicates dropped: 0.
Bootstrap: entry-clustered, 10000 draws, seed 20260912.

## Run

| matches | entries | W | D | L | winrate | entry-clustered 95% CI | unclustered normal 95% (contrast only) |
|---|---|---|---|---|---|---|---|
| 10 | 10 | 5 | 0 | 5 | 50.0% | 20.0% .. 80.0% (entry-weighted 50.0%) | 19.0% .. 81.0% |

| per seed k | n | winrate |
|---|---|---|
| 0 | 10 | 50.0% |

| per slot | n | winrate |
|---|---|---|
| 0 | 10 | 50.0% |

Decided BEFORE the ghost script ended (end <= last ghost tick + 200): 5/10 = 50.0%. Wins after the script ended: 0 (0.0% of wins).
Wins where the real pro lost: 4 of 7 such matches.

| ghost plays delivered | n | wins | winrate | share of wins |
|---|---|---|---|---|
| <=10 | 2 | 0 | 0.0% | 0.0% |
| 11-30 | 7 | 4 | 57.1% | 80.0% |
| >30 | 1 | 1 | 100.0% | 20.0% |

| distinct ghost cards delivered | n | wins | winrate | share of wins |
|---|---|---|---|---|
| <=3 | 0 | 0 | n/a | 0.0% |
| 4-6 | 1 | 0 | 0.0% | 0.0% |
| >6 | 9 | 5 | 55.6% | 100.0% |

| plays/min | accepted/min | accepted frac | attempted/match | stall fires/match | no-affordable/match | mean s | mean s won | ghost refused/match | wall s/match |
|---|---|---|---|---|---|---|---|---|---|
| 12.88 | 10.97 | 85.2% | 35.2 | 0.00 | 175.5 | 164.0 | 175.6 | 1.10 | 11.6 |

Matches whose degraded-observation count != decisions: 0. Policies: {'live': 10}.

