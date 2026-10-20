# Small fixed-set fit assay, registered October 6 before optimization

The original ordinary_v5 training-fit audit and the rejected additional 8,000-step
candidate weaken the simple claim that more ordinary training alone fixes aim.
This assay asks whether the unchanged model and loss can fit a bounded training
sample. It is not a generalization test or a deployable candidate recipe.

Use only the original 213,995 inner-training rows. Seed 2026100610 determines a
single sample: 64 original PLAY rows for each of the eight Icebow cards and 512
WAIT rows, taking at most one row per replay within each label stratum. Select
by a seeded permutation before looking at predictions. Keep every selected row,
original label, form and public input. Fail if a stratum lacks enough replays;
do not resample, replace labels, or use development/reserved/old-validation data.

Restart from verified ordinary_v5 portable, never the rejected extended model.
Exactly 4,096 additional updates, batch 128, uniform replacement from the 1,024
sample rows, original 50% whole-batch mirroring, original expert loss, version 5,
fp32, fresh AdamW 1e-5, weight decay .01 and clip 1. Original dropout and all
training mechanics remain. Save only the final assay model and optimizer. This
tests concentrated exposure under a fixed recipe; failure does not establish
an architectural impossibility. No adaptive budget or checkpoint/seed rescue.

P1 freezes sources, sample, all 524,288 draws and mirror flags, proves original
label/split joins, exercises malformed sample controls, and runs one excluded
CPU backward with exact unchanged weights and no optimizer. T1 trains once.
V1 independently reconstructs selection/draws, finite update logs, final tensor
and optimizer states BEFORE final inference. E1 evaluates final assay, ordinary_v5
and corrected-input R1e once each on both orientations of the same sample (2,048
views/model). This is new assay inference, not repeated development inference.
V2 independently recounts every label, mask, count and per-replay count with
corruption controls. R1 binds receipts, review and one diagnostic-model report.

The sample is balanced by labels, not representative of natural frequencies.
Native and mirrored views are not independent examples. Parent exposure remains
disclosed. No development, confirmation, native games, live play or physical
benefit is measured. Assay weights are quarantined and may NEVER become a policy
candidate, learning parent or live checkpoint. A successful fit only supports
learning on this selected small set; a failure rejects these fixed conditions.

One shared development_iteration_1 chain lock covers all five serial jobs. On
failure preserve sources, partial output and receipt; no automatic retry. New
helpers go outside this leaf once bound. Owner deadline October6 13Z applies.
STOP remains untouched. All final/statistical/component/physical/gameplay/
public-input/Q4/Q5 gates remain open. Review and rethink before any next recipe.
