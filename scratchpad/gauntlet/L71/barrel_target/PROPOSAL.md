# Goblin Barrel target / Log lane correction

Recorded before implementation. The owner authorizes proceeding without waiting for another review.

## Measured evidence

The native audit covers1,010 accepted Barrel plays in161 Icebow replays and7,040 projectile observations.5,977 targets lie within half a tile of the cast. Every one of the1,063 remaining observations is a second reflected target with another simultaneous projectile aimed at the cast point. There are0 unexplained far targets in this audit.14,080 checks confirm both observer orientations and26-tick look-ahead preserve each public target. This does not identify a secret real/decoy flag, nor validate live Barrel offsets from recordings that omitted the flights.

The R1e held-out diagnostic finds249 visible enemy-Barrel rows,95 with one unambiguous own-half target and affordable Log. In39 rows the pro plays Log in the target lane; R1e fires Log in the opposite lane in11/39, despite a correct encoded target and high gate confidence. Swapping only the public target does not change its predicted Log lane in any of95 cases. That perturbation is a feature-sensitivity diagnostic, not a physically valid game state; a second diagnostic reflects the whole flight while holding other threats fixed.

The current model embeds projectile location/target/time into a pooled global feature. Its placement head receives spatial body patches, but no projectile landing feature at the corresponding patch. This is a possible learning bottleneck, not proof that changing architecture improves wins.

## Implementation and acceptance

1. Add a bounded offline cohort containing all expert states with a visible enemy Barrel, including WAITs, other card choices and paired flights. Preserve all expert labels. Compare a5% exposure arm against the same training recipe without it; no rule forces Log or chooses a lane.
2. Prepare a separate generic learned spatial target adapter: project each public projectile's card/side/position/target/timing features into its target patch, use a learned3x3 depthwise spatial convolution to support offsets around the landing point, then condition placement on the existing learned card query. It applies to every recognised projectile, including own Rocket flight, and has no Log-specific or Barrel-specific runtime branch or fixed placement offset. Unknown targets contribute nothing. The residual starts exactly at zero, preserving the original checkpoint outputs before training. Learn it from expert cell labels, with a separate architecture ablation so a sampling change is not mistaken for an architecture effect.
3. Preserve legacy checkpoint loading and opt-in versioning. Verify initial-output parity, trainable gradients, both lanes/sides, unknown/padded targets, multiple simultaneous flights and end-to-end SIM/live input parity. Train only on training replays; use fixed final-step selection and held-out diagnostics plus fresh same-code gameplay acceptance.
4. Record public raw target, normalized/projected target and actual chosen Log location in live audit logs. Do not infer intended target from which lane the model chose. Keep paired flights explicit. Confirm source-to-token-to-tap correspondence at the authorized deployment.

The small39-row pro-response subset is a diagnostic gate, not a win-rate estimate. Adoption requires broader checks and no gameplay regression. No hardcoded pre-emptive Log, hidden opponent information or secret decoy identity is introduced.
