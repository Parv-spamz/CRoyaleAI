# Registered correction to diagnostic target-cell descriptors

Source inspection found metadata grid=lattice and pipeline.model_v3.cell_label
uses round, while small_set_aim_audit and local_cell_contribution used floor
cells for exact-target, target-patch and target-score descriptors. Their floor
arithmetic remains preserved; those descriptors are NOT actual training-label
statistics. Continuous <=1 tile aim, gate/card/full actions and failed fit verdicts
do not depend on that conversion and must remain identical.

Use ONLY the existing eight prediction caches (four models, two orientations,
1024 rows each), the two saved contribution score/activation archives, original
1024 sample membership/raw labels and frozen metadata/checkpoint arguments.
No inference, backward, optimizer, checkpoint, new labels, development, reserved,
old validation, native game or live work. No change to floor/lattice decoding,
original <=1 tile threshold or any final acceptance requirement.

C1 recomputes actual lattice exact labels/patch membership for all4096 cached
PLAY records, and actual lattice CE/margins/direct residual contributions for
the1024 saved local-cell PLAY score records. Preserve floor descriptors beside
lattice descriptors, raw distances and all row/replay/card denominators. Reconcile
new continuous aim counts to both old audits exactly. Independent V1 uses original
raw source labels, scalar round-to-even and original float32 products, separate
geometry/counting and scalar logsumexp. Verify metadata and original label function
on all source PLAY views, and boundary fixtures with positive/corruption controls.
All raw arrays, sources, old reports and receipts are hashed. R1 closes only this
diagnostic correction. No revised model report is due because model performance,
failed fit criteria and NOT ACCEPTED/NOT DEPLOYED verdicts are unchanged.

One common chain lock spans collection and verifier; cutoff13Z. Fail closed;
preserve any failure, never edit bound sources or retry unchanged. The correction
must be considered before another training recipe; no successor recipe is selected
from favorable descriptors alone. Quarantined assay weights stay permanently
ineligible for policy, training parent and live use. STOP stays intact.
