# Train aim across the board while freezing decision timing and card choice

Register before optimization. The frozen-branch Rocket diagnosis must independently
pass before preflight/launch. Iteration7 remains rejected, including its exact
cached-logit failure; do not reuse its trained weights or loosen that criterion.

The diagnostic finds607/955 expert Rocket rows without valid projectile targets;
their196 correct aims and411 misses are unchanged. Only15 Rocket argmax cells
change, all between patches, with one gained/three lost aim successes. This
supports expanding the trainable aim path beyond the local projectile residual.
It does not establish the cause of poor strategy, damage or gameplay outcomes.

Candidate aim_heads_v6 starts from the same verified ordinary_v5 parent as trial7
and adds the same zero-initialized v6 projectile branch. ONLY trainability changes:
in addition to the five projectile tensors, allow existing query.*, cell_key.*,
cell_emb and cell_bias to learn. These eight tensors are used only for aim.
Freeze every encoder, embedding, global feature, gate/card/wait/value parameter.
Keep the base in eval mode, original expert loss, ordinary1000x128 draws/mirror,
seed20261005, AdamW weight decay.01, gradient clip1, fp32 and final checkpoint only.
Original aim tensors use the established base LR1e-5; new projectile tensors
retain LR1e-3. No new inputs, architecture, labels, spatial/loss weights, target
filtering, phase/card tactics or spell-frequency reward. No failed recipe mix.

Use unchanged213995 train rows/1573 replay groups and54723 development/405 groups;
no old validation, reserved confirmation or owner-bot expert targets. Parent
exposure is disclosed. No extra baseline training or inference. Reuse verified
R1e(corrected), ordinary_v5, ordinary_v6 and trial7 caches. Primary continuation
compares against ordinary_v5; trial7 describes the trainability contrast.

Before launch, two original training-batch CPU steps must keep every frozen
tensor and gate/card/wait/value output exact, update aim and projectile paths,
and allow changed aim logits even without valid projectile targets. Initial
outputs/loss equal v5; standard weights-only roundtrip and masks/splits pass.
Smoke saves no checkpoint and is not full training. Preserve all failures.

Frozen continuation versus ordinary_v5: Rocket forced aim+5pp, full expert Rocket
action+2pp and late Rocket action+2pp; Barrel correct response+15pp, wrong-lane
count at least halved and full Barrel action nondecreasing; no point decrease in
Witch/Night Witch/Furnace, defense or all late actions. General card choices and
gate/card logits must remain exact across all54723 cached rows, as in trial7.
Small GPU discrepancies still fail this filter; independently complete all
statistics with a false filter rather than interrupting the whole recount.
Do not silently replace equality with tolerance. All strata must be present.

One GPU lock spans serial1000-update training, evaluation and independent raw-
label/cache/replay recount. Fail closed, no automatic resume, adaptive steps or
checkpoint picking. At cutoff finish active job and start no next job. Review
all receipts/paired counts then send this new model's report once, explicitly
DEVELOPMENT/NOT ACCEPTED. A pass only supports separately registered gameplay;
all final untouched/component/gameplay/statistical/Q4/Q5 gates remain mandatory.
Owner STOP intact. No pipeline/runtime/live source changes.
