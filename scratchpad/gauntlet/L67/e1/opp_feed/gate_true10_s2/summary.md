# opp_est_audit summary

n_ticks=7602 n_matches=10 port=38031 split=heldout entries=100:110 decide_every=10 estimator_step=5

| condition | MAE | bias | P90\|err\| | share<=1.0 | share<=2.0 |
|---|---|---|---|---|---|
| A+ perfect detection (+spells, no whitelist) | 1.3195895422257302 | 0.23132324388318865 | 4.0714 | 0.6181268087345435 | 0.7152065245987898 |
| A perfect detection (units only, NO whitelist -- loose upper bound) | 1.3195895422257302 | 0.23132324388318865 | 4.0714 | 0.6181268087345435 | 0.7152065245987898 |
| A_wl perfect detection (units only, live's detector_cards whitelist) | 2.6394081425940543 | 2.4732753617469085 | 6.1843100000000035 | 0.3784530386740331 | 0.47790055248618785 |
| B degraded (live) | 5.487546132596686 | -5.483788805577479 | 9.0 | 0.06945540647198106 | 0.11891607471717969 |
| B_tt IDEALISED: bill once per TeamTracker-confirmed track (min_hits), no whitelist -- a design under test, NOT live's current path | 3.2557724151539067 | -2.9177535516969217 | 6.45312 | 0.232175743225467 | 0.39068666140489344 |
| B_tt_wl live-reachable: B_tt's billing, restricted to live's detector_cards whitelist | 2.740988726650881 | 0.5412046172059984 | 5.93098 | 0.30005261773217573 | 0.4556695606419363 |

## Condition A+ perfect detection (+spells, no whitelist)
- single: n=4620 MAE=0.928910735930736 bias=0.36734242424242425 P90=3.0574000000000003
- double: n=2132 MAE=1.9418999530956846 bias=-0.008447983114446526 P90=4.5724
- overtime: n=850 MAE=1.8821428235294118 bias=0.09342164705882353 P90=4.57264
- opponent-play ticks: n=238 MAE=1.9781012605042017 bias=0.9912071428571428
- our accepted-play ticks: n=351 MAE=1.4746370370370372 bias=0.3151464387464387
- truth>=9.0 (near cap): n=1309 MAE=0.5809408708938121 bias=-0.43677020626432395
- truth<9.0: n=6293 MAE=1.473235038932147 bias=0.3702926267281106
- per-match MAE: n_matches=10 median=1.2301956927367925 p90=1.8643855086686485
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=920.0 total_ghost_delivered=868.0 total_over_charge=52.0 share_from_never_played_bases=0.012
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | boss_bandit | 4 | 24.0 | 13 | 78.0 | 54.0 |
  | miner | 3 | 9.0 | 17 | 51.0 | 42.0 |
  | barbarians | 3 | 15.0 | 8 | 40.0 | 25.0 |
  | fireball | 6 | 24.0 | 0 | 0.0 | -24.0 |
  | lightning | 4 | 24.0 | 0 | 0.0 | -24.0 |
  | zap | 11 | 22.0 | 0 | 0.0 | -22.0 |
  | hog_rider | 6 | 24.0 | 10 | 40.0 | 16.0 |
  | bandit | 4 | 12.0 | 8 | 24.0 | 12.0 |
  | goblin_barrel | 4 | 12.0 | 0 | 0.0 | -12.0 |
  | barbarian_barrel | 5 | 10.0 | 0 | 0.0 | -10.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition A perfect detection (units only, NO whitelist -- loose upper bound)
- single: n=4620 MAE=0.928910735930736 bias=0.36734242424242425 P90=3.0574000000000003
- double: n=2132 MAE=1.9418999530956846 bias=-0.008447983114446526 P90=4.5724
- overtime: n=850 MAE=1.8821428235294118 bias=0.09342164705882353 P90=4.57264
- opponent-play ticks: n=238 MAE=1.9781012605042017 bias=0.9912071428571428
- our accepted-play ticks: n=351 MAE=1.4746370370370372 bias=0.3151464387464387
- truth>=9.0 (near cap): n=1309 MAE=0.5809408708938121 bias=-0.43677020626432395
- truth<9.0: n=6293 MAE=1.473235038932147 bias=0.3702926267281106
- per-match MAE: n_matches=10 median=1.2301956927367925 p90=1.8643855086686485
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=920.0 total_ghost_delivered=868.0 total_over_charge=52.0 share_from_never_played_bases=0.012
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | boss_bandit | 4 | 24.0 | 13 | 78.0 | 54.0 |
  | miner | 3 | 9.0 | 17 | 51.0 | 42.0 |
  | barbarians | 3 | 15.0 | 8 | 40.0 | 25.0 |
  | fireball | 6 | 24.0 | 0 | 0.0 | -24.0 |
  | lightning | 4 | 24.0 | 0 | 0.0 | -24.0 |
  | zap | 11 | 22.0 | 0 | 0.0 | -22.0 |
  | hog_rider | 6 | 24.0 | 10 | 40.0 | 16.0 |
  | bandit | 4 | 12.0 | 8 | 24.0 | 12.0 |
  | goblin_barrel | 4 | 12.0 | 0 | 0.0 | -12.0 |
  | barbarian_barrel | 5 | 10.0 | 0 | 0.0 | -10.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition A_wl perfect detection (units only, live's detector_cards whitelist)
- single: n=4620 MAE=2.4587537662337664 bias=2.367861904761905 P90=6.0534
- double: n=2132 MAE=2.8881301594746716 bias=2.6487171200750472 P90=6.142800000000001
- overtime: n=850 MAE=2.997464470588235 bias=2.6061792941176467 P90=6.6578
- opponent-play ticks: n=238 MAE=3.9784075630252103 bias=3.9138058823529414
- our accepted-play ticks: n=351 MAE=3.0818467236467235 bias=2.973046723646724
- truth>=9.0 (near cap): n=1309 MAE=0.256153705118411 bias=0.12572330022918257
- truth<9.0: n=6293 MAE=3.1351462736373747 bias=2.961587080883522
- per-match MAE: n_matches=10 median=2.38447644862791 p90=3.6855867663568436
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=457.0 total_ghost_delivered=868.0 total_over_charge=-411.0 share_from_never_played_bases=0.0219
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | dark_prince | 14 | 56.0 | 0 | 0.0 | -56.0 |
  | miner | 3 | 9.0 | 17 | 51.0 | 42.0 |
  | executioner | 7 | 35.0 | 0 | 0.0 | -35.0 |
  | golem | 4 | 32.0 | 0 | 0.0 | -32.0 |
  | archer_queen | 5 | 25.0 | 0 | 0.0 | -25.0 |
  | barbarians | 3 | 15.0 | 8 | 40.0 | 25.0 |
  | boss_bandit | 4 | 24.0 | 0 | 0.0 | -24.0 |
  | elite_barbarians | 4 | 24.0 | 0 | 0.0 | -24.0 |
  | fireball | 6 | 24.0 | 0 | 0.0 | -24.0 |
  | lightning | 4 | 24.0 | 0 | 0.0 | -24.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition B degraded (live)
- single: n=4620 MAE=5.550566277056277 bias=-5.544383766233766 P90=9.0
- double: n=2132 MAE=5.261004971857411 bias=-5.261004971857411 P90=8.6406
- overtime: n=850 MAE=5.713231647058824 bias=-5.713231647058824 P90=9.099990000000002
- opponent-play ticks: n=238 MAE=3.7093991596638656 bias=-3.631933613445378
- our accepted-play ticks: n=351 MAE=4.918682905982906 bias=-4.918068660968661
- truth>=9.0 (near cap): n=1309 MAE=8.019363407181054 bias=-8.019363407181054
- truth<9.0: n=6293 MAE=4.960905609407278 bias=-4.956366724932464
- per-match MAE: n_matches=10 median=5.560854900107991 p90=6.131799078734557
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=10099.5 total_ghost_delivered=868.0 total_over_charge=9231.5 share_from_never_played_bases=0.4539
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | knight | 9 | 27.0 | 98 | 294.0 | 267.0 |
  | ice_wizard | 0 | 0.0 | 76 | 228.0 | 228.0 |
  | tesla | 0 | 0.0 | 55 | 220.0 | 220.0 |
  | valkyrie | 0 | 0.0 | 52 | 208.0 | 208.0 |
  | pekka | 2 | 14.0 | 31 | 217.0 | 203.0 |
  | dark_prince | 14 | 56.0 | 64 | 256.0 | 200.0 |
  | balloon | 2 | 10.0 | 40 | 200.0 | 190.0 |
  | wizard | 0 | 0.0 | 38 | 190.0 | 190.0 |
  | mega_knight | 4 | 28.0 | 31 | 217.0 | 189.0 |
  | boss_bandit | 4 | 24.0 | 35 | 210.0 | 186.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition B_tt IDEALISED: bill once per TeamTracker-confirmed track (min_hits), no whitelist -- a design under test, NOT live's current path
- single: n=4620 MAE=3.22118341991342 bias=-2.8927603896103897 P90=6.7576
- double: n=2132 MAE=3.0846178236397748 bias=-2.631549061913696 P90=5.592690000000001
- overtime: n=850 MAE=3.8730697647058823 bias=-3.7714669411764707 P90=7.0
- opponent-play ticks: n=238 MAE=2.4171697478991594 bias=0.09075546218487394
- our accepted-play ticks: n=351 MAE=2.9992629629629626 bias=-2.2912880341880344
- truth>=9.0 (near cap): n=1309 MAE=4.352131627196333 bias=-4.314244996180291
- truth<9.0: n=6293 MAE=3.02771994279358 bias=-2.627270904179247
- per-match MAE: n_matches=10 median=3.2231707177445275 p90=4.315494144162546
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=1640.5 total_ghost_delivered=868.0 total_over_charge=772.5 share_from_never_played_bases=0.2588
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | tombstone | 0 | 0.0 | 17 | 51.0 | 51.0 |
  | valkyrie | 0 | 0.0 | 10 | 40.0 | 40.0 |
  | bowler | 3 | 15.0 | 10 | 50.0 | 35.0 |
  | goblin_drill | 0 | 0.0 | 8 | 32.0 | 32.0 |
  | barbarians | 3 | 15.0 | 9 | 45.0 | 30.0 |
  | boss_bandit | 4 | 24.0 | 9 | 54.0 | 30.0 |
  | giant | 4 | 20.0 | 10 | 50.0 | 30.0 |
  | mega_knight | 4 | 28.0 | 8 | 56.0 | 28.0 |
  | wizard | 0 | 0.0 | 5 | 25.0 | 25.0 |
  | elite_barbarians | 4 | 24.0 | 8 | 48.0 | 24.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition B_tt_wl live-reachable: B_tt's billing, restricted to live's detector_cards whitelist
- single: n=4620 MAE=2.6271532034632035 bias=0.7582136363636364 P90=5.957140000000002
- double: n=2132 MAE=3.0111469981238277 bias=0.3288167917448406 P90=5.9257500000000025
- overtime: n=850 MAE=2.6820977647058823 bias=-0.10558458823529412 P90=5.831510000000001
- opponent-play ticks: n=238 MAE=3.8855378151260505 bias=3.248318487394958
- our accepted-play ticks: n=351 MAE=3.0505831908831906 bias=1.1574299145299145
- truth>=9.0 (near cap): n=1309 MAE=1.6876468296409473 bias=-1.4571021390374332
- truth<9.0: n=6293 MAE=2.9600932146829813 bias=0.9568702049896711
- per-match MAE: n_matches=10 median=2.6974362390141913 p90=3.48585963763684
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=832.0 total_ghost_delivered=868.0 total_over_charge=-36.0 share_from_never_played_bases=0.2007
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | dark_prince | 14 | 56.0 | 0 | 0.0 | -56.0 |
  | valkyrie | 0 | 0.0 | 10 | 40.0 | 40.0 |
  | barbarians | 3 | 15.0 | 10 | 50.0 | 35.0 |
  | bowler | 3 | 15.0 | 10 | 50.0 | 35.0 |
  | executioner | 7 | 35.0 | 0 | 0.0 | -35.0 |
  | golem | 4 | 32.0 | 0 | 0.0 | -32.0 |
  | giant | 4 | 20.0 | 10 | 50.0 | 30.0 |
  | mega_knight | 4 | 28.0 | 8 | 56.0 | 28.0 |
  | archer_queen | 5 | 25.0 | 0 | 0.0 | -25.0 |
  | boss_bandit | 4 | 24.0 | 0 | 0.0 | -24.0 |
  (top 10 shown here; top 25 in summary.json)
