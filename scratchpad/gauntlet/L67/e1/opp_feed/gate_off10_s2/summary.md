# opp_est_audit summary

n_ticks=7555 n_matches=10 port=38031 split=heldout entries=100:110 decide_every=10 estimator_step=5

| condition | MAE | bias | P90\|err\| | share<=1.0 | share<=2.0 |
|---|---|---|---|---|---|
| A+ perfect detection (+spells, no whitelist) | 1.268298716082065 | 0.3086944540039709 | 3.9320400000000015 | 0.6308405029781602 | 0.7585704831237591 |
| A perfect detection (units only, NO whitelist -- loose upper bound) | 1.268298716082065 | 0.3086944540039709 | 3.9320400000000015 | 0.6308405029781602 | 0.7585704831237591 |
| A_wl perfect detection (units only, live's detector_cards whitelist) | 2.4322688418266045 | 2.1962588087359367 | 6.05196 | 0.3957643944407677 | 0.5155526141628061 |
| B degraded (live) | 5.563200132362674 | -5.562052574454004 | 8.95376 | 0.05029781601588352 | 0.10046326935804104 |
| B_tt IDEALISED: bill once per TeamTracker-confirmed track (min_hits), no whitelist -- a design under test, NOT live's current path | 3.2383452812706817 | -2.8521915552614163 | 6.5079600000000015 | 0.23070814030443415 | 0.3662475181998676 |
| B_tt_wl live-reachable: B_tt's billing, restricted to live's detector_cards whitelist | 2.645858954334878 | 0.34178594308405025 | 5.840160000000002 | 0.32653871608206486 | 0.47902051621442754 |

## Condition A+ perfect detection (+spells, no whitelist)
- single: n=4584 MAE=0.9296534031413614 bias=0.37472905759162306 P90=3.0652
- double: n=2145 MAE=1.8485179953379953 bias=0.0001814918414918497 P90=4.1428
- overtime: n=826 MAE=1.6409134382566588 bias=0.7433889830508474 P90=4.541099999999999
- opponent-play ticks: n=246 MAE=1.8813943089430896 bias=1.134218699186992
- our accepted-play ticks: n=382 MAE=1.3791921465968586 bias=0.2918450261780105
- truth>=9.0 (near cap): n=1291 MAE=0.4712428350116189 bias=-0.3122068938807126
- truth<9.0: n=6264 MAE=1.432570609833972 bias=0.4366611909323116
- per-match MAE: n_matches=10 median=0.9934807375329608 p90=1.9514208820936745
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=922.5 total_ghost_delivered=883.0 total_over_charge=39.5 share_from_never_played_bases=0.0136
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | lightning | 7 | 42.0 | 0 | 0.0 | -42.0 |
  | miner | 3 | 9.0 | 17 | 51.0 | 42.0 |
  | boss_bandit | 4 | 24.0 | 10 | 60.0 | 36.0 |
  | barbarians | 3 | 15.0 | 9 | 45.0 | 30.0 |
  | fireball | 6 | 24.0 | 0 | 0.0 | -24.0 |
  | hog_rider | 5 | 20.0 | 11 | 44.0 | 24.0 |
  | bandit | 4 | 12.0 | 10 | 30.0 | 18.0 |
  | zap | 9 | 18.0 | 0 | 0.0 | -18.0 |
  | goblin_barrel | 5 | 15.0 | 0 | 0.0 | -15.0 |
  | tornado | 5 | 15.0 | 0 | 0.0 | -15.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition A perfect detection (units only, NO whitelist -- loose upper bound)
- single: n=4584 MAE=0.9296534031413614 bias=0.37472905759162306 P90=3.0652
- double: n=2145 MAE=1.8485179953379953 bias=0.0001814918414918497 P90=4.1428
- overtime: n=826 MAE=1.6409134382566588 bias=0.7433889830508474 P90=4.541099999999999
- opponent-play ticks: n=246 MAE=1.8813943089430896 bias=1.134218699186992
- our accepted-play ticks: n=382 MAE=1.3791921465968586 bias=0.2918450261780105
- truth>=9.0 (near cap): n=1291 MAE=0.4712428350116189 bias=-0.3122068938807126
- truth<9.0: n=6264 MAE=1.432570609833972 bias=0.4366611909323116
- per-match MAE: n_matches=10 median=0.9934807375329608 p90=1.9514208820936745
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=922.5 total_ghost_delivered=883.0 total_over_charge=39.5 share_from_never_played_bases=0.0136
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | lightning | 7 | 42.0 | 0 | 0.0 | -42.0 |
  | miner | 3 | 9.0 | 17 | 51.0 | 42.0 |
  | boss_bandit | 4 | 24.0 | 10 | 60.0 | 36.0 |
  | barbarians | 3 | 15.0 | 9 | 45.0 | 30.0 |
  | fireball | 6 | 24.0 | 0 | 0.0 | -24.0 |
  | hog_rider | 5 | 20.0 | 11 | 44.0 | 24.0 |
  | bandit | 4 | 12.0 | 10 | 30.0 | 18.0 |
  | zap | 9 | 18.0 | 0 | 0.0 | -18.0 |
  | goblin_barrel | 5 | 15.0 | 0 | 0.0 | -15.0 |
  | tornado | 5 | 15.0 | 0 | 0.0 | -15.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition A_wl perfect detection (units only, live's detector_cards whitelist)
- single: n=4584 MAE=2.307830017452007 bias=2.178873909249564 P90=6.0534
- double: n=2145 MAE=2.496694731934732 bias=2.0583691375291373 P90=5.770400000000001
- overtime: n=826 MAE=2.9555546004842617 bias=2.6508177966101694 P90=6.3337
- opponent-play ticks: n=246 MAE=3.6209414634146344 bias=3.484641463414634
- our accepted-play ticks: n=382 MAE=2.55339109947644 bias=2.2603031413612564
- truth>=9.0 (near cap): n=1291 MAE=0.2542872192099148 bias=0.12117319907048799
- truth<9.0: n=6264 MAE=2.8811472381864625 bias=2.6239305076628354
- per-match MAE: n_matches=10 median=2.4644906859202718 p90=3.1106576563296993
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=510.0 total_ghost_delivered=883.0 total_over_charge=-373.0 share_from_never_played_bases=0.0235
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | dark_prince | 12 | 48.0 | 0 | 0.0 | -48.0 |
  | lightning | 7 | 42.0 | 0 | 0.0 | -42.0 |
  | miner | 3 | 9.0 | 17 | 51.0 | 42.0 |
  | executioner | 7 | 35.0 | 0 | 0.0 | -35.0 |
  | barbarians | 3 | 15.0 | 9 | 45.0 | 30.0 |
  | electro_giant | 4 | 28.0 | 0 | 0.0 | -28.0 |
  | archer_queen | 5 | 25.0 | 0 | 0.0 | -25.0 |
  | boss_bandit | 4 | 24.0 | 0 | 0.0 | -24.0 |
  | fireball | 6 | 24.0 | 0 | 0.0 | -24.0 |
  | golden_knight | 6 | 24.0 | 0 | 0.0 | -24.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition B degraded (live)
- single: n=4584 MAE=5.730582504363002 bias=-5.728710078534031 P90=9.0
- double: n=2145 MAE=5.235265407925408 bias=-5.235225034965035 P90=8.42698
- overtime: n=826 MAE=5.4858868038740916 bias=-5.4858868038740916 P90=9.0
- opponent-play ticks: n=246 MAE=3.8197939024390246 bias=-3.790291463414634
- our accepted-play ticks: n=382 MAE=5.227247905759162 bias=-5.227247905759162
- truth>=9.0 (near cap): n=1291 MAE=8.219505344694035 bias=-8.219505344694035
- truth<9.0: n=6264 MAE=5.015740038314176 bias=-5.0143559706257985
- per-match MAE: n_matches=10 median=5.612656063452458 p90=6.193888067512749
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=9878.0 total_ghost_delivered=883.0 total_over_charge=8995.0 share_from_never_played_bases=0.4279
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | knight | 12 | 36.0 | 116 | 348.0 | 312.0 |
  | ice_wizard | 0 | 0.0 | 76 | 228.0 | 228.0 |
  | dark_prince | 12 | 48.0 | 65 | 260.0 | 212.0 |
  | mega_knight | 2 | 14.0 | 31 | 217.0 | 203.0 |
  | musketeer | 0 | 0.0 | 50 | 200.0 | 200.0 |
  | valkyrie | 0 | 0.0 | 48 | 192.0 | 192.0 |
  | bowler | 6 | 30.0 | 42 | 210.0 | 180.0 |
  | elite_barbarians | 3 | 18.0 | 32 | 192.0 | 174.0 |
  | pekka | 2 | 14.0 | 26 | 182.0 | 168.0 |
  | balloon | 2 | 10.0 | 35 | 175.0 | 165.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition B_tt IDEALISED: bill once per TeamTracker-confirmed track (min_hits), no whitelist -- a design under test, NOT live's current path
- single: n=4584 MAE=3.273849432809773 bias=-3.0753505671902266 P90=6.6661199999999985
- double: n=2145 MAE=3.2449204195804198 bias=-2.4156446153846156 P90=6.019060000000004
- overtime: n=826 MAE=3.024235472154964 bias=-2.747388014527845 P90=6.4535
- opponent-play ticks: n=246 MAE=2.3898686991869917 bias=-0.14801504065040652
- our accepted-play ticks: n=382 MAE=2.877791884816754 bias=-2.3293421465968587
- truth>=9.0 (near cap): n=1291 MAE=3.7173096824167313 bias=-3.671093261037955
- truth<9.0: n=6264 MAE=3.1396315134099617 bias=-2.6834172733077906
- per-match MAE: n_matches=10 median=3.14754655277683 p90=3.9418401302155766
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=1478.5 total_ghost_delivered=883.0 total_over_charge=595.5 share_from_never_played_bases=0.2012
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | barbarians | 3 | 15.0 | 13 | 65.0 | 50.0 |
  | lightning | 7 | 42.0 | 0 | 0.0 | -42.0 |
  | knight | 12 | 36.0 | 24 | 72.0 | 36.0 |
  | giant | 3 | 15.0 | 10 | 50.0 | 35.0 |
  | barbarian_hut | 0 | 0.0 | 5 | 30.0 | 30.0 |
  | magic_archer | 4 | 16.0 | 11 | 44.0 | 28.0 |
  | tombstone | 0 | 0.0 | 9 | 27.0 | 27.0 |
  | baby_dragon | 6 | 24.0 | 12 | 48.0 | 24.0 |
  | boss_bandit | 4 | 24.0 | 8 | 48.0 | 24.0 |
  | fireball | 6 | 24.0 | 0 | 0.0 | -24.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition B_tt_wl live-reachable: B_tt's billing, restricted to live's detector_cards whitelist
- single: n=4584 MAE=2.5767725567190225 bias=0.5206354712041884 P90=5.812659999999999
- double: n=2145 MAE=2.706194731934732 bias=-0.09419939393939393 P90=5.783800000000001
- overtime: n=826 MAE=2.8725802663438254 bias=0.4814255447941889 P90=6.0
- opponent-play ticks: n=246 MAE=3.663845121951219 bias=2.8845052845528456
- our accepted-play ticks: n=382 MAE=2.6610630890052356 bias=0.6811290575916231
- truth>=9.0 (near cap): n=1291 MAE=1.829285050348567 bias=-1.611449573973664
- truth<9.0: n=6264 MAE=2.814153480204342 bias=0.744344540229885
- per-match MAE: n_matches=10 median=2.497712753642553 p90=3.363545985609041
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=822.0 total_ghost_delivered=883.0 total_over_charge=-61.0 share_from_never_played_bases=0.135
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | barbarians | 3 | 15.0 | 13 | 65.0 | 50.0 |
  | dark_prince | 12 | 48.0 | 0 | 0.0 | -48.0 |
  | lightning | 7 | 42.0 | 0 | 0.0 | -42.0 |
  | knight | 12 | 36.0 | 24 | 72.0 | 36.0 |
  | executioner | 7 | 35.0 | 0 | 0.0 | -35.0 |
  | giant | 3 | 15.0 | 10 | 50.0 | 35.0 |
  | electro_giant | 4 | 28.0 | 0 | 0.0 | -28.0 |
  | magic_archer | 4 | 16.0 | 11 | 44.0 | 28.0 |
  | archer_queen | 5 | 25.0 | 0 | 0.0 | -25.0 |
  | baby_dragon | 6 | 24.0 | 12 | 48.0 | 24.0 |
  (top 10 shown here; top 25 in summary.json)
