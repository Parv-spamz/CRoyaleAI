# Exact public-input collision diagnostic

Registered before execution after extended_fit_audit completed. Broad training
fit remains weak for BOTH final models: native complete PLAY10956/10950of67106,
Rocket forced aim1109/1114of3852, despite the small-set dropout-free fit pass.
This does not identify an optimization, capacity or data cause. Before changing
another learning recipe, test the narrow data hypothesis that byte-identical
model inputs carry incompatible expert targets.

Use ONLY the original213995 native inner-training rows. No development, reserved,
old validation, mirrored input, saved-model inference, backward, optimization,
native game or live activity. No model loads or checkpoint changes. Existing
dataset and original training membership stay frozen. Original labels are never
changed, excluded or repaired. No new model/report or acceptance criterion.

Producer uses original CPU GenRows.batch with128-row batches and the16public
tensor keys consumed by original feature5 GenModel encode/heads. Exclude expert
targets, row/replay IDs and other bookkeeping from the input hash. Include exact
ordered padded64unit tokens/masks/forms,scalar state,hand/deck/next card/forms,
own/opponent history,opponent public cycle,projectiles,effects andownability.
Hash canonical key/dtype/shape headers plus exact contiguous tensor bytes.
This is strict tensor-byte equality, a SUFFICIENT condition for identical
deterministic inputs, not an exhaustive test of functional equivalence. Permuted
sets,clamped/ignored fields,+0/-0,nearby states and latent representation collapse
may escape grouping. Zero collisions would only reject this narrow explanation.

Within duplicate groups retain all original row/replay IDs and targets. Count
gate-label conflicts; PLAY card-label conflicts; conditioned card/form lattice
label conflicts; and largest original<=1tile accepted target coverage among all
2304lattice predictions. The latter may allow different class labels to agree
within the existing continuous criterion. Compute per-head minimum disagreements
inside groups only; do not add overlapping heads or call them full-action limits.
Expert alternatives may both be sensible; conflicts are not mislabeled data proof.

Independent verifier reconstructs every tensor from raw subset arrays using a
separate scalar padding/casting path, regenerates every hash and original labels,
checks positive duplicate-group payloads byte-for-byte, and separately recounts
groups/targets with scalar geometry. Original-label joins to uncorrected source
must match. Positive/conflicting/compatible geometry fixtures and malformed saved
hash/ID/label/group-summary controls run before trusting absence.

Two serial jobs under the existing commonchain.lock: collect+controls/sourcebind,
independent verification. Outside once-only receipt review follows. No duplicate
execution,editing bound/failedsources or unchanged retry. Preserve originals before
any separate diagnosis. All jobs/batches check owner13Z/09EDT cutoff. STOP intact;
all finalN2-N7/statistical/component/physical/gameplay/public/Q4/Q5 remainOPEN.
