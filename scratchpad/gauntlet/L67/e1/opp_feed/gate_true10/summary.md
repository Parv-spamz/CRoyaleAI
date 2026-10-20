# opp_est_audit summary

n_ticks=8197 n_matches=10 port=38031 split=heldout entries=0:10 decide_every=10 estimator_step=5

| condition | MAE | bias | P90\|err\| | share<=1.0 | share<=2.0 |
|---|---|---|---|---|---|
| A+ perfect detection (+spells, no whitelist) | 1.3749209832865683 | -0.3821855922898621 | 3.9671000000000003 | 0.569354641942174 | 0.7135537391728681 |
| A perfect detection (units only, NO whitelist -- loose upper bound) | 1.3749209832865683 | -0.3821855922898621 | 3.9671000000000003 | 0.569354641942174 | 0.7135537391728681 |
| A_wl perfect detection (units only, live's detector_cards whitelist) | 2.1812507624740762 | 1.6363764426009517 | 5.37488 | 0.4223496401122362 | 0.5498353055996096 |
| B degraded (live) | 6.01694131999512 | -6.006114285714285 | 9.2898 | 0.05465414175918019 | 0.08722703428083445 |
| B_tt IDEALISED: bill once per TeamTracker-confirmed track (min_hits), no whitelist -- a design under test, NOT live's current path | 3.5194134195437354 | -3.31421481029645 | 7.203400000000001 | 0.23667195315359277 | 0.37696718311577404 |
| B_tt_wl live-reachable: B_tt's billing, restricted to live's detector_cards whitelist | 2.6358045870440407 | -0.6105427351470051 | 5.980600000000006 | 0.32084909113090154 | 0.5004269854824936 |

## Condition A+ perfect detection (+spells, no whitelist)
- single: n=4620 MAE=1.0897132467532467 bias=-0.476787012987013 P90=3.4682000000000004
- double: n=2383 MAE=1.9989537138061266 bias=-0.5150054133445238 P90=4.888
- overtime: n=1194 MAE=1.2330363484087101 bias=0.24894355108877725 P90=4.26262
- opponent-play ticks: n=248 MAE=1.902144758064516 bias=0.23822701612903227
- our accepted-play ticks: n=406 MAE=1.5510541871921182 bias=-0.21387980295566503
- truth>=9.0 (near cap): n=1989 MAE=0.7764159376571141 bias=-0.669846103569633
- truth<9.0: n=6208 MAE=1.5666778350515465 bias=-0.2900211662371134
- per-match MAE: n_matches=10 median=1.3579917515241267 p90=2.1675007353963833
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=963.0 total_ghost_delivered=894.0 total_over_charge=69.0 share_from_never_played_bases=0.055
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | miner | 4 | 12.0 | 22 | 66.0 | 54.0 |
  | barbarians | 0 | 0.0 | 10 | 50.0 | 50.0 |
  | bandit | 4 | 12.0 | 16 | 48.0 | 36.0 |
  | witch | 6 | 30.0 | 13 | 65.0 | 35.0 |
  | graveyard | 6 | 30.0 | 0 | 0.0 | -30.0 |
  | lightning | 5 | 30.0 | 0 | 0.0 | -30.0 |
  | giant_snowball | 13 | 26.0 | 0 | 0.0 | -26.0 |
  | poison | 6 | 24.0 | 0 | 0.0 | -24.0 |
  | barbarian_barrel | 10 | 20.0 | 0 | 0.0 | -20.0 |
  | lumberjack | 3 | 12.0 | 7 | 28.0 | 16.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition A perfect detection (units only, NO whitelist -- loose upper bound)
- single: n=4620 MAE=1.0897132467532467 bias=-0.476787012987013 P90=3.4682000000000004
- double: n=2383 MAE=1.9989537138061266 bias=-0.5150054133445238 P90=4.888
- overtime: n=1194 MAE=1.2330363484087101 bias=0.24894355108877725 P90=4.26262
- opponent-play ticks: n=248 MAE=1.902144758064516 bias=0.23822701612903227
- our accepted-play ticks: n=406 MAE=1.5510541871921182 bias=-0.21387980295566503
- truth>=9.0 (near cap): n=1989 MAE=0.7764159376571141 bias=-0.669846103569633
- truth<9.0: n=6208 MAE=1.5666778350515465 bias=-0.2900211662371134
- per-match MAE: n_matches=10 median=1.3579917515241267 p90=2.1675007353963833
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=963.0 total_ghost_delivered=894.0 total_over_charge=69.0 share_from_never_played_bases=0.055
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | miner | 4 | 12.0 | 22 | 66.0 | 54.0 |
  | barbarians | 0 | 0.0 | 10 | 50.0 | 50.0 |
  | bandit | 4 | 12.0 | 16 | 48.0 | 36.0 |
  | witch | 6 | 30.0 | 13 | 65.0 | 35.0 |
  | graveyard | 6 | 30.0 | 0 | 0.0 | -30.0 |
  | lightning | 5 | 30.0 | 0 | 0.0 | -30.0 |
  | giant_snowball | 13 | 26.0 | 0 | 0.0 | -26.0 |
  | poison | 6 | 24.0 | 0 | 0.0 | -24.0 |
  | barbarian_barrel | 10 | 20.0 | 0 | 0.0 | -20.0 |
  | lumberjack | 3 | 12.0 | 7 | 28.0 | 16.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition A_wl perfect detection (units only, live's detector_cards whitelist)
- single: n=4620 MAE=1.988428354978355 bias=1.339858658008658 P90=5.085
- double: n=2383 MAE=2.86679068401175 bias=2.4885000419639107 P90=6.1387000000000045
- overtime: n=1194 MAE=1.5591384422110552 bias=1.0830277219430486 P90=4.73524
- opponent-play ticks: n=248 MAE=3.3891995967741932 bias=3.0801342741935485
- our accepted-play ticks: n=406 MAE=2.5936199507389164 bias=2.050599261083744
- truth>=9.0 (near cap): n=1989 MAE=0.4430562091503268 bias=-0.1544426344896933
- truth<9.0: n=6208 MAE=2.7381562016752574 bias=2.210142413015464
- per-match MAE: n_matches=10 median=2.0841146925846497 p90=3.0812706980119673
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=517.0 total_ghost_delivered=894.0 total_over_charge=-377.0 share_from_never_played_bases=0.0967
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | miner | 4 | 12.0 | 22 | 66.0 | 54.0 |
  | barbarians | 0 | 0.0 | 10 | 50.0 | 50.0 |
  | archer_queen | 7 | 35.0 | 0 | 0.0 | -35.0 |
  | witch | 6 | 30.0 | 13 | 65.0 | 35.0 |
  | graveyard | 6 | 30.0 | 0 | 0.0 | -30.0 |
  | lightning | 5 | 30.0 | 0 | 0.0 | -30.0 |
  | giant_snowball | 13 | 26.0 | 0 | 0.0 | -26.0 |
  | poison | 6 | 24.0 | 0 | 0.0 | -24.0 |
  | zappies | 6 | 24.0 | 0 | 0.0 | -24.0 |
  | barbarian_barrel | 10 | 20.0 | 0 | 0.0 | -20.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition B degraded (live)
- single: n=4620 MAE=5.746696277056277 bias=-5.728424675324676 P90=9.080080000000002
- double: n=2383 MAE=5.748228829206882 bias=-5.746409945446916 P90=9.0
- overtime: n=1194 MAE=7.598912814070352 bias=-7.598912814070352 P90=10.0
- opponent-play ticks: n=248 MAE=4.158203629032259 bias=-4.053652016129032
- our accepted-play ticks: n=406 MAE=5.546438669950739 bias=-5.537004187192118
- truth>=9.0 (near cap): n=1989 MAE=8.189766465560583 bias=-8.184182956259427
- truth<9.0: n=6208 MAE=5.320783263530928 bias=-5.308276240335051
- per-match MAE: n_matches=10 median=5.928930129710981 p90=6.840977361709631
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=12071.5 total_ghost_delivered=894.0 total_over_charge=11177.5 share_from_never_played_bases=0.4837
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | knight | 0 | 0.0 | 102 | 306.0 | 306.0 |
  | tesla | 0 | 0.0 | 67 | 268.0 | 268.0 |
  | ice_wizard | 0 | 0.0 | 85 | 255.0 | 255.0 |
  | giant | 7 | 35.0 | 57 | 285.0 | 250.0 |
  | valkyrie | 7 | 28.0 | 69 | 276.0 | 248.0 |
  | mega_knight | 4 | 28.0 | 39 | 273.0 | 245.0 |
  | wizard | 0 | 0.0 | 47 | 235.0 | 235.0 |
  | musketeer | 3 | 12.0 | 61 | 244.0 | 232.0 |
  | x_bow | 0 | 0.0 | 35 | 210.0 | 210.0 |
  | royal_recruits | 0 | 0.0 | 28 | 196.0 | 196.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition B_tt IDEALISED: bill once per TeamTracker-confirmed track (min_hits), no whitelist -- a design under test, NOT live's current path
- single: n=4620 MAE=3.5012576623376623 bias=-3.36814329004329 P90=7.0796600000000005
- double: n=2383 MAE=3.5453027696181283 bias=-3.249137599664289 P90=7.566320000000001
- overtime: n=1194 MAE=3.5379940536013397 bias=-3.2354287269681743 P90=7.405900000000003
- opponent-play ticks: n=248 MAE=2.609952016129032 bias=-0.700829435483871
- our accepted-play ticks: n=406 MAE=3.1939120689655174 bias=-2.832570689655172
- truth>=9.0 (near cap): n=1989 MAE=4.059786375062846 bias=-4.031342332830568
- truth<9.0: n=6208 MAE=3.3462816849226806 bias=-3.0844521423969073
- per-match MAE: n_matches=10 median=3.1896465382843155 p90=4.975439603772732
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=1912.5 total_ghost_delivered=894.0 total_over_charge=1018.5 share_from_never_played_bases=0.3197
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | goblin_drill | 0 | 0.0 | 18 | 72.0 | 72.0 |
  | witch | 6 | 30.0 | 20 | 100.0 | 70.0 |
  | tombstone | 6 | 18.0 | 27 | 81.0 | 63.0 |
  | barbarian_hut | 0 | 0.0 | 10 | 60.0 | 60.0 |
  | barbarians | 0 | 0.0 | 11 | 55.0 | 55.0 |
  | mortar | 4 | 16.0 | 16 | 64.0 | 48.0 |
  | goblin_cage | 0 | 0.0 | 10 | 40.0 | 40.0 |
  | tesla | 0 | 0.0 | 10 | 40.0 | 40.0 |
  | knight | 0 | 0.0 | 11 | 33.0 | 33.0 |
  | valkyrie | 7 | 28.0 | 15 | 60.0 | 32.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition B_tt_wl live-reachable: B_tt's billing, restricted to live's detector_cards whitelist
- single: n=4620 MAE=2.627241645021645 bias=-0.7408705627705628 P90=6.0
- double: n=2383 MAE=2.7988098615190937 bias=0.10734582459085187 P90=6.0
- overtime: n=1194 MAE=2.343609631490787 bias=-1.539030067001675 P90=5.51835
- opponent-play ticks: n=248 MAE=3.3218262096774196 bias=1.7971544354838709
- our accepted-play ticks: n=406 MAE=2.7360179802955664 bias=-0.045624876847290635
- truth>=9.0 (near cap): n=1989 MAE=2.1722305178481647 bias=-2.024555002513826
- truth<9.0: n=6208 MAE=2.784330492912371 bias=-0.1575030444587629
- per-match MAE: n_matches=10 median=2.50650793354042 p90=3.408435233301743
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=992.0 total_ghost_delivered=894.0 total_over_charge=98.0 share_from_never_played_bases=0.3105
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | witch | 6 | 30.0 | 20 | 100.0 | 70.0 |
  | barbarians | 0 | 0.0 | 11 | 55.0 | 55.0 |
  | goblin_cage | 0 | 0.0 | 10 | 40.0 | 40.0 |
  | tesla | 0 | 0.0 | 10 | 40.0 | 40.0 |
  | archer_queen | 7 | 35.0 | 0 | 0.0 | -35.0 |
  | knight | 0 | 0.0 | 11 | 33.0 | 33.0 |
  | valkyrie | 7 | 28.0 | 15 | 60.0 | 32.0 |
  | graveyard | 6 | 30.0 | 0 | 0.0 | -30.0 |
  | lightning | 5 | 30.0 | 0 | 0.0 | -30.0 |
  | giant_snowball | 13 | 26.0 | 0 | 0.0 | -26.0 |
  (top 10 shown here; top 25 in summary.json)
