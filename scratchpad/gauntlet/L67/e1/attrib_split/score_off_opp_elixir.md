# split arm: opp_elixir noise OFF (true opponent elixir known)

Run dirs: `scratchpad\gauntlet\L67\e1\attrib_split\off_opp_elixir\slot0`. Duplicates dropped: 0.
Bootstrap: entry-clustered, 10000 draws, seed 20260912.

## Run

| matches | entries | W | D | L | winrate | entry-clustered 95% CI | unclustered normal 95% (contrast only) |
|---|---|---|---|---|---|---|---|
| 100 | 100 | 68 | 0 | 32 | 68.0% | 59.0% .. 77.0% (entry-weighted 68.0%) | 58.9% .. 77.1% |

| per seed k | n | winrate |
|---|---|---|
| 0 | 100 | 68.0% |

| per slot | n | winrate |
|---|---|---|
| 0 | 100 | 68.0% |

Decided BEFORE the ghost script ended (end <= last ghost tick + 200): 51/79 = 64.6%. Wins after the script ended: 17 (25.0% of wins).
Wins where the real pro lost: 33 of 46 such matches.

| ghost plays delivered | n | wins | winrate | share of wins |
|---|---|---|---|---|
| <=10 | 9 | 3 | 33.3% | 4.4% |
| 11-30 | 71 | 52 | 73.2% | 76.5% |
| >30 | 20 | 13 | 65.0% | 19.1% |

| distinct ghost cards delivered | n | wins | winrate | share of wins |
|---|---|---|---|---|
| <=3 | 1 | 1 | 100.0% | 1.5% |
| 4-6 | 10 | 3 | 30.0% | 4.4% |
| >6 | 89 | 64 | 71.9% | 94.1% |

| plays/min | accepted/min | accepted frac | attempted/match | stall fires/match | no-affordable/match | mean s | mean s won | ghost refused/match | wall s/match |
|---|---|---|---|---|---|---|---|---|---|
| 12.06 | 10.92 | 90.6% | 37.6 | 0.21 | 113.9 | 187.1 | 194.8 | 0.83 | 15.2 |

Matches whose degraded-observation count != decisions: 0. Policies: {'live': 100}.

