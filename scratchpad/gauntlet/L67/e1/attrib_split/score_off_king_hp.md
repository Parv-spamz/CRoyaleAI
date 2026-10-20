# split arm: king_hp noise OFF (true king tower hp supplied)

Run dirs: `scratchpad\gauntlet\L67\e1\attrib_split\off_king_hp\slot0`. Duplicates dropped: 0.
Bootstrap: entry-clustered, 10000 draws, seed 20260912.

## Run

| matches | entries | W | D | L | winrate | entry-clustered 95% CI | unclustered normal 95% (contrast only) |
|---|---|---|---|---|---|---|---|
| 100 | 100 | 55 | 0 | 45 | 55.0% | 45.0% .. 65.0% (entry-weighted 55.0%) | 45.2% .. 64.8% |

| per seed k | n | winrate |
|---|---|---|
| 0 | 100 | 55.0% |

| per slot | n | winrate |
|---|---|---|
| 0 | 100 | 55.0% |

Decided BEFORE the ghost script ended (end <= last ghost tick + 200): 39/78 = 50.0%. Wins after the script ended: 16 (29.1% of wins).
Wins where the real pro lost: 25 of 46 such matches.

| ghost plays delivered | n | wins | winrate | share of wins |
|---|---|---|---|---|
| <=10 | 10 | 3 | 30.0% | 5.5% |
| 11-30 | 67 | 33 | 49.3% | 60.0% |
| >30 | 23 | 19 | 82.6% | 34.5% |

| distinct ghost cards delivered | n | wins | winrate | share of wins |
|---|---|---|---|---|
| <=3 | 1 | 1 | 100.0% | 1.8% |
| 4-6 | 8 | 4 | 50.0% | 7.3% |
| >6 | 91 | 50 | 54.9% | 90.9% |

| plays/min | accepted/min | accepted frac | attempted/match | stall fires/match | no-affordable/match | mean s | mean s won | ghost refused/match | wall s/match |
|---|---|---|---|---|---|---|---|---|---|
| 13.22 | 11.88 | 89.9% | 41.7 | 0.00 | 210.3 | 189.4 | 203.4 | 0.72 | 12.1 |

Matches whose degraded-observation count != decisions: 0. Policies: {'live': 100}.

