# REPLICATION, disjoint slice: scalars noise OFF, entries 100:200

Run dirs: `scratchpad\gauntlet\L67\e1\attrib_noise\off_scalars_slice2\slot0`. Duplicates dropped: 0.
Bootstrap: entry-clustered, 10000 draws, seed 20260912.

## Run

| matches | entries | W | D | L | winrate | entry-clustered 95% CI | unclustered normal 95% (contrast only) |
|---|---|---|---|---|---|---|---|
| 100 | 100 | 71 | 0 | 29 | 71.0% | 62.0% .. 80.0% (entry-weighted 71.0%) | 62.1% .. 79.9% |

| per seed k | n | winrate |
|---|---|---|
| 0 | 100 | 71.0% |

| per slot | n | winrate |
|---|---|---|
| 0 | 100 | 71.0% |

Decided BEFORE the ghost script ended (end <= last ghost tick + 200): 54/79 = 68.4%. Wins after the script ended: 17 (23.9% of wins).
Wins where the real pro lost: 28 of 40 such matches.

| ghost plays delivered | n | wins | winrate | share of wins |
|---|---|---|---|---|
| <=10 | 7 | 3 | 42.9% | 4.2% |
| 11-30 | 72 | 53 | 73.6% | 74.6% |
| >30 | 21 | 15 | 71.4% | 21.1% |

| distinct ghost cards delivered | n | wins | winrate | share of wins |
|---|---|---|---|---|
| <=3 | 0 | 0 | n/a | 0.0% |
| 4-6 | 6 | 2 | 33.3% | 2.8% |
| >6 | 94 | 69 | 73.4% | 97.2% |

| plays/min | accepted/min | accepted frac | attempted/match | stall fires/match | no-affordable/match | mean s | mean s won | ghost refused/match | wall s/match |
|---|---|---|---|---|---|---|---|---|---|
| 12.12 | 11.11 | 91.6% | 39.5 | 0.39 | 111.0 | 195.4 | 197.7 | 0.74 | 13.5 |

Matches whose degraded-observation count != decisions: 0. Policies: {'live': 100}.

