# Spawner defence: measured cause and implementation plan

This proposal is recorded before implementation. The owner authorizes proceeding without waiting for review.

## Evidence

`audit.json` scans the2,262 Icebow pro replay sources already verified for the Rocket curriculum, plus21 historical live logs containing frames. It uses exact catalog maximum-HP matches to distinguish parent bodies from child bodies; unmatched cases remain unknown.

| Card | Pro replays | Identified child bodies | Children currently labelled as the parent |
|---|---:|---:|---:|
| Witch |133|4,643|4,643|
| Furnace |127|2,743|2,743|
| Night Witch |92|2,488|2,488|
| Goblin Hut |104|1,209|1,209|
| Barbarian Hut |1|54|54|
| Tombstone |165|8,521|8,521|

Saved live opponent bodies confirm279 Witch skeletons in4 matches and18 Goblin Hut spear goblins in1 match are encoded as their parent. There were no saved Furnace examples in these live logs; that is missing coverage, not evidence Furnace works correctly.

The unit input has class, position and **HP fraction**, but no absolute maximum HP. A healthy81-HP Witch skeleton and a healthy839-HP Witch both enter the model with class=witch and hp_fraction=1. The native card ID identifies the card that created the body. Existing `vocab.engine_unit_id` disambiguates Golem and several other child bodies but omits these periodic spawners. Child bodies also inherit parent form IDs in the native data.

`sim_identity_probe.json` supplies a controlled simulator witness: one Witch produces12 skeletons labelled Witch, at ticks130/270/410 (140-tick wave gaps). One Furnace produces FireSpirits labelled correctly in the simulator, while the native recordings label them Furnace. That establishes an additional SIM/native representation mismatch for Furnace.

Held-out R1e pro-card agreement: Witch60.75%(n186), Furnace65.73%(n213), no observed spawner64.60%(n10822). These associations do not prove the bug's effect on wins. They also do not establish that future-wave prediction is the only remaining defence problem.

## Proposed correction

1. Add a catalog-derived body resolver using public parent identity, observed maximum HP, form and the catalog's child relationships/level tables. Preserve the parent when evidence is ambiguous. Do not add tactical card-choice rules, query hidden opponent state, charge elixir for spawned children or invent future units.
2. Use the same opt-in corrected body contract in dataset construction, SIM and live. Distinguish ordinary child forms from parent evolutions/heroes. Old checkpoints/default decisions retain their current contract. A new checkpoint must explicitly identify the corrected contract.
3. Reconstruct affected public training rows against native source frames, prove the original rows reproduce before patching, and retain expert targets and split membership. Measure the correction on held-out rows and train under the same bounded recipe/control, so old weights are not silently claimed to understand a changed input distribution.
4. Verify catalogue boundaries/unknowns, repeated waves, native/SIM/live parity, legacy default parity and actual model loading. Run same-code ghost/reactive/behaviour comparisons before adoption. Only then enable the corrected contract in the authorized deployment.
5. After identities are correct, measure whether wave timing still causes mistakes. Inspect unit-age availability and observed parent/wave history before proposing new time-to-spawn inputs. Position extrapolation deliberately does not invent unobserved births; keep that boundary.

Implementation is prepared separately while Q3's existing source snapshot is running. Do not mutate the modules used by that active acceptance chain.

## Prototype evidence, October5 00:05

Night Witch is explicitly in scope per the owner's amendment. `prototype_checks.json` records13 passing tests and a controlled SIM probe with12 Witch skeletons,9 Night Witch bats and4 Furnace spirits across repeated waves. The derived catalog/native Furnace child maximum is217 at level11; SIM's explicitly named FireSpirits body has215. Explicit child names remain recognisable without guessing a parent threshold.

The eight-replay smoke reconstructs850 original affected rows exactly, then changes550 rows/1,192 class tokens/209 forms. `verify_dataset.py` independently confirms all other archive members, labels and splits are unchanged. This smoke artifact has `trainable=false`. The full version5 reconstruction is separate and must verify484,437 affected rows; it is not a trained checkpoint.

The existing `body_only_board` already masks age/deployment in dataset, SIM and live v4. The earlier sparse age sample therefore indicates the intended shared contract, not an additional live age bug. No age-channel change is included without further evidence.
