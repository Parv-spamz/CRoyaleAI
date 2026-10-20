# CONTROL, disjoint slice: v6lat live view, entries 100:200, zero switches

Run dirs: `scratchpad\gauntlet\L67\e1\attrib_noise\ctrl_slice2\slot0`. Duplicates dropped: 0.
Bootstrap: entry-clustered, 10000 draws, seed 20260912.

## Run

| matches | entries | W | D | L | winrate | entry-clustered 95% CI | unclustered normal 95% (contrast only) |
|---|---|---|---|---|---|---|---|
| 100 | 100 | 47 | 0 | 53 | 47.0% | 37.0% .. 57.0% (entry-weighted 47.0%) | 37.2% .. 56.8% |

| per seed k | n | winrate |
|---|---|---|
| 0 | 100 | 47.0% |

| per slot | n | winrate |
|---|---|---|
| 0 | 100 | 47.0% |

Decided BEFORE the ghost script ended (end <= last ghost tick + 200): 34/79 = 43.0%. Wins after the script ended: 13 (27.7% of wins).
Wins where the real pro lost: 16 of 40 such matches.

| ghost plays delivered | n | wins | winrate | share of wins |
|---|---|---|---|---|
| <=10 | 9 | 3 | 33.3% | 6.4% |
| 11-30 | 68 | 32 | 47.1% | 68.1% |
| >30 | 23 | 12 | 52.2% | 25.5% |

| distinct ghost cards delivered | n | wins | winrate | share of wins |
|---|---|---|---|---|
| <=3 | 0 | 0 | n/a | 0.0% |
| 4-6 | 8 | 3 | 37.5% | 6.4% |
| >6 | 92 | 44 | 47.8% | 93.6% |

| plays/min | accepted/min | accepted frac | attempted/match | stall fires/match | no-affordable/match | mean s | mean s won | ghost refused/match | wall s/match |
|---|---|---|---|---|---|---|---|---|---|
| 13.42 | 12.08 | 90.0% | 42.8 | 0.01 | 211.0 | 191.5 | 193.9 | 0.69 | 13.4 |

Matches whose degraded-observation count != decisions: 0. Policies: {'live': 100}.

