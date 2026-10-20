# noise attrib arm: scalar noise OFF (exact elixir, opponent elixir known)

Run dirs: `scratchpad\gauntlet\L67\e1\attrib_noise\off_scalars\slot0`. Duplicates dropped: 0.
Bootstrap: entry-clustered, 10000 draws, seed 20260912.

## Run

| matches | entries | W | D | L | winrate | entry-clustered 95% CI | unclustered normal 95% (contrast only) |
|---|---|---|---|---|---|---|---|
| 100 | 100 | 72 | 0 | 28 | 72.0% | 63.0% .. 81.0% (entry-weighted 72.0%) | 63.2% .. 80.8% |

| per seed k | n | winrate |
|---|---|---|
| 0 | 100 | 72.0% |

| per slot | n | winrate |
|---|---|---|
| 0 | 100 | 72.0% |

Decided BEFORE the ghost script ended (end <= last ghost tick + 200): 48/75 = 64.0%. Wins after the script ended: 24 (33.3% of wins).
Wins where the real pro lost: 32 of 46 such matches.

| ghost plays delivered | n | wins | winrate | share of wins |
|---|---|---|---|---|
| <=10 | 6 | 3 | 50.0% | 4.2% |
| 11-30 | 70 | 49 | 70.0% | 68.1% |
| >30 | 24 | 20 | 83.3% | 27.8% |

| distinct ghost cards delivered | n | wins | winrate | share of wins |
|---|---|---|---|---|
| <=3 | 1 | 1 | 100.0% | 1.4% |
| 4-6 | 7 | 2 | 28.6% | 2.8% |
| >6 | 92 | 69 | 75.0% | 95.8% |

| plays/min | accepted/min | accepted frac | attempted/match | stall fires/match | no-affordable/match | mean s | mean s won | ghost refused/match | wall s/match |
|---|---|---|---|---|---|---|---|---|---|
| 12.29 | 11.13 | 90.6% | 40.5 | 0.47 | 120.2 | 197.8 | 200.3 | 0.78 | 13.9 |

Matches whose degraded-observation count != decisions: 0. Policies: {'live': 100}.

