# REPLICATION, disjoint slice 100:200: opp_elixir noise OFF

Run dirs: `scratchpad\gauntlet\L67\e1\attrib_split\off_opp_elixir_slice2\slot0`. Duplicates dropped: 0.
Bootstrap: entry-clustered, 10000 draws, seed 20260912.

## Run

| matches | entries | W | D | L | winrate | entry-clustered 95% CI | unclustered normal 95% (contrast only) |
|---|---|---|---|---|---|---|---|
| 100 | 100 | 73 | 0 | 27 | 73.0% | 64.0% .. 82.0% (entry-weighted 73.0%) | 64.3% .. 81.7% |

| per seed k | n | winrate |
|---|---|---|
| 0 | 100 | 73.0% |

| per slot | n | winrate |
|---|---|---|
| 0 | 100 | 73.0% |

Decided BEFORE the ghost script ended (end <= last ghost tick + 200): 55/81 = 67.9%. Wins after the script ended: 18 (24.7% of wins).
Wins where the real pro lost: 30 of 40 such matches.

| ghost plays delivered | n | wins | winrate | share of wins |
|---|---|---|---|---|
| <=10 | 8 | 5 | 62.5% | 6.8% |
| 11-30 | 73 | 53 | 72.6% | 72.6% |
| >30 | 19 | 15 | 78.9% | 20.5% |

| distinct ghost cards delivered | n | wins | winrate | share of wins |
|---|---|---|---|---|
| <=3 | 1 | 1 | 100.0% | 1.4% |
| 4-6 | 7 | 2 | 28.6% | 2.7% |
| >6 | 92 | 70 | 76.1% | 95.9% |

| plays/min | accepted/min | accepted frac | attempted/match | stall fires/match | no-affordable/match | mean s | mean s won | ghost refused/match | wall s/match |
|---|---|---|---|---|---|---|---|---|---|
| 11.96 | 10.82 | 90.5% | 37.4 | 0.25 | 109.4 | 187.7 | 190.5 | 0.65 | 11.6 |

Matches whose degraded-observation count != decisions: 0. Policies: {'live': 100}.

