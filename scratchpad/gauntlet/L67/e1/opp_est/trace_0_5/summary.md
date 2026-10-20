# opp_est_audit summary

n_ticks=2955 n_matches=5 port=38031 split=heldout entries=0:5 decide_every=10 estimator_step=5

| condition | MAE | bias | P90\|err\| | share<=1.0 | share<=2.0 |
|---|---|---|---|---|---|
| A+ perfect detection (+spells, no whitelist) | 3.3574207445008457 | -3.130033468697124 | 6.8192 | 0.1692047377326565 | 0.35736040609137054 |
| A perfect detection (units only, NO whitelist -- loose upper bound) | 3.3574207445008457 | -3.130033468697124 | 6.8192 | 0.1692047377326565 | 0.35736040609137054 |
| A_wl perfect detection (units only, live's detector_cards whitelist) | 2.0223558037225042 | -0.1231960744500846 | 5.1104 | 0.438917089678511 | 0.5932318104906937 |
| B degraded (live) | 6.212413401015229 | -6.212047851099831 | 9.5596 | 0.05245346869712352 | 0.0751269035532995 |

## Condition A+ perfect detection (+spells, no whitelist)
- single: n=2162 MAE=3.199187881591119 bias=-3.002735892691952 P90=6.434
- double: n=742 MAE=3.8297664420485176 bias=-3.4966125336927223 P90=7.749300000000001
- overtime: n=51 MAE=3.193086274509804 bias=-3.193086274509804 P90=6.9278
- opponent-play ticks: n=74 MAE=2.547833783783784 bias=-1.7261986486486485
- our accepted-play ticks: n=134 MAE=3.3898828358208957 bias=-3.065264925373134
- truth>=9.0 (near cap): n=650 MAE=3.8223516923076923 bias=-3.7772018461538464
- truth<9.0: n=2305 MAE=3.226312234273319 bias=-2.947534793926247
- per-match MAE: n_matches=5 median=3.3648243393602226 p90=4.3594256959861095
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=684.0 total_ghost_delivered=289.0 total_over_charge=395.0 share_from_never_played_bases=0.0292
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | witch | 4 | 20.0 | 30 | 150.0 | 130.0 |
  | tombstone | 3 | 9.0 | 34 | 102.0 | 93.0 |
  | bandit | 4 | 12.0 | 15 | 45.0 | 33.0 |
  | night_witch | 1 | 4.0 | 9 | 36.0 | 32.0 |
  | skeleton_army | 1 | 3.0 | 11 | 33.0 | 30.0 |
  | zappies | 4 | 16.0 | 11 | 44.0 | 28.0 |
  | minion_horde | 1 | 5.0 | 6 | 30.0 | 25.0 |
  | skeletons | 0 | 0.0 | 16 | 16.0 | 16.0 |
  | wall_breakers | 4 | 8.0 | 11 | 22.0 | 14.0 |
  | giant_snowball | 5 | 10.0 | 0 | 0.0 | -10.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition A perfect detection (units only, NO whitelist -- loose upper bound)
- single: n=2162 MAE=3.199187881591119 bias=-3.002735892691952 P90=6.434
- double: n=742 MAE=3.8297664420485176 bias=-3.4966125336927223 P90=7.749300000000001
- overtime: n=51 MAE=3.193086274509804 bias=-3.193086274509804 P90=6.9278
- opponent-play ticks: n=74 MAE=2.547833783783784 bias=-1.7261986486486485
- our accepted-play ticks: n=134 MAE=3.3898828358208957 bias=-3.065264925373134
- truth>=9.0 (near cap): n=650 MAE=3.8223516923076923 bias=-3.7772018461538464
- truth<9.0: n=2305 MAE=3.226312234273319 bias=-2.947534793926247
- per-match MAE: n_matches=5 median=3.3648243393602226 p90=4.3594256959861095
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=684.0 total_ghost_delivered=289.0 total_over_charge=395.0 share_from_never_played_bases=0.0292
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | witch | 4 | 20.0 | 30 | 150.0 | 130.0 |
  | tombstone | 3 | 9.0 | 34 | 102.0 | 93.0 |
  | bandit | 4 | 12.0 | 15 | 45.0 | 33.0 |
  | night_witch | 1 | 4.0 | 9 | 36.0 | 32.0 |
  | skeleton_army | 1 | 3.0 | 11 | 33.0 | 30.0 |
  | zappies | 4 | 16.0 | 11 | 44.0 | 28.0 |
  | minion_horde | 1 | 5.0 | 6 | 30.0 | 25.0 |
  | skeletons | 0 | 0.0 | 16 | 16.0 | 16.0 |
  | wall_breakers | 4 | 8.0 | 11 | 22.0 | 14.0 |
  | giant_snowball | 5 | 10.0 | 0 | 0.0 | -10.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition A_wl perfect detection (units only, live's detector_cards whitelist)
- single: n=2162 MAE=1.8919582793709528 bias=-0.4114981498612396 P90=5.1104
- double: n=742 MAE=2.312553638814016 bias=0.6960067385444744 P90=5.0369
- overtime: n=51 MAE=3.328094117647059 bias=0.1799529411764706 P90=6.7493
- opponent-play ticks: n=74 MAE=2.624113513513514 bias=1.5732945945945946
- our accepted-play ticks: n=134 MAE=2.0754992537313433 bias=0.0417574626865672
- truth>=9.0 (near cap): n=650 MAE=1.522975076923077 bias=-1.3058526153846155
- truth<9.0: n=2305 MAE=2.1631790021691972 bias=0.2103079392624729
- per-match MAE: n_matches=5 median=2.0226585987261143 p90=2.5545582475660638
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=341.0 total_ghost_delivered=289.0 total_over_charge=52.0 share_from_never_played_bases=0.0469
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | witch | 4 | 20.0 | 30 | 150.0 | 130.0 |
  | skeletons | 0 | 0.0 | 16 | 16.0 | 16.0 |
  | zappies | 4 | 16.0 | 0 | 0.0 | -16.0 |
  | archer_queen | 3 | 15.0 | 0 | 0.0 | -15.0 |
  | bandit | 4 | 12.0 | 0 | 0.0 | -12.0 |
  | giant_snowball | 5 | 10.0 | 0 | 0.0 | -10.0 |
  | graveyard | 2 | 10.0 | 0 | 0.0 | -10.0 |
  | guards | 3 | 9.0 | 6 | 18.0 | 9.0 |
  | minions | 4 | 12.0 | 7 | 21.0 | 9.0 |
  | tombstone | 3 | 9.0 | 0 | 0.0 | -9.0 |
  (top 10 shown here; top 25 in summary.json)

## Condition B degraded (live)
- single: n=2162 MAE=6.214486123959296 bias=-6.214145698427382 P90=9.542040000000002
- double: n=742 MAE=6.155139757412399 bias=-6.154675876010782 P90=9.53898
- overtime: n=51 MAE=6.957821568627451 bias=-6.957821568627451 P90=10.0
- opponent-play ticks: n=74 MAE=4.063448648648649 bias=-4.063448648648649
- our accepted-play ticks: n=134 MAE=6.0075223880597015 bias=-6.0075223880597015
- truth>=9.0 (near cap): n=650 MAE=8.453002615384614 bias=-8.453002615384614
- truth<9.0: n=2305 MAE=5.580576963123645 bias=-5.580108329718004
- per-match MAE: n_matches=5 median=5.943160500695411 p90=7.22630629767104
- OVER-CHARGE vs DELIVERED (FIX 1, not scripted): total_charged=5974.0 total_ghost_delivered=289.0 total_over_charge=5685.0 share_from_never_played_bases=0.6045
  | base | ghost_plays(delivered) | ghost_elixir | charges | charged_elixir | over_charge |
  |---|---|---|---|---|---|
  | ice_wizard | 0 | 0.0 | 78 | 234.0 | 234.0 |
  | knight | 0 | 0.0 | 78 | 234.0 | 234.0 |
  | witch | 4 | 20.0 | 45 | 225.0 | 205.0 |
  | mega_knight | 3 | 21.0 | 27 | 189.0 | 168.0 |
  | zappies | 4 | 16.0 | 41 | 164.0 | 148.0 |
  | giant | 5 | 25.0 | 31 | 155.0 | 130.0 |
  | tombstone | 3 | 9.0 | 46 | 138.0 | 129.0 |
  | bowler | 4 | 20.0 | 29 | 145.0 | 125.0 |
  | mini_pekka | 2 | 8.0 | 31 | 124.0 | 116.0 |
  | tesla | 0 | 0.0 | 29 | 116.0 | 116.0 |
  (top 10 shown here; top 25 in summary.json)
