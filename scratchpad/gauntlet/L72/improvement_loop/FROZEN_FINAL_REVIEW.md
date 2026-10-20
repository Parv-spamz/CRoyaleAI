# Frozen L71 final verdict, October 5

All34 original jobs are complete; all eight candidates are REJECTED. N1 can close; the new-model objective remains open. No checkpoint was deployed. Every fixed run completed1000 finite IL updates/128000 draws. Existing independent caches remain hash-identical:344853 predictions across nine reports.

| Candidate | Ghost /299 | Reactive /48 | Ghost delta vs R1e, 95% CI (pp) | Ghost Rockets / tower |
|---|---:|---:|---|---|
| R1e | 285 | 32 | comparator | 42 / 5 |
| v4_uniform | 283 | 27 | -0.67 [-3.34, +2.01] | 87 / 16 |
| v4_rocket | 274 | 25 | -3.68 [-7.02, -0.33] | 226 / 41 |
| v5_uniform | 277 | 28 | -2.68 [-5.69, +0.00] | 73 / 9 |
| v5_rocket | 281 | 27 | -1.34 [-4.35, +1.67] | 213 / 33 |
| v5_rocket_xbow | 283 | 29 | -0.67 [-3.68, +2.34] | 182 / 18 |
| v5_rocket_barrel | 283 | 22 | -0.67 [-4.01, +3.01] | 242 / 34 |
| v6_rocket_barrel | 281 | 21 | -1.34 [-4.68, +2.01] | 223 / 38 |
| v6_rocket_both | 270 | 31 | -5.02 [-8.70, -1.34] | 169 / 20 |

| Candidate | Rocket /671 | Finish /10 | Combo Rocket,Tornado /69 each | Barrel correct,wrong /39 | Witch /519 | Night Witch /390 | Furnace /534 | X-Bow /157 | Global card /11934 |
|---|---:|---:|---|---|---:|---:|---:|---:|---:|
| r1e | 81 | 0 | 5,16 | 23,11 | 255 | 179 | 273 | 99 | 7708 |
| v4_uniform | 151 | 0 | 17,21 | 26,12 | 261 | 179 | 285 | 99 | 7738 |
| v4_rocket | 342 | 0 | 41,21 | 28,10 | 259 | 181 | 278 | 99 | 7621 |
| v5_uniform | 147 | 0 | 16,21 | 25,13 | 251 | 171 | 281 | 99 | 7727 |
| v5_rocket | 345 | 0 | 41,21 | 28,10 | 253 | 174 | 278 | 99 | 7623 |
| v5_rocket_xbow | 318 | 0 | 39,19 | 28,9 | 250 | 172 | 282 | 99 | 7635 |
| v5_rocket_barrel | 328 | 0 | 42,22 | 29,8 | 257 | 173 | 279 | 99 | 7600 |
| v6_rocket_barrel | 327 | 0 | 42,22 | 36,1 | 256 | 172 | 276 | 99 | 7585 |
| v6_rocket_both | 321 | 0 | 41,22 | 37,1 | 247 | 172 | 274 | 100 | 7617 |

The component table is historical held-out imitation, including WAIT or gated correct card/aim for action contexts. It is not a live success rate. All models have zero actual Rocket finish-offs in both gameplay screens as well. Rocket-then-Tornado counts and both orders, cycles, defensive Rockets and unknown impacts remain separately available in frozen_reconciled.json.

Additional literal primary-control Rocket-behavior review rejects v5_rocket_xbow and v6_rocket_both on both share/tower conditions, and v6_rocket_barrel on share. The original scorer compares these to ordinary IL; both comparisons are retained. Full failure lists and action-control deltas are in frozen_supplement.json.

Attribution: corrected-body ordinary IL lowers Witch/Night Witch/Furnace agreement versus original-body ordinary IL; corrected Rocket IL also fails to isolate a family improvement. The generic projectile-target residual improves Barrel correct/wrong responses29/8 to36/1 on39 cases, but its combined policy loses ghost/reactive games and general card agreement. Extra X-Bow exposure changes context accuracy99/157 to100/157 only in the v6 pair while lowering ghost wins281->270; neither X-Bow arm establishes useful resource/tower outcomes. More Rocket frequency is not an accepted defense/cycling improvement.

These are matched frozen OLD-runtime tests. They do not establish acceptance on the updated simulator, untouched confirmation or actual live Barrel landings. The original X-Bow fork had no demonstrated resource/tower benefit. Q3 sampling/area options remain rejected. No threshold changed. Continue L72 with training-only diagnosis, new replay evidence, preregistered controls and bounded learned improvements.

Evidence: frozen_reconciled.json, frozen_supplement.json, existing heldout_metrics_verified.json/all_predictions_verified.json, and l72-frozen-final-reconciliation/l72-frozen-component-supplement receipts.
