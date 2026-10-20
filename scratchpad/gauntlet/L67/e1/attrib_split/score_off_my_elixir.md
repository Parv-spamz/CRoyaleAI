# split arm: my_elixir noise OFF (exact unfloored own elixir)

Run dirs: `scratchpad\gauntlet\L67\e1\attrib_split\off_my_elixir\slot0`. Duplicates dropped: 0.
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

Decided BEFORE the ghost script ended (end <= last ghost tick + 200): 32/77 = 41.6%. Wins after the script ended: 20 (38.5% of wins).
Wins where the real pro lost: 24 of 46 such matches.

| ghost plays delivered | n | wins | winrate | share of wins |
|---|---|---|---|---|
| <=10 | 6 | 3 | 50.0% | 5.8% |
| 11-30 | 71 | 35 | 49.3% | 67.3% |
| >30 | 23 | 14 | 60.9% | 26.9% |

| distinct ghost cards delivered | n | wins | winrate | share of wins |
|---|---|---|---|---|
| <=3 | 1 | 1 | 100.0% | 1.9% |
| 4-6 | 9 | 3 | 33.3% | 5.8% |
| >6 | 90 | 48 | 53.3% | 92.3% |

| plays/min | accepted/min | accepted frac | attempted/match | stall fires/match | no-affordable/match | mean s | mean s won | ghost refused/match | wall s/match |
|---|---|---|---|---|---|---|---|---|---|
| 13.38 | 11.88 | 88.8% | 42.6 | 0.04 | 208.9 | 191.3 | 197.1 | 0.82 | 10.9 |

Matches whose degraded-observation count != decisions: 0. Policies: {'live': 100}.

