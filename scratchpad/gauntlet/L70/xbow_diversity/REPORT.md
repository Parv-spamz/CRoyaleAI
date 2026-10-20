# X-Bow placement diversity -- diagnosis (L70, 2026-10-04)

Script `xbow_diversity.py`, numbers `results.json`. CPU only, no training. Pro rows: gen_dataset_v3, all 11,401 pro X-Bow plays (2,792 replays) for pro stats and H3; **model tests on the val split only** (1,379 plays / 345 replays). Models `gen_v3_s0/gen_s0.pt` and live `rseries_r1/rseries_r1_u0155.pt` (feature_version 1), teacher-forced on the X-Bow card+form exactly as `live_decide` (raw cell logits, no masking). All CIs are replay-clustered bootstrap.

## 0. The premise needs correcting (measured)
Pros use 12 y-rows over ALL X-Bow plays, but most are not tower lock-on placements. Offensive rule used: own half, and an ALIVE enemy tower within 11.5 (X-Bow range) + tower radius (+1.0 tile slack for tap-to-building/lattice rounding). **Strict engine geometry (slack 0, lead ruling R1) admits only 233/11,401 = 2.0% of pro X-Bows** (25 in val), so the pros' own modal cells (row y=.609, 13.0 tiles from the princess centre) fail it by about 0.5 tile; with slack 1.0 it is 8,426 = 74% (1,046 val). The slack is post hoc; R1 as written would label ~98% of pro X-Bows defensive, so the tap-to-building offset needs checking before R1 is used (not done here, outside scope). Under the lax rule pros use **2 offensive rows (cy 37, 39: 9% / 91%), 24 distinct cells** (18 in val), 15 cells carry 99.3% of the train plays. Lock-capable cells per state: ~67 on the pro lattice over 8 rows (cy 33-40), pros pick the far edge of that zone only. The bot's rows (.609 and .703) are 39 and 45; row 45 is not lock-capable.

## H1 vs H2 (val, offensive rows n=1,046; gen_v3_s0 / live u0155)
| metric | gen_v3 | live |
|---|---|---|
| entropy nats (effective cells exp H) | 2.26 (10.6 [10.3,11.0]) | 2.00 (8.5 [8.2,8.9]) |
| top-1 prob; cells with >5% mass | .42; 3.4 | .47; 3.4 |
| mass on pro cell / within 1 tile | .29 / .38 | .32 / .41 |
| mass on the 15 pro cells / lock-capable cells | .78 / .80 | .80 / .81 |
| argmax = pro cell | .49 [.46,.52] | .51 [.48,.54] |
| distinct argmax cells / rows (pros: 18 / 2) | 11 / 3 | 9 / 3 |
| pro top-2 cells (the two lane modes): pro share .742, model mean mass, argmax share | .571, .934 | .613, .945 |

**H1 holds, H2 does not.** The model is spread (about 9-11 effective cells, top-1 under half), not a spike. Argmax converts 57-61% of mass on the two modal cells into 93-94% of choices, versus 74% in the pros. Row-wise argmax is 96% row 39 vs 91% for pros, so most of the gap is lane/column spread, not rows. The model is context-aware: argmax lane = pro lane 67-69% (weaker-tower rule 64.7%), argmax=pro .49-.51 vs .37 for the best context-free cell. Top-1 confidence is roughly calibrated (bins .24 -> .30-.35, .52 -> .51-.63, .67-.70 -> .74).

Sampling (live; gen_v3 similar), one draw per row, 200 repeats: argmax 9 cells / agree .51 / lock-capable .97; **top-p .9: 31 cells / 6 rows, agree .35, lock-capable .85**; T=.7: 31 / 6.9, .41, .89; T=1: 61 / 12, .32, .81. Sampling adds diversity, but 11-19% of X-Bows land outside lock-capable cells and exact agreement drops 10-19 pp; the extra rows (43, 45, 47...) are non-lock rows (hedge mass for pocket plays), not new lock-on spots.

## H3: pro placement vs public context (offensive rows, replay-clustered CIs)
Contextual in the lane, weakly elsewhere. Lane: pros play the weaker enemy princess' lane 65.3% [63.8,66.8] (n=5,530, null 50%); per SD OR 1.67 [1.55,1.79] for tower-HP gap, 1.33 [1.23,1.42] for enemy-troop pressure; grouped-CV AUC .67 (pseudo-R2 4.9%). Row (non-modal 9%): AUC .63 / R2 2.7%, OR/SD elixir .83 [.77,.89], match progress 1.17 [1.06,1.28], enemy troops in lane 1.27 [1.18,1.36]. Central pocket vs lane: AUC .61. **Enemy defensive buildings (Tesla/Cannon/Inferno/Bomb) barely matter**: present in only 7.8% of rows; in-lane count OR 1.00 [.94,1.07]; pros place no farther from them than the mirrored cell would (+0.18 tiles [-0.11,+0.49]); lane with fewer buildings 56.5% [50,63], n=230. Dead-lane: 44.9% [38,52] (n=272). So within a lane most of the spread is NOT explained by public features (R2 under 5%).

## Recommendation (no X-Bow rule)
1. Do not blanket-switch to top-p/temperature sampling for X-Bow on this evidence: it buys diversity that is mostly off-target (see lock-capable column). If diversity is wanted, test a sampler for all cards (top-p .9 or T .7 on the cell head) as a RoyaleSim A/B on win rate and tower damage before live; untested here.
2. The real lever is data: the model hedges 16% of mass onto non-lock rows 43/45 because offensive and defensive/pocket X-Bows share one label. gen_v3.1's offensive/defensive separation (already planned) should concentrate mass and let a lower temperature be safe. Measure again on that checkpoint with this script.
3. Before any claim that "pros use 12 offensive rows", fix the offensive geometry (R1 strict vs slack) and re-count.

## Caveats
Val only 345 replays; clean teacher-forced states (no latency shift/extrapolation); lax slack chosen after seeing the modal cells; H3 is descriptive, features are only tower HP, building/troop counts, phase and elixir; sampling stats use one 200-draw seed; live checkpoint is feature_version 1 (opp_past unused).
