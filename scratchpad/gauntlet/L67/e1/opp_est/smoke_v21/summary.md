# opp_est_audit summary

n_ticks=600 n_matches=1 port=38031 split=heldout entries=0:2 decide_every=10 estimator_step=5

| condition | MAE | bias | P90\|err\| | share<=1.0 | share<=2.0 |
|---|---|---|---|---|---|
| A+ perfect detection (+spells, no whitelist) | 2.260972333333333 | 0.07675699999999999 | 4.9466 | 0.35333333333333333 | 0.43666666666666665 |
| A perfect detection (units only, NO whitelist -- loose upper bound) | 2.260972333333333 | 0.07675699999999999 | 4.9466 | 0.35333333333333333 | 0.43666666666666665 |
| A_wl perfect detection (units only, live's detector_cards whitelist) | 2.642174 | 0.4579586666666666 | 4.9466 | 0.23 | 0.33166666666666667 |
| B degraded (live) | 5.7710735 | -5.760922166666667 | 8.854320000000001 | 0.03833333333333333 | 0.08166666666666667 |
| B_tt IDEALISED: bill once per TeamTracker-confirmed track (min_hits), no whitelist -- a design under test, NOT live's current path | 4.005849833333333 | -3.910922166666667 | 7.570819999999999 | 0.17666666666666667 | 0.21833333333333332 |
| B_tt_wl live-reachable: B_tt's billing, restricted to live's detector_cards whitelist | 3.2154145 | -2.5259221666666667 | 7.0 | 0.14833333333333334 | 0.3516666666666667 |
| B_corrS correlated-degrade, SHORT persistence | 5.745922166666666 | -5.745922166666666 | 8.82678 | 0.04833333333333333 | 0.115 |
| B_corrS_tt IDEALISED tracker-input on SHORT correlated -- design under test, NOT live's current path | 5.204246833333333 | -5.050922166666667 | 8.145019999999999 | 0.07666666666666666 | 0.14833333333333334 |
| B_corrS_tt_wl live-reachable tracker-input on SHORT correlated | 4.645679166666667 | -4.4917555 | 7.4249 | 0.08666666666666667 | 0.16833333333333333 |
| B_corrL correlated-degrade, LONG persistence | 4.613093833333333 | -4.600922166666667 | 7.5215000000000005 | 0.09333333333333334 | 0.17833333333333334 |
| B_corrL_tt IDEALISED tracker-input on LONG correlated -- design under test, NOT live's current path | 5.0940515 | -5.085922166666666 | 7.68578 | 0.08833333333333333 | 0.11833333333333333 |
| B_corrL_tt_wl live-reachable tracker-input on LONG correlated | 3.6211015 | -3.4059221666666666 | 6.848700000000001 | 0.195 | 0.3466666666666667 |

## Condition A+ perfect detection (+spells, no whitelist)
- single: n=462 MAE=2.1969406926406925 bias=-0.6397025974025974 P90=4.663600000000001
- double: n=138 MAE=2.4753391304347825 bias=2.4753391304347825 P90=5.3456
- overtime: n=0 MAE=None bias=None P90=None
- opponent-play ticks: n=16 MAE=2.6845125 bias=1.8572625
- our accepted-play ticks: n=27 MAE=2.2680370370370366 bias=0.5353851851851852
- truth>=9.0 (near cap): n=95 MAE=2.1505073684210525 bias=-1.828456842105263
- truth<9.0: n=505 MAE=2.2817528712871287 bias=0.43516356435643566
- per-match MAE: n_matches=1 median=2.260972333333333 p90=2.260972333333333
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=55.0 total_ghost_delivered=64.0 total_over_charge=-9.0 share_from_never_played_bases=0.0545
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | bowler | 3 | 15.0 | 2 | 10.0 | -5.0 |
  | graveyard | 1 | 5.0 | 0 | 0.0 | -5.0 |
  | witch | 1 | 5.0 | 2 | 10.0 | 5.0 |
  | giant_snowball | 2 | 4.0 | 0 | 0.0 | -4.0 |
  | arrows | 1 | 3.0 | 0 | 0.0 | -3.0 |
  | skeletons | 0 | 0.0 | 3 | 3.0 | 3.0 |
  | giant | 3 | 15.0 | 3 | 15.0 | 0.0 |
  | guards | 3 | 9.0 | 3 | 9.0 | 0.0 |
  | zappies | 2 | 8.0 | 2 | 8.0 | 0.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition A perfect detection (units only, NO whitelist -- loose upper bound)
- single: n=462 MAE=2.1969406926406925 bias=-0.6397025974025974 P90=4.663600000000001
- double: n=138 MAE=2.4753391304347825 bias=2.4753391304347825 P90=5.3456
- overtime: n=0 MAE=None bias=None P90=None
- opponent-play ticks: n=16 MAE=2.6845125 bias=1.8572625
- our accepted-play ticks: n=27 MAE=2.2680370370370366 bias=0.5353851851851852
- truth>=9.0 (near cap): n=95 MAE=2.1505073684210525 bias=-1.828456842105263
- truth<9.0: n=505 MAE=2.2817528712871287 bias=0.43516356435643566
- per-match MAE: n_matches=1 median=2.260972333333333 p90=2.260972333333333
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=55.0 total_ghost_delivered=64.0 total_over_charge=-9.0 share_from_never_played_bases=0.0545
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | bowler | 3 | 15.0 | 2 | 10.0 | -5.0 |
  | graveyard | 1 | 5.0 | 0 | 0.0 | -5.0 |
  | witch | 1 | 5.0 | 2 | 10.0 | 5.0 |
  | giant_snowball | 2 | 4.0 | 0 | 0.0 | -4.0 |
  | arrows | 1 | 3.0 | 0 | 0.0 | -3.0 |
  | skeletons | 0 | 0.0 | 3 | 3.0 | 3.0 |
  | giant | 3 | 15.0 | 3 | 15.0 | 0.0 |
  | guards | 3 | 9.0 | 3 | 9.0 | 0.0 |
  | zappies | 2 | 8.0 | 2 | 8.0 | 0.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition A_wl perfect detection (units only, live's detector_cards whitelist)
- single: n=462 MAE=2.387178787878788 bias=-0.4494645021645022 P90=4.663600000000001
- double: n=138 MAE=3.4958536231884056 bias=3.4958536231884056 P90=5.3456
- overtime: n=0 MAE=None bias=None P90=None
- opponent-play ticks: n=16 MAE=3.4067625 bias=2.5795125
- our accepted-play ticks: n=27 MAE=2.7090740740740737 bias=0.9764222222222222
- truth>=9.0 (near cap): n=95 MAE=2.1763705263157895 bias=-1.8025936842105263
- truth<9.0: n=505 MAE=2.729800396039604 bias=0.8832110891089109
- per-match MAE: n_matches=1 median=2.642174 p90=2.642174
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=47.0 total_ghost_delivered=64.0 total_over_charge=-17.0 share_from_never_played_bases=0.0638
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | zappies | 2 | 8.0 | 0 | 0.0 | -8.0 |
  | bowler | 3 | 15.0 | 2 | 10.0 | -5.0 |
  | graveyard | 1 | 5.0 | 0 | 0.0 | -5.0 |
  | witch | 1 | 5.0 | 2 | 10.0 | 5.0 |
  | giant_snowball | 2 | 4.0 | 0 | 0.0 | -4.0 |
  | arrows | 1 | 3.0 | 0 | 0.0 | -3.0 |
  | skeletons | 0 | 0.0 | 3 | 3.0 | 3.0 |
  | giant | 3 | 15.0 | 3 | 15.0 | 0.0 |
  | guards | 3 | 9.0 | 3 | 9.0 | 0.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition B degraded (live)
- single: n=462 MAE=6.095609523809524 bias=-6.095609523809524 P90=9.0
- double: n=138 MAE=4.684583333333333 bias=-4.640447101449276 P90=8.0375
- overtime: n=0 MAE=None bias=None P90=None
- opponent-play ticks: n=16 MAE=3.64484375 bias=-3.5787062499999998
- our accepted-play ticks: n=27 MAE=5.169696296296296 bias=-5.096096296296297
- truth>=9.0 (near cap): n=95 MAE=7.864646315789473 bias=-7.864646315789473
- truth<9.0: n=505 MAE=5.37723306930693 bias=-5.3651720792079205
- per-match MAE: n_matches=1 median=5.7710735 p90=5.7710735
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=826.0 total_ghost_delivered=64.0 total_over_charge=762.0 share_from_never_played_bases=0.8535
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | pekka | 0 | 0.0 | 5 | 35.0 | 35.0 |
  | bowler | 3 | 15.0 | 9 | 45.0 | 30.0 |
  | knight | 0 | 0.0 | 10 | 30.0 | 30.0 |
  | giant | 3 | 15.0 | 8 | 40.0 | 25.0 |
  | royal_recruits | 0 | 0.0 | 3 | 21.0 | 21.0 |
  | balloon | 0 | 0.0 | 4 | 20.0 | 20.0 |
  | mini_pekka | 0 | 0.0 | 5 | 20.0 | 20.0 |
  | tesla | 0 | 0.0 | 5 | 20.0 | 20.0 |
  | elite_barbarians | 0 | 0.0 | 3 | 18.0 | 18.0 |
  | goblin_giant | 0 | 0.0 | 3 | 18.0 | 18.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition B_tt IDEALISED: bill once per TeamTracker-confirmed track (min_hits), no whitelist -- a design under test, NOT live's current path
- single: n=462 MAE=4.433374025974026 bias=-4.372665800865801 P90=7.867100000000001
- double: n=138 MAE=2.574573188405797 bias=-2.365084782608696 P90=5.9162
- overtime: n=0 MAE=None bias=None P90=None
- opponent-play ticks: n=16 MAE=1.74718125 bias=-0.20370624999999995
- our accepted-play ticks: n=27 MAE=3.2280814814814818 bias=-3.022022222222222
- truth>=9.0 (near cap): n=95 MAE=5.464646315789474 bias=-5.464646315789474
- truth<9.0: n=505 MAE=3.7314227722772277 bias=-3.618637425742574
- per-match MAE: n_matches=1 median=4.005849833333333 p90=4.005849833333333
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=147.0 total_ghost_delivered=64.0 total_over_charge=83.0 share_from_never_played_bases=0.4422
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | witch | 1 | 5.0 | 5 | 25.0 | 20.0 |
  | barbarian_hut | 0 | 0.0 | 1 | 6.0 | 6.0 |
  | elite_barbarians | 0 | 0.0 | 1 | 6.0 | 6.0 |
  | bowler | 3 | 15.0 | 4 | 20.0 | 5.0 |
  | giant | 3 | 15.0 | 4 | 20.0 | 5.0 |
  | graveyard | 1 | 5.0 | 0 | 0.0 | -5.0 |
  | wizard | 0 | 0.0 | 1 | 5.0 | 5.0 |
  | battle_healer | 0 | 0.0 | 1 | 4.0 | 4.0 |
  | giant_snowball | 2 | 4.0 | 0 | 0.0 | -4.0 |
  | goblin_cage | 0 | 0.0 | 1 | 4.0 | 4.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition B_tt_wl live-reachable: B_tt's billing, restricted to live's detector_cards whitelist
- single: n=462 MAE=3.5015766233766232 bias=-3.0696354978354976 P90=7.340700000000003
- double: n=138 MAE=2.2573934782608696 bias=-0.7056644927536232 P90=3.9122
- overtime: n=0 MAE=None bias=None P90=None
- opponent-play ticks: n=16 MAE=1.94856875 bias=1.23379375
- our accepted-play ticks: n=27 MAE=2.7165555555555554 bias=-1.836837037037037
- truth>=9.0 (near cap): n=95 MAE=4.384322105263158 bias=-4.222541052631579
- truth<9.0: n=505 MAE=2.99552099009901 bias=-2.2067562376237624
- per-match MAE: n_matches=1 median=3.2154145 p90=3.2154145
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=97.0 total_ghost_delivered=64.0 total_over_charge=33.0 share_from_never_played_bases=0.2371
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | witch | 1 | 5.0 | 5 | 25.0 | 20.0 |
  | zappies | 2 | 8.0 | 0 | 0.0 | -8.0 |
  | bowler | 3 | 15.0 | 4 | 20.0 | 5.0 |
  | giant | 3 | 15.0 | 4 | 20.0 | 5.0 |
  | graveyard | 1 | 5.0 | 0 | 0.0 | -5.0 |
  | giant_snowball | 2 | 4.0 | 0 | 0.0 | -4.0 |
  | goblin_cage | 0 | 0.0 | 1 | 4.0 | 4.0 |
  | magic_archer | 0 | 0.0 | 1 | 4.0 | 4.0 |
  | valkyrie | 0 | 0.0 | 1 | 4.0 | 4.0 |
  | archers | 0 | 0.0 | 1 | 3.0 | 3.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition B_corrS correlated-degrade, SHORT persistence
- single: n=462 MAE=6.09128051948052 bias=-6.09128051948052 P90=9.0
- double: n=138 MAE=4.589722463768116 bias=-4.589722463768116 P90=8.0375
- overtime: n=0 MAE=None bias=None P90=None
- opponent-play ticks: n=16 MAE=3.2662062499999998 bias=-3.2662062499999998
- our accepted-play ticks: n=27 MAE=5.096096296296297 bias=-5.096096296296297
- truth>=9.0 (near cap): n=95 MAE=7.990962105263158 bias=-7.990962105263158
- truth<9.0: n=505 MAE=5.32358792079208 bias=-5.32358792079208
- per-match MAE: n_matches=1 median=5.745922166666666 p90=5.745922166666666
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=640.5 total_ghost_delivered=64.0 total_over_charge=576.5 share_from_never_played_bases=0.8017
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | musketeer | 0 | 0.0 | 9 | 36.0 | 36.0 |
  | bowler | 3 | 15.0 | 9 | 45.0 | 30.0 |
  | giant | 3 | 15.0 | 9 | 45.0 | 30.0 |
  | valkyrie | 0 | 0.0 | 6 | 24.0 | 24.0 |
  | ronin | 0 | 0.0 | 4 | 20.0 | 20.0 |
  | dark_prince | 0 | 0.0 | 4 | 16.0 | 16.0 |
  | electro_wizard | 0 | 0.0 | 4 | 16.0 | 16.0 |
  | balloon | 0 | 0.0 | 3 | 15.0 | 15.0 |
  | witch | 1 | 5.0 | 4 | 20.0 | 15.0 |
  | wizard | 0 | 0.0 | 3 | 15.0 | 15.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition B_corrS_tt IDEALISED tracker-input on SHORT correlated -- design under test, NOT live's current path
- single: n=462 MAE=5.656166233766234 bias=-5.630241558441559 P90=8.306920000000002
- double: n=138 MAE=3.6912992753623186 bias=-3.1114615942028987 P90=6.7377
- overtime: n=0 MAE=None bias=None P90=None
- opponent-play ticks: n=16 MAE=3.26539375 bias=-2.4537062499999998
- our accepted-play ticks: n=27 MAE=4.168140740740741 bias=-3.836837037037037
- truth>=9.0 (near cap): n=95 MAE=6.622541052631579 bias=-6.622541052631579
- truth<9.0: n=505 MAE=4.93743900990099 bias=-4.755271089108911
- per-match MAE: n_matches=1 median=5.204246833333333 p90=5.204246833333333
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=332.0 total_ghost_delivered=64.0 total_over_charge=268.0 share_from_never_played_bases=0.756
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | witch | 1 | 5.0 | 6 | 30.0 | 25.0 |
  | valkyrie | 0 | 0.0 | 4 | 16.0 | 16.0 |
  | royal_recruits | 0 | 0.0 | 2 | 14.0 | 14.0 |
  | goblin_giant | 0 | 0.0 | 2 | 12.0 | 12.0 |
  | mega_minion | 0 | 0.0 | 4 | 12.0 | 12.0 |
  | balloon | 0 | 0.0 | 2 | 10.0 | 10.0 |
  | minion_horde | 0 | 0.0 | 2 | 10.0 | 10.0 |
  | monk | 0 | 0.0 | 2 | 10.0 | 10.0 |
  | golem | 0 | 0.0 | 1 | 8.0 | 8.0 |
  | hog_rider | 0 | 0.0 | 2 | 8.0 | 8.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition B_corrS_tt_wl live-reachable tracker-input on SHORT correlated
- single: n=462 MAE=5.023049350649351 bias=-4.997124675324676 P90=7.6069
- double: n=138 MAE=3.3823094202898547 bias=-2.799867391304348 P90=5.6061
- overtime: n=0 MAE=None bias=None P90=None
- opponent-play ticks: n=16 MAE=2.43071875 bias=-1.60995625
- our accepted-play ticks: n=27 MAE=3.4142592592592593 bias=-3.077577777777778
- truth>=9.0 (near cap): n=95 MAE=5.106751578947368 bias=-5.106751578947368
- truth<9.0: n=505 MAE=4.558942772277227 bias=-4.376063168316832
- per-match MAE: n_matches=1 median=4.645679166666667 p90=4.645679166666667
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=189.5 total_ghost_delivered=64.0 total_over_charge=125.5 share_from_never_played_bases=0.6359
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | witch | 1 | 5.0 | 6 | 30.0 | 25.0 |
  | valkyrie | 0 | 0.0 | 4 | 16.0 | 16.0 |
  | royal_recruits | 0 | 0.0 | 2 | 14.0 | 14.0 |
  | balloon | 0 | 0.0 | 2 | 10.0 | 10.0 |
  | hog_rider | 0 | 0.0 | 2 | 8.0 | 8.0 |
  | magic_archer | 0 | 0.0 | 2 | 8.0 | 8.0 |
  | musketeer | 0 | 0.0 | 2 | 8.0 | 8.0 |
  | zappies | 2 | 8.0 | 0 | 0.0 | -8.0 |
  | lava_hound | 0 | 0.0 | 1 | 7.0 | 7.0 |
  | pekka | 0 | 0.0 | 1 | 7.0 | 7.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition B_corrL correlated-degrade, LONG persistence
- single: n=462 MAE=5.051331601731602 bias=-5.047990476190477 P90=7.589900000000001
- double: n=138 MAE=3.14595 bias=-3.1042152173913045 P90=4.7515
- overtime: n=0 MAE=None bias=None P90=None
- opponent-play ticks: n=16 MAE=2.95734375 bias=-2.7662062499999998
- our accepted-play ticks: n=27 MAE=3.602866666666667 bias=-3.577577777777778
- truth>=9.0 (near cap): n=95 MAE=5.085698947368421 bias=-5.085698947368421
- truth<9.0: n=505 MAE=4.524187920792079 bias=-4.509726534653465
- per-match MAE: n_matches=1 median=4.613093833333333 p90=4.613093833333333
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=232.5 total_ghost_delivered=64.0 total_over_charge=168.5 share_from_never_played_bases=0.7118
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | wizard | 0 | 0.0 | 7 | 35.0 | 35.0 |
  | goblin_demolisher | 0 | 0.0 | 5 | 20.0 | 20.0 |
  | mega_knight | 0 | 0.0 | 2 | 14.0 | 14.0 |
  | bowler | 3 | 15.0 | 5 | 25.0 | 10.0 |
  | mega_minion | 0 | 0.0 | 3 | 9.0 | 9.0 |
  | battle_healer | 0 | 0.0 | 2 | 8.0 | 8.0 |
  | dark_prince | 0 | 0.0 | 2 | 8.0 | 8.0 |
  | skeleton_dragons | 0 | 0.0 | 2 | 8.0 | 8.0 |
  | dart_goblin | 0 | 0.0 | 2 | 6.0 | 6.0 |
  | elite_barbarians | 0 | 0.0 | 1 | 6.0 | 6.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition B_corrL_tt IDEALISED tracker-input on LONG correlated -- design under test, NOT live's current path
- single: n=462 MAE=5.533651082251082 bias=-5.532838961038961 P90=7.78422
- double: n=138 MAE=3.6223485507246376 bias=-3.589722463768116 P90=5.5592
- overtime: n=0 MAE=None bias=None P90=None
- opponent-play ticks: n=16 MAE=2.34141875 bias=-2.1412062499999998
- our accepted-play ticks: n=27 MAE=4.333888888888889 bias=-4.3183185185185184
- truth>=9.0 (near cap): n=95 MAE=6.759383157894737 bias=-6.759383157894737
- truth<9.0: n=505 MAE=4.7807712871287125 bias=-4.771112673267327
- per-match MAE: n_matches=1 median=5.0940515 p90=5.0940515
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=239.5 total_ghost_delivered=64.0 total_over_charge=175.5 share_from_never_played_bases=0.6576
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | wizard | 0 | 0.0 | 4 | 20.0 | 20.0 |
  | witch | 1 | 5.0 | 4 | 20.0 | 15.0 |
  | bowler | 3 | 15.0 | 5 | 25.0 | 10.0 |
  | goblin_demolisher | 0 | 0.0 | 2 | 8.0 | 8.0 |
  | golem | 0 | 0.0 | 1 | 8.0 | 8.0 |
  | mega_knight | 0 | 0.0 | 1 | 7.0 | 7.0 |
  | boss_bandit | 0 | 0.0 | 1 | 6.0 | 6.0 |
  | dart_goblin | 0 | 0.0 | 2 | 6.0 | 6.0 |
  | elite_barbarians | 0 | 0.0 | 1 | 6.0 | 6.0 |
  | goblin_giant | 0 | 0.0 | 1 | 6.0 | 6.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition B_corrL_tt_wl live-reachable tracker-input on LONG correlated
- single: n=462 MAE=3.7794112554112553 bias=-3.558812987012987 P90=7.02214
- double: n=138 MAE=3.091107971014493 bias=-2.8940702898550725 P90=4.575
- overtime: n=0 MAE=None bias=None P90=None
- opponent-play ticks: n=16 MAE=2.24105625 bias=0.42129375
- our accepted-play ticks: n=27 MAE=3.0811333333333333 bias=-2.725725925925926
- truth>=9.0 (near cap): n=95 MAE=4.864646315789473 bias=-4.864646315789473
- truth<9.0: n=505 MAE=3.3871673267326736 bias=-3.131508712871287
- per-match MAE: n_matches=1 median=3.6211015 p90=3.6211015
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=106.0 total_ghost_delivered=64.0 total_over_charge=42.0 share_from_never_played_bases=0.3019
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | witch | 1 | 5.0 | 4 | 20.0 | 15.0 |
  | bowler | 3 | 15.0 | 5 | 25.0 | 10.0 |
  | zappies | 2 | 8.0 | 0 | 0.0 | -8.0 |
  | mega_knight | 0 | 0.0 | 1 | 7.0 | 7.0 |
  | giant | 3 | 15.0 | 4 | 20.0 | 5.0 |
  | graveyard | 1 | 5.0 | 0 | 0.0 | -5.0 |
  | royal_hogs | 0 | 0.0 | 1 | 5.0 | 5.0 |
  | baby_dragon | 0 | 0.0 | 1 | 4.0 | 4.0 |
  | giant_snowball | 2 | 4.0 | 0 | 0.0 | -4.0 |
  | hunter | 0 | 0.0 | 1 | 4.0 | 4.0 |
  (top 10 shown here; top 25 in summary.json)
