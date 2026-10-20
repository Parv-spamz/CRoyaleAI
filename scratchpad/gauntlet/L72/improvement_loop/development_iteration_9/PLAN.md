# Additional ordinary imitation budget

Registered October6 before preparation or optimizer work. The completed
training_fit_audit found weak fit on actual original draws: Rocket full175/2366,
aim674/2366, compared with cached development77/955 and292/955. It does not show
a large training advantage and does not prove a cause. After failed targeting,
exposure and outcome-RL recipes, test whether additional ordinary supervised
optimization can improve the unchanged policy before changing its architecture.

One candidate ordinary_extended_v5 starts from the verified ordinary_v5 portable
checkpoint. This is a new continuation with a fresh AdamW state, not an exact
continuation of the unsaved original optimizer. Control is the unchanged v5
checkpoint and its verified cached development predictions. Do not rerun the
completed1000-update original training or any baseline inference.

Exactly8000 additional updates,batch128,seed2026100609. Uniform replacement draws
from the original213995 inner-training rows, independent50% batch mirroring,
unchanged original expert losses, feature_version5, AdamW1e-5,weight_decay.01,
clip_norm1,fp32. No LR schedule, new network/features, loss reweighting, card
rules, rejected weights, outcome reward, label edits or sampling curriculum.
Record all1024000 row draws and mirror flags before optimization. No adaptive
budget, intermediate evaluation, best checkpoint or seed rescue. Only final8000
is eligible. Fail closed on nonfinite update or source/runtime drift.

Preparation binds original data/split/labels/checkpoint, dependency sources,
all draws, and fixed scoring masks. Strict schedule controls and one excluded
new-driver CPU backward probe must pass; no smoke optimizer update or saved
smoke model. Training's data access is restricted to original training indices
and its registered schedule. No reserved/old validation/live bot labels.
The parent was exposed to both inner-training/development subsets; this is not
untouched generalization evidence. Fresh optimizer and extra compute are part
of this single registered additional-fit treatment, not an isolated measurement
of optimizer duration under identical historical Adam state.

After training, independently verify8000 finite updates, full schedule,
changed finite final weights and all source bindings before development inference.
Then predict once on the original54723 development rows/405 replay groups,
reuse cached R1e-corrected and v5 controls, and independently recount all original
labels/masks/per-replay statistics. Keep old within1tile coordinates unchanged;
do not substitute physical hit labels. METRICS freezes all continuation floors.

One serial chain holds the common development_iteration_1 lock across five jobs:
prepare,train,training-independent,eval,results-independent. Run outer review
once only after all five succeed, report the new final model once to Discord,
bind message/delivery/receipts and publish accurate handoff. Do not edit bound
sources or automatically retry failures. New jobs/updates honor13Z owner cutoff.
Development success alone cannot deploy; all final N2-N7/statistical/component/
physical/gameplay/public/Q4/Q5 gates remain mandatory. STOP remains intact.
