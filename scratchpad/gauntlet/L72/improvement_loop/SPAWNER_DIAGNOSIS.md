# Training-only spawner diagnosis

Before reading new predictions, select at most200 PLAY and200 WAIT examples per
Witch, Night Witch and Furnace from split0 Icebow context rows. Use seed20261005,
one random row per replay per family/gate stratum. Families are defined from
original enemy tokens, keeping membership fixed across observation versions.
The original family can include misidentified children; report whether the
corrected observation retains a parent or contains only corrected children.

Compare R1e original observations, R1e corrected observations (zero adaptation),
v4 ordinary IL, v5 ordinary IL, v4 Rocket IL and v5 Rocket IL on identical rows.
Separate gate, card, expert-forced aim within1 tile and joint action agreement.
Preserve WAIT failures separately. Record actual changed tokens, expected
exposure under original mixtures, source/checkpoint hashes and raw predictions.
No optimizer, held-out rows, tactical rules or new model selection are involved.
These are failure diagnostics, not acceptance or generalization evidence.

## Result

Completed618 rows: one PLAY and one WAIT from each of113 Witch,80 Night Witch
and116 Furnace training replays. Six conditions use identical rows. An independent
recount verifies source labels/splits, all stage counts and paired action flips.

| Condition | Witch PLAY / WAIT correct | Night Witch PLAY / WAIT correct | Furnace PLAY / WAIT correct |
|---|---:|---:|---:|
| R1e original |17/113;73/113|11/80;60/80|18/116;83/116|
| R1e corrected, no adaptation |15/113;73/113|8/80;56/80|18/116;82/116|
| v4 ordinary IL |23/113;73/113|12/80;63/80|15/116;87/116|
| v5 ordinary IL |21/113;72/113|12/80;60/80|16/116;85/116|
| v4 Rocket IL |20/113;73/113|10/80;62/80|12/116;86/116|
| v5 Rocket IL |22/113;73/113|9/80;60/80|13/116;85/116|

PLAY means gated correct card and expert-forced aim within1 tile; WAIT means
no affordable play is called. These strata have equal PLAY/WAIT sampling and must not
be presented as population win rates. Corrected parent bodies remain present
in88/113 Witch,73/80 Night Witch and115/116 Furnace PLAY rows, so this is not
merely a test of isolated child tokens.

The correction creates a measurable adaptation problem, especially for Night
Witch. Ordinary v5 IL recovers some of the zero-adaptation loss but does not
beat its v4 ordinary control. The Rocket mixture also changes other decisions:
Furnace card agreement drops83->73/116 in v4 and81->74/116 in v5 versus their
ordinary controls. This occurs despite expected Furnace exposure rising from
3,218 to4,892 draws; reduced raw spawner sampling is not the explanation.
Expected draws are mixture probabilities times128,000, not logged realized draws.

Aim is another bottleneck: v5 ordinary IL's expert-forced within1-tile counts
are39/113 Witch,23/80 Night Witch and36/116 Furnace, while the corresponding
gates pass91/113,64/80 and97/116. More frequent casting is therefore not a
sufficient fix. Do not turn these results into manual response rules.

Next controlled experiments should isolate adaptation to corrected bodies from
Rocket exposure, and isolate the generic projectile-target residual from both.
Any recipe/architecture change needs the L72 preregistration and data gates first.
No successor optimization or held-out tuning occurred in this diagnosis.
Evidence: train_spawner_diagnosis.json, train_spawner_predictions.npz,
discovery_diagnosis_verified.json and integration/checks/l72-training-spawner-diagnosis.*
and l72-discovery-diagnosis-recount.*.
