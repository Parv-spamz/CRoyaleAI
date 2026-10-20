# noise attrib arm: confidence noise OFF (detector conf exact)

Run dirs: `scratchpad\gauntlet\L67\e1\attrib_noise\off_conf\slot0`. Duplicates dropped: 0.
Bootstrap: entry-clustered, 10000 draws, seed 20260912.

## Run

| matches | entries | W | D | L | winrate | entry-clustered 95% CI | unclustered normal 95% (contrast only) |
|---|---|---|---|---|---|---|---|
| 100 | 100 | 52 | 0 | 48 | 52.0% | 42.0% .. 62.0% (entry-weighted 52.0%) | 42.2% .. 61.8% |

| per seed k | n | winrate |
|---|---|---|
| 0 | 100 | 52.0% |

| per slot | n | winrate |
|---|---|---|
| 0 | 100 | 52.0% |

Decided BEFORE the ghost script ended (end <= last ghost tick + 200): 36/76 = 47.4%. Wins after the script ended: 16 (30.8% of wins).
Wins where the real pro lost: 23 of 46 such matches.

| ghost plays delivered | n | wins | winrate | share of wins |
|---|---|---|---|---|
| <=10 | 7 | 3 | 42.9% | 5.8% |
| 11-30 | 74 | 38 | 51.4% | 73.1% |
| >30 | 19 | 11 | 57.9% | 21.2% |

| distinct ghost cards delivered | n | wins | winrate | share of wins |
|---|---|---|---|---|
| <=3 | 1 | 1 | 100.0% | 1.9% |
| 4-6 | 7 | 2 | 28.6% | 3.8% |
| >6 | 92 | 49 | 53.3% | 94.2% |

| plays/min | accepted/min | accepted frac | attempted/match | stall fires/match | no-affordable/match | mean s | mean s won | ghost refused/match | wall s/match |
|---|---|---|---|---|---|---|---|---|---|
| 13.22 | 11.75 | 88.9% | 41.5 | 0.00 | 208.0 | 188.3 | 196.2 | 0.67 | 12.7 |

Matches whose degraded-observation count != decisions: 0. Policies: {'live': 100}.

