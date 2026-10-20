# Fixed-weight imitation-loss interaction diagnostic

Registered before execution October6 after input_collision_audit and
extended_fit_audit completed. Broader training fit stayed weak with and without
dropout, whereas a small balanced subset could be fit. Exact byte-input conflicts
provide only small overlapping lower bounds and no repeated conditioned Rocket
aim input. These results do not identify the cause. Test a different mechanism:
whether the existing imitation-loss components oppose one another locally.

Use two FIXED checkpoints: ordinary_v5 and rejected ordinary_no_dropout_v5 final.
Both are observation-only diagnostic subjects, never learning parents or policies.
Use16 original development10 training batches at zero-based schedule indices
0,500,...,7500, retaining128 draws and the original batch mirror flag. Use original
training inputs and labels ONLY. No development, reserved, old validation, native
games, optimizer steps, parameter perturbations, checkpoints or live work.

Both models are in EVAL mode to remove dropout noise. This describes deterministic
loss geometry, not stochastic training gradients or actual historical Adam steps.
Reconstruct the original five differentiable loss components with their original
weights: cell,card,0.5wait,gate,0.5value. Require exact scalar agreement against the
existing original losses function on every batch before gradient collection.
Save the five raw parameter-gradient vectors and the original total-loss gradient.
All model tensors remain byte-exact and parameter .grad remains empty.

Measure each component norm, every pairwise inner product/cosine, cell versus the
sum of other components, and cell versus total. Also report the tensors reachable
by both cell and other losses. Negative cell-total dot would mean infinitesimal
unpreconditioned descent on this batch's total loss raises its cell loss locally;
it is NOT an Adam, finite-step, Rocket-specific, population or gameplay claim.
Do not infer a training recipe, drop a loss, change weights or promote a model.

Before model work run aligned, opposed and zero-vector arithmetic fixtures.
Independently reconstruct the full original8000 draw/mirror stream, verify sampled
membership and original raw labels, saved vectors/reachability and every numeric
reduction. Test malformed vector, missing component, identity, reachability,
linearity and summary corruptions. Save all failures before any separate repair.

One common chain.lock spans collection and independent verification. No duplicate
or unchanged rerun; helpers outside this leaf after launch. Every batch and stage
checks the owner09EDT/13Z cutoff. Preserve STOP and all final acceptance floors.
No new model report is due. A once-only outside receipt review closes the leaf.
