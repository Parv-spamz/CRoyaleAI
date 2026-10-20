# One-factor generic spatial-frequency cell loss

October5 15:49 EDT. The independently verified tower_aim_localization leaf finds
469/627 tower_spatial_v7 Rocket misses in different expert patches,158 in the
same patch. Ordinary_v6 has515/662 different-patch misses. Narrow targets within
1tile of an alive enemy princess show no aim improvement (5/43 across all PLAY;
late expert Rocket1/22). These are descriptive geometric labels, not physical
tower hits or all cycling use cases. The ordinary schedule covers only78/162
matching training Rocket rows (109draws);84 are unseen in that new1000-step run.
This does not prove a cause, but supports testing spatial target imbalance.

Candidate spatial_cell_balance_v6 starts from the SAME R1e31u0155 and ordinary_v6
architecture/corrected observations/draws/mirror/dropout/1000updates/batch128,
seed20261005,AdamWwd.01/baseLR1e-5/projectileLR1e-3/clip1/fp32/finalstep only.
Do NOT use or combine rejected tower_v7, phase, defense or3x Rocket loss recipes.
Only the cell cross-entropy weighting changes. All original expert PLAY/WAIT,
cards, positions, values, split membership and row sampling remain unchanged.
No card-specific, tower-specific, phase, HP or outcome condition; no new inputs,
decoders, tactical rules or reward for casting a spell.

Count target regions from ALL67106 training PLAY rows only. Quantize x*36/y*64
by float32 multiply and nearest-even rounding. Fold horizontal reflection using
min(cx,36-cx), before clamping cx to35; region=(clamped cy//4)*5+folded cx//4.
This gives80 shared two-tile vertical/reflected-horizontal bins, with the central
folded bin narrower. No tower target definition enters the weights. For each
nonempty region r, raw weight=sqrt(Nplay/(Knonempty*count[r])), clipped to[.25,4].
Unoccupied bins receive4 but supply no training targets. No tuning these constants.
Assign weights to ORIGINAL row IDs before augmentation; mirrors retain exactly
the original weight, so jitter/clamping cannot change weight during mirroring.

Cell term is sum(weight*original per-PLAY CE)/sum(PLAY weights) in each batch.
All-one weights take the original CE reduction exactly. Gate/card/WAIT/value
terms are byte-identical at fixed model outputs, with a single original forward
and unchanged RNG. This changes relative spatial supervision, not overall spell
frequency or exposure. All non-PLAY weights are ignored by the cell term.

Before optimization independently regenerate every region/count/weight and every
scheduled row weight, check original eight labels/IDs against the existing bound
rows, no reserved/development weight-fitting, mirror identity, positive/corruption
controls and unit-weight exact original loss/parameter-gradient identity. Fixed
output controls prove only cell gradients change on PLAY rows and no changes to
gate/card/WAIT/value terms; finite checkpoint-free first-batch smoke and plain
metadata standard-loader roundtrip must pass. Preserve any failed version.

Use the existing54723 development rows/405groups and all original/phase-context
metric groups from the prior model comparison (do not use the localization-only
groups as new acceptance criteria). Continuation against verified ordinary_v6:
global Rocket forced aim within1tile+5pp AND full action+2pp AND late Rocket
action+2pp; general card decline<=.5pp; no W/NW/F/defense/all-late action point
decline; no Barrel correct-lane fall/wrong-lane rise. Original development metrics
and all final untouched/gameplay/statistical gates remain unchanged. Historical
parent exposure disclosed, no oldvalidation/confirmation/live bot labels.

One GPU serial train/eval/independent recount, failclosed/no automaticresume.
Report the new model once after review, DEVELOPMENT/NOT ACCEPTED pending final
gates. Keep ownerSTOP intact and frozen historical experiments unchanged.
