# Isolate projectile learning from base-policy drift

October5 after the updated-runtime gameplay failure. ordinary_v6 wins39/64,
ordinary_v5 42/64, R1e45/64. The completed raw first-divergence audit finds41/64
pairs differing first in learner accepted commands with identical preceding
public frames;23 have no command difference. Card/timing changes exist as well
as aim changes. The generic residual directly changes only spatial patches;
end-to-end training also moved shared parameters. This motivates testing whether
the useful projectile branch can be learned while retaining the entire v5 base.
It does NOT prove shared-weight drift caused the losses or promise an improvement.

Candidate frozen_base_projectile_v6 starts from the independently verified
ordinary_v5 portable checkpoint, adds the same zero-initialized generic residual,
and updates ONLY projectile_target_in/projectile_target_spread. All existing
weights, including embeddings, spatial backbone, positional biases, gate/card/
value heads and aim query remain byte-identical to ordinary_v5. The frozen base
stays in evaluation mode during training; the new modules contain no dropout.
No shared fine-tuning, new inputs, labels, tactical rules or card-specific masks.

Use the original213995 training rows/1573 groups,54723development/405groups,
original1000x128 draw/mirror schedule,seed20261005,original expert loss, AdamW
targetLR1e-3,wd.01,clip1,fp32,1000final-only updates. Existing verified ordinary_v5
is the no-additional-update control; this is explicitly additional branch-only
learning from a fine-tuned checkpoint, not another same-R1e end-to-end arm.
Compare all same-corrected-input R1e/v5/v6 development caches, no new baseline
inference. Parent exposure disclosed; no reserved/oldvalidation/bot expert labels.

Preflight: verify all original bindings, schedule membership and labels; zero
residual reproduces v5 outputs/loss exactly. A training-only two-step CPU smoke
must change both new-layer stages while leaving every base tensor unchanged;
gate/card/value outputs must stay exact, including with a nonzero residual.
Unknown/padded/no-valid-projectile targets yield zero residual and unchanged
full outputs. Require standard weights-only metadata/tensor roundtrip and
independent development masks; smoke saves no checkpoint, not full training.

Frozen developmental continuation versus ordinary_v5: primary Barrel correct
gated-lane responses +15pp and wrong-lane count reduced by at least50%; full
Barrel actions nondecreasing; all gate/card logits exactly unchanged on all54723
rows; no point decline in Rocket forced aim/full actions/late Rocket actions,
all late actions, each Witch/Night Witch/Furnace and defensive actions. No missing
strata. These are strict developmental branch tests, not Rocket material-gain
claims or lowered final deployment floors. Report per-replay paired counts,
all baseline comparisons and remaining Rocket/strategy gaps. A pass only permits
a separately declared gameplay comparison; prior end-to-end gameplay stays failed.

One GPU lock across train/eval/independent recount; no automatic resume, source
editing, extra steps or checkpoint selection. Freeze source/runtime/data hashes
before launching. Every new checkpoint receives one reviewed Discord report.
OwnerSTOP remains intact. All final untouched/material component/gameplay/power/
multiplicity/Q4/Q5 gates remain open. This branch cannot act when public target
information is absent, so it is not offered as a complete Rocket-cycle remedy.
