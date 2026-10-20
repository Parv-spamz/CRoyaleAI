# opp_est_audit summary

n_ticks=6387 n_matches=10 port=38031 split=heldout entries=0:10 decide_every=10 estimator_step=5

| condition | MAE | bias | P90\|err\| | share<=1.0 | share<=2.0 |
|---|---|---|---|---|---|
| A+ perfect detection (+spells, no whitelist) | 1.4286437920776578 | -0.6622122905902614 | 3.4738800000000047 | 0.542351651792704 | 0.6785658368561139 |
| A perfect detection (units only, NO whitelist -- loose upper bound) | 1.4286437920776578 | -0.6622122905902614 | 3.4738800000000047 | 0.542351651792704 | 0.6785658368561139 |
| A_wl perfect detection (units only, live's detector_cards whitelist) | 2.234078957256928 | 1.6961403006106155 | 5.36808 | 0.40911225927665573 | 0.5398465633317676 |
| B degraded (live) | 5.986912306247064 | -5.984036777829967 | 9.3878 | 0.05229372162204478 | 0.08720839204634413 |
| B_tt IDEALISED: bill once per TeamTracker-confirmed track (min_hits), no whitelist -- a design under test, NOT live's current path | 3.7844967433850005 | -3.621425223109441 | 7.74694 | 0.2008767809613277 | 0.31971191482699235 |
| B_tt_wl live-reachable: B_tt's billing, restricted to live's detector_cards whitelist | 2.994154924064506 | -0.6528953968999531 | 6.946960000000003 | 0.2786910912791608 | 0.4516987631125724 |

## Condition A+ perfect detection (+spells, no whitelist)
- single: n=4446 MAE=1.147548088169141 bias=-0.5802065677013045 P90=3.170200000000001
- double: n=1702 MAE=2.019325205640423 bias=-0.7951898354876615 P90=5.2535
- overtime: n=239 MAE=2.4512870292887032 bias=-1.2407464435146442 P90=4.964300000000001
- opponent-play ticks: n=186 MAE=1.9239537634408603 bias=-0.11763118279569891
- our accepted-play ticks: n=300 MAE=1.5452253333333335 bias=-0.6668626666666666
- truth>=9.0 (near cap): n=1442 MAE=0.9650655339805825 bias=-0.8551710818307906
- truth<9.0: n=4945 MAE=1.563826774519717 bias=-0.6059440242669363
- per-match MAE: n_matches=10 median=1.2713197036747548 p90=2.418175564954079
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=732.0 total_ghost_delivered=657.0 total_over_charge=75.0 share_from_never_played_bases=0.0628
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | barbarians | 0 | 0.0 | 9 | 45.0 | 45.0 |
  | bandit | 4 | 12.0 | 14 | 42.0 | 30.0 |
  | miner | 2 | 6.0 | 11 | 33.0 | 27.0 |
  | barbarian_barrel | 9 | 18.0 | 0 | 0.0 | -18.0 |
  | goblinstein | 4 | 20.0 | 7 | 35.0 | 15.0 |
  | witch | 4 | 20.0 | 7 | 35.0 | 15.0 |
  | giant_snowball | 7 | 14.0 | 0 | 0.0 | -14.0 |
  | lightning | 2 | 12.0 | 0 | 0.0 | -12.0 |
  | royal_ghost | 4 | 12.0 | 8 | 24.0 | 12.0 |
  | bowler | 4 | 20.0 | 2 | 10.0 | -10.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition A perfect detection (units only, NO whitelist -- loose upper bound)
- single: n=4446 MAE=1.147548088169141 bias=-0.5802065677013045 P90=3.170200000000001
- double: n=1702 MAE=2.019325205640423 bias=-0.7951898354876615 P90=5.2535
- overtime: n=239 MAE=2.4512870292887032 bias=-1.2407464435146442 P90=4.964300000000001
- opponent-play ticks: n=186 MAE=1.9239537634408603 bias=-0.11763118279569891
- our accepted-play ticks: n=300 MAE=1.5452253333333335 bias=-0.6668626666666666
- truth>=9.0 (near cap): n=1442 MAE=0.9650655339805825 bias=-0.8551710818307906
- truth<9.0: n=4945 MAE=1.563826774519717 bias=-0.6059440242669363
- per-match MAE: n_matches=10 median=1.2713197036747548 p90=2.418175564954079
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=732.0 total_ghost_delivered=657.0 total_over_charge=75.0 share_from_never_played_bases=0.0628
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | barbarians | 0 | 0.0 | 9 | 45.0 | 45.0 |
  | bandit | 4 | 12.0 | 14 | 42.0 | 30.0 |
  | miner | 2 | 6.0 | 11 | 33.0 | 27.0 |
  | barbarian_barrel | 9 | 18.0 | 0 | 0.0 | -18.0 |
  | goblinstein | 4 | 20.0 | 7 | 35.0 | 15.0 |
  | witch | 4 | 20.0 | 7 | 35.0 | 15.0 |
  | giant_snowball | 7 | 14.0 | 0 | 0.0 | -14.0 |
  | lightning | 2 | 12.0 | 0 | 0.0 | -12.0 |
  | royal_ghost | 4 | 12.0 | 8 | 24.0 | 12.0 |
  | bowler | 4 | 20.0 | 2 | 10.0 | -10.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition A_wl perfect detection (units only, live's detector_cards whitelist)
- single: n=4446 MAE=1.8634285650022493 bias=1.2210028340080972 P90=4.9466
- double: n=1702 MAE=3.0964071680376026 bias=2.841985546415981 P90=6.5022
- overtime: n=239 MAE=2.9881753138075315 bias=2.3749376569037657 P90=5.922140000000001
- opponent-play ticks: n=186 MAE=3.5893618279569894 bias=3.282613440860215
- our accepted-play ticks: n=300 MAE=2.3713040000000003 bias=1.8594873333333333
- truth>=9.0 (near cap): n=1442 MAE=0.5192036754507628 bias=-0.20202475728155342
- truth<9.0: n=4945 MAE=2.7341497674418607 bias=2.249659817997978
- per-match MAE: n_matches=10 median=2.021608204159002 p90=3.1473312910493223
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=362.0 total_ghost_delivered=657.0 total_over_charge=-295.0 share_from_never_played_bases=0.1243
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | barbarians | 0 | 0.0 | 9 | 45.0 | 45.0 |
  | archer_queen | 7 | 35.0 | 0 | 0.0 | -35.0 |
  | miner | 2 | 6.0 | 11 | 33.0 | 27.0 |
  | cannon_cart | 4 | 20.0 | 0 | 0.0 | -20.0 |
  | goblinstein | 4 | 20.0 | 0 | 0.0 | -20.0 |
  | barbarian_barrel | 9 | 18.0 | 0 | 0.0 | -18.0 |
  | three_musketeers | 2 | 18.0 | 0 | 0.0 | -18.0 |
  | bomb_tower | 4 | 16.0 | 0 | 0.0 | -16.0 |
  | lumberjack | 4 | 16.0 | 0 | 0.0 | -16.0 |
  | mortar | 4 | 16.0 | 0 | 0.0 | -16.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition B degraded (live)
- single: n=4446 MAE=6.010353261358524 bias=-6.007804633378318 P90=9.4116
- double: n=1702 MAE=5.84414330199765 bias=-5.840010047003525 P90=9.17694
- overtime: n=239 MAE=6.5675581589958165 bias=-6.5675581589958165 P90=10.0
- opponent-play ticks: n=186 MAE=4.202920967741935 bias=-4.168182258064516
- our accepted-play ticks: n=300 MAE=5.785390333333333 bias=-5.775721
- truth>=9.0 (near cap): n=1442 MAE=8.379437031900139 bias=-8.379437031900139
- truth<9.0: n=4945 MAE=5.289233710819009 bias=-5.285519656218402
- per-match MAE: n_matches=10 median=5.782314150354218 p90=7.001045159590019
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=9539.0 total_ghost_delivered=657.0 total_over_charge=8882.0 share_from_never_played_bases=0.4853
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | knight | 0 | 0.0 | 84 | 252.0 | 252.0 |
  | wizard | 0 | 0.0 | 42 | 210.0 | 210.0 |
  | mega_knight | 4 | 28.0 | 33 | 231.0 | 203.0 |
  | giant | 5 | 25.0 | 44 | 220.0 | 195.0 |
  | boss_bandit | 0 | 0.0 | 29 | 174.0 | 174.0 |
  | musketeer | 2 | 8.0 | 45 | 180.0 | 172.0 |
  | valkyrie | 3 | 12.0 | 46 | 184.0 | 172.0 |
  | barbarians | 0 | 0.0 | 32 | 160.0 | 160.0 |
  | electro_dragon | 1 | 5.0 | 33 | 165.0 | 160.0 |
  | goblinstein | 4 | 20.0 | 36 | 180.0 | 160.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition B_tt IDEALISED: bill once per TeamTracker-confirmed track (min_hits), no whitelist -- a design under test, NOT live's current path
- single: n=4446 MAE=3.722942555105713 bias=-3.606657534862798 P90=7.7498000000000005
- double: n=1702 MAE=3.843938601645123 bias=-3.601173384253819 P90=7.39094
- overtime: n=239 MAE=4.506253556485356 bias=-4.040361506276151 P90=9.0
- opponent-play ticks: n=186 MAE=2.490429569892473 bias=-0.735386559139785
- our accepted-play ticks: n=300 MAE=3.409076333333333 bias=-3.1440543333333335
- truth>=9.0 (near cap): n=1442 MAE=4.7911452149791955 bias=-4.772987656033287
- truth<9.0: n=4945 MAE=3.490950313447927 bias=-3.285620768452983
- per-match MAE: n_matches=10 median=3.7936843532684286 p90=4.8176480189854765
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=1434.0 total_ghost_delivered=657.0 total_over_charge=777.0 share_from_never_played_bases=0.2497
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | barbarians | 0 | 0.0 | 10 | 50.0 | 50.0 |
  | mortar | 4 | 16.0 | 15 | 60.0 | 44.0 |
  | goblin_drill | 0 | 0.0 | 10 | 40.0 | 40.0 |
  | barbarian_hut | 0 | 0.0 | 6 | 36.0 | 36.0 |
  | goblin_cage | 0 | 0.0 | 9 | 36.0 | 36.0 |
  | goblinstein | 4 | 20.0 | 11 | 55.0 | 35.0 |
  | witch | 4 | 20.0 | 11 | 55.0 | 35.0 |
  | giant | 5 | 25.0 | 10 | 50.0 | 25.0 |
  | tombstone | 3 | 9.0 | 11 | 33.0 | 24.0 |
  | skeleton_barrel | 3 | 9.0 | 10 | 30.0 | 21.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition B_tt_wl live-reachable: B_tt's billing, restricted to live's detector_cards whitelist
- single: n=4446 MAE=2.7961067476383263 bias=-1.3956813765182188 P90=6.8740000000000006
- double: n=1702 MAE=3.42129312573443 bias=1.016335428907168 P90=7.00108
- overtime: n=239 MAE=3.63655230125523 bias=1.2776301255230127 P90=6.659400000000002
- opponent-play ticks: n=186 MAE=3.845875806451613 bias=2.4904198924731182
- our accepted-play ticks: n=300 MAE=2.9287750000000004 bias=0.052612333333333365
- truth>=9.0 (near cap): n=1442 MAE=2.9090108183079058 bias=-2.733459223300971
- truth<9.0: n=4945 MAE=3.018983599595551 bias=-0.04618699696663296
- per-match MAE: n_matches=10 median=2.9270125160113 p90=3.800675227813654
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=657.5 total_ghost_delivered=657.0 total_over_charge=0.5 share_from_never_played_bases=0.2608
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | barbarians | 0 | 0.0 | 10 | 50.0 | 50.0 |
  | goblin_cage | 0 | 0.0 | 9 | 36.0 | 36.0 |
  | archer_queen | 7 | 35.0 | 0 | 0.0 | -35.0 |
  | witch | 4 | 20.0 | 11 | 55.0 | 35.0 |
  | giant | 5 | 25.0 | 10 | 50.0 | 25.0 |
  | cannon_cart | 4 | 20.0 | 0 | 0.0 | -20.0 |
  | goblinstein | 4 | 20.0 | 0 | 0.0 | -20.0 |
  | barbarian_barrel | 9 | 18.0 | 0 | 0.0 | -18.0 |
  | elixir_collector | 1 | 6.0 | 4 | 24.0 | 18.0 |
  | three_musketeers | 2 | 18.0 | 0 | 0.0 | -18.0 |
  (top 10 shown here; top 25 in summary.json)
