# opp_est_audit summary

n_ticks=74229 n_matches=100 port=38031 split=heldout entries=0:100 decide_every=10 estimator_step=5

| condition | MAE | bias | P90\|err\| | share<=1.0 | share<=2.0 |
|---|---|---|---|---|---|
| A+ perfect detection (+spells, no whitelist) | 1.4026629578736074 | -0.12069085802045022 | 3.9822 | 0.5594848374624473 | 0.7079173907771895 |
| A perfect detection (units only, NO whitelist -- loose upper bound) | 1.4026629578736074 | -0.12069085802045022 | 3.9822 | 0.5594848374624473 | 0.7079173907771895 |
| A_wl perfect detection (units only, live's detector_cards whitelist) | 2.2637178878874833 | 1.7156089762761184 | 5.4783 | 0.3933907233022134 | 0.5294830861253688 |
| B degraded (live) | 5.728380114241065 | -5.719079121367659 | 9.0812 | 0.06116207951070336 | 0.1085963706907004 |
| B_tt IDEALISED: bill once per TeamTracker-confirmed track (min_hits), no whitelist -- a design under test, NOT live's current path | 3.2930584798394156 | -3.01901580379636 | 6.896559999999999 | 0.25002357569144135 | 0.38701855070120844 |
| B_tt_wl live-reachable: B_tt's billing, restricted to live's detector_cards whitelist | 2.659734369316574 | -0.4971308262269464 | 6.0 | 0.31844696816608065 | 0.47387139797114336 |

## Condition A+ perfect detection (+spells, no whitelist)
- single: n=45611 MAE=1.2733856218894566 bias=-0.19839169498585868 P90=3.5002
- double: n=22173 MAE=1.6134627339557122 bias=-0.07359176475894105 P90=4.3558
- overtime: n=6445 MAE=1.59233016291699 bias=0.26715781225756396 P90=4.303120000000001
- opponent-play ticks: n=2362 MAE=1.8535272226926331 bias=0.4372343353090601
- our accepted-play ticks: n=3456 MAE=1.4755614004629631 bias=-0.15549230324074073
- truth>=9.0 (near cap): n=15444 MAE=0.6770165954415955 bias=-0.5764147176897177
- truth<9.0: n=58785 MAE=1.5933048294632985 bias=-0.0009630483966998339
- per-match MAE: n_matches=100 median=1.3846081363004172 p90=2.2719795126412254
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=8578.5 total_ghost_delivered=7989.0 total_over_charge=589.5 share_from_never_played_bases=0.0079
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | miner | 31 | 93.0 | 228 | 684.0 | 591.0 |
  | barbarians | 14 | 70.0 | 125 | 625.0 | 555.0 |
  | barbarian_barrel | 112 | 224.0 | 0 | 0.0 | -224.0 |
  | goblinstein | 33 | 165.0 | 65 | 325.0 | 160.0 |
  | lightning | 25 | 150.0 | 0 | 0.0 | -150.0 |
  | rocket | 20 | 120.0 | 0 | 0.0 | -120.0 |
  | witch | 12 | 60.0 | 35 | 175.0 | 115.0 |
  | graveyard | 21 | 105.0 | 0 | 0.0 | -105.0 |
  | zap | 49 | 98.0 | 0 | 0.0 | -98.0 |
  | fireball | 23 | 92.0 | 0 | 0.0 | -92.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition A perfect detection (units only, NO whitelist -- loose upper bound)
- single: n=45611 MAE=1.2733856218894566 bias=-0.19839169498585868 P90=3.5002
- double: n=22173 MAE=1.6134627339557122 bias=-0.07359176475894105 P90=4.3558
- overtime: n=6445 MAE=1.59233016291699 bias=0.26715781225756396 P90=4.303120000000001
- opponent-play ticks: n=2362 MAE=1.8535272226926331 bias=0.4372343353090601
- our accepted-play ticks: n=3456 MAE=1.4755614004629631 bias=-0.15549230324074073
- truth>=9.0 (near cap): n=15444 MAE=0.6770165954415955 bias=-0.5764147176897177
- truth<9.0: n=58785 MAE=1.5933048294632985 bias=-0.0009630483966998339
- per-match MAE: n_matches=100 median=1.3846081363004172 p90=2.2719795126412254
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=8578.5 total_ghost_delivered=7989.0 total_over_charge=589.5 share_from_never_played_bases=0.0079
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | miner | 31 | 93.0 | 228 | 684.0 | 591.0 |
  | barbarians | 14 | 70.0 | 125 | 625.0 | 555.0 |
  | barbarian_barrel | 112 | 224.0 | 0 | 0.0 | -224.0 |
  | goblinstein | 33 | 165.0 | 65 | 325.0 | 160.0 |
  | lightning | 25 | 150.0 | 0 | 0.0 | -150.0 |
  | rocket | 20 | 120.0 | 0 | 0.0 | -120.0 |
  | witch | 12 | 60.0 | 35 | 175.0 | 115.0 |
  | graveyard | 21 | 105.0 | 0 | 0.0 | -105.0 |
  | zap | 49 | 98.0 | 0 | 0.0 | -98.0 |
  | fireball | 23 | 92.0 | 0 | 0.0 | -92.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition A_wl perfect detection (units only, live's detector_cards whitelist)
- single: n=45611 MAE=2.0863940014470193 bias=1.5209379579487403 P90=5.1274
- double: n=22173 MAE=2.610495260000902 bias=2.033537175844496 P90=5.902819999999999
- overtime: n=6445 MAE=2.325599208688906 bias=1.9995062373933281 P90=5.57706
- opponent-play ticks: n=2362 MAE=3.3786663420829806 bias=2.979167019475021
- our accepted-play ticks: n=3456 MAE=2.4738756655092593 bias=1.8425758391203704
- truth>=9.0 (near cap): n=15444 MAE=0.44178563843563845 bias=-0.18465297850297852
- truth<9.0: n=58785 MAE=2.742376077230586 bias=2.21484595219869
- per-match MAE: n_matches=100 median=2.1045744192380353 p90=3.4120339777468707
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=5112.0 total_ghost_delivered=7989.0 total_over_charge=-2877.0 share_from_never_played_bases=0.007
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | miner | 31 | 93.0 | 228 | 684.0 | 591.0 |
  | barbarians | 14 | 70.0 | 125 | 625.0 | 555.0 |
  | barbarian_barrel | 112 | 224.0 | 0 | 0.0 | -224.0 |
  | goblinstein | 33 | 165.0 | 0 | 0.0 | -165.0 |
  | lightning | 25 | 150.0 | 0 | 0.0 | -150.0 |
  | royal_ghost | 49 | 147.0 | 0 | 0.0 | -147.0 |
  | tombstone | 49 | 147.0 | 0 | 0.0 | -147.0 |
  | golden_knight | 33 | 132.0 | 0 | 0.0 | -132.0 |
  | rocket | 20 | 120.0 | 0 | 0.0 | -120.0 |
  | zappies | 30 | 120.0 | 0 | 0.0 | -120.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition B degraded (live)
- single: n=45611 MAE=5.571211878713468 bias=-5.557480217491395 P90=9.0
- double: n=22173 MAE=5.874953713976458 bias=-5.872088138727281 P90=9.1777
- overtime: n=6445 MAE=6.336390038789759 bias=-6.336304670287044 P90=10.0
- opponent-play ticks: n=2362 MAE=3.9824158340389504 bias=-3.9071422523285353
- our accepted-play ticks: n=3456 MAE=5.476925462962964 bias=-5.464125694444444
- truth>=9.0 (near cap): n=15444 MAE=8.222850110075111 bias=-8.222163474488474
- truth<9.0: n=58785 MAE=5.073032753253381 bias=-5.0614685957302035
- per-match MAE: n_matches=100 median=5.750937766662358 p90=6.800035853773778
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=105026.0 total_ghost_delivered=7989.0 total_over_charge=97037.0 share_from_never_played_bases=0.0714
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | knight | 47 | 141.0 | 961 | 2883.0 | 2742.0 |
  | tesla | 16 | 64.0 | 633 | 2532.0 | 2468.0 |
  | ice_wizard | 20 | 60.0 | 717 | 2151.0 | 2091.0 |
  | wizard | 14 | 70.0 | 428 | 2140.0 | 2070.0 |
  | x_bow | 4 | 24.0 | 342 | 2052.0 | 2028.0 |
  | musketeer | 44 | 176.0 | 519 | 2076.0 | 1900.0 |
  | bowler | 39 | 195.0 | 416 | 2080.0 | 1885.0 |
  | balloon | 37 | 185.0 | 407 | 2035.0 | 1850.0 |
  | valkyrie | 31 | 124.0 | 483 | 1932.0 | 1808.0 |
  | giant | 31 | 155.0 | 386 | 1930.0 | 1775.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition B_tt IDEALISED: bill once per TeamTracker-confirmed track (min_hits), no whitelist -- a design under test, NOT live's current path
- single: n=45611 MAE=3.138239394005832 bias=-2.8726563811361294 P90=6.764
- double: n=22173 MAE=3.5442357055878775 bias=-3.2771754070265637 P90=7.0
- overtime: n=6445 MAE=3.5245713886733903 bias=-3.166638262218774 P90=7.142
- opponent-play ticks: n=2362 MAE=2.479329551227773 bias=-0.5000719729043184
- our accepted-play ticks: n=3456 MAE=3.2098115162037035 bias=-2.897140740740741
- truth>=9.0 (near cap): n=15444 MAE=3.9632883255633256 bias=-3.9382344405594405
- truth<9.0: n=58785 MAE=3.116975640044229 bias=-2.77751860848856
- per-match MAE: n_matches=100 median=3.1161162726008342 p90=4.543447251821837
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=16090.5 total_ghost_delivered=7989.0 total_over_charge=8101.5 share_from_never_played_bases=0.0385
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | barbarians | 14 | 70.0 | 136 | 680.0 | 610.0 |
  | tombstone | 49 | 147.0 | 245 | 735.0 | 588.0 |
  | goblin_cage | 8 | 32.0 | 126 | 504.0 | 472.0 |
  | goblin_drill | 14 | 56.0 | 118 | 472.0 | 416.0 |
  | tesla | 16 | 64.0 | 94 | 376.0 | 312.0 |
  | elixir_collector | 10 | 60.0 | 53 | 318.0 | 258.0 |
  | barbarian_hut | 0 | 0.0 | 42 | 252.0 | 252.0 |
  | knight | 47 | 141.0 | 131 | 393.0 | 252.0 |
  | goblinstein | 33 | 165.0 | 82 | 410.0 | 245.0 |
  | mortar | 6 | 24.0 | 67 | 268.0 | 244.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition B_tt_wl live-reachable: B_tt's billing, restricted to live's detector_cards whitelist
- single: n=45611 MAE=2.558759084431387 bias=-0.6046837429567429 P90=6.0
- double: n=22173 MAE=2.8503577368872053 bias=-0.26375818788616784 P90=6.009419999999999
- overtime: n=6445 MAE=2.718522854926299 bias=-0.5388647944142746 P90=6.071
- opponent-play ticks: n=2362 MAE=3.3621155800169347 bias=1.9961176968670618
- our accepted-play ticks: n=3456 MAE=2.736236226851852 bias=-0.3669034722222222
- truth>=9.0 (near cap): n=15444 MAE=2.1454694832944834 bias=-2.010463137788138
- truth<9.0: n=58785 MAE=2.7948420821638176 bias=-0.0995480377647359
- per-match MAE: n_matches=100 median=2.6184855041468262 p90=3.65072793539479
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=8854.0 total_ghost_delivered=7989.0 total_over_charge=865.0 share_from_never_played_bases=0.0167
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | barbarians | 14 | 70.0 | 136 | 680.0 | 610.0 |
  | goblin_cage | 8 | 32.0 | 126 | 504.0 | 472.0 |
  | tesla | 16 | 64.0 | 94 | 376.0 | 312.0 |
  | elixir_collector | 10 | 60.0 | 53 | 318.0 | 258.0 |
  | knight | 47 | 141.0 | 131 | 393.0 | 252.0 |
  | barbarian_barrel | 112 | 224.0 | 0 | 0.0 | -224.0 |
  | witch | 12 | 60.0 | 55 | 275.0 | 215.0 |
  | x_bow | 4 | 24.0 | 38 | 228.0 | 204.0 |
  | musketeer | 44 | 176.0 | 93 | 372.0 | 196.0 |
  | goblinstein | 33 | 165.0 | 0 | 0.0 | -165.0 |
  (top 10 shown here; top 25 in summary.json)
