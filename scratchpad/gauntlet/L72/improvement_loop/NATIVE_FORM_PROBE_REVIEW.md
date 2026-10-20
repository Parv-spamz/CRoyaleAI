# Native form diagnosis and isolated correction

The main data blockage was partly a stale catalog, not missing native evolution
mechanics. The pinned native engine resolves Elite Barbarians as
26000043 / 13000043 / 26000043 across three deployments, while the base control
stays 26000043. Two evolved troops spawn at level 11 with 1341 maximum HP each.
The known Knight control resolves 26000000 / 26000000 / 13000000. The original
catalog incorrectly leaves Elite Barbarians' evolution fields empty and labels
13000043 unknown.

The original compressed `characters/angry_barbarian_evo.toml` contains the
AngryBarbarians_EV1 summon definitions. Top-level `spells_evolved.csv` alone was
misleading because its row is a placeholder. No runtime asset or binary changed.

The isolated `catalog_corrected/native_core` package contains seven byte-identical
Python files. Its catalog changes exactly three Elite Barbarians fields (form
name, native form ID and two-deployment cycle) and increments the evolution
count from 41 to 42. Production/original catalogs and all earlier results remain
unchanged. The validator remains unchanged, including unsupported hero/both-form
rejection. Original deck evolution flags are retained.

`native_elite_form_probe_v5.json` passes all three controls and an additional
Elite Barbarians evolution repeat. The repeat matches command ticks/cards/aims
and resolved IDs. Evolved entities retain native `card_id=13000043` and now have
`base_card_id=26000043`, `card_form=evolution`. This is synthetic form-resolution
evidence, not full-game parity or replay qualification.

Failed attempts remain preserved: v1 selected tile corners and got 60 placement
rejections; v2 fixed placement but ended in a native three-crown win after only
two base casts; v3 used a bounded synthetic opponent and completed all three
arms. v4 completed all four native arms but its final assertion incorrectly
expected the native card ID to become the base ID. The documented schema keeps
these separate; v5 corrects that assertion. No failure was reclassified as pass.

The corrected static preflight checks the same 239,939 immutable groups:
222,362 are now card/form compatible, with 17,577 still rejected for unverified
Void mapping. Of 183 exact-Icebow groups, 173 are now compatible; 11 were already
in the original pilot and 162 are newly eligible. The remaining ten still fail.
All exact-Icebow groups retain their confirmation assignments. The new group
contains 20 Night Witch, 15 Furnace and 3 Witch deck encounters, with overlap
allowed. These are deck/reconstruction candidates, not tactical opportunities.

All 162 new groups are selected in tag order without outcome filtering. Their
12,957 converted source commands and original forms were checked; 17 repeats
are scheduled. The separate collector and independent verifier are running/
queued under `NATIVE_CATALOG_CORRECTION_PLAN.md`. Original 645-pilot evidence is
not overwritten or rerun. Source/runtime drift or repeat mismatch stops this
new batch; missing/rejected/skipped/delayed commands and crown failures exclude
individual records. Initial four-record independent reconciliation passed.

N2 remains open. Actual usable yield, component opportunities and sufficient
power/multiplicity must be established before successor optimization or final
model predictions. Three Witch source encounters already signal a possible
remaining scarcity; do not substitute other decks or lower replacement gates.
No new model, live change or Discord performance report resulted from this work.
