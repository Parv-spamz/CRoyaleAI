# opp_est_audit summary

n_ticks=74065 n_matches=100 port=38031 split=heldout entries=0:100 decide_every=10 estimator_step=5

| condition | MAE | bias | P90\|err\| | share<=1.0 | share<=2.0 |
|---|---|---|---|---|---|
| A+ perfect detection (+spells, no whitelist) | 2.508277222709782 | -1.9530112752312159 | 5.8950000000000005 | 0.3610882333085803 | 0.4941200297036387 |
| A perfect detection (units only, NO whitelist -- loose upper bound) | 2.508277222709782 | -1.9530112752312159 | 5.8950000000000005 | 0.3610882333085803 | 0.4941200297036387 |
| A_wl perfect detection (units only, live's detector_cards whitelist) | 2.351189714440019 | 0.7392367244987511 | 5.598599999999999 | 0.3669344494700601 | 0.5236616485519476 |
| B degraded (live) | 5.90376247485317 | -5.899144752582192 | 9.3806 | 0.047039762370890435 | 0.09470060082360089 |

## Condition A+ perfect detection (+spells, no whitelist)
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

## Condition A perfect detection (units only, NO whitelist -- loose upper bound)
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

## Condition A_wl perfect detection (units only, live's detector_cards whitelist)
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

## Condition B degraded (live)
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
