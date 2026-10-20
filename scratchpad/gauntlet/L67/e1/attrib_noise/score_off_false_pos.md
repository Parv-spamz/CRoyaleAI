# noise attrib arm: false-positive noise OFF (phantom detections removed)

Run dirs: `scratchpad\gauntlet\L67\e1\attrib_noise\off_false_pos\slot0`. Duplicates dropped: 0.
Bootstrap: entry-clustered, 10000 draws, seed 20260912.

## Run

| matches | entries | W | D | L | winrate | entry-clustered 95% CI | unclustered normal 95% (contrast only) |
|---|---|---|---|---|---|---|---|
| 100 | 100 | 58 | 0 | 42 | 58.0% | 48.0% .. 68.0% (entry-weighted 58.0%) | 48.3% .. 67.7% |

| per seed k | n | winrate |
|---|---|---|
| 0 | 100 | 58.0% |

| per slot | n | winrate |
|---|---|---|
| 0 | 100 | 58.0% |

Decided BEFORE the ghost script ended (end <= last ghost tick + 200): 39/72 = 54.2%. Wins after the script ended: 19 (32.8% of wins).
Wins where the real pro lost: 27 of 46 such matches.

| ghost plays delivered | n | wins | winrate | share of wins |
|---|---|---|---|---|
| <=10 | 9 | 4 | 44.4% | 6.9% |
| 11-30 | 67 | 40 | 59.7% | 69.0% |
| >30 | 24 | 14 | 58.3% | 24.1% |

| distinct ghost cards delivered | n | wins | winrate | share of wins |
|---|---|---|---|---|
| <=3 | 1 | 1 | 100.0% | 1.7% |
| 4-6 | 7 | 3 | 42.9% | 5.2% |
| >6 | 92 | 54 | 58.7% | 93.1% |

| plays/min | accepted/min | accepted frac | attempted/match | stall fires/match | no-affordable/match | mean s | mean s won | ghost refused/match | wall s/match |
|---|---|---|---|---|---|---|---|---|---|
| 13.33 | 11.92 | 89.4% | 42.9 | 0.00 | 210.0 | 193.1 | 193.2 | 0.60 | 12.7 |

Matches whose degraded-observation count != decisions: 0. Policies: {'live': 100}.

