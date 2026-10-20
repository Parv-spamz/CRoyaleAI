# Pre-emptive Log vs Goblin / Skeleton Barrel -- pros vs bot (2026-10-04)

Same definition as the bot's acceptance telemetry (pipeline/public_outcomes.py summarize: our Log played between the
first and last tick the barrel is visible in flight, +10 ticks; denominator = ALL opposing barrels), same deck (icebow),
icebow side only. Pros: 2,241 public re-drive replays (2,244 icebow sides), replay-cluster bootstrap 2,000, seed 0.

| | n | denominator | rate (95% CI) |
|---|---|---|---|
| Bot gen_v3.1a (299 ghost-screen games, action delay 26 ticks) | 64 | 272 | 23.5% (binomial ~18.5-28.9) |
| Pros, all barrels | 826 | 2,114 | 39.1% (36.7-41.4) |
| Pros, Log in hand and elixir >= 2 in the window | 826 | 1,385 | 59.6% (57.0-62.3) |
| Pros, share of barrels with Log playable | 1,385 | 2,114 | 65.5% (63.1-67.9) |
| Goblin Barrel: all / Log playable | 396/997, 396/594 | | 39.7% / 66.7% |
| Skeleton Barrel: all / Log playable | 430/1,117, 430/791 | | 38.5% / 54.4% |

Comparable: the all-barrels rate (same logic, window, denominator, deck, side): the bot is ~15.6 pp below pros.
NOT yet comparable: the bot's conditional rate (needs its hand/elixir per barrel), and latency -- the bot's screen
runs with a 26-tick (1.3 s) action delay (the live condition) while pros act with their own timing; the delay alone
may push a late Log outside the flight window. Pro frames are every 10 ticks (window edges up to ~10 ticks coarse).
Opponents differ (pro opponents vs the sim's ghost replays). CI clusters by replay, not by player.
Script: barrel_log.py (2.7 min CPU); numbers: results.json, per_barrel.json.
