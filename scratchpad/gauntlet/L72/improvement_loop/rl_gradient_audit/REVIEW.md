# Shared critic gradients did not dominate the sampled policy gradients

October5 20:23 EDT. G1-G3 COMPLETE. Collection244.85s, independent5.38s and
review1.40s all exit0/token matched. All27 fixed policy-update starts6..32 and
6912 sampled original training rows reconcile from saved raw gradient vectors.
No optimizer updates, saved candidate, development predictions or native games.
Do NOT repeat collection, gradient computation or completed verification.

Weighted critic norm was smaller than actor-plus-KL norm in every sampled update
(0/27 critic-larger). Its norm share ranged2.824% to12.905%, median7.430%.
Shared-vector dot products were negative in13/27 samples; cosine ranged
-0.164625 to+0.155918, median+0.002850. Thus the critic reaches the shared encoder
and sometimes opposes the actor-plus-KL direction, but these measurements do not
support a simple claim that critic gradients dominated the policy gradients.

These are fixed256-row samples at update starts, not every PPO minibatch or the
Adam-preconditioned optimizer trajectory. They do not establish which component
caused the final gate/card/aim changes, or what detaching the critic would do to
policy strength. No detach remedy or successor recipe is authorized by this
result alone. Original outcome_rl_v5 remains rejected and reported once.

Every original tensor stayed unchanged and .grad remained unset. Detached critic
non-value gradients and actor value-head gradients were exactly zero. Independent
CPU reductions reconciled every tensor and shared total under the prospectively
registered float64 reduction tolerance; prior model exactness failures remain.
Three positive/eight corrupt-vector controls passed; outer review added one
positive/four missing/duplicate/wrong-update/wrong-checkpoint membership controls
and rebound every source, trajectory, checkpoint, original beta and cohort count.
See report.json, verified.json, reviewed.json and l72-rl-gradient-* receipts.

Next supported investigation is a separately registered cached training-credit
analysis: original sampled PLAY/WAIT/Rocket decisions, saved advantages/returns,
terminal distance and direct terminal-reward contribution through GAE. Include
all32 updates, distinguish five critic-only warmups from27 policy updates, and
preserve original outcomes and refused/unlanded actions. Source inspection shows
GAE lambda=.95 applies once per contributing decision; actual credit distribution
has not been measured in this leaf. Do not infer sparse-credit failure from that
formula alone, change lambda, detach the critic or start a blind parameter grid.

Owner STOP is intact. No runtime/live change, new model report or acceptance.
Final material/component/physical/gameplay/untouched/statistical/Q4/Q5 gates remain
open. This diagnostic completed its registered engineering scope only.
