# opp_est_audit summary

n_ticks=75817 n_matches=100 port=38031 split=heldout entries=0:100 decide_every=10 estimator_step=5

| condition | MAE | bias | P90\|err\| | share<=1.0 | share<=2.0 |
|---|---|---|---|---|---|
| A+ perfect detection (+spells, no whitelist) | 1.4048643312185922 | -0.20792741469591253 | 3.8532000000000264 | 0.5548227969980347 | 0.7100914043024652 |
| A perfect detection (units only, NO whitelist -- loose upper bound) | 1.4048643312185922 | -0.20792741469591253 | 3.8532000000000264 | 0.5548227969980347 | 0.7100914043024652 |
| A_wl perfect detection (units only, live's detector_cards whitelist) | 2.267613411240223 | 1.636390524552541 | 5.458320000000007 | 0.38289565664692615 | 0.5282192648086841 |
| B degraded (live) | 5.748162770882519 | -5.7403848450875135 | 9.0538 | 0.059234736272867565 | 0.10758800796655103 |
| B_tt IDEALISED: bill once per TeamTracker-confirmed track (min_hits), no whitelist -- a design under test, NOT live's current path | 3.346063837925531 | -3.0600295158078 | 6.8694 | 0.2346307556352797 | 0.36789902000870517 |
| B_tt_wl live-reachable: B_tt's billing, restricted to live's detector_cards whitelist | 2.6672103037577326 | -0.4349124576282364 | 5.966360000000003 | 0.30588126673437355 | 0.46775789071052665 |
| B_corrS correlated-degrade, SHORT persistence | 5.539980202329293 | -5.524931846419669 | 9.0 | 0.0673859424667291 | 0.11968292071698959 |
| B_corrS_tt IDEALISED tracker-input on SHORT correlated -- design under test, NOT live's current path | 5.042754464038409 | -5.009361459830909 | 8.6344 | 0.09247266444201169 | 0.1650025719825369 |
| B_corrS_tt_wl live-reachable tracker-input on SHORT correlated | 3.9421839165358694 | -3.4939361594365383 | 7.6262400000000055 | 0.1691045543875384 | 0.28688816492343405 |
| B_corrL correlated-degrade, LONG persistence | 4.192146914280438 | -4.052808180223433 | 7.712 | 0.14635240117651713 | 0.23898334146695333 |
| B_corrL_tt IDEALISED tracker-input on LONG correlated -- design under test, NOT live's current path | 4.48915855546909 | -4.421320519144783 | 8.0 | 0.12454990305604284 | 0.208660326839627 |
| B_corrL_tt_wl live-reachable tracker-input on LONG correlated | 3.2223030929738714 | -2.273246868116649 | 6.7622 | 0.23750610021499136 | 0.3818800532862023 |

## Condition A+ perfect detection (+spells, no whitelist)
- single: n=45672 MAE=1.2744466894377298 bias=-0.23969007707129095 P90=3.5161999999999995
- double: n=22016 MAE=1.5987450763081394 bias=-0.24380188045058138 P90=4.1067
- overtime: n=8129 MAE=1.6125105425021529 bias=0.06768785828515192 P90=4.252219999999998
- opponent-play ticks: n=2468 MAE=1.8290075769854135 bias=0.3821072528363047
- our accepted-play ticks: n=3673 MAE=1.4667071603593793 bias=-0.21284263544786278
- truth>=9.0 (near cap): n=15695 MAE=0.7067145906339599 bias=-0.6086874737177445
- truth<9.0: n=60122 MAE=1.5871180848940487 bias=-0.10330798875619572
- per-match MAE: n_matches=100 median=1.3829807317783709 p90=2.3961826243403714
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=9176.0 total_ghost_delivered=8363.0 total_over_charge=813.0 share_from_never_played_bases=0.0073
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | miner | 34 | 102.0 | 251 | 753.0 | 651.0 |
  | barbarians | 13 | 65.0 | 140 | 700.0 | 635.0 |
  | barbarian_barrel | 127 | 254.0 | 0 | 0.0 | -254.0 |
  | witch | 16 | 80.0 | 49 | 245.0 | 165.0 |
  | lightning | 26 | 156.0 | 0 | 0.0 | -156.0 |
  | goblinstein | 35 | 175.0 | 66 | 330.0 | 155.0 |
  | graveyard | 30 | 150.0 | 0 | 0.0 | -150.0 |
  | hog_rider | 41 | 164.0 | 71 | 284.0 | 120.0 |
  | fireball | 28 | 112.0 | 0 | 0.0 | -112.0 |
  | royal_ghost | 53 | 159.0 | 89 | 267.0 | 108.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition A perfect detection (units only, NO whitelist -- loose upper bound)
- single: n=45672 MAE=1.2744466894377298 bias=-0.23969007707129095 P90=3.5161999999999995
- double: n=22016 MAE=1.5987450763081394 bias=-0.24380188045058138 P90=4.1067
- overtime: n=8129 MAE=1.6125105425021529 bias=0.06768785828515192 P90=4.252219999999998
- opponent-play ticks: n=2468 MAE=1.8290075769854135 bias=0.3821072528363047
- our accepted-play ticks: n=3673 MAE=1.4667071603593793 bias=-0.21284263544786278
- truth>=9.0 (near cap): n=15695 MAE=0.7067145906339599 bias=-0.6086874737177445
- truth<9.0: n=60122 MAE=1.5871180848940487 bias=-0.10330798875619572
- per-match MAE: n_matches=100 median=1.3829807317783709 p90=2.3961826243403714
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=9176.0 total_ghost_delivered=8363.0 total_over_charge=813.0 share_from_never_played_bases=0.0073
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | miner | 34 | 102.0 | 251 | 753.0 | 651.0 |
  | barbarians | 13 | 65.0 | 140 | 700.0 | 635.0 |
  | barbarian_barrel | 127 | 254.0 | 0 | 0.0 | -254.0 |
  | witch | 16 | 80.0 | 49 | 245.0 | 165.0 |
  | lightning | 26 | 156.0 | 0 | 0.0 | -156.0 |
  | goblinstein | 35 | 175.0 | 66 | 330.0 | 155.0 |
  | graveyard | 30 | 150.0 | 0 | 0.0 | -150.0 |
  | hog_rider | 41 | 164.0 | 71 | 284.0 | 120.0 |
  | fireball | 28 | 112.0 | 0 | 0.0 | -112.0 |
  | royal_ghost | 53 | 159.0 | 89 | 267.0 | 108.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition A_wl perfect detection (units only, live's detector_cards whitelist)
- single: n=45672 MAE=2.0852863198458573 bias=1.4588298213347346 P90=5.111799999999999
- double: n=22016 MAE=2.609799563953488 bias=1.9544839117005814 P90=5.8271
- overtime: n=8129 MAE=2.365248124000492 bias=1.77249686308279 P90=5.73538
- opponent-play ticks: n=2468 MAE=3.3975073338735817 bias=2.92034914910859
- our accepted-play ticks: n=3673 MAE=2.481661992921318 bias=1.8064281241491968
- truth>=9.0 (near cap): n=15695 MAE=0.48400410321758525 bias=-0.22673987894233832
- truth<9.0: n=60122 MAE=2.7332291274408704 bias=2.1227654236386013
- per-match MAE: n_matches=100 median=2.1299998532123006 p90=3.251071641168289
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=5473.0 total_ghost_delivered=8363.0 total_over_charge=-2890.0 share_from_never_played_bases=0.0066
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | miner | 34 | 102.0 | 251 | 753.0 | 651.0 |
  | barbarians | 13 | 65.0 | 140 | 700.0 | 635.0 |
  | barbarian_barrel | 127 | 254.0 | 0 | 0.0 | -254.0 |
  | goblinstein | 35 | 175.0 | 0 | 0.0 | -175.0 |
  | tombstone | 55 | 165.0 | 0 | 0.0 | -165.0 |
  | witch | 16 | 80.0 | 49 | 245.0 | 165.0 |
  | royal_ghost | 53 | 159.0 | 0 | 0.0 | -159.0 |
  | lightning | 26 | 156.0 | 0 | 0.0 | -156.0 |
  | graveyard | 30 | 150.0 | 0 | 0.0 | -150.0 |
  | rascals | 28 | 140.0 | 0 | 0.0 | -140.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition B degraded (live)
- single: n=45672 MAE=5.5713618759852865 bias=-5.560110019267823 P90=9.0
- double: n=22016 MAE=5.896132403706395 bias=-5.894773083212209 P90=9.037500000000001
- overtime: n=8129 MAE=6.340751162504613 bias=-6.335107491696395 P90=10.0
- opponent-play ticks: n=2468 MAE=4.05096961102107 bias=-3.982709400324149
- our accepted-play ticks: n=3673 MAE=5.528372229784917 bias=-5.517193846991559
- truth>=9.0 (near cap): n=15695 MAE=8.22921652118509 bias=-8.228540866518
- truth<9.0: n=60122 MAE=5.100477420910815 bias=-5.090845429293769
- per-match MAE: n_matches=100 median=5.810975312934632 p90=6.700568915159945
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=108888.0 total_ghost_delivered=8363.0 total_over_charge=100525.0 share_from_never_played_bases=0.0721
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | knight | 51 | 153.0 | 959 | 2877.0 | 2724.0 |
  | tesla | 16 | 64.0 | 586 | 2344.0 | 2280.0 |
  | ice_wizard | 25 | 75.0 | 763 | 2289.0 | 2214.0 |
  | wizard | 16 | 80.0 | 445 | 2225.0 | 2145.0 |
  | x_bow | 4 | 24.0 | 351 | 2106.0 | 2082.0 |
  | balloon | 39 | 195.0 | 447 | 2235.0 | 2040.0 |
  | bowler | 43 | 215.0 | 439 | 2195.0 | 1980.0 |
  | musketeer | 47 | 188.0 | 533 | 2132.0 | 1944.0 |
  | mega_knight | 10 | 70.0 | 280 | 1960.0 | 1890.0 |
  | giant | 30 | 150.0 | 400 | 2000.0 | 1850.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition B_tt IDEALISED: bill once per TeamTracker-confirmed track (min_hits), no whitelist -- a design under test, NOT live's current path
- single: n=45672 MAE=3.156832352425994 bias=-2.8676397968120515 P90=6.7589000000000015
- double: n=22016 MAE=3.6412824763808143 bias=-3.3467852561773257 P90=6.9956
- overtime: n=8129 MAE=3.6096936646573994 bias=-3.3643238774757043 P90=7.0
- opponent-play ticks: n=2468 MAE=2.512528930307942 bias=-0.6026445705024311
- our accepted-play ticks: n=3673 MAE=3.1980368091478355 bias=-2.885829839368364
- truth>=9.0 (near cap): n=15695 MAE=3.8696978719337367 bias=-3.840678489964957
- truth<9.0: n=60122 MAE=3.209367850370912 bias=-2.856239128771498
- per-match MAE: n_matches=100 median=3.2394327538247563 p90=4.278640302058388
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=16910.0 total_ghost_delivered=8363.0 total_over_charge=8547.0 share_from_never_played_bases=0.0396
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | barbarians | 13 | 65.0 | 157 | 785.0 | 720.0 |
  | tombstone | 55 | 165.0 | 228 | 684.0 | 519.0 |
  | goblin_drill | 16 | 64.0 | 127 | 508.0 | 444.0 |
  | goblin_cage | 8 | 32.0 | 112 | 448.0 | 416.0 |
  | tesla | 16 | 64.0 | 106 | 424.0 | 360.0 |
  | barbarian_hut | 0 | 0.0 | 45 | 270.0 | 270.0 |
  | knight | 51 | 153.0 | 141 | 423.0 | 270.0 |
  | goblinstein | 35 | 175.0 | 87 | 435.0 | 260.0 |
  | barbarian_barrel | 127 | 254.0 | 0 | 0.0 | -254.0 |
  | witch | 16 | 80.0 | 65 | 325.0 | 245.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition B_tt_wl live-reachable: B_tt's billing, restricted to live's detector_cards whitelist
- single: n=45672 MAE=2.5502125240847784 bias=-0.5790713084603257 P90=5.84358
- double: n=22016 MAE=2.875128015988372 bias=-0.19005833030523256 P90=6.03975
- overtime: n=8129 MAE=2.7614416041333496 bias=-0.2881152417271497 P90=6.0
- opponent-play ticks: n=2468 MAE=3.3622755267423012 bias=2.0892111831442466
- our accepted-play ticks: n=3673 MAE=2.6906247753879664 bias=-0.06075496869044377
- truth>=9.0 (near cap): n=15695 MAE=2.1147001911436765 bias=-1.9723127683975787
- truth<9.0: n=60122 MAE=2.8114444645886696 bias=-0.03357022221482985
- per-match MAE: n_matches=100 median=2.655279555892043 p90=3.3842048399112574
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=9200.5 total_ghost_delivered=8363.0 total_over_charge=837.5 share_from_never_played_bases=0.0095
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | barbarians | 13 | 65.0 | 159 | 795.0 | 730.0 |
  | goblin_cage | 8 | 32.0 | 112 | 448.0 | 416.0 |
  | tesla | 16 | 64.0 | 106 | 424.0 | 360.0 |
  | knight | 51 | 153.0 | 141 | 423.0 | 270.0 |
  | barbarian_barrel | 127 | 254.0 | 0 | 0.0 | -254.0 |
  | witch | 16 | 80.0 | 65 | 325.0 | 245.0 |
  | elixir_collector | 9 | 54.0 | 44 | 264.0 | 210.0 |
  | cannon | 11 | 33.0 | 79 | 237.0 | 204.0 |
  | musketeer | 47 | 188.0 | 97 | 388.0 | 200.0 |
  | bowler | 43 | 215.0 | 82 | 410.0 | 195.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition B_corrS correlated-degrade, SHORT persistence
- single: n=45672 MAE=5.368265169031354 bias=-5.345843072341916 P90=8.990260000000001
- double: n=22016 MAE=5.722773155886628 bias=-5.718106113735465 P90=9.0
- overtime: n=8129 MAE=6.009681190798377 bias=-6.007945479148726 P90=9.20548
- opponent-play ticks: n=2468 MAE=3.9650092382495945 bias=-3.880399837925446
- our accepted-play ticks: n=3673 MAE=5.304001089028043 bias=-5.273659950993737
- truth>=9.0 (near cap): n=15695 MAE=7.8129065625995535 bias=-7.811401650207072
- truth<9.0: n=60122 MAE=4.94662703336549 bias=-4.928043127307808
- per-match MAE: n_matches=100 median=5.575758344105816 p90=6.594324292799971
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=83692.5 total_ghost_delivered=8363.0 total_over_charge=75329.5 share_from_never_played_bases=0.0691
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | wizard | 16 | 80.0 | 410 | 2050.0 | 1970.0 |
  | bowler | 43 | 215.0 | 383 | 1915.0 | 1700.0 |
  | giant | 30 | 150.0 | 349 | 1745.0 | 1595.0 |
  | pekka | 16 | 112.0 | 240 | 1680.0 | 1568.0 |
  | valkyrie | 37 | 148.0 | 404 | 1616.0 | 1468.0 |
  | mega_knight | 10 | 70.0 | 215 | 1505.0 | 1435.0 |
  | musketeer | 47 | 188.0 | 405 | 1620.0 | 1432.0 |
  | balloon | 39 | 195.0 | 323 | 1615.0 | 1420.0 |
  | goblinstein | 35 | 175.0 | 305 | 1525.0 | 1350.0 |
  | barbarians | 13 | 65.0 | 280 | 1400.0 | 1335.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition B_corrS_tt IDEALISED tracker-input on SHORT correlated -- design under test, NOT live's current path
- single: n=45672 MAE=4.897112313890348 bias=-4.854426011560694 P90=8.5034
- double: n=22016 MAE=5.1862441224563955 bias=-5.166802516351744 P90=8.7108
- overtime: n=8129 MAE=5.472413704022634 bias=-5.453449231147743 P90=9.0
- opponent-play ticks: n=2468 MAE=3.2796415721231766 bias=-2.8609508914100488
- our accepted-play ticks: n=3673 MAE=4.766679934658318 bias=-4.705187312823305
- truth>=9.0 (near cap): n=15695 MAE=7.016910385473081 bias=-7.014013947116917
- truth<9.0: n=60122 MAE=4.5273960729849305 bias=-4.4860418632114705
- per-match MAE: n_matches=100 median=5.070809963616009 p90=6.003235159944368
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=40389.5 total_ghost_delivered=8363.0 total_over_charge=32026.5 share_from_never_played_bases=0.0677
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | barbarians | 13 | 65.0 | 222 | 1110.0 | 1045.0 |
  | bowler | 43 | 215.0 | 200 | 1000.0 | 785.0 |
  | wizard | 16 | 80.0 | 162 | 810.0 | 730.0 |
  | tombstone | 55 | 165.0 | 293 | 879.0 | 714.0 |
  | musketeer | 47 | 188.0 | 222 | 888.0 | 700.0 |
  | goblin_cage | 8 | 32.0 | 177 | 708.0 | 676.0 |
  | giant | 30 | 150.0 | 158 | 790.0 | 640.0 |
  | goblin_drill | 16 | 64.0 | 175 | 700.0 | 636.0 |
  | pekka | 16 | 112.0 | 106 | 742.0 | 630.0 |
  | goblinstein | 35 | 175.0 | 159 | 795.0 | 620.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition B_corrS_tt_wl live-reachable tracker-input on SHORT correlated
- single: n=45672 MAE=3.9244321334734633 bias=-3.4687520756699946 P90=7.676760000000001
- double: n=22016 MAE=4.007701253633721 bias=-3.546685328851744 P90=7.5333
- overtime: n=8129 MAE=3.864478139992619 bias=-3.4925684340017225 P90=7.4626600000000005
- opponent-play ticks: n=2468 MAE=2.858905510534846 bias=-1.3492004862236628
- our accepted-play ticks: n=3673 MAE=3.717132208004356 bias=-3.1523694527634087
- truth>=9.0 (near cap): n=15695 MAE=5.222062497610704 bias=-5.200602032494425
- truth<9.0: n=60122 MAE=3.6080683792954322 bias=-3.048406721333289
- per-match MAE: n_matches=100 median=3.956140890125174 p90=4.890759652294855
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=19965.5 total_ghost_delivered=8363.0 total_over_charge=11602.5 share_from_never_played_bases=0.0386
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | barbarians | 13 | 65.0 | 225 | 1125.0 | 1060.0 |
  | bowler | 43 | 215.0 | 200 | 1000.0 | 785.0 |
  | musketeer | 47 | 188.0 | 222 | 888.0 | 700.0 |
  | goblin_cage | 8 | 32.0 | 177 | 708.0 | 676.0 |
  | giant | 30 | 150.0 | 158 | 790.0 | 640.0 |
  | pekka | 16 | 112.0 | 106 | 742.0 | 630.0 |
  | valkyrie | 37 | 148.0 | 186 | 744.0 | 596.0 |
  | witch | 16 | 80.0 | 135 | 675.0 | 595.0 |
  | elixir_collector | 9 | 54.0 | 108 | 648.0 | 594.0 |
  | mega_knight | 10 | 70.0 | 90 | 630.0 | 560.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition B_corrL correlated-degrade, LONG persistence
- single: n=45672 MAE=4.172988535645472 bias=-4.040229129444736 P90=7.806
- double: n=22016 MAE=4.243325372456395 bias=-4.084339761991279 P90=7.4959999999999996
- overtime: n=8129 MAE=4.1611783491204335 bias=-4.038084487636856 P90=7.609679999999997
- opponent-play ticks: n=2468 MAE=3.2776342787682333 bias=-2.8336008103727712
- our accepted-play ticks: n=3673 MAE=4.000038224884291 bias=-3.8432216172066433
- truth>=9.0 (near cap): n=15695 MAE=5.172341605606881 bias=-5.164093590315387
- truth<9.0: n=60122 MAE=3.9362646136189747 bias=-3.7627043162236786
- per-match MAE: n_matches=100 median=4.134436050086158 p90=5.191113630041725
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=27325.0 total_ghost_delivered=8363.0 total_over_charge=18962.0 share_from_never_played_bases=0.0583
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | barbarians | 13 | 65.0 | 165 | 825.0 | 760.0 |
  | miner | 34 | 102.0 | 212 | 636.0 | 534.0 |
  | wizard | 16 | 80.0 | 120 | 600.0 | 520.0 |
  | knight | 51 | 153.0 | 223 | 669.0 | 516.0 |
  | pekka | 16 | 112.0 | 86 | 602.0 | 490.0 |
  | musketeer | 47 | 188.0 | 162 | 648.0 | 460.0 |
  | mega_knight | 10 | 70.0 | 73 | 511.0 | 441.0 |
  | mortar | 10 | 40.0 | 114 | 456.0 | 416.0 |
  | tesla | 16 | 64.0 | 118 | 472.0 | 408.0 |
  | giant | 30 | 150.0 | 107 | 535.0 | 385.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition B_corrL_tt IDEALISED tracker-input on LONG correlated -- design under test, NOT live's current path
- single: n=45672 MAE=4.416668812401471 bias=-4.349915589420213 P90=8.0
- double: n=22016 MAE=4.58598234011628 bias=-4.506759820130814 P90=8.0
- overtime: n=8129 MAE=4.634204576208636 bias=-4.5911045393037275 P90=8.0
- opponent-play ticks: n=2468 MAE=2.842867504051864 bias=-2.1626121555915723
- our accepted-play ticks: n=3673 MAE=4.363027879117888 bias=-4.269984481350395
- truth>=9.0 (near cap): n=15695 MAE=5.907737999362855 bias=-5.901780751831794
- truth<9.0: n=60122 MAE=4.118834807557965 bias=-4.03484263497555
- per-match MAE: n_matches=100 median=4.411984075104311 p90=5.58947768243163
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=27973.5 total_ghost_delivered=8363.0 total_over_charge=19610.5 share_from_never_played_bases=0.0603
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | barbarians | 13 | 65.0 | 185 | 925.0 | 860.0 |
  | witch | 16 | 80.0 | 121 | 605.0 | 525.0 |
  | wizard | 16 | 80.0 | 120 | 600.0 | 520.0 |
  | musketeer | 47 | 188.0 | 164 | 656.0 | 468.0 |
  | goblin_drill | 16 | 64.0 | 129 | 516.0 | 452.0 |
  | pekka | 16 | 112.0 | 77 | 539.0 | 427.0 |
  | tombstone | 55 | 165.0 | 193 | 579.0 | 414.0 |
  | valkyrie | 37 | 148.0 | 136 | 544.0 | 396.0 |
  | goblinstein | 35 | 175.0 | 113 | 565.0 | 390.0 |
  | giant | 30 | 150.0 | 106 | 530.0 | 380.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition B_corrL_tt_wl live-reachable tracker-input on LONG correlated
- single: n=45672 MAE=3.2761888772114203 bias=-2.4572351725345944 P90=6.8658
- double: n=22016 MAE=3.1801460301598836 bias=-1.9636775163517444 P90=6.6112
- overtime: n=8129 MAE=3.033726190183294 bias=-2.0779417886578915 P90=6.44926
- opponent-play ticks: n=2468 MAE=2.783170016207455 bias=0.11453533225283631
- our accepted-play ticks: n=3673 MAE=3.1924543424993193 bias=-2.088252926762864
- truth>=9.0 (near cap): n=15695 MAE=3.584970264415419 bias=-3.531503593501115
- truth<9.0: n=60122 MAE=3.127627911579788 bias=-1.9447757709324374
- per-match MAE: n_matches=100 median=3.093606362221556 p90=4.364971210013909
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=14025.0 total_ghost_delivered=8363.0 total_over_charge=5662.0 share_from_never_played_bases=0.034
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | barbarians | 13 | 65.0 | 187 | 935.0 | 870.0 |
  | witch | 16 | 80.0 | 121 | 605.0 | 525.0 |
  | musketeer | 47 | 188.0 | 164 | 656.0 | 468.0 |
  | pekka | 16 | 112.0 | 77 | 539.0 | 427.0 |
  | valkyrie | 37 | 148.0 | 136 | 544.0 | 396.0 |
  | giant | 30 | 150.0 | 106 | 530.0 | 380.0 |
  | mega_knight | 10 | 70.0 | 63 | 441.0 | 371.0 |
  | goblin_cage | 8 | 32.0 | 99 | 396.0 | 364.0 |
  | balloon | 39 | 195.0 | 110 | 550.0 | 355.0 |
  | bowler | 43 | 215.0 | 113 | 565.0 | 350.0 |
  (top 10 shown here; top 25 in summary.json)
