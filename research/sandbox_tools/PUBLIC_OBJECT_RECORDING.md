# Public object evidence capture

Status 2026-10-03: **offline verified, engine untested**. This prepares source validation; it does not fix the
already-running VM corpus or complete gen_v3.1 input parity. No remote file, service, live reader, experiment
recipe, or running process was changed. Any additional paid re-drive remains an owner decision in BLOCKERS.

`replay_drive.py` and `replay_batch.py` now accept `--record-public-objects`, default off. It requires
`--record-full --record-native --record-every N` with positive N. Existing default snapshot serialization is
identical to HEAD in all four full/native combinations, including play frames. The batch's determinism rerun
still omits recording; recording does not change its command timeline.

The option adds `public_objects` to each saved board/play frame and an output schema marker. The existing
`projectiles` and generic `effects` fields remain unchanged. The new evidence object retains:

- Projectile side/card/position/target coordinates, object ID and generation key.
- **Separate** area-effect side/card/position, ID and category.
- Area `source_elapsed_ms`, `source_life_ms` and `source_remaining_ms`, labelled
  `UNVALIDATED_NOT_MODEL_INPUT`. They are raw source assertions, not verified elapsed/lifetime semantics.
- Missing export as `null`; a present empty export as `[]`. Generic effects never substitute for actual areas.

The allowlist excludes both player blocks, hand/next/elixir/deck forms, projectile source/target entity pointers,
owner slots, damage internals and ability state. Object identity supports offline tracking, not an embedding.
The existing full replay format still contains private replay-engine fields elsewhere; only the versioned
public adapter may supply model inputs. This option does not declare the entire recording public.

No consumer treats the evidence timers as validated model timing. The required next checks are matching this
build's observed area timer progression against independent visible expiration, measuring projectile impact
events at adequate sampling cadence, and establishing semantic parity with reader v2 and SIM. The current
one-second native sample intervals cannot validate a half-second landing metric. The cadence and scope of a
new paid capture must be approved by the owner; do not silently resume or overwrite the six `_abil` corpora.

Verification: `runs/1552_recorder_tests.out` under `.foreman/codex_autopilot`:26 tests passed, including six new
public-source/CLI/default-parity tests and20 existing replay ability/dataset tests. The initial test-only fixture
mistakenly replaced player rows and failed; corrected before the successful run. No engine parity is claimed.
