# opp_est_audit summary

n_ticks=74065 n_matches=100 port=38031 split=heldout entries=0:100 decide_every=10 estimator_step=5

| condition | MAE | bias | P90\|err\| | share<=1.0 | share<=2.0 |
|---|---|---|---|---|---|
| A+ perfect detection (+spells, no whitelist) [v1] | 2.508277222709782 | -1.9530112752312159 | 5.8950000000000005 | 0.3610882333085803 | 0.4941200297036387 |
| A+ perfect detection (+spells, no whitelist) [v2] | 2.012362161614798 | -1.1995168581651252 | 5.0534 | 0.42747586579355973 | 0.5851076756902721 |
| A perfect detection (units only, NO whitelist -- loose upper bound) [v1] | 2.508277222709782 | -1.9530112752312159 | 5.8950000000000005 | 0.3610882333085803 | 0.4941200297036387 |
| A perfect detection (units only, NO whitelist -- loose upper bound) [v2] | 2.012362161614798 | -1.1995168581651252 | 5.0534 | 0.42747586579355973 | 0.5851076756902721 |
| A_wl perfect detection (units only, live's detector_cards whitelist) [v1] | 2.351189714440019 | 0.7392367244987511 | 5.598599999999999 | 0.3669344494700601 | 0.5236616485519476 |
| A_wl perfect detection (units only, live's detector_cards whitelist) [v2] | 2.3242421805171136 | 1.0883694795112402 | 5.545600000000006 | 0.3763991088908391 | 0.5244717477891042 |
| B degraded (live) [v1] | 5.90376247485317 | -5.899144752582192 | 9.3806 | 0.047039762370890435 | 0.09470060082360089 |
| B degraded (live) [v2] | 5.811292503881725 | -5.805875327077567 | 9.1769 | 0.05002362789441707 | 0.10095186660365894 |

## Condition A+ perfect detection (+spells, no whitelist) [v1]
- single: n=45524 MAE=2.3294600474475002 bias=-1.835346322818733 P90=5.8274
- double: n=21089 MAE=2.8382266489639147 bias=-2.30658340367016 P90=6.033380000000001
- overtime: n=7452 MAE=2.66691512345679 bias=-1.6712207058507784 P90=5.9643
- opponent-play ticks: n=2427 MAE=2.454324186238154 bias=-1.2839057272352699
- our accepted-play ticks: n=3770 MAE=2.5003575596816976 bias=-1.9064981962864722
- truth>=9.0 (near cap): n=14783 MAE=2.2906272001623487 bias=-2.2430316376919435
- truth<9.0: n=59282 MAE=2.562552049525994 bias=-1.8806896427246043
- per-match MAE: n_matches=100 median=2.2011532014909596 p90=4.152420132477904
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=14364.0 total_ghost_delivered=8179.0 total_over_charge=6185.0 share_from_never_played_bases=0.01
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | tombstone | 58 | 174.0 | 442 | 1326.0 | 1152.0 |
  | barbarians | 14 | 70.0 | 180 | 900.0 | 830.0 |
  | royal_hogs | 49 | 245.0 | 197 | 985.0 | 740.0 |
  | witch | 16 | 80.0 | 142 | 710.0 | 630.0 |
  | skeleton_army | 21 | 63.0 | 199 | 597.0 | 534.0 |
  | miner | 28 | 84.0 | 201 | 603.0 | 519.0 |
  | skeletons | 133 | 133.0 | 571 | 571.0 | 438.0 |
  | goblin_gang | 27 | 81.0 | 119 | 357.0 | 276.0 |
  | barbarian_barrel | 133 | 266.0 | 0 | 0.0 | -266.0 |
  | night_witch | 10 | 40.0 | 76 | 304.0 | 264.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition A+ perfect detection (+spells, no whitelist) [v2]
- single: n=45524 MAE=1.847680304894122 bias=-1.1930649547491432 P90=4.982200000000001
- double: n=21089 MAE=2.2735456446488693 bias=-1.4813304044762672 P90=5.1428
- overtime: n=7452 MAE=2.279254052603328 bias=-0.4414050187869028 P90=5.107100000000001
- opponent-play ticks: n=2427 MAE=2.1948030490317265 bias=-0.5123964565306963
- our accepted-play ticks: n=3770 MAE=2.009612519893899 bias=-1.106223395225464
- truth>=9.0 (near cap): n=14783 MAE=1.4665528309544749 bias=-1.4045258540215113
- truth<9.0: n=59282 MAE=2.1484692318072938 bias=-1.1483942916905638
- per-match MAE: n_matches=100 median=1.8072312875245533 p90=3.225344714582947
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=10835.5 total_ghost_delivered=8179.0 total_over_charge=2656.5 share_from_never_played_bases=0.0063
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | barbarians | 14 | 70.0 | 166 | 830.0 | 760.0 |
  | miner | 28 | 84.0 | 201 | 603.0 | 519.0 |
  | royal_hogs | 49 | 245.0 | 120 | 600.0 | 355.0 |
  | witch | 16 | 80.0 | 84 | 420.0 | 340.0 |
  | barbarian_barrel | 133 | 266.0 | 0 | 0.0 | -266.0 |
  | skeletons | 133 | 133.0 | 390 | 390.0 | 257.0 |
  | skeleton_barrel | 20 | 60.0 | 85 | 255.0 | 195.0 |
  | graveyard | 34 | 170.0 | 0 | 0.0 | -170.0 |
  | skeleton_army | 21 | 63.0 | 77 | 231.0 | 168.0 |
  | goblins | 12 | 24.0 | 91 | 182.0 | 158.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition A perfect detection (units only, NO whitelist -- loose upper bound) [v1]
- single: n=45524 MAE=2.3294600474475002 bias=-1.835346322818733 P90=5.8274
- double: n=21089 MAE=2.8382266489639147 bias=-2.30658340367016 P90=6.033380000000001
- overtime: n=7452 MAE=2.66691512345679 bias=-1.6712207058507784 P90=5.9643
- opponent-play ticks: n=2427 MAE=2.454324186238154 bias=-1.2839057272352699
- our accepted-play ticks: n=3770 MAE=2.5003575596816976 bias=-1.9064981962864722
- truth>=9.0 (near cap): n=14783 MAE=2.2906272001623487 bias=-2.2430316376919435
- truth<9.0: n=59282 MAE=2.562552049525994 bias=-1.8806896427246043
- per-match MAE: n_matches=100 median=2.2011532014909596 p90=4.152420132477904
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=14364.0 total_ghost_delivered=8179.0 total_over_charge=6185.0 share_from_never_played_bases=0.01
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | tombstone | 58 | 174.0 | 442 | 1326.0 | 1152.0 |
  | barbarians | 14 | 70.0 | 180 | 900.0 | 830.0 |
  | royal_hogs | 49 | 245.0 | 197 | 985.0 | 740.0 |
  | witch | 16 | 80.0 | 142 | 710.0 | 630.0 |
  | skeleton_army | 21 | 63.0 | 199 | 597.0 | 534.0 |
  | miner | 28 | 84.0 | 201 | 603.0 | 519.0 |
  | skeletons | 133 | 133.0 | 571 | 571.0 | 438.0 |
  | goblin_gang | 27 | 81.0 | 119 | 357.0 | 276.0 |
  | barbarian_barrel | 133 | 266.0 | 0 | 0.0 | -266.0 |
  | night_witch | 10 | 40.0 | 76 | 304.0 | 264.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition A perfect detection (units only, NO whitelist -- loose upper bound) [v2]
- single: n=45524 MAE=1.847680304894122 bias=-1.1930649547491432 P90=4.982200000000001
- double: n=21089 MAE=2.2735456446488693 bias=-1.4813304044762672 P90=5.1428
- overtime: n=7452 MAE=2.279254052603328 bias=-0.4414050187869028 P90=5.107100000000001
- opponent-play ticks: n=2427 MAE=2.1948030490317265 bias=-0.5123964565306963
- our accepted-play ticks: n=3770 MAE=2.009612519893899 bias=-1.106223395225464
- truth>=9.0 (near cap): n=14783 MAE=1.4665528309544749 bias=-1.4045258540215113
- truth<9.0: n=59282 MAE=2.1484692318072938 bias=-1.1483942916905638
- per-match MAE: n_matches=100 median=1.8072312875245533 p90=3.225344714582947
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=10835.5 total_ghost_delivered=8179.0 total_over_charge=2656.5 share_from_never_played_bases=0.0063
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | barbarians | 14 | 70.0 | 166 | 830.0 | 760.0 |
  | miner | 28 | 84.0 | 201 | 603.0 | 519.0 |
  | royal_hogs | 49 | 245.0 | 120 | 600.0 | 355.0 |
  | witch | 16 | 80.0 | 84 | 420.0 | 340.0 |
  | barbarian_barrel | 133 | 266.0 | 0 | 0.0 | -266.0 |
  | skeletons | 133 | 133.0 | 390 | 390.0 | 257.0 |
  | skeleton_barrel | 20 | 60.0 | 85 | 255.0 | 195.0 |
  | graveyard | 34 | 170.0 | 0 | 0.0 | -170.0 |
  | skeleton_army | 21 | 63.0 | 77 | 231.0 | 168.0 |
  | goblins | 12 | 24.0 | 91 | 182.0 | 158.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition A_wl perfect detection (units only, live's detector_cards whitelist) [v1]
- single: n=45524 MAE=2.222982795887883 bias=0.6271462700992882 P90=5.4852
- double: n=21089 MAE=2.5992820901891984 bias=1.0431066717245958 P90=5.819500000000001
- overtime: n=7452 MAE=2.4323050724637683 bias=0.5640478529253892 P90=5.540180000000001
- opponent-play ticks: n=2427 MAE=3.1720028842192005 bias=1.9543892871858264
- our accepted-play ticks: n=3770 MAE=2.43815549071618 bias=0.8774842970822281
- truth>=9.0 (near cap): n=14783 MAE=0.9664272407495096 bias=-0.7574590204965163
- truth<9.0: n=59282 MAE=2.696504374008974 bias=1.112463896292298
- per-match MAE: n_matches=100 median=2.3186230180806677 p90=3.234364607475485
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=7729.0 total_ghost_delivered=8179.0 total_over_charge=-450.0 share_from_never_played_bases=0.0047
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | barbarians | 14 | 70.0 | 180 | 900.0 | 830.0 |
  | royal_hogs | 49 | 245.0 | 197 | 985.0 | 740.0 |
  | witch | 16 | 80.0 | 142 | 710.0 | 630.0 |
  | miner | 28 | 84.0 | 201 | 603.0 | 519.0 |
  | skeletons | 133 | 133.0 | 571 | 571.0 | 438.0 |
  | barbarian_barrel | 133 | 266.0 | 0 | 0.0 | -266.0 |
  | goblins | 12 | 24.0 | 137 | 274.0 | 250.0 |
  | tombstone | 58 | 174.0 | 0 | 0.0 | -174.0 |
  | graveyard | 34 | 170.0 | 0 | 0.0 | -170.0 |
  | goblinstein | 32 | 160.0 | 0 | 0.0 | -160.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition A_wl perfect detection (units only, live's detector_cards whitelist) [v2]
- single: n=45524 MAE=2.167603659608119 bias=0.9225290352341622 P90=5.351700000000005
- double: n=21089 MAE=2.599791441035611 bias=1.3852353406989426 P90=5.7557
- overtime: n=7452 MAE=2.501342780461621 bias=1.2613587761674718 P90=5.749490000000006
- opponent-play ticks: n=2427 MAE=3.2542078697981047 bias=2.364953152039555
- our accepted-play ticks: n=3770 MAE=2.455895305039788 bias=1.2446096286472148
- truth>=9.0 (near cap): n=14783 MAE=0.8030980653453291 bias=-0.5761048298721504
- truth<9.0: n=59282 MAE=2.7035659795553455 bias=1.5034351607570595
- per-match MAE: n_matches=100 median=2.3024139777468706 p90=3.267358932374996
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=6535.0 total_ghost_delivered=8179.0 total_over_charge=-1644.0 share_from_never_played_bases=0.0055
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | barbarians | 14 | 70.0 | 166 | 830.0 | 760.0 |
  | miner | 28 | 84.0 | 201 | 603.0 | 519.0 |
  | royal_hogs | 49 | 245.0 | 120 | 600.0 | 355.0 |
  | witch | 16 | 80.0 | 84 | 420.0 | 340.0 |
  | barbarian_barrel | 133 | 266.0 | 0 | 0.0 | -266.0 |
  | skeletons | 133 | 133.0 | 391 | 391.0 | 258.0 |
  | tombstone | 58 | 174.0 | 0 | 0.0 | -174.0 |
  | graveyard | 34 | 170.0 | 0 | 0.0 | -170.0 |
  | goblinstein | 32 | 160.0 | 0 | 0.0 | -160.0 |
  | goblins | 12 | 24.0 | 91 | 182.0 | 158.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition B degraded (live) [v1]
- single: n=45524 MAE=5.843916681310956 bias=-5.8367284113874 P90=9.293280000000001
- double: n=21089 MAE=5.961061349518706 bias=-5.960648546635687 P90=9.291420000000002
- overtime: n=7452 MAE=6.1072036902844875 bias=-6.106389519592057 P90=10.0
- opponent-play ticks: n=2427 MAE=4.085423485784919 bias=-4.050594643592913
- our accepted-play ticks: n=3770 MAE=5.668548885941645 bias=-5.6633481962864725
- truth>=9.0 (near cap): n=14783 MAE=8.738439917472773 bias=-8.737826997226543
- truth<9.0: n=59282 MAE=5.196886245403327 bias=-5.191269855942783
- per-match MAE: n_matches=100 median=5.936920653685675 p90=6.891969944592031
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=146102.5 total_ghost_delivered=8179.0 total_over_charge=137923.5 share_from_never_played_bases=0.0694
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | knight | 65 | 195.0 | 2573 | 7719.0 | 7524.0 |
  | ice_wizard | 29 | 87.0 | 1820 | 5460.0 | 5373.0 |
  | skeletons | 133 | 133.0 | 3770 | 3770.0 | 3637.0 |
  | royal_hogs | 49 | 245.0 | 713 | 3565.0 | 3320.0 |
  | barbarians | 14 | 70.0 | 644 | 3220.0 | 3150.0 |
  | tombstone | 58 | 174.0 | 975 | 2925.0 | 2751.0 |
  | bowler | 46 | 230.0 | 567 | 2835.0 | 2605.0 |
  | wizard | 17 | 85.0 | 530 | 2650.0 | 2565.0 |
  | musketeer | 52 | 208.0 | 683 | 2732.0 | 2524.0 |
  | balloon | 33 | 165.0 | 503 | 2515.0 | 2350.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition B degraded (live) [v2]
- single: n=45524 MAE=5.745614704331781 bias=-5.737703721114138 P90=9.094
- double: n=21089 MAE=5.886012214898763 bias=-5.885087827777514 P90=9.1063
- overtime: n=7452 MAE=6.0010606414385395 bias=-5.998163539989265 P90=10.0
- opponent-play ticks: n=2427 MAE=4.0180974866089825 bias=-3.974574866089823
- our accepted-play ticks: n=3770 MAE=5.5504556763925725 bias=-5.542791167108754
- truth>=9.0 (near cap): n=14783 MAE=8.576304058716094 bias=-8.575613644050598
- truth<9.0: n=59282 MAE=5.121788677844878 bias=-5.115192800512804
- per-match MAE: n_matches=100 median=5.879806675938804 p90=6.815426148454831
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=120168.5 total_ghost_delivered=8179.0 total_over_charge=111989.5 share_from_never_played_bases=0.0814
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | knight | 65 | 195.0 | 1289 | 3867.0 | 3672.0 |
  | ice_wizard | 29 | 87.0 | 977 | 2931.0 | 2844.0 |
  | wizard | 17 | 85.0 | 493 | 2465.0 | 2380.0 |
  | barbarians | 14 | 70.0 | 482 | 2410.0 | 2340.0 |
  | bowler | 46 | 230.0 | 504 | 2520.0 | 2290.0 |
  | musketeer | 52 | 208.0 | 621 | 2484.0 | 2276.0 |
  | tesla | 19 | 76.0 | 555 | 2220.0 | 2144.0 |
  | balloon | 33 | 165.0 | 453 | 2265.0 | 2100.0 |
  | giant | 29 | 145.0 | 436 | 2180.0 | 2035.0 |
  | valkyrie | 33 | 132.0 | 540 | 2160.0 | 2028.0 |
  (top 10 shown here; top 25 in summary.json)
