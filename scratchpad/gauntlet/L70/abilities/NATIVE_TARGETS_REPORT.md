# Native ability share and delay targets

Measured on the 14,661 source-verified ability-driven native replays. Final artifact: `native_targets_2326/report.json` and `deployments.jsonl`; the first `native_targets_2305` result is superseded. The repair re-read 2,457 affected replays and preserved all other deployment rows exactly.

There are 137,456 accepted deployments across 24 abilities. Stable-ID/public-controller checks linked 129,567; 37,990 linked deployments have an accepted press. Every ability has its own denominator, first-delay distribution and 1,000-replay-cluster-bootstrap confidence interval in the JSON report. A deployment share is not a ready-button hazard or a predicted play rate.

Examples from the final measured subset:

| Ability | Linked / accepted deployments | Pressed / linked | First-delay median |
|---|---:|---:|---:|
| Archer Queen | 2,177 / 2,177 | 1,760 / 2,177 | 9.80 s |
| Boss Bandit | 562 / 562 | 354 / 562 | 9.65 s |
| Goblinstein | 6,024 / 6,027 | 2,022 / 6,024 | 8.00 s [7.725, 8.30] |
| Hero Goblins | 388 / 2,842 | 82 / 388 | 5.375 s [5.15, 6.00] |
| Hero Tombstone | 36 / 2,641 | 0 / 36 | unavailable |

Goblinstein's share is 33.57% [32.20, 35.12] in the linked subset. Hero Goblins and hero Tombstone have severe selection/coverage limitations: their numbers must not be used as population calibration targets. Missing/ambiguous controllers and accepted presses without a unique deployment are counted and censored. The zero among 36 Tombstone links is not evidence that pros never press that ability.

The old bridge's native card IDs alias some composite units. The repair uses the existing public max-HP contracts for the Goblinstein doctor, Goblins controller and Tombstone controller. Tombstone still produces multiple plausible entities; Goblins has delayed/missing controllers under the declared five-second linkage window. These require event-to-deployment validation before all 24 timing models can be calibrated reliably.

Four tests cover exact stable-ID linkage, opponent-private-field invariance, overlapping commands, unmatched presses and composite sibling rejection. The script is offline, below-normal priority, and paces source reads. No intercept/timing fit, held-out per-ability model-error report, simulator replacement or R1e launch is claimed. Native accepted timing differs from original human timing when the driver delays or rejects input.
