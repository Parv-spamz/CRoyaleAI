# noise attrib arm: team noise OFF (side tagging exact)

Run dirs: `scratchpad\gauntlet\L67\e1\attrib_noise\off_team\slot0`. Duplicates dropped: 0.
Bootstrap: entry-clustered, 10000 draws, seed 20260912.

## Run

| matches | entries | W | D | L | winrate | entry-clustered 95% CI | unclustered normal 95% (contrast only) |
|---|---|---|---|---|---|---|---|
| 100 | 100 | 56 | 0 | 44 | 56.0% | 46.0% .. 66.0% (entry-weighted 56.0%) | 46.3% .. 65.7% |

| per seed k | n | winrate |
|---|---|---|
| 0 | 100 | 56.0% |

| per slot | n | winrate |
|---|---|---|
| 0 | 100 | 56.0% |

Decided BEFORE the ghost script ended (end <= last ghost tick + 200): 33/75 = 44.0%. Wins after the script ended: 23 (41.1% of wins).
Wins where the real pro lost: 29 of 46 such matches.

| ghost plays delivered | n | wins | winrate | share of wins |
|---|---|---|---|---|
| <=10 | 8 | 3 | 37.5% | 5.4% |
| 11-30 | 67 | 42 | 62.7% | 75.0% |
| >30 | 25 | 11 | 44.0% | 19.6% |

| distinct ghost cards delivered | n | wins | winrate | share of wins |
|---|---|---|---|---|
| <=3 | 1 | 1 | 100.0% | 1.8% |
| 4-6 | 8 | 2 | 25.0% | 3.6% |
| >6 | 91 | 53 | 58.2% | 94.6% |

| plays/min | accepted/min | accepted frac | attempted/match | stall fires/match | no-affordable/match | mean s | mean s won | ghost refused/match | wall s/match |
|---|---|---|---|---|---|---|---|---|---|
| 13.38 | 11.98 | 89.6% | 43.4 | 0.01 | 199.6 | 194.8 | 192.8 | 0.80 | 12.4 |

Matches whose degraded-observation count != decisions: 0. Policies: {'live': 100}.

