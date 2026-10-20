# Held-out review, October 5 03:28 EDT

All eight fixed 1,000-update IL runs and their held-out evaluations completed
by03:12:51. An independent CPU recount checked all nine prediction caches,
38,317 validation rows each (344,853 predictions total), including legality,
exact row membership and every diagnostic numerator. Every report matched.
`all_predictions_verified.json` binds report/cache hashes;
`heldout_metrics_verified.json` preserves the verified diagnostic values.

The unchanged scorer's partial reconciliation verifies all completed recipes,
finite updates and source/input/output hashes. `heldout_partial_0327.json`
has17 gameplay jobs pending and no nomination. Frozen gameplay continues;
these are learning diagnostics, not win results.

| Arm | Correct card /11934 | Gated Rocket /671 | Aimed finish /10 | Combo Rocket,Tornado /69 | Barrel correct,wrong /39 |
|---|---:|---:|---:|---:|---:|
| Untrained R1e | 7708 | 81 | 0 | 5,16 | 23,11 |
| v4_uniform | 7738 | 151 | 0 | 17,21 | 26,12 |
| v4_rocket | 7621 | 342 | 0 | 41,21 | 28,10 |
| v5_uniform | 7727 | 147 | 0 | 16,21 | 25,13 |
| v5_rocket | 7623 | 345 | 0 | 41,21 | 28,10 |
| v5_rocket_xbow | 7635 | 318 | 0 | 39,19 | 28,9 |
| v5_rocket_barrel | 7600 | 328 | 0 | 42,22 | 29,8 |
| v6_rocket_barrel | 7585 | 327 | 0 | 42,22 | 36,1 |
| v6_rocket_both | 7617 | 321 | 0 | 41,22 | 37,1 |

Every proposed fix arm fails at least one mandatory learning gate. All Rocket
arms fail the finishing requirement; all version5/6 arms fail required spawner
action improvement, and all except v5_rocket also fail the Night Witch bound.
v6_rocket_barrel additionally fails global agreement versus source. The X-Bow
only exposure arm fails its context-improvement gate. See the partial report
for every failed predicate, including Tornado recall comparisons.

The large Barrel gains and increased Rocket recall are measured improvements,
but do not make these combined candidates deployable. v4_uniform is the
ordinary-training control and supplies no accepted requested fix. Preserve
R1e as fallback; no candidate currently qualifies, regardless of future game
wins. Do not tune on these held-out failures, relax thresholds, or stop the
authorized frozen chain. Retain full gameplay outcomes and final reconciliation.

This does not establish a resource/tower benefit for the dead-lane X-Bow change,
reliable Rocket finish-offs, or actual live Barrel landing correctness. No
Rocket-area comparison is required unless a learned candidate first passes its
declared gates. Updated-engine runtime acceptance remains separately incomplete
because Windows blocked16 Rust test executables before launch.
