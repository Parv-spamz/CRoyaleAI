# Updated-engine sampled-trajectory readiness

Registered October5 18:42 EDT before execution. This engineering leaf follows the
completed IL and terminal-wrapper work. It produces no trained checkpoint, expert
labels, policy improvement claim or Discord model report. All final gates remain.

Use eight new serial sampled matches: seeds2026100600 and2026100601, gen/S1,
R1e(original feature4) and ordinary_v5(feature5). Use the first two gen deck
descriptions from the frozen development_gameplay_1 manifest, original Icebow
learner/S1 forms, seed parity side and new tags. These are excluded readiness
scenarios, never final confirmation or a basis for selecting the better parent.
Pin existing checkpoints, main updated runtime, abilitiesv2 and source hashes.
The qualified terminal adapter is enabled. No old192/32-game or fixture reruns.

Learner uses existing sample_decide_batch, tau.35,T.5, affordability, original
stall handling, noise off,26tick delay/extrapolation,10tick decision cadence.
Opponents use existing live decoder/tau.27. Record only learner public rows and
sampled decisions; native outcomes/accepted commands stay separate diagnostics.
Public row key contract and existing source paths are bound. Do not load any
expert dataset, v3val, old heldout pool, reserved confirmation, or live bot labels.
Explicitly prohibit stock Learner construction/gen_v3val_arrays in this leaf.

For every contributing row compare stored gate/card/cell log probabilities with
recomputed policy_terms on the unchanged policy in eval mode. Require finite
values and max absolute joint probability-ratio deviation<1e-4 (the existing PPO
on-policy threshold), over all rows, not merely the first minibatch. This is a
separate numerical contract; trial7/8 exact-logit failures remain rejected.
Check masked/card/cell decisions and no post-fulltime recorded decisions. Require
actual native termination, no missing/truncated/forms-fallback cases. Exact
initial bytes/forms must match across the two policies for each scenario.

Collate with outcome-only +/-1/0 reward, per-tick gamma.99994, terminal-gap on and
lambda1 for an independent analytic return identity. Compare every contributing
row with reward*gamma**(actual_end_tick-decision_tick), separately retain all
unknown/failure data. No summed-HP or spell-frequency shaping.

On the first<=256 contributing rows per policy, run backward-only policy and
critic losses using existing functions. Require finite nonzero gradient paths;
zero optimizer steps and exact unchanged parameter tensors. No model saved.
This demonstrates plumbing, not useful learning or sufficient exploration.

One GPU lock spans collection/recompute/independent verification; fail closed,
no automatic resume, source snapshots frozen before inference. Independent verifier
uses saved arrays and raw native/result records without model inference; recompute
membership, masks, ratios, discounts, terminal outcome and counts. Reject missing,
duplicate, probability, outcome, terminal, mask and discount corruptions. No
adaptive expansion if fulltime coverage is absent; retain prior terminal evidence.
Production pipeline/live untouched; owner STOP retained. A pass permits drafting
a separate bounded development RL recipe with explicit data/scenario controls;
it is not authorization to reuse the inherited validation-reading launcher.
