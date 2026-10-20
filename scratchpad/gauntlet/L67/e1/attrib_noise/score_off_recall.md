# noise attrib arm: recall noise OFF (detector misses removed)

Run dirs: `scratchpad\gauntlet\L67\e1\attrib_noise\off_recall\slot0`. Duplicates dropped: 0.
Bootstrap: entry-clustered, 10000 draws, seed 20260912.

## Run

| matches | entries | W | D | L | winrate | entry-clustered 95% CI | unclustered normal 95% (contrast only) |
|---|---|---|---|---|---|---|---|
| 100 | 100 | 55 | 0 | 45 | 55.0% | 45.0% .. 65.0% (entry-weighted 55.0%) | 45.2% .. 64.8% |

| per seed k | n | winrate |
|---|---|---|
| 0 | 100 | 55.0% |

| per slot | n | winrate |
|---|---|---|
| 0 | 100 | 55.0% |

Decided BEFORE the ghost script ended (end <= last ghost tick + 200): 36/77 = 46.8%. Wins after the script ended: 19 (34.5% of wins).
Wins where the real pro lost: 25 of 46 such matches.

| ghost plays delivered | n | wins | winrate | share of wins |
|---|---|---|---|---|
| <=10 | 8 | 3 | 37.5% | 5.5% |
| 11-30 | 71 | 39 | 54.9% | 70.9% |
| >30 | 21 | 13 | 61.9% | 23.6% |

| distinct ghost cards delivered | n | wins | winrate | share of wins |
|---|---|---|---|---|
| <=3 | 1 | 1 | 100.0% | 1.8% |
| 4-6 | 8 | 3 | 37.5% | 5.5% |
| >6 | 91 | 51 | 56.0% | 92.7% |

| plays/min | accepted/min | accepted frac | attempted/match | stall fires/match | no-affordable/match | mean s | mean s won | ghost refused/match | wall s/match |
|---|---|---|---|---|---|---|---|---|---|
| 13.08 | 11.65 | 89.1% | 40.7 | 0.00 | 205.6 | 186.7 | 192.4 | 0.75 | 12.1 |

Matches whose degraded-observation count != decisions: 0. Policies: {'live': 100}.

