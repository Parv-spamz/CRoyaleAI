# opp_est_audit summary

n_ticks=76271 n_matches=100 port=38031 split=heldout entries=100:200 decide_every=10 estimator_step=5

| condition | MAE | bias | P90\|err\| | share<=1.0 | share<=2.0 |
|---|---|---|---|---|---|
| A+ perfect detection (+spells, no whitelist) | 1.4394757129184093 | -0.23772082311756762 | 3.9397 | 0.5374782027244955 | 0.6864470113149166 |
| A perfect detection (units only, NO whitelist -- loose upper bound) | 1.4394757129184093 | -0.23772082311756762 | 3.9397 | 0.5374782027244955 | 0.6864470113149166 |
| A_wl perfect detection (units only, live's detector_cards whitelist) | 2.4316048760341413 | 1.8191139030562073 | 5.780600000000001 | 0.36932779169015745 | 0.5007014461590906 |
| B degraded (live) | 5.662019737514914 | -5.650263326821466 | 9.0 | 0.056522138165226624 | 0.10707870619239292 |
| B_tt IDEALISED: bill once per TeamTracker-confirmed track (min_hits), no whitelist -- a design under test, NOT live's current path | 3.2406701183936226 | -2.9931131648988476 | 6.6832 | 0.23552857573651848 | 0.37787625703085054 |
| B_tt_wl live-reachable: B_tt's billing, restricted to live's detector_cards whitelist | 2.594992576470742 | 0.027228773714780195 | 5.818 | 0.31251720837539826 | 0.4814936214288524 |

## Condition A+ perfect detection (+spells, no whitelist)
- single: n=45745 MAE=1.2531881167340693 bias=-0.317360209859001 P90=3.6050399999999994
- double: n=22662 MAE=1.76736406318948 bias=-0.0873677963110052 P90=4.1464
- overtime: n=7864 MAE=1.5782244786368262 bias=-0.20773564343845372 P90=3.9928
- opponent-play ticks: n=2543 MAE=1.7942096736138418 bias=0.3979749901690916
- our accepted-play ticks: n=3586 MAE=1.4971462632459565 bias=-0.266801087562744
- truth>=9.0 (near cap): n=14870 MAE=0.7828259448554137 bias=-0.6790690383322125
- truth<9.0: n=61401 MAE=1.5985021465448446 bias=-0.1308357893193922
- per-match MAE: n_matches=100 median=1.328771835883171 p90=2.2411064644692793
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=9304.0 total_ghost_delivered=8381.0 total_over_charge=923.0 share_from_never_played_bases=0.0039
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | miner | 43 | 129.0 | 294 | 882.0 | 753.0 |
  | barbarians | 13 | 65.0 | 106 | 530.0 | 465.0 |
  | fireball | 51 | 204.0 | 0 | 0.0 | -204.0 |
  | barbarian_barrel | 94 | 188.0 | 0 | 0.0 | -188.0 |
  | witch | 13 | 65.0 | 49 | 245.0 | 180.0 |
  | the_log | 80 | 160.0 | 0 | 0.0 | -160.0 |
  | hog_rider | 64 | 256.0 | 103 | 412.0 | 156.0 |
  | goblin_barrel | 38 | 114.0 | 0 | 0.0 | -114.0 |
  | skeleton_barrel | 66 | 198.0 | 103 | 309.0 | 111.0 |
  | lightning | 18 | 108.0 | 0 | 0.0 | -108.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition A perfect detection (units only, NO whitelist -- loose upper bound)
- single: n=45745 MAE=1.2531881167340693 bias=-0.317360209859001 P90=3.6050399999999994
- double: n=22662 MAE=1.76736406318948 bias=-0.0873677963110052 P90=4.1464
- overtime: n=7864 MAE=1.5782244786368262 bias=-0.20773564343845372 P90=3.9928
- opponent-play ticks: n=2543 MAE=1.7942096736138418 bias=0.3979749901690916
- our accepted-play ticks: n=3586 MAE=1.4971462632459565 bias=-0.266801087562744
- truth>=9.0 (near cap): n=14870 MAE=0.7828259448554137 bias=-0.6790690383322125
- truth<9.0: n=61401 MAE=1.5985021465448446 bias=-0.1308357893193922
- per-match MAE: n_matches=100 median=1.328771835883171 p90=2.2411064644692793
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=9304.0 total_ghost_delivered=8381.0 total_over_charge=923.0 share_from_never_played_bases=0.0039
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | miner | 43 | 129.0 | 294 | 882.0 | 753.0 |
  | barbarians | 13 | 65.0 | 106 | 530.0 | 465.0 |
  | fireball | 51 | 204.0 | 0 | 0.0 | -204.0 |
  | barbarian_barrel | 94 | 188.0 | 0 | 0.0 | -188.0 |
  | witch | 13 | 65.0 | 49 | 245.0 | 180.0 |
  | the_log | 80 | 160.0 | 0 | 0.0 | -160.0 |
  | hog_rider | 64 | 256.0 | 103 | 412.0 | 156.0 |
  | goblin_barrel | 38 | 114.0 | 0 | 0.0 | -114.0 |
  | skeleton_barrel | 66 | 198.0 | 103 | 309.0 | 111.0 |
  | lightning | 18 | 108.0 | 0 | 0.0 | -108.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition A_wl perfect detection (units only, live's detector_cards whitelist)
- single: n=45745 MAE=2.327068042409006 bias=1.6811355820308231 P90=5.7509999999999994
- double: n=22662 MAE=2.6401679463418937 bias=2.010592021886859 P90=5.89606
- overtime: n=7864 MAE=2.4386726729399797 bias=2.069945689216684 P90=5.7948
- opponent-play ticks: n=2543 MAE=3.4887876130554463 bias=3.0701372001572946
- our accepted-play ticks: n=3586 MAE=2.548048968209704 bias=1.8837696040156162
- truth>=9.0 (near cap): n=14870 MAE=0.4861463887020847 bias=-0.19565626092804306
- truth<9.0: n=61401 MAE=2.9027530284523055 bias=2.3070478510121983
- per-match MAE: n_matches=100 median=2.4388512646267966 p90=3.476573334196252
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=5378.0 total_ghost_delivered=8381.0 total_over_charge=-3003.0 share_from_never_played_bases=0.0061
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | miner | 43 | 129.0 | 294 | 882.0 | 753.0 |
  | barbarians | 13 | 65.0 | 107 | 535.0 | 470.0 |
  | archer_queen | 45 | 225.0 | 0 | 0.0 | -225.0 |
  | fireball | 51 | 204.0 | 0 | 0.0 | -204.0 |
  | skeleton_barrel | 66 | 198.0 | 0 | 0.0 | -198.0 |
  | barbarian_barrel | 94 | 188.0 | 0 | 0.0 | -188.0 |
  | royal_ghost | 61 | 183.0 | 0 | 0.0 | -183.0 |
  | witch | 13 | 65.0 | 49 | 245.0 | 180.0 |
  | dark_prince | 40 | 160.0 | 0 | 0.0 | -160.0 |
  | the_log | 80 | 160.0 | 0 | 0.0 | -160.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition B degraded (live)
- single: n=45745 MAE=5.474541449338726 bias=-5.457290873319488 P90=9.0
- double: n=22662 MAE=5.824912748212867 bias=-5.82252361221428 P90=9.0
- overtime: n=7864 MAE=6.283168374872838 bias=-6.2763775559511705 P90=10.0
- opponent-play ticks: n=2543 MAE=4.027415768777035 bias=-3.9235175383405427
- our accepted-play ticks: n=3586 MAE=5.456737479085332 bias=-5.4442298382599
- truth>=9.0 (near cap): n=14870 MAE=8.291531519838601 bias=-8.290731143241425
- truth<9.0: n=61401 MAE=5.025208607351672 bias=-5.010798881125714
- per-match MAE: n_matches=100 median=5.650422870739389 p90=6.744933560500695
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=101451.5 total_ghost_delivered=8381.0 total_over_charge=93070.5 share_from_never_played_bases=0.0715
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | knight | 43 | 129.0 | 930 | 2790.0 | 2661.0 |
  | tesla | 10 | 40.0 | 642 | 2568.0 | 2528.0 |
  | ice_wizard | 14 | 42.0 | 754 | 2262.0 | 2220.0 |
  | x_bow | 7 | 42.0 | 349 | 2094.0 | 2052.0 |
  | wizard | 12 | 60.0 | 409 | 2045.0 | 1985.0 |
  | mega_knight | 19 | 133.0 | 286 | 2002.0 | 1869.0 |
  | balloon | 39 | 195.0 | 397 | 1985.0 | 1790.0 |
  | valkyrie | 46 | 184.0 | 467 | 1868.0 | 1684.0 |
  | musketeer | 32 | 128.0 | 442 | 1768.0 | 1640.0 |
  | giant | 10 | 50.0 | 336 | 1680.0 | 1630.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition B_tt IDEALISED: bill once per TeamTracker-confirmed track (min_hits), no whitelist -- a design under test, NOT live's current path
- single: n=45745 MAE=3.075738957263089 bias=-2.823352738004153 P90=6.512599999999998
- double: n=22662 MAE=3.535804019945283 bias=-3.2621582428735327 P90=6.8921
- overtime: n=7864 MAE=3.349577988301119 bias=-3.2052941378433366 P90=7.0
- opponent-play ticks: n=2543 MAE=2.439973692489186 bias=-0.5827782540306725
- our accepted-play ticks: n=3586 MAE=3.197197099832683 bias=-2.9369794199665367
- truth>=9.0 (near cap): n=14870 MAE=3.897122602555481 bias=-3.873448022864829
- truth<9.0: n=61401 MAE=3.081691462679761 bias=-2.7799150192993602
- per-match MAE: n_matches=100 median=3.193828250682426 p90=4.229051557719054
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=16080.0 total_ghost_delivered=8381.0 total_over_charge=7699.0 share_from_never_played_bases=0.0374
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | barbarians | 13 | 65.0 | 124 | 620.0 | 555.0 |
  | tombstone | 25 | 75.0 | 209 | 627.0 | 552.0 |
  | goblin_cage | 6 | 24.0 | 130 | 520.0 | 496.0 |
  | goblin_drill | 21 | 84.0 | 137 | 548.0 | 464.0 |
  | tesla | 10 | 40.0 | 92 | 368.0 | 328.0 |
  | skeleton_barrel | 66 | 198.0 | 164 | 492.0 | 294.0 |
  | witch | 13 | 65.0 | 66 | 330.0 | 265.0 |
  | knight | 43 | 129.0 | 122 | 366.0 | 237.0 |
  | barbarian_hut | 0 | 0.0 | 34 | 204.0 | 204.0 |
  | fireball | 51 | 204.0 | 0 | 0.0 | -204.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition B_tt_wl live-reachable: B_tt's billing, restricted to live's detector_cards whitelist
- single: n=45745 MAE=2.5248207104601597 bias=-0.005449141982730353 P90=5.76
- double: n=22662 MAE=2.727865823846086 bias=0.017715554673020915 P90=5.890380000000002
- overtime: n=7864 MAE=2.6202772253306206 bias=0.2447312945066124 P90=5.92284
- opponent-play ticks: n=2543 MAE=3.47064376720409 bias=2.4117164372788045
- our accepted-play ticks: n=3586 MAE=2.660487060791969 bias=0.09481087562744005
- truth>=9.0 (near cap): n=14870 MAE=1.9162254539340955 bias=-1.7500788231338265
- truth<9.0: n=61401 MAE=2.759375357078875 bias=0.4576544013941141
- per-match MAE: n_matches=100 median=2.4670878450106155 p90=3.564231015299027
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=8595.0 total_ghost_delivered=8381.0 total_over_charge=214.0 share_from_never_played_bases=0.0287
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | barbarians | 13 | 65.0 | 125 | 625.0 | 560.0 |
  | goblin_cage | 6 | 24.0 | 130 | 520.0 | 496.0 |
  | tesla | 10 | 40.0 | 92 | 368.0 | 328.0 |
  | witch | 13 | 65.0 | 66 | 330.0 | 265.0 |
  | knight | 43 | 129.0 | 122 | 366.0 | 237.0 |
  | archer_queen | 45 | 225.0 | 0 | 0.0 | -225.0 |
  | fireball | 51 | 204.0 | 0 | 0.0 | -204.0 |
  | goblin_hut | 20 | 80.0 | 70 | 280.0 | 200.0 |
  | elixir_collector | 0 | 0.0 | 33 | 198.0 | 198.0 |
  | skeleton_barrel | 66 | 198.0 | 0 | 0.0 | -198.0 |
  (top 10 shown here; top 25 in summary.json)
