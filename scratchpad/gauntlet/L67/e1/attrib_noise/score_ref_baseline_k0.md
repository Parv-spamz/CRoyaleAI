# REF: v6lat live, entries 0:293 shard 0/2 (n=147)

Run dirs: `scratchpad\gauntlet\L67\e1\baseline_k0\slot0`. Duplicates dropped: 0.
Bootstrap: entry-clustered, 10000 draws, seed 20260912.

## Run

| matches | entries | W | D | L | winrate | entry-clustered 95% CI | unclustered normal 95% (contrast only) |
|---|---|---|---|---|---|---|---|
| 147 | 147 | 78 | 0 | 69 | 53.1% | 44.9% .. 61.2% (entry-weighted 53.1%) | 45.0% .. 61.1% |

| per seed k | n | winrate |
|---|---|---|
| 0 | 147 | 53.1% |

| per slot | n | winrate |
|---|---|---|
| 0 | 147 | 53.1% |

Decided BEFORE the ghost script ended (end <= last ghost tick + 200): 58/113 = 51.3%. Wins after the script ended: 20 (25.6% of wins).
Wins where the real pro lost: 38 of 70 such matches.

| ghost plays delivered | n | wins | winrate | share of wins |
|---|---|---|---|---|
| <=10 | 13 | 3 | 23.1% | 3.8% |
| 11-30 | 94 | 49 | 52.1% | 62.8% |
| >30 | 40 | 26 | 65.0% | 33.3% |

| distinct ghost cards delivered | n | wins | winrate | share of wins |
|---|---|---|---|---|
| <=3 | 0 | 0 | n/a | 0.0% |
| 4-6 | 13 | 3 | 23.1% | 3.8% |
| >6 | 134 | 75 | 56.0% | 96.2% |

| plays/min | accepted/min | accepted frac | attempted/match | stall fires/match | no-affordable/match | mean s | mean s won | ghost refused/match | wall s/match |
|---|---|---|---|---|---|---|---|---|---|
| 13.43 | 12.12 | 90.2% | 42.9 | 0.01 | 215.1 | 191.5 | 197.4 | 0.89 | 12.4 |

Matches whose degraded-observation count != decisions: 0. Policies: {'live': 147}.

