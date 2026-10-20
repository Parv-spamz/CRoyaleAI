# Completed imitation-loss gradient audit

C1/V1 complete08:50:11EDT; outside R1 complete08:56EDT. Collection160.699687s,
independent24.850928s, outside review0.644249s; all exit0/expected token. All70
source bindings,32 model/batch records,4096 model-row views/2038 unique source
rows, original8000 draw/mirror stream, original AND corrected raw labels and
all saved vector reductions reconcile. Producer3positive; independent3positive/
7malformed controls. Every original component and total scalar loss matched
exactly, every model tensor stayed unchanged, parameter .grad stayed empty.
No optimizer step, parameter perturbation, new checkpoint, development prediction,
reserved/old-validation access, native game or live activity. Never repeat jobs.

For BOTH ordinary_v5 and ordinary_no_dropout_v5, cell-versus-other gradient dot
was negative in8/16 batches (all parameters AND shared tensors). Yet cell-versus-
TOTAL dot was positive in16/16 for BOTH scopes/models: no sampled total gradient
reversed the infinitesimal unpreconditioned cell-descent direction.

Shared cell/rest cosine ranges v5[-0.12967235,+0.13078369], no-dropout
[-0.09989913,+0.09534171]; medians+0.00735735/-0.00118224. Shared cell/total dot
ranges[5.44271790,15.28589957]/[7.09240378,18.36228907]. Partial opposition exists,
but it does not cancel the cell descent direction in these measured batches.
This does NOT establish absence of harmful interference elsewhere, nor explain
weak fitting. These fixed EVAL gradients are NOT actual stochastic training or
Adam-preconditioned updates, finite-step responses, population gradients,
Rocket-only losses, statistical strength or causal gameplay evidence.

Mean original weighted loss components (cell/card/wait/gate/value) across the16
fixed batches: v5 2.895525888/.786819894/.524239637/.404803950/.393762553;
no-dropout2.804852739/.739598695/.501159005/.396581909/.382690227. This small matched
sample is descriptive and does not replace the completed broad fit audit or
original development rejection. Max gradient-sum error5.513429642e-7, max relative
L2 error3.795424005e-7, both within the prospectively frozen diagnostic limits.

See DETAILS.md and verified.json for all32 results, original collected.json and
ignored bench raw vectors for complete five-by-five interactions/reachability.
No new loss weighting or training recipe is justified automatically. Both models
remain NOT ACCEPTED/NOT DEPLOYED; no new model or Discord model report is due.
All final N2-N7/statistical/component/physical/gameplay/public/Q4/Q5 remain OPEN.
STOP13:39:32 remains intact. The overall replacement objective is UNFINISHED.

Outside review_il_gradients.py ran ONCE as l72-il-gradient-reviewed /
IL_GRADIENT_REVIEWED; reviewed.json binds sources/results and successful receipts.
