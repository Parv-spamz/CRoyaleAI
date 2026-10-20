# Controlled stochastic-regularization fit assay, registered before training

The original small_set_fit failed fullPLAY90% and Rocket aim95%; the generic
local-cell branch added only7 correctPLAY/orientation and no Rocket aim improvement.
The fixed-weight contribution audit found only6/13 net aim gains overall and0/1
Rocket gains. The separate lattice_label_audit corrected floor-based diagnostic
target descriptors: actual lattice-target final CE is about.50, while original
local-cell training cell-loss last256 mean is.614. These are different weights,
sample weightings and modes; the gap alone does NOT prove dropout caused misses.

Test ONE different factor: disable stochastic training dropout, including
MultiheadAttention.dropout and every nn.Dropout.p. Start a FRESH verified
ordinary_v5 portable model with the ORIGINAL architecture, no local-cell branch,
no rejected/quarantined weight reuse. All trainable tensors, public inputs,
original lattice labels, original loss and optimizer settings remain unchanged.
This tests fit under reduced regularization; it does not establish generalization
or justify removing dropout from a deployment recipe.

Use the EXACT original1024sample/798replays and524288draw/mirror stream from
small_set_fit, seed2026100610,4096additionalsteps,batch128,AdamW1e-5,wd.01,clip1,
fp32. Original whole-batch50% mirroring. No adaptive budget/seed/checkpoint rescue,
no repeated old inference; finalonly. Freeze ordinary_v5/SOURCE/DATA/source hashes.
All NEW weights also forever quarantined: NEVER policy, learning parent or live.

P1 independently reselects/reconstructs original labels/draws,2positive6malformed
sample controls; proves every changed dropout attribute was originally.1 and now0,
state tensors and initial EVAL outputs identical in both orientations and in-memory
roundtrip. Fixed CPU training batch: separate seeds give identical outputs with
dropout0 and different cell outputs with ordinary dropout.1. A re-enabled dropout
attribute must fail the configuration validator. Finite original-loss backward,
unchanged tensors, zero optimizer, no saved probe/development inference.
T1 trains once. V1 independent original draw/log/final-tensor/optimizer accounting
and1positive8corruptions precedes E1. E1 only final predicts2048views once; prior
small_set_fit,ordinary_v5,corrected-inputR1e6144views are reused without inference.
V2 independently reconciles all original labels, masks, choices and per-replay
counts with9positive12corruptions. R1 reviews and reports once with all controls.

Common chain.lock spans all5jobs including gaps. Ownercutoff13Z. Failclosed;
preserve original failures, no unchangedretry/source edits. Outside review helpers.
No development/reserved/oldvalidation/nativegame/live work. Parent exposure remains
disclosed; all sample is training, balanced strata and mirrored views are not
natural distribution or independent observations. All original fit/final gates
stay unchanged, including exact continuous1tile comparisons. No epsilon rescue
for near-boundary misses. Original objective remains unmet and STOP stays intact.
