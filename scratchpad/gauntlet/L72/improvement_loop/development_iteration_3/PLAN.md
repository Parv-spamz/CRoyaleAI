# Isolate Rocket expert aim learning

October5: ordinary_v6 passes the isolated projectile-target development filter,
but only73/955 expert Rocket rows have correct full actions and293/955 forced
expert aims are within1tile. The20% defensive-sequence curriculum regressed
defense/Rocket actions and Witch/Furnace; preserve that rejection, do not combine
it. Earlier Rocket exposure improved selection while aim stayed weak. Test aim
loss emphasis separately from card/gate/exposure changes.

Candidate rocket_aim3_v6 starts from the SAME R1e checkpoint, corrected-v5 data,
version6 architecture, ordinary draw schedule, train/development split, seeds,
optimizer and1000 final-only updates as iteration1 ordinary_v6. Reuse that fully
verified control, not an extra optimized control. Do not initialize from its
learned candidate weights. Only change: each original expert PLAY Rocket row's
cell cross-entropy contribution is multiplied by3. Preserve all original labels,
including troop-aimed Rockets; do not filter for tower aim, low HP or success.
The mean denominator remains ALL PLAY rows, so other cells retain their original
coefficient. Card, gate, WAIT and value terms remain exactly unchanged. No
additional forward pass or RNG consumption; no reward for casting Rocket.

Use1000updates,batch128,seed20261005,AdamWwd.01,baseLR1e-5,targetLR1e-3,clip1,
fp32,ordinary iteration1 draw/mirror stream. No curriculum, scheduler, extra
training, model picking within a run, tactical rule or sampling decoder change.
No confirmation or old validation access. This is historical parent-exposed
development, not untouched evidence. Keep original runtime/model/data hashes.

Before optimization validate weight1 exact equality to the old loss and gradients
under the same dropout RNG, positive Rocket-only added loss/gradient, zero added
loss on non-Rocket/WAIT rows, unchanged non-cell loss components and finite
backward. Freeze original iteration1 masks and iteration2 defense masks before
candidate predictions. Primitive metadata must load through the standard loader.

Development continuation versus ordinary_v6 requires forced expert Rocket aim
within1tile +5pp, full expert Rocket actions +2pp, no general card decline over
0.5pp, no Witch/Night Witch/Furnace full-action point decline, no primary Barrel
correct-lane decrease/wrong-lane increase and no defensive-sequence action point
decline. Require all strata present. Report whole-replay paired differences,
R1e and control, gate/card/aim separation, narrow finishing/combo context limits.
These iteration filters do not change any final replacement floor.

Launch only when iteration2 is complete and its independent results reviewed;
hold the same GPU lock across train/eval/independent recount. Fail closed, never
automatically repeat. Preserve failures, report this new model once to Discord,
and keep NOT ACCEPTED until final physical/outcome/statistical gates pass.
