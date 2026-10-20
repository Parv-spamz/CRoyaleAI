# noise attrib arm: position noise OFF (unit x/y jitter removed)

Run dirs: `scratchpad\gauntlet\L67\e1\attrib_noise\off_position\slot0`. Duplicates dropped: 0.
Bootstrap: entry-clustered, 10000 draws, seed 20260912.

## Run

| matches | entries | W | D | L | winrate | entry-clustered 95% CI | unclustered normal 95% (contrast only) |
|---|---|---|---|---|---|---|---|
| 100 | 100 | 54 | 0 | 46 | 54.0% | 44.0% .. 64.0% (entry-weighted 54.0%) | 44.2% .. 63.8% |

| per seed k | n | winrate |
|---|---|---|
| 0 | 100 | 54.0% |

| per slot | n | winrate |
|---|---|---|
| 0 | 100 | 54.0% |

Decided BEFORE the ghost script ended (end <= last ghost tick + 200): 34/75 = 45.3%. Wins after the script ended: 20 (37.0% of wins).
Wins where the real pro lost: 26 of 46 such matches.

| ghost plays delivered | n | wins | winrate | share of wins |
|---|---|---|---|---|
| <=10 | 6 | 3 | 50.0% | 5.6% |
| 11-30 | 73 | 39 | 53.4% | 72.2% |
| >30 | 21 | 12 | 57.1% | 22.2% |

| distinct ghost cards delivered | n | wins | winrate | share of wins |
|---|---|---|---|---|
| <=3 | 1 | 1 | 100.0% | 1.9% |
| 4-6 | 7 | 4 | 57.1% | 7.4% |
| >6 | 92 | 49 | 53.3% | 90.7% |

| plays/min | accepted/min | accepted frac | attempted/match | stall fires/match | no-affordable/match | mean s | mean s won | ghost refused/match | wall s/match |
|---|---|---|---|---|---|---|---|---|---|
| 13.29 | 11.85 | 89.2% | 42.5 | 0.00 | 214.7 | 192.1 | 193.8 | 0.78 | 12.6 |

Matches whose degraded-observation count != decisions: 0. Policies: {'live': 100}.

