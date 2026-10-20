Audited 201 begun matches (202 selected logs; 1 empty session excluded), with 27 recordings and 7024 play attempts.
Paired 199/201 matches to navigation runs; 197/201 have win/loss outcomes.
Rocket: 72/7024 plays (1.03%); zero in 144/201 (71.6%) matches; median play elixir 6.76 (n=72 plays).
Win rates with/without Rocket: with 37/57 (64.9%); without 63/140 (45.0%); descriptive only.
At measured 497-HP Rocket damage (n=3 drops), 14 finish-off periods across 6/27 recordings: 0 Rocket conversions, 6 other deaths, 8 survived to end, 0 unresolved (n=14 periods).
Median damage concentration: 71.9% (n=26 end-covered matches); both enemy princess towers below half, neither destroyed: 3/26 end-covered matches.
Recorded X-Bows: 117/117 (100.0%) defensive; 0/0 (undefined) offensive placements in a dead lane.
At 1-1: 8 X-Bows across 4 recordings; 5 in the destroyed-princess lane, 3 in the remaining-princess lane (n=8 placements).
S1 Icebow replay proxy: Rocket 1267/21687 (5.8%) of plays; median simulated elixir 8.72 (n=1267 Rocket plays; 493 replays).
Limits: 1/201 begun logs lack an end; 1/27 recordings lack covered normal ends; hand availability and causal Rocket kills are unverified.

## Scope and methods

This is a descriptive audit of existing files, with no bot changes or play-quality verdict. A includes every selected log with a play or frame; empty sessions are excluded. Partial matches contribute only observed plays. All card and placement counts use `play` decisions, with confirmation receipts retained in JSON.

Inputs: `scratchpad/gauntlet/L68/live_reader/live_play_20261002_2*.jsonl` and `live_play_20261003_*.jsonl`, filtered by `start.ckpt` containing `league1c`; navigation glob `ladder_nav_2026100[23]_*.jsonl`. Every input snapshot has a byte count and SHA-256 in `audit.json.source_manifest`. `input_manifest.json` freezes the first successful audit file list and exact byte prefixes because source logs were growing. Later runs read only those prefixes and reject hash mismatches; new logs and appended bytes are excluded. Card/dataset/source-code artifact hashes are in `artifact_sources`.

Outcome pairing: filename local EDT start + `end.seconds` estimates the log end. Require exactly one nav start in [-1, +30] seconds, before the next selected live log starts, and enforce one-to-one use. The filename has one-second resolution; setup before the elapsed-time timer can add a few seconds. Missing/null outcomes are excluded from binary win-rate denominators, not counted as losses.

Pairing gaps: median 5.99 s, range 0.01–8.63 s (n=199 pairs). Empty sessions (n=1): live_play_20261002_213044.jsonl.

Tower identification: choose the largest-max-HP entity within 500 native units of each expected static location in the first frame; verify card_id=-1 and match address, side, position and max HP together. Freed addresses can be reused by troops; those are not towers. Native princess centres are (3500,6500)/(14500,6500) for side 0 and (3500,25500)/(14500,25500) for side 1; kings are (9000,3000)/(9000,29000). Kind alone is not used, because it changes. Our coordinates exactly follow `live_play.py:158-160`: side 0=(x/18000,1-y/32000), side 1=(1-x/18000,y/32000). Our-frame x<0.5 is left; enemy princess y=0.203125. Tower HP/max HP and observed kinds appear per match in JSON.

A tower is dead after explicit zero HP or disappearance lasting at least three samples and 0.19 seconds through the recording end, backdated to first absence. Short missing runs remain unknown. The last observed state counts as match-end-covered only with a normal battle-over stop within 20 ticks (1 game second). Tick-stalled and missing-end recordings are censored. Final observed state is still reported for all recordings.

Finish-off periods: maximal continuous sampled runs with 0<enemy princess HP<=497 and our elixir>=6, duration>=2 seconds on `t_dev`; gaps>0.5 seconds or failed/unknown conditions break a run. Dead towers are excluded. A response is a confirmed Rocket cast aimed within 3.5 tiles of that tower centre, during the run or through +5 seconds. This is an operational targeting proxy, not verified hitbox geometry or proof of a kill. If no response, classify a later tower death as other only if no nearby confirmed Rocket was cast in its preceding 7 seconds and no simultaneous king collapse; otherwise mark ambiguous. A surviving tower requires a covered end; all other cases are censored. Each period is counted, so repeated periods can share one eventual death.

Damage concentration = max(maxHP-left_finalHP, maxHP-right_finalHP) / summed enemy princess HP loss. Unknown HP or zero total damage makes the ratio undefined. Missing destroyed towers are zero as above. These are HP-loss totals, not attacker-attributed damage; king-collapse and tiebreak HP changes are included. The both-below-half test is strictly 0<HP<0.5*maxHP for both towers.

X-Bow classification uses intended play xy and the last frame at or before the play (maximum age 10 ticks). Defensive means y>0.58; every other placement is offensive. Dead-lane means the enemy princess in that x lane is dead. A 1-1 score requires one destroyed princess on each side and both kings alive; unknown states remain unclassified. The per-placement JSON also retains receipt and observed spawn coordinates.

## Rocket damage evidence

`icebow/config/cards_stats.json` says level 11 crown damage 341 HP. The bot's Rocket level is not logged. Use the repeated measured 497-HP drop instead (n=3 supporting steps / 3 candidate steps). Candidates are positive, nonlethal 300–700 HP steps within 3–6 seconds of a confirmed nearby Rocket, with adjacent frames no more than 0.5 seconds apart.

| Match | Rocket tick | HP-step ticks | HP before → after | Drop | Delay (s) |
|---|---:|---|---|---:|---:|
| live_play_20261002_204204.jsonl | 1505 | 1595→1597 | 3938→3441 | 497 | 4.606 |
| live_play_20261003_021629.jsonl | 4642 | 4732→4734 | 3883→3386 | 497 | 4.607 |
| live_play_20261003_081246.jsonl | 3380 | 3465→3466 | 1212→715 | 497 | 4.319 |

Recorded Rocket attempts (n=5 plays in 27 recordings); nearest-princess HP at play and later disappearance timing:

| Match | Play tick | Receipt | Nearest tower | Distance (tiles) | HP at play | Later death delay (s) |
|---|---:|---|---|---:|---:|---:|
| live_play_20261002_204204.jsonl | 1505 | confirmed | enemy_right | 1.415 | 3938 | not observed |
| live_play_20261002_211210.jsonl | 2654 | confirmed | enemy_right | 2.828 | 482 | 2.303 |
| live_play_20261003_000535.jsonl | 3119 | confirmed | enemy_right | 2.828 | 225 | 1.005 |
| live_play_20261003_021629.jsonl | 4642 | confirmed | enemy_right | 1.415 | 3938 | 46.316 |
| live_play_20261003_081246.jsonl | 3380 | confirmed | enemy_left | 2.828 | 1212 | 124.875 |

Threshold sensitivity (same n=27 recordings): 341 HP: 11 periods, 497 HP: 14 periods.

## A. All begun matches

All per-match distributions include zeros (n=201 matches). Elixir denominators are play attempts.

| Card | Plays / all plays | Mean/match | Median/match | Counts per match: matches | Median elixir (n plays) | Receipts |
|---|---|---:|---:|---|---|---|
| IceWizard | 1175/7024 (16.7%) | 5.846 | 5 | {"0": 1, "1": 3, "2": 3, "3": 4, "4": 43, "5": 60, "6": 29, "7": 19, "8": 11, "9": 13, "10": 3, "11": 8, "12": 1, "13": 2, "14": 1} | 4.7794 (n=1175) | {"confirmed": 1113, "missing": 24, "unconfirmed": 38} |
| Knight | 1259/7024 (17.9%) | 6.264 | 6 | {"1": 2, "2": 5, "3": 5, "4": 21, "5": 62, "6": 39, "7": 19, "8": 14, "9": 8, "10": 14, "11": 3, "12": 5, "13": 2, "14": 2} | 4.9944 (n=1259) | {"confirmed": 1178, "unconfirmed": 65, "missing": 16} |
| Log | 1140/7024 (16.2%) | 5.672 | 5 | {"1": 1, "2": 4, "3": 15, "4": 39, "5": 53, "6": 39, "7": 17, "8": 10, "9": 9, "10": 8, "11": 4, "13": 1, "14": 1} | 4.2166 (n=1140) | {"confirmed": 1092, "missing": 9, "unconfirmed": 39} |
| Rocket | 72/7024 (1.0%) | 0.358 | 0 | {"0": 144, "1": 46, "2": 9, "3": 1, "5": 1} | 6.7553 (n=72) | {"confirmed": 59, "missing": 9, "unconfirmed": 4} |
| Skeletons | 1236/7024 (17.6%) | 6.149 | 6 | {"1": 3, "2": 2, "3": 6, "4": 22, "5": 61, "6": 44, "7": 18, "8": 18, "9": 7, "10": 10, "11": 4, "12": 2, "13": 3, "14": 1} | 3.8792 (n=1236) | {"confirmed": 1193, "unconfirmed": 19, "missing": 24} |
| Tesla | 927/7024 (13.2%) | 4.612 | 4 | {"0": 3, "1": 13, "2": 15, "3": 37, "4": 39, "5": 39, "6": 23, "7": 6, "8": 12, "9": 6, "10": 4, "12": 2, "13": 1, "15": 1} | 5.7160 (n=927) | {"confirmed": 858, "unconfirmed": 46, "missing": 23} |
| Tornado | 445/7024 (6.3%) | 2.214 | 2 | {"0": 26, "1": 48, "2": 51, "3": 36, "4": 24, "5": 8, "6": 5, "7": 3} | 3.4914 (n=445) | {"confirmed": 395, "unconfirmed": 43, "missing": 7} |
| Xbow | 770/7024 (11.0%) | 3.831 | 4 | {"0": 1, "1": 13, "2": 26, "3": 55, "4": 50, "5": 24, "6": 17, "7": 8, "8": 3, "9": 2, "10": 2} | 7.6179 (n=770) | {"confirmed": 717, "unconfirmed": 23, "missing": 30} |

| Rocket group | Matches | W / L / null / unknown | Win rate (known binary outcomes) |
|---|---:|---|---|
| rocket_ge_1 | 57 | 37 / 20 / 0 / 0 | 37/57 (64.9%) |
| rocket_0 | 144 | 63 / 77 / 0 / 4 | 63/140 (45.0%) |

Descriptive only: match duration, deck/opponent, match state, and selection can affect both Rocket use and outcome; this split does not estimate an effect of playing Rocket.

All-log X-Bow defensive placement share: 770/770 (100.0%).

## B. Recorded matches

Frame sample n=27; covered normal ends n=26; opportunities n=14 periods on 7 towers in 6 matches. Status counts (denominator 14 periods): {"died_other": 6, "expired_survived_end": 8}.

Any Rocket attempted anywhere during period/+5 s: 0/14 periods; thus the zero-conversion finding does not depend on target-radius choice. Other-death periods refer to 3 unique towers; 1/6 such period outcomes died within +5 s, with the rest dying later in the recording.

| Match | Lane | Start–end tick | Duration (s) | Start/min HP | Status | Rocket attempt ticks | Death tick | Outcome |
|---|---|---|---:|---|---|---|---|---|
| live_play_20261002_213943.jsonl | enemy_left | 4705–4850 | 7.21 | 462/462 | expired_survived_end | [] | None | loss |
| live_play_20261002_213943.jsonl | enemy_left | 6110–6171 | 3.90 | 145/145 | expired_survived_end | [] | None | loss |
| live_play_20261002_223100.jsonl | enemy_right | 3837–3877 | 2.00 | 444/444 | died_other | [] | 4634 | win |
| live_play_20261002_223100.jsonl | enemy_right | 4005–4154 | 7.42 | 314/267 | died_other | [] | 4634 | win |
| live_play_20261002_223100.jsonl | enemy_right | 4426–4530 | 5.21 | 267/267 | died_other | [] | 4634 | win |
| live_play_20261002_233441.jsonl | enemy_left | 1068–1180 | 5.61 | 82/82 | died_other | [] | 2137 | loss |
| live_play_20261002_233441.jsonl | enemy_left | 1967–2051 | 4.20 | 35/35 | died_other | [] | 2137 | loss |
| live_play_20261003_010938.jsonl | enemy_right | 3222–3310 | 4.41 | 472/472 | died_other | [] | 3629 | win |
| live_play_20261003_024942.jsonl | enemy_left | 3418–3476 | 2.91 | 323/323 | expired_survived_end | [] | None | win |
| live_play_20261003_024942.jsonl | enemy_left | 3586–3681 | 5.31 | 323/323 | expired_survived_end | [] | None | win |
| live_play_20261003_035713.jsonl | enemy_left | 2604–2740 | 6.81 | 203/203 | expired_survived_end | [] | None | loss |
| live_play_20261003_035713.jsonl | enemy_left | 3109–3185 | 3.80 | 167/167 | expired_survived_end | [] | None | loss |
| live_play_20261003_035713.jsonl | enemy_left | 3529–3681 | 8.11 | 167/167 | expired_survived_end | [] | None | loss |
| live_play_20261003_035713.jsonl | enemy_right | 3536–3681 | 7.71 | 435/341 | expired_survived_end | [] | None | loss |

Tower validation (n=162 towers): princess max-HP distribution (n=108) {"3571": 2, "3918": 2, "4013": 6, "4032": 28, "4424": 70}; king max-HP distribution (n=54) {"6408": 15, "7032": 39}. Address reuse after removal affects 4/162 towers and is ignored. Death/endpoint classifications (n=162): {"alive_at_endpoint": 125, "persistent_disappearance": 35, "explicit_zero_hp": 2}. HP increases: 0; transient missing samples: 0 (over all 162 tower tracks).

Damage concentration at covered ends: median 0.7190, mean 0.7218 (n=26). All observed recording endpoints, including censored: median 0.7211 (n=27).

| Match | End covered | Enemy left HP/max | Enemy right HP/max | Left/right damage | Concentration | Both low at end | Outcome |
|---|---|---|---|---|---:|---|---|
| live_play_20261002_201818.jsonl | True | 681/4032 | 675/4032 | 3351/3357 | 0.5004 | True | unknown |
| live_play_20261002_203116.jsonl | True | 0/4424 | 0/4424 | 4424/4424 | 0.5000 | False | win |
| live_play_20261002_204204.jsonl | True | 0/4032 | 2581/4032 | 4032/1451 | 0.7354 | False | win |
| live_play_20261002_211210.jsonl | True | 1272/4424 | 0/4424 | 3152/4424 | 0.5839 | False | win |
| live_play_20261002_213943.jsonl | True | 145/4424 | 3518/4424 | 4279/906 | 0.8253 | False | loss |
| live_play_20261002_215217.jsonl | False | 3949/4032 | 2763/4032 | 83/1269 | 0.9386 | False | unknown |
| live_play_20261002_215926.jsonl | True | 1615/4424 | 2442/4424 | 2809/1982 | 0.5863 | False | loss |
| live_play_20261002_223100.jsonl | True | 2461/4013 | 0/4013 | 1552/4013 | 0.7211 | False | win |
| live_play_20261002_230259.jsonl | True | 1839/4424 | 0/4424 | 2585/4424 | 0.6312 | False | win |
| live_play_20261002_233441.jsonl | True | 0/4424 | 2849/4424 | 4424/1575 | 0.7375 | False | loss |
| live_play_20261003_000535.jsonl | True | 2440/4032 | 0/4032 | 1592/4032 | 0.7169 | False | loss |
| live_play_20261003_003811.jsonl | True | 764/4032 | 3709/4032 | 3268/323 | 0.9101 | False | loss |
| live_play_20261003_010938.jsonl | True | 4032/4032 | 0/4032 | 0/4032 | 1.0000 | False | win |
| live_play_20261003_014333.jsonl | True | 1039/3571 | 1695/3571 | 2532/1876 | 0.5744 | True | loss |
| live_play_20261003_021629.jsonl | True | 2111/4032 | 0/4032 | 1921/4032 | 0.6773 | False | win |
| live_play_20261003_024942.jsonl | True | 323/4032 | 0/4032 | 3709/4032 | 0.5209 | False | win |
| live_play_20261003_032324.jsonl | True | 1787/4032 | 0/4032 | 2245/4032 | 0.6423 | False | win |
| live_play_20261003_035713.jsonl | True | 167/4032 | 341/4032 | 3865/3691 | 0.5115 | True | loss |
| live_play_20261003_043035.jsonl | True | 3600/3918 | 2414/3918 | 318/1504 | 0.8255 | False | loss |
| live_play_20261003_050148.jsonl | True | 3158/4032 | 3985/4032 | 874/47 | 0.9490 | False | loss |
| live_play_20261003_053419.jsonl | True | 0/4032 | 0/4032 | 4032/4032 | 0.5000 | False | win |
| live_play_20261003_060432.jsonl | True | 3515/4032 | 0/4032 | 517/4032 | 0.8863 | False | win |
| live_play_20261003_063831.jsonl | True | 0/4424 | 3459/4424 | 4424/965 | 0.8209 | False | loss |
| live_play_20261003_070921.jsonl | True | 980/4013 | 3872/4013 | 3033/141 | 0.9556 | False | loss |
| live_play_20261003_074144.jsonl | True | 2013/4424 | 3409/4424 | 2411/1015 | 0.7037 | False | loss |
| live_play_20261003_081246.jsonl | True | 0/4032 | 3335/4032 | 4032/697 | 0.8526 | False | win |
| live_play_20261003_084518.jsonl | True | 839/4013 | 3659/4013 | 3174/354 | 0.8997 | False | loss |

Both low, neither destroyed at covered end: 3/26 matches; outcomes (n=3): {"unknown": 1, "loss": 2}. The qualifying matches are marked above.

Intended X-Bow y distribution, all logs (n=770 placements): {"0.6094": 746, "0.7031": 24}.

Recorded X-Bow placements n=117 in 27/27 matches. Defensive 117/117 (100.0%); offensive n=0, lane states {}. Receipts (n=117): {"confirmed": 104, "missing": 5, "unconfirmed": 8}. Observed-spawn defensive share: 104/104 (100.0%) (only receipts with spawn coordinates).

1-1 placements: n=8 in 4 matches. Each row is one placement; all placements are also in JSON.

| Match | Tick | Intended xy | Defensive | Lane | Enemy lane HP | Remaining princess lane | Receipt |
|---|---:|---|---|---|---:|---|---|
| live_play_20261002_233441.jsonl | 2664 | [0.1389, 0.6094] | True | left | 0 | False | confirmed |
| live_play_20261002_233441.jsonl | 3128 | [0.1389, 0.6094] | True | left | 0 | False | confirmed |
| live_play_20261003_000535.jsonl | 3344 | [0.1389, 0.6094] | True | left | 3662 | True | confirmed |
| live_play_20261003_053419.jsonl | 2456 | [0.1389, 0.6094] | True | left | 0 | False | confirmed |
| live_play_20261003_053419.jsonl | 3610 | [0.8611, 0.6094] | True | right | 3410 | True | confirmed |
| live_play_20261003_053419.jsonl | 4958 | [0.8611, 0.6094] | True | right | 2071 | True | confirmed |
| live_play_20261003_063831.jsonl | 2427 | [0.1389, 0.6094] | True | left | 0 | False | confirmed |
| live_play_20261003_063831.jsonl | 3046 | [0.1389, 0.6094] | True | left | 0 | False | confirmed |

## C. Existing replay comparison

Generalist metadata `icebow/data/pipeline/gen_dataset_v2.json`: Rocket 9176/928165 (1.0%) across 14661 source replays. Mixed decks; not deck-matched; metadata has no elixir-at-play.

S1 `icebow/data/pipeline/s1_dataset.npz`: 21687 accepted PLAY rows, 493 replays, 495 replay sides. Use `y_gate==1`, card slot from embedded `meta.cards`, and sc[:,3] * 10; pipeline/obs_contract.py:569,614-615. WAIT rows are excluded; dataset is the unaugmented, unshifted S1 file. Existing replay-engine states for the Icebow corpus; original live elixir and player pro status are not independently verified. Not a causal or skill ranking.

| Card | Share of S1 plays | Median simulated elixir (n plays) |
|---|---|---|
| tornado | 1757/21687 (8.1%) | 5.9096 (n=1757) |
| tesla_evo | 3046/21687 (14.0%) | 7.8544 (n=3046) |
| ice_wizard | 3423/21687 (15.8%) | 7.6362 (n=3423) |
| x_bow | 1978/21687 (9.1%) | 8.7477 (n=1978) |
| rocket | 1267/21687 (5.8%) | 8.7206 (n=1267) |
| knight_evo | 3523/21687 (16.2%) | 7.6057 (n=3523) |
| the_log | 3132/21687 (14.4%) | 6.5098 (n=3132) |
| skeletons | 3561/21687 (16.4%) | 6.2247 (n=3561) |

For a verified live-pro elixir comparison, the needed data are player/provenance labels plus original time-aligned card-play and pre-play elixir observations for matching Icebow decks. Existing S1 engine-derived states cannot verify those facts.

## Concerns

- 1 begun match log(s) lack an end event; included in observed-play counts and excluded from end-state claims: live_play_20261003_085511.jsonl
- 1/27 recordings lack covered normal match ends: live_play_20261002_215217.jsonl
- 4/201 matches lack a binary paired outcome: live_play_20261002_201818.jsonl, live_play_20261002_214507.jsonl, live_play_20261002_215217.jsonl, live_play_20261003_085511.jsonl
- Source logs grew during inspection. input_manifest.json freezes the first successful audit file list and byte prefixes; reruns verify SHA-256 and ignore later appends/new logs.
- Play events are decisions/tap attempts; receipt counts are reported separately. A confirmed cast is not proof of a Rocket kill.
- Frame logs are a recording-selected subset, not a random sample. No hand contents are logged: HP/elixir opportunities do not establish Rocket availability.
- Rocket damage is measured from repeated HP steps; exact card level and exclusive damage attribution are not recorded.
- Tower destruction is inferred from persistent disappearance when zero HP is absent; final-frame damage can include king-collapse and tiebreak effects.
- Opportunity periods use sampled device time, split on gaps over 0.5 s; counts are period-level and can revisit the same tower.
- Rocket-on-tower uses a declared 3.5-tile centre-distance proxy; confirmed-target casts and causal kills are distinct.
- All logged X-Bows are defensive under the requested y>0.58 rule; there is no offensive sample for a dead-lane rate.
- S1 comparison uses accepted replay-engine plays and simulated elixir; mixed-deck generalist share is contextual only, and original player pro status is unverified.

## Reproduction

`python scratchpad/gauntlet/L70/audit/play_audit.py`

Single process; standard library plus numpy for selective S1 arrays. No device connections, project imports, engine execution, GPU work, or writes outside this audit directory.
