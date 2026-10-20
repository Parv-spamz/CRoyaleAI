# Ordinary model training-fit diagnosis

Registered October 6 before new inference. The paired full/late outcome recipes
failed every Rocket material floor; late selection did not rescue the unchanged
ordinary_v5 control. Before another optimizer recipe, measure whether ordinary_v5
fits its own available and actually drawn training examples. Poor training fit
and poor development fit suggest different next experiments from good training
fit and poor development fit. Neither establishes a cause by itself.

Freeze ordinary_v5's verified portable checkpoint, existing 213995 training rows
and 54723 development rows, original labels, original 1000x128 draws and mirror
flags. All these groups were already exposed through the parent; development is
an inner split, not untouched generalization evidence. No reserved, original
validation, live-bot labels, new data, model change or optimization.

One inference pass on all native training views, then one pass on each unique
training row that actually appeared in a mirrored draw. Reuse native predictions
for native draws; weight each orientation by its original draw multiplicity to
describe the exact training draw stream. Mirrored views use the original frozen
augmentation, including mirrored expert coordinates. They are not new matches.
Evaluation mode disables dropout: this is final-checkpoint fit, not historical
per-step train loss. Reuse the verified ordinary_v5 development prediction cache;
never repeat development inference. No new checkpoint or model report is due.

Report native train, drawn native, undrawn native, drawn mirrored, multiplicity-
weighted actual training views, and cached development. Per group retain row/view
and distinct replay counts. Report all rows, expert PLAY, expert Rocket, late
Rocket (original tick>=4800) and every expert PLAY card. Gate/card/forced aim and
full action counts stay separately visible. First-failure order is gate, then
card, then aim; this is arithmetic decomposition, not causal attribution.
Retain PLAY successes separately from correct WAIT, continuous coordinate errors
and per-replay counts. Descriptive only: no new model-selection threshold.

P1 binds exact input/source hashes and known positive/malformed scoring controls.
C1 collects fresh training predictions with one shared chain lock, original
128-row batch size, model weights exact before/after and no backward/optimizer.
V1 independently joins raw source labels, reconstructs draw orientations/weights,
recomputes all counts and per-replay totals with a separate scalar implementation,
and checks malformed caches. R1 reviews process receipts and interpretations.
Fail closed; no unchanged retry or editing failed bound sources. New jobs check
the owner's October6 13Z cutoff. STOP and all final acceptance floors remain.
