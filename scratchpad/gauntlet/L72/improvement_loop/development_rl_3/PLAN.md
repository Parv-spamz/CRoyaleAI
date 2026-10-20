# Matched-budget full-history late-decision curriculum

Registered October6 2026 before preparation or optimization. The owner overnight
extension allows new jobs through13Z. This development experiment follows the
independently reviewed64-game readiness:24late games/1047contributing rows,
408PLAY rows, median31.6seconds to termination versus119.5seconds for full rows.
It tests whether focusing outcome learning on late decisions improves execution.
Readiness proved mechanics, not that this curriculum helps strategy.

## One comparison and fixed budget

Both arms restart the verified ordinary_v5 checkpoint. `full_budget_v5` learns
from all contributing decisions; `late_budget_v5` learns only from decisions at
tick>=regular_ticks+overtime_ticks//2 (4800 standard). This is a training row
selection, never a tactical switch. Both policies play their own complete prefix
and suffix with unchanged public history, from reset through actual native end.
Their trajectories may diverge after learning. No saved-root restart, policy
switch, outcome filtering, minimum-game resampling, or added tactical labels.

16updates per arm,64fresh complete games per update:1024games per arm/2048total.
Same1024initial setups and seeds2026102000..2026103023 across arms, no readiness
game reused.32gen/32S1 per update,balanced learner sides, the same8exposed gen
decks used in readiness cycled by fixed index. Four simultaneous matches in one
process. Interleave full then late at each update under one chain lock/GPU.
The prepared schedule and native initial bytes/forms must match both arms.
These are training games, not independent final testing or original pro matches.

Both arms use the SAME fixed2048equal-match draws per update with replacement,
then2passes/batch256=16Adam steps. Same two-column random uniforms select a
nonempty eligible match uniformly, then a contributing row uniformly within it.
Per-draw weight1/2048; this estimates an equal-match objective in each arm.
Compute GAE on the complete eligible sequences BEFORE drawing; retain all
original rows, selected membership, uniforms, draw indices, returns and values.
Normalize advantages on the2048draws. This common budget mechanism differs from
old all-row RL and therefore gets its own matched full-row control. It must not
be attributed to late selection using the old256-game RL as the control.

The only between-arm recipe difference is eligible row membership. Each arm
must have>=4nonempty eligible games and>=256eligible rows EACH update. Empty
late games remain in the64game denominator. On insufficient coverage stop the
chain, retain raw evidence, and reassess; never extend a cohort or move boundary.
Budget16updates is fixed before results, with5critic-head-only warmup and11
policy/critic updates. Each arm completes256Adam steps,176with policy updates.
No best checkpoint, seed selection, continuation, or adaptive budget.

## Shared learning/runtime

Use updated MAIN RoyaleSim0.1.13/RoyaleGym0.1.15, abilitiesv2, qualified terminal
adapter ON, public sampler tau.35/T.5,26tickdelay/extrapolation,10tickcadence,
noiseOFF. Outcome-only+1/-1/0,gamma_tick.99994,lambda.95,actual terminal gap.
No frequency reward, shaping, rejected weights, new network/features or card rules.
Adam1e-5,clipgrad.5,PPOclip.2,valuecoef.5/valueclip.2,shared critic trunk after
warmup,reference ordinary_v5,beta.3adaptive.03..3,target.1/maxhead leash.
Existing guards retained:2consecutive violations,plays/min .6..1.6 of initial,
cellKL.5/gateKL.1,entropyfloor.5. Full-game monitors in both arms.
Sampling and optimizer RNG are paired by update; exact uniforms/draws saved.
All public feature/action arrays are literal selected rows; opponent private
state, native bytes, seed/schedule/phase-selection metadata are not model inputs.
np.load during training restricted to this experiment's own outputs. Block
stockLearner/gen_v3val. No expert/reserved/oldvalidation/bot labels in training.
Parent exposure retained. Fixed existing54723development rows only after both
final checkpoints. Source and runtime hashes checked before/after every stage.

## Execution and evidence

P1: bind1024native setups and independent fixed-draw/projection controls before
optimization. No model optimizer in preparation. T1: complete both16updates,
full raw trajectories/native bytes/checkpoints/contracts. V1: independently
reconcile every game/selected row/native outcome/probability/return/draw/weight,
all finite steps and unchanged nonvalue warmup tensors before development.
E1: evaluate both finalu016checkpoints once. V2: independent original-label
development recount and paired replay summaries. R1: outside receipt/hash review,
one compound model report through intended Discord sender, exact delivery ledger.
Failclosed/no automatic resume. Preserve all partial/failed original artifacts.

No deployment or gameplay superiority is inferred from training/continuation.
FinalN2-N7/untouched/statistical/physical/component/gameplay/public/Q4/Q5 gates
remain. STOP retained until a qualifying NEW policy meets all agreed floors.
