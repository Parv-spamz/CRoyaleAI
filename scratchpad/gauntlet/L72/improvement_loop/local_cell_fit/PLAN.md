# Generic local-cell mechanism assay, registered before implementation/training

The independently verified small_set_aim_audit finds 93/95 native and 83/93
mirrored residual aim misses inside the expert's two-tile patch. Rocket has
12/13 and14/15 such misses. Every label is representable within one tile by its
original floor cell. Source and144synthetic controls show the patch-specific
spatial score is shared among16cells; relative scores within a patch currently
depend on the global query and fixed cell embeddings/biases. The global query
already contains spatial information; this is not proof of capacity failure.

Test one architecture factor: a generic learned residual that conditions the
16 within-patch cell scores on BOTH that transformed patch and the existing
card-conditioned global query. No new public/private inputs, labels, card rules,
target heuristic, exposure weighting, reward or network trunk changes. Implement
in an isolated GenModel subclass outside production pipeline. For each patch,
concatenate p and q, Linear(256,128),GELU,Linear(128,16),subtract per-patch mean,
and gather by the original cell_patch and row-major4x4 offset. Use model.d for
dimensions. Initialize the last layer to zero for exact initial cell outputs.
Initialization seed2026100612; training seed2026100610 as matched control.

Start again from verified ordinary_v5, NEVER the prior quarantined fitted model.
Reuse the exact small_set_fit sample and draw/mirror stream:1024original rows,
4096updates,128batch,524288draws,original loss/fp32/freshAdamW1e-5/wd.01/clip1.
All original trainable tensors and the new residual train. Fixed final-only;
no adaptivebudget/checkpoint/seed rescue. The completed small_set_fit is the
matched architectural control; do not rerun it. Parent and assay exposure
disclosed; this is still only training-set learning, not generalization.

P1 checks sample/schedule/source bindings and independent cell-offset mapping,
exact initial state/base tensors/gate/card/cell outputs, serialization roundtrip,
finite original-loss CPUbackward with unchanged weights and zero optimizer.
Probe the new mechanism with synthetic patch/query vectors and fixed nonzero
test weights in a disposable copy; prove within-patch relative outputs change
when only local patch contents change. Prove query dependence and per-patch
zero-mean. Use positive and malformed mapping/sample controls before training.
T1 trains4096once. V1 independently validates logs/draws/optimizer/finalfinite
tensors and nonzero learned residual before any final inference. E1 evaluates
only the new model on both1024-row orientations; all3oldassay caches reused.
V2 independently reconciles labels/masks/counts/criteria with corruptions. R1
binds all receipts and one new diagnostic-model report.

Every produced weight remains quarantined: never a policy/learningparent/live
checkpoint. If this diagnostic passes, any broad-data candidate must be freshly
registered from eligible ordinary_v5 and reinitialize the branch; no assay-weight
transfer. A passing fit does not replace any final/statistical/material/component/
physical/gameplay/public-input/Q4/Q5 requirement. STOP unchanged. No native games,
development/reserved/old-validation/live data or inference. One shared chain lock
across all jobs. Owner13Zcutoff; failclosed, preserve failures, no unchanged retry.
