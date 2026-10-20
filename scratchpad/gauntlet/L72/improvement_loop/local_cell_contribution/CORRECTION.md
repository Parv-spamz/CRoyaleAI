# Diagnostic label conversion correction, October6 06:42 EDT

The dataset and training checkpoint grid is lattice: pipeline.model_v3.cell_label
rounds float32 x*36/y*64, with ties to even. This audit used floor labels for
exact-cell/target-patch descriptors (and local_cell_contribution target scores).
Those are not actual training-label descriptors. Original sources, artifacts,
receipts and floor arithmetic are preserved; do not silently reinterpret them.
Separate ../lattice_label_audit is registered to independently reconstruct actual
labels from the original raw sample and cached predictions/logits. No inference
or optimization. Continuous <=1tile aim, full-action/card/WAIT counts, original
failed fit verdicts and permanent checkpoint quarantine are unchanged.

The separate lattice_label_audit is now COMPLETE; see its REVIEW.md and
reviewed.json. Original continuous aim and failed fit verdicts are unchanged.
