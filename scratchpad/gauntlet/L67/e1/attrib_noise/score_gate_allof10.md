# noise attrib gate: all 8 noise components off

Run dirs: `scratchpad\gauntlet\L67\e1\attrib_noise\gate_allof10\slot0`. Duplicates dropped: 0.
Bootstrap: entry-clustered, 10000 draws, seed 20260912.

## Run

| matches | entries | W | D | L | winrate | entry-clustered 95% CI | unclustered normal 95% (contrast only) |
|---|---|---|---|---|---|---|---|
| 10 | 10 | 9 | 0 | 1 | 90.0% | 70.0% .. 100.0% (entry-weighted 90.0%) | 71.4% .. 108.6% |

| per seed k | n | winrate |
|---|---|---|
| 0 | 10 | 90.0% |

| per slot | n | winrate |
|---|---|---|
| 0 | 10 | 90.0% |

Decided BEFORE the ghost script ended (end <= last ghost tick + 200): 8/9 = 88.9%. Wins after the script ended: 1 (11.1% of wins).
Wins where the real pro lost: 6 of 7 such matches.

| ghost plays delivered | n | wins | winrate | share of wins |
|---|---|---|---|---|
| <=10 | 0 | 0 | n/a | 0.0% |
| 11-30 | 9 | 9 | 100.0% | 100.0% |
| >30 | 1 | 0 | 0.0% | 0.0% |

| distinct ghost cards delivered | n | wins | winrate | share of wins |
|---|---|---|---|---|
| <=3 | 0 | 0 | n/a | 0.0% |
| 4-6 | 0 | 0 | n/a | 0.0% |
| >6 | 10 | 9 | 90.0% | 100.0% |

| plays/min | accepted/min | accepted frac | attempted/match | stall fires/match | no-affordable/match | mean s | mean s won | ghost refused/match | wall s/match |
|---|---|---|---|---|---|---|---|---|---|
| 12.02 | 10.91 | 90.8% | 40.0 | 1.20 | 59.5 | 199.7 | 188.0 | 0.70 | 13.7 |

Matches whose degraded-observation count != decisions: 0. Policies: {'live': 10}.

