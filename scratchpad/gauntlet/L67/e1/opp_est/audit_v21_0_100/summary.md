# opp_est_audit summary

n_ticks=74065 n_matches=100 port=38031 split=heldout entries=0:100 decide_every=10 estimator_step=5

| condition | MAE | bias | P90\|err\| | share<=1.0 | share<=2.0 |
|---|---|---|---|---|---|
| A+ perfect detection (+spells, no whitelist) | 1.5133354202389793 | -0.14252804023492877 | 4.135 | 0.5327752649699589 | 0.6811314386012286 |
| A perfect detection (units only, NO whitelist -- loose upper bound) | 1.5133354202389793 | -0.14252804023492877 | 4.135 | 0.5327752649699589 | 0.6811314386012286 |
| A_wl perfect detection (units only, live's detector_cards whitelist) | 2.3302980341591844 | 1.6941598933369337 | 5.5998 | 0.38152973739283064 | 0.5159252008371026 |
| B degraded (live) | 5.773079531492607 | -5.76754413150611 | 9.0698 | 0.05092823870924188 | 0.10269357996354553 |
| B_tt IDEALISED: bill once per TeamTracker-confirmed track (min_hits), no whitelist -- a design under test, NOT live's current path | 3.331446349827854 | -3.0098245608587053 | 6.8925 | 0.23717005333153313 | 0.37125497873489505 |
| B_tt_wl live-reachable: B_tt's billing, restricted to live's detector_cards whitelist | 2.6840131033551606 | -0.4217532721258354 | 6.0 | 0.3032336461216499 | 0.47061365017214607 |
| B_corrS correlated-degrade, SHORT persistence | 5.578267531222575 | -5.56573490987646 | 9.0 | 0.06012286505096874 | 0.11579018429757645 |
| B_corrS_tt IDEALISED tracker-input on SHORT correlated -- design under test, NOT live's current path | 5.050431284682373 | -5.018931426449741 | 8.646680000000005 | 0.08877337473840545 | 0.15952204145007765 |
| B_corrS_tt_wl live-reachable tracker-input on SHORT correlated | 3.8790916856814963 | -3.463284359684061 | 7.60376 | 0.17664213866198608 | 0.2963613042597718 |
| B_corrL correlated-degrade, LONG persistence | 4.265858263687301 | -4.127856019712415 | 7.789999999999999 | 0.1376088570849929 | 0.2384797137649362 |
| B_corrL_tt IDEALISED tracker-input on LONG correlated -- design under test, NOT live's current path | 4.6165513845946125 | -4.538454818065214 | 8.0 | 0.1120367244987511 | 0.19994599338418956 |
| B_corrL_tt_wl live-reachable tracker-input on LONG correlated | 3.4626502113008844 | -2.4504105326402486 | 7.0 | 0.20411800445554582 | 0.3440626476743401 |

## Condition A+ perfect detection (+spells, no whitelist)
- single: n=45524 MAE=1.2969281609700378 bias=-0.2023562516474826 P90=3.5162000000000004
- double: n=21089 MAE=1.7527393902034236 bias=-0.29065671202996823 P90=4.609299999999999
- overtime: n=7452 MAE=2.1578514895330114 bias=0.6421613123993558 P90=5.282480000000001
- opponent-play ticks: n=2427 MAE=2.0323158632056035 bias=0.5426908941079521
- our accepted-play ticks: n=3770 MAE=1.5819422015915119 bias=-0.07087949602122015
- truth>=9.0 (near cap): n=14783 MAE=0.7578026584590408 bias=-0.6564197862409524
- truth<9.0: n=59282 MAE=1.701740683512702 bias=-0.014380176107418772
- per-match MAE: n_matches=100 median=1.4211297635605007 p90=2.4181755649540793
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=8717.0 total_ghost_delivered=8179.0 total_over_charge=538.0 share_from_never_played_bases=0.0075
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | barbarians | 14 | 70.0 | 147 | 735.0 | 665.0 |
  | miner | 28 | 84.0 | 201 | 603.0 | 519.0 |
  | barbarian_barrel | 133 | 266.0 | 0 | 0.0 | -266.0 |
  | graveyard | 34 | 170.0 | 0 | 0.0 | -170.0 |
  | goblinstein | 32 | 160.0 | 61 | 305.0 | 145.0 |
  | lightning | 22 | 132.0 | 0 | 0.0 | -132.0 |
  | fireball | 30 | 120.0 | 0 | 0.0 | -120.0 |
  | goblin_barrel | 37 | 111.0 | 0 | 0.0 | -111.0 |
  | witch | 16 | 80.0 | 38 | 190.0 | 110.0 |
  | rocket | 18 | 108.0 | 0 | 0.0 | -108.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition A perfect detection (units only, NO whitelist -- loose upper bound)
- single: n=45524 MAE=1.2969281609700378 bias=-0.2023562516474826 P90=3.5162000000000004
- double: n=21089 MAE=1.7527393902034236 bias=-0.29065671202996823 P90=4.609299999999999
- overtime: n=7452 MAE=2.1578514895330114 bias=0.6421613123993558 P90=5.282480000000001
- opponent-play ticks: n=2427 MAE=2.0323158632056035 bias=0.5426908941079521
- our accepted-play ticks: n=3770 MAE=1.5819422015915119 bias=-0.07087949602122015
- truth>=9.0 (near cap): n=14783 MAE=0.7578026584590408 bias=-0.6564197862409524
- truth<9.0: n=59282 MAE=1.701740683512702 bias=-0.014380176107418772
- per-match MAE: n_matches=100 median=1.4211297635605007 p90=2.4181755649540793
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=8717.0 total_ghost_delivered=8179.0 total_over_charge=538.0 share_from_never_played_bases=0.0075
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | barbarians | 14 | 70.0 | 147 | 735.0 | 665.0 |
  | miner | 28 | 84.0 | 201 | 603.0 | 519.0 |
  | barbarian_barrel | 133 | 266.0 | 0 | 0.0 | -266.0 |
  | graveyard | 34 | 170.0 | 0 | 0.0 | -170.0 |
  | goblinstein | 32 | 160.0 | 61 | 305.0 | 145.0 |
  | lightning | 22 | 132.0 | 0 | 0.0 | -132.0 |
  | fireball | 30 | 120.0 | 0 | 0.0 | -120.0 |
  | goblin_barrel | 37 | 111.0 | 0 | 0.0 | -111.0 |
  | witch | 16 | 80.0 | 38 | 190.0 | 110.0 |
  | rocket | 18 | 108.0 | 0 | 0.0 | -108.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition A_wl perfect detection (units only, live's detector_cards whitelist)
- single: n=45524 MAE=2.099866769176698 bias=1.5059371935682275 P90=5.1498
- double: n=21089 MAE=2.753204751292143 bias=2.0629280952155153 P90=6.043900000000003
- overtime: n=7452 MAE=2.5411774154589373 bias=1.8003995034889964 P90=5.881450000000002
- opponent-play ticks: n=2427 MAE=3.4676861145447058 bias=2.978773300370828
- our accepted-play ticks: n=3770 MAE=2.4868841114058355 bias=1.8389547214854112
- truth>=9.0 (near cap): n=14783 MAE=0.5097651423932896 bias=-0.24654810931475343
- truth<9.0: n=59282 MAE=2.784279643061975 bias=2.17810926082116
- per-match MAE: n_matches=100 median=2.185630943509158 p90=3.424659749652296
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=5357.0 total_ghost_delivered=8179.0 total_over_charge=-2822.0 share_from_never_played_bases=0.0067
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | barbarians | 14 | 70.0 | 147 | 735.0 | 665.0 |
  | miner | 28 | 84.0 | 201 | 603.0 | 519.0 |
  | barbarian_barrel | 133 | 266.0 | 0 | 0.0 | -266.0 |
  | tombstone | 58 | 174.0 | 0 | 0.0 | -174.0 |
  | graveyard | 34 | 170.0 | 0 | 0.0 | -170.0 |
  | goblinstein | 32 | 160.0 | 0 | 0.0 | -160.0 |
  | royal_ghost | 47 | 141.0 | 0 | 0.0 | -141.0 |
  | zappies | 34 | 136.0 | 0 | 0.0 | -136.0 |
  | lightning | 22 | 132.0 | 0 | 0.0 | -132.0 |
  | golden_knight | 31 | 124.0 | 0 | 0.0 | -124.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition B degraded (live)
- single: n=45524 MAE=5.7158230252174675 bias=-5.707807402688692 P90=9.014880000000002
- double: n=21089 MAE=5.831422713262839 bias=-5.83031993930485 P90=9.0
- overtime: n=7452 MAE=5.957747517444981 bias=-5.954819471282877 P90=10.0
- opponent-play ticks: n=2427 MAE=3.988585249278945 bias=-3.943672517511331
- our accepted-play ticks: n=3770 MAE=5.496017161803714 bias=-5.48735350132626
- truth>=9.0 (near cap): n=14783 MAE=8.516539464249476 bias=-8.51584904958398
- truth<9.0: n=59282 MAE=5.088949978070915 bias=-5.082206396545327
- per-match MAE: n_matches=100 median=5.8230058711167505 p90=6.797553656709847
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=106588.5 total_ghost_delivered=8179.0 total_over_charge=98409.5 share_from_never_played_bases=0.0881
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | knight | 65 | 195.0 | 999 | 2997.0 | 2802.0 |
  | ice_wizard | 29 | 87.0 | 793 | 2379.0 | 2292.0 |
  | wizard | 17 | 85.0 | 462 | 2310.0 | 2225.0 |
  | bowler | 46 | 230.0 | 457 | 2285.0 | 2055.0 |
  | musketeer | 52 | 208.0 | 565 | 2260.0 | 2052.0 |
  | balloon | 33 | 165.0 | 424 | 2120.0 | 1955.0 |
  | mega_knight | 10 | 70.0 | 281 | 1967.0 | 1897.0 |
  | valkyrie | 33 | 132.0 | 501 | 2004.0 | 1872.0 |
  | giant | 29 | 145.0 | 395 | 1975.0 | 1830.0 |
  | pekka | 13 | 91.0 | 253 | 1771.0 | 1680.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition B_tt IDEALISED: bill once per TeamTracker-confirmed track (min_hits), no whitelist -- a design under test, NOT live's current path
- single: n=45524 MAE=3.179686552148317 bias=-2.9011998989543977 P90=6.7524200000000025
- double: n=21089 MAE=3.632084480060695 bias=-3.384589937882308 P90=7.0
- overtime: n=7452 MAE=3.4077420424047236 bias=-2.612830743424584 P90=7.0
- opponent-play ticks: n=2427 MAE=2.459572805933251 bias=-0.4525311907704986
- our accepted-play ticks: n=3770 MAE=3.06019074270557 bias=-2.6162659681697615
- truth>=9.0 (near cap): n=14783 MAE=3.909326002841101 bias=-3.8871201041737127
- truth<9.0: n=59282 MAE=3.1873419857629637 bias=-2.791055625653655
- per-match MAE: n_matches=100 median=3.292220155862992 p90=4.441846008344923
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=16322.5 total_ghost_delivered=8179.0 total_over_charge=8143.5 share_from_never_played_bases=0.0385
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | barbarians | 14 | 70.0 | 161 | 805.0 | 735.0 |
  | tombstone | 58 | 174.0 | 196 | 588.0 | 414.0 |
  | goblin_cage | 8 | 32.0 | 98 | 392.0 | 360.0 |
  | knight | 65 | 195.0 | 183 | 549.0 | 354.0 |
  | goblin_drill | 14 | 56.0 | 91 | 364.0 | 308.0 |
  | witch | 16 | 80.0 | 70 | 350.0 | 270.0 |
  | barbarian_barrel | 133 | 266.0 | 0 | 0.0 | -266.0 |
  | tesla | 19 | 76.0 | 82 | 328.0 | 252.0 |
  | goblinstein | 32 | 160.0 | 79 | 395.0 | 235.0 |
  | mortar | 6 | 24.0 | 63 | 252.0 | 228.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition B_tt_wl live-reachable: B_tt's billing, restricted to live's detector_cards whitelist
- single: n=45524 MAE=2.561216531939197 bias=-0.5561291670327739 P90=5.9222800000000015
- double: n=21089 MAE=2.9435774953767364 bias=-0.1670120536772725 P90=6.20612
- overtime: n=7452 MAE=2.6996112855609233 bias=-0.3217679414922168 P90=5.96133
- opponent-play ticks: n=2427 MAE=3.372558796868562 bias=2.1049471775854967
- our accepted-play ticks: n=3770 MAE=2.622831697612732 bias=-0.004727506631299726
- truth>=9.0 (near cap): n=14783 MAE=2.2405442805925726 bias=-2.0973277751471286
- truth<9.0: n=59282 MAE=2.794599784082858 bias=-0.003919564117269999
- per-match MAE: n_matches=100 median=2.6332141716863244 p90=3.355636311313751
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=9067.0 total_ghost_delivered=8179.0 total_over_charge=888.0 share_from_never_played_bases=0.0203
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | barbarians | 14 | 70.0 | 161 | 805.0 | 735.0 |
  | goblin_cage | 8 | 32.0 | 98 | 392.0 | 360.0 |
  | knight | 65 | 195.0 | 183 | 549.0 | 354.0 |
  | witch | 16 | 80.0 | 70 | 350.0 | 270.0 |
  | barbarian_barrel | 133 | 266.0 | 0 | 0.0 | -266.0 |
  | tesla | 19 | 76.0 | 82 | 328.0 | 252.0 |
  | valkyrie | 33 | 132.0 | 84 | 336.0 | 204.0 |
  | bowler | 46 | 230.0 | 86 | 430.0 | 200.0 |
  | musketeer | 52 | 208.0 | 102 | 408.0 | 200.0 |
  | skeletons | 133 | 133.0 | 308 | 308.0 | 175.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition B_corrS correlated-degrade, SHORT persistence
- single: n=45524 MAE=5.513826944029523 bias=-5.4992360996397505 P90=9.0
- double: n=21089 MAE=5.670901417800749 bias=-5.665494674949025 P90=9.0
- overtime: n=7452 MAE=5.709780850778315 bias=-5.689655756843801 P90=9.344280000000001
- opponent-play ticks: n=2427 MAE=3.9213609394313966 bias=-3.853849690976514
- our accepted-play ticks: n=3770 MAE=5.244651697612731 bias=-5.228069681697613
- truth>=9.0 (near cap): n=14783 MAE=8.142081532841777 bias=-8.141161908949469
- truth<9.0: n=59282 MAE=4.938935822003306 bias=-4.923507297324652
- per-match MAE: n_matches=100 median=5.6016252931280235 p90=6.619428340395481
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=81122.0 total_ghost_delivered=8179.0 total_over_charge=72943.0 share_from_never_played_bases=0.0913
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | wizard | 17 | 85.0 | 423 | 2115.0 | 2030.0 |
  | bowler | 46 | 230.0 | 374 | 1870.0 | 1640.0 |
  | giant | 29 | 145.0 | 355 | 1775.0 | 1630.0 |
  | musketeer | 52 | 208.0 | 444 | 1776.0 | 1568.0 |
  | pekka | 13 | 91.0 | 227 | 1589.0 | 1498.0 |
  | valkyrie | 33 | 132.0 | 407 | 1628.0 | 1496.0 |
  | balloon | 33 | 165.0 | 329 | 1645.0 | 1480.0 |
  | barbarians | 14 | 70.0 | 308 | 1540.0 | 1470.0 |
  | mega_knight | 10 | 70.0 | 218 | 1526.0 | 1456.0 |
  | goblinstein | 32 | 160.0 | 297 | 1485.0 | 1325.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition B_corrS_tt IDEALISED tracker-input on SHORT correlated -- design under test, NOT live's current path
- single: n=45524 MAE=4.970717410596609 bias=-4.938246292065723 P90=8.5992
- double: n=21089 MAE=5.171737673668737 bias=-5.144915225947176 P90=8.566880000000001
- overtime: n=7452 MAE=5.194105998389694 bias=-5.155302563070317 P90=9.0
- opponent-play ticks: n=2427 MAE=3.2263586320560362 bias=-2.8223292954264525
- our accepted-play ticks: n=3770 MAE=4.671266763925729 bias=-4.612154562334218
- truth>=9.0 (near cap): n=14783 MAE=7.282153263884191 bias=-7.27993617668944
- truth<9.0: n=59282 MAE=4.493912509699403 bias=-4.455110482102493
- per-match MAE: n_matches=100 median=5.0674420541232275 p90=6.09292862861805
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=39435.0 total_ghost_delivered=8179.0 total_over_charge=31256.0 share_from_never_played_bases=0.082
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | barbarians | 14 | 70.0 | 234 | 1170.0 | 1100.0 |
  | wizard | 17 | 85.0 | 183 | 915.0 | 830.0 |
  | giant | 29 | 145.0 | 170 | 850.0 | 705.0 |
  | witch | 16 | 80.0 | 149 | 745.0 | 665.0 |
  | goblin_drill | 14 | 56.0 | 177 | 708.0 | 652.0 |
  | pekka | 13 | 91.0 | 105 | 735.0 | 644.0 |
  | musketeer | 52 | 208.0 | 211 | 844.0 | 636.0 |
  | bowler | 46 | 230.0 | 173 | 865.0 | 635.0 |
  | goblin_giant | 3 | 18.0 | 105 | 630.0 | 612.0 |
  | mega_knight | 10 | 70.0 | 97 | 679.0 | 609.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition B_corrS_tt_wl live-reachable tracker-input on SHORT correlated
- single: n=45524 MAE=3.809174576047799 bias=-3.4084488225990683 P90=7.6052
- double: n=21089 MAE=4.005691516904547 bias=-3.554299265019678 P90=7.5395
- overtime: n=7452 MAE=3.9479379898013955 bias=-3.540702455716586 P90=7.834840000000009
- opponent-play ticks: n=2427 MAE=2.748484136794396 bias=-1.2071665430572724
- our accepted-play ticks: n=3770 MAE=3.5237162599469496 bias=-2.9927911671087535
- truth>=9.0 (near cap): n=14783 MAE=5.141083535141717 bias=-5.1130553000067644
- truth<9.0: n=59282 MAE=3.5643920211868694 bias=-3.051885219796903
- per-match MAE: n_matches=100 median=3.8018634745191022 p90=4.920977595512593
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=19527.5 total_ghost_delivered=8179.0 total_over_charge=11348.5 share_from_never_played_bases=0.0539
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | barbarians | 14 | 70.0 | 236 | 1180.0 | 1110.0 |
  | giant | 29 | 145.0 | 170 | 850.0 | 705.0 |
  | witch | 16 | 80.0 | 149 | 745.0 | 665.0 |
  | pekka | 13 | 91.0 | 105 | 735.0 | 644.0 |
  | musketeer | 52 | 208.0 | 211 | 844.0 | 636.0 |
  | bowler | 46 | 230.0 | 173 | 865.0 | 635.0 |
  | mega_knight | 10 | 70.0 | 97 | 679.0 | 609.0 |
  | valkyrie | 33 | 132.0 | 183 | 732.0 | 600.0 |
  | balloon | 33 | 165.0 | 150 | 750.0 | 585.0 |
  | goblin_cage | 8 | 32.0 | 151 | 604.0 | 572.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition B_corrL correlated-degrade, LONG persistence
- single: n=45524 MAE=4.272025072489237 bias=-4.166532470784641 P90=7.804420000000002
- double: n=21089 MAE=4.283408383517473 bias=-4.109991806154867 P90=7.743860000000001
- overtime: n=7452 MAE=4.178518988191089 bias=-3.9421383118625872 P90=7.88562
- opponent-play ticks: n=2427 MAE=3.274246971569839 bias=-2.7955472599917592
- our accepted-play ticks: n=3770 MAE=3.8788229442970823 bias=-3.674488779840849
- truth>=9.0 (near cap): n=14783 MAE=5.522572109855916 bias=-5.5163563890955825
- truth<9.0: n=59282 MAE=3.952474761310347 bias=-3.781609250700044
- per-match MAE: n_matches=100 median=4.189836979352253 p90=5.232646650891156
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=26079.0 total_ghost_delivered=8179.0 total_over_charge=17900.0 share_from_never_played_bases=0.0805
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | barbarians | 14 | 70.0 | 160 | 800.0 | 730.0 |
  | miner | 28 | 84.0 | 190 | 570.0 | 486.0 |
  | valkyrie | 33 | 132.0 | 147 | 588.0 | 456.0 |
  | wizard | 17 | 85.0 | 103 | 515.0 | 430.0 |
  | knight | 65 | 195.0 | 199 | 597.0 | 402.0 |
  | mega_knight | 10 | 70.0 | 67 | 469.0 | 399.0 |
  | goblinstein | 32 | 160.0 | 105 | 525.0 | 365.0 |
  | boss_bandit | 0 | 0.0 | 60 | 360.0 | 360.0 |
  | musketeer | 52 | 208.0 | 140 | 560.0 | 352.0 |
  | pekka | 13 | 91.0 | 63 | 441.0 | 350.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition B_corrL_tt IDEALISED tracker-input on LONG correlated -- design under test, NOT live's current path
- single: n=45524 MAE=4.639851704595378 bias=-4.574207543273878 P90=8.045880000000002
- double: n=21089 MAE=4.557146607236 bias=-4.461976253022903 P90=8.0
- overtime: n=7452 MAE=4.642324812130972 bias=-4.53647540257649 P90=8.0
- opponent-play ticks: n=2427 MAE=2.913613514627112 bias=-2.269589287185826
- our accepted-play ticks: n=3770 MAE=4.233322944297083 bias=-4.105921140583555
- truth>=9.0 (near cap): n=14783 MAE=6.336403537847527 bias=-6.331921565311506
- truth<9.0: n=59282 MAE=4.187676272730339 bias=-4.091222624068013
- per-match MAE: n_matches=100 median=4.5430853255368175 p90=5.645609235048679
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=27388.5 total_ghost_delivered=8179.0 total_over_charge=19209.5 share_from_never_played_bases=0.0787
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | barbarians | 14 | 70.0 | 198 | 990.0 | 920.0 |
  | witch | 16 | 80.0 | 125 | 625.0 | 545.0 |
  | wizard | 17 | 85.0 | 110 | 550.0 | 465.0 |
  | pekka | 13 | 91.0 | 73 | 511.0 | 420.0 |
  | mega_knight | 10 | 70.0 | 65 | 455.0 | 385.0 |
  | giant | 29 | 145.0 | 105 | 525.0 | 380.0 |
  | elite_barbarians | 2 | 12.0 | 64 | 384.0 | 372.0 |
  | valkyrie | 33 | 132.0 | 126 | 504.0 | 372.0 |
  | musketeer | 52 | 208.0 | 144 | 576.0 | 368.0 |
  | goblinstein | 32 | 160.0 | 105 | 525.0 | 365.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition B_corrL_tt_wl live-reachable tracker-input on LONG correlated
- single: n=45524 MAE=3.4878507380722255 bias=-2.6994052411914593 P90=7.081880000000003
- double: n=21089 MAE=3.406599051638295 bias=-2.0025424249608803 P90=6.8568
- overtime: n=7452 MAE=3.4673246779388083 bias=-2.196767941492217 P90=6.901600000000001
- opponent-play ticks: n=2427 MAE=2.9584523279769264 bias=-0.0046531520395550075
- our accepted-play ticks: n=3770 MAE=3.233249681697613 bias=-1.9457089389920423
- truth>=9.0 (near cap): n=14783 MAE=4.078945782317527 bias=-4.026942873570993
- truth<9.0: n=59282 MAE=3.308966168482845 bias=-2.0572747140784724
- per-match MAE: n_matches=100 median=3.4644340205123507 p90=4.45715307719496
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=13937.0 total_ghost_delivered=8179.0 total_over_charge=5758.0 share_from_never_played_bases=0.0502
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | barbarians | 14 | 70.0 | 201 | 1005.0 | 935.0 |
  | witch | 16 | 80.0 | 125 | 625.0 | 545.0 |
  | pekka | 13 | 91.0 | 73 | 511.0 | 420.0 |
  | mega_knight | 10 | 70.0 | 65 | 455.0 | 385.0 |
  | giant | 29 | 145.0 | 105 | 525.0 | 380.0 |
  | valkyrie | 33 | 132.0 | 126 | 504.0 | 372.0 |
  | musketeer | 52 | 208.0 | 144 | 576.0 | 368.0 |
  | balloon | 33 | 165.0 | 104 | 520.0 | 355.0 |
  | bowler | 46 | 230.0 | 116 | 580.0 | 350.0 |
  | mini_pekka | 31 | 124.0 | 111 | 444.0 | 320.0 |
  (top 10 shown here; top 25 in summary.json)
