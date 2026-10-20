# Prospective fit-assay measurements

Score native and mirrored views separately. PLAY means original gate label 1;
WAIT means gate label 0. Called means gate probability > .35 and an affordable
hand card exists. Card choice is the original masked argmax. Forced expert aim
uses the original 36x64 floor-cell grid, decoded to 18x32 tiles, <=1 tile from
the unchanged expert coordinate. Full PLAY requires called, correct card and
correct aim. Correct WAIT means not called. Report all eight card strata,
Rocket, late Rocket descriptively, all PLAY, correct WAIT and per-replay counts.

The diagnostic fit criterion is ALL of the following in EACH orientation:
- Full PLAY success >=90% of 512 PLAY rows.
- Rocket card agreement >=95% of 64 Rocket rows.
- Rocket forced aim >=95% of 64 Rocket rows.
- Correct WAIT >=95% of 512 WAIT rows.

These are prospective diagnostic thresholds, not relaxed replacement floors.
Compare final assay with ordinary_v5 and corrected-input R1e using the same
sample/views. Report exact denominators, changes, and training-loss first/last
256-step means. No significance/generalization claim: all rows used in fitting.
Do not reinterpret failed subcriteria or make a best-orientation selection.

Validation requires: 1,024 unique original rows, per-stratum replay uniqueness,
original split membership and label equality, exactly 4,096 finite update logs,
all 524,288 draws/mirror flags, unchanged source bindings, final finite changed
weights, optimizer step counts, all 6,144 cached views, public affordability,
masked choices, both orientations, original labels and per-replay counts.
Run positive and corrupted sample/log/cache controls before accepting validators.
No model inference may occur before independent training verification, except
the excluded preparation backward. No development inference is permitted.
