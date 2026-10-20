# Generic public crown-state spatial residual

October5 15:23 EDT. Iterations2/3/4 respectively reject defense exposure,3x Rocket
aim loss and equal phase exposure. Ordinary_v6 retains weak Rocket aim despite
useful Barrel target representation. TRAIN_AIM_DECOMPOSITION_REVIEW.md and current
source confirm crowns are dropped from unit tokens and represented only in
global scalars; global context reaches patches, so this is not proof of missing
information or that the proposed representation will succeed.

Test tower_spatial_v7 against verified ordinary_v6. Same R1e31u0155 start,
corrected data, ordinary iteration1 row/mirror draws,1000 updates,batch128,
seed20261005,AdamWwd.01,baseLR1e-5,existing projectile residualLR1e-3,clip1,fp32,
original expert losses and final-step-only selection. ONLY change: add a learned
generic spatial residual from the six existing public crown-state scalar slots.
Do not combine any rejected exposure or loss recipe. No extra raw/native HP,
actual multiplier, hidden information, forced action or reward for spell rate.

Both sides' kings/princesses use the same learned MLP on side,kind,known HP
fraction,HP-known and alive. Public board geometry comes from the unchanged
obs_contract anchors. Scatter vectors to their spatial patches, then a learned
depthwise3x3 convolution initialized to zero. Add this residual after the existing
encoder/projectile residual. Unknown HP contributes zero HP with known=false;
destroyed towers contribute zero vectors. Include alive unknown-HP kings without
inventing their HP. Do not use raw king health from the native diagnostic.
No card-dependent branch, tower preference, weakest-tower selection, HP cutoff
or phase switch. Every card can learn from the same spatial features.

New tower-module parameters useLR1e-3, as the existing new projectile path does.
All old tensors and optimizer settings stay identical; reset dropout RNG after
architecture construction. A separate isolated subclass/loader/checkpoint tag
keeps production pipeline sources and live unchanged. Standard production loader
must reject the unintegrated extension; acceptance would require a later explicit
integration/control check. Zero residual must exactly reproduce the control's
initial gate/card/cell outputs and expert loss at identical RNG.

Before optimization freeze source/data/geometry/control/mask hashes and check:
all base tensors identical; public scalar-layout assertions; exact zero-residual
migration/dropout/loss; unknown HP invariance including hidden king perturbation;
destroyed/no-alive zero contribution; same-side/type left-right scatter/mirror;
geometry agrees with native explicit crown coordinates on fixed original training
frames and both observer sides; finite/nonzero new gradient path; two training-only
smoke steps demonstrate the upstream MLP can learn after the zero output layer;
strict extension-aware weights-only roundtrip; normal loader fails closed.
Smoke saves no checkpoint and is not the1000-update run.
Geometry fixtures are the first four tag-sorted original training replay groups,
using each first recorded frame and both observer orientations. No confirmation
frame is accessed by this new check.

Development continuation versus ordinary_v6: global expert Rocket forced aim
within1tile +5pp AND full expert Rocket action +2pp; late expert Rocket action
+2pp. General card decline<=.5pp; no Witch/Night Witch/Furnace/defensive-sequence
or all-late action point decline; no primary Barrel correct-lane decline or
wrong-lane increase. Missing strata are inconclusive. These development filters
preserve all final untouched/gameplay/component/statistical acceptance criteria.
Replay-group comparisons and every existing context group remain visible.

Use only the unchanged213995 training rows/1573 groups and54723 development rows/
405 groups, no old validation/reserved/owner-bot expert labels. Parent exposure
disclosed. One GPU serial train/eval/independent recount chain, failclosed, no
automatic resume, no adaptive extra updates. Review/report each new model once
to Discord, developmental/NOT ACCEPTED. Preserve ownerSTOP and all old evidence.
