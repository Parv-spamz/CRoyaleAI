# noise attrib arm: unit HP noise OFF (exact per-unit hp_frac supplied)

Run dirs: `scratchpad\gauntlet\L67\e1\attrib_noise\off_unit_hp\slot0`. Duplicates dropped: 0.
Bootstrap: entry-clustered, 10000 draws, seed 20260912.

## Run

| matches | entries | W | D | L | winrate | entry-clustered 95% CI | unclustered normal 95% (contrast only) |
|---|---|---|---|---|---|---|---|
| 100 | 100 | 49 | 0 | 51 | 49.0% | 39.0% .. 59.0% (entry-weighted 49.0%) | 39.2% .. 58.8% |

| per seed k | n | winrate |
|---|---|---|
| 0 | 100 | 49.0% |

| per slot | n | winrate |
|---|---|---|
| 0 | 100 | 49.0% |

Decided BEFORE the ghost script ended (end <= last ghost tick + 200): 30/74 = 40.5%. Wins after the script ended: 19 (38.8% of wins).
Wins where the real pro lost: 27 of 46 such matches.

| ghost plays delivered | n | wins | winrate | share of wins |
|---|---|---|---|---|
| <=10 | 6 | 3 | 50.0% | 6.1% |
| 11-30 | 68 | 33 | 48.5% | 67.3% |
| >30 | 26 | 13 | 50.0% | 26.5% |

| distinct ghost cards delivered | n | wins | winrate | share of wins |
|---|---|---|---|---|
| <=3 | 1 | 1 | 100.0% | 2.0% |
| 4-6 | 7 | 3 | 42.9% | 6.1% |
| >6 | 92 | 45 | 48.9% | 91.8% |

| plays/min | accepted/min | accepted frac | attempted/match | stall fires/match | no-affordable/match | mean s | mean s won | ghost refused/match | wall s/match |
|---|---|---|---|---|---|---|---|---|---|
| 13.31 | 11.94 | 89.7% | 43.0 | 0.00 | 207.2 | 193.8 | 198.7 | 0.67 | 12.9 |

Matches whose degraded-observation count != decisions: 0. Policies: {'live': 100}.

