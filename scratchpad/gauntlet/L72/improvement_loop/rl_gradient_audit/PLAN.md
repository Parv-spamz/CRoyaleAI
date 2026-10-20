# Shared critic-gradient mechanism audit

Registered October5 after independently verified rl_failure_audit. The final RL
model's aggregate gains came from859 more correct WAIT labels while correct PLAY
fell137; all Rocket components declined. This does not prove gameplay harm or
critic causation. Existing pipeline.rl_royale.vf_grad_share explicitly describes
shared value-loss gradients, but the isolated completed driver did not log them.

Measure all27 policy-phase starts (training updates6..32), using their exact saved
pre-update checkpoints u005..u031 and original saved trajectories/contracts.
No optimizer, new checkpoint, held-out/development predictions, native games,
hyperparameter grid, partial-checkpoint selection or accepted model. Freeze this
mechanism diagnostic before reading its gradient results. Original rejection and
original exact-summary failure stay unchanged; all final N2-N7 gates remain open.

Use the existing stock vf_grad_share strided256-row selection per update, pinned
before gradient inspection. This is a descriptive minibatch sample, not all PPO
steps or a causal replay of the optimizer. At each start use original beta (the
previous update's beta_next), per-match weights, saved normalized advantages,
returns, v_old and parent reference. Both policy and critic paths use the original
minibatch_loss. No stock Learner, validation evaluator, _entries or expert data.

Compute separate actor-plus-KL and weighted critic gradients for every parameter.
Also compute critic gradients with the existing trunk detach switch, without
updating weights. Save raw flattened vectors and parameter names/shapes/reachability.
Measure norms and inner products on the shared encoder tensors reachable by
critic loss (excluding value_head), plus per-tensor values. Record cosine and
norm share, keeping zero denominators unknown. Count norm_v>norm_policy and dot<0
descriptively; neither is a new acceptance floor or sufficient causal evidence.

Controls: detached critic must have exactly zero non-value gradients, actor loss
exactly zero value-head gradients, losses/gradients finite and every model tensor
unchanged. Independent CPU recount from saved gradient vectors must reconcile
all per-tensor/aggregate norms/dots and source/trajectory/checkpoint identities.
Norm/dot arithmetic uses float64 with rtol1e-10/atol1e-12 between reduction orders;
this prospective diagnostic tolerance does not waive any model exactness gate.
Synthetic aligned/opposed/zero-vector positives and corrupted vectors/summaries/
membership controls must fail honestly. No gradient or returned reward is a
physical improvement, and no result automatically launches a training recipe.

One GPU-chain lock across collection and independent verification, no duplicate
jobs or automatic resume. Tuesday cutoff stops before the next diagnostic update
and preserves partial outputs. Sources frozen at launch; future helpers outside
this directory. Preserve failures before any corrected implementation.

Ownership: this leaf, ignored icebow/data/bench/rl_gradient_audit_20261005,
fresh l72-rl-gradient-* receipts, HANDOFF and existing same-thread automation.
Do not edit original runtime/pipeline/training sources or owner STOP. No new model
report due: outcome_rl_v5 has already been reported once.
