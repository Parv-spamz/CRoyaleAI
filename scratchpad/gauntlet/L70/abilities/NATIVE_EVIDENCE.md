# Native ability evidence — October 3, 2026

MEASURED across all 14,661 unique, source-verified native replay tags:

| Logged ability event | Count |
|---|---:|
| All events |45,040|
| Accepted activations |40,496|
| Explicit rejections |4|
| Skipped intents |4,540|
| Accepted activations with a native controller entity ID |40,496|
| Accepted activations with that living controller in a fresh recorded frame |40,496|

Coverage requires the correct side and entity ID in the latest frame at or before the event,
no more than 20 ticks old. All same-tick observations must agree. Future sightings, a different
side, and conflicting controller observations cannot establish coverage. Three tests cover
these cases, rejection/skip accounting and invariance to private fields.

The 24 attributed ability names all have accepted activations. A separate `unattributed` category
contains 2,731 skipped intents. Raw recorder names are preserved rather than silently mapped onto
trained model labels. Per-ability counts, refusal/skip reasons, native controller card IDs and
first-observed ages are in `native_evidence_1903/report.json`.

This resolves controller-frame coverage for accepted activations in this corpus. It does not
establish the eligible-lifetime denominator, ability readiness, original-human-match fidelity,
or exact deployment-to-press delay. Age since first observed alive is labelled separately and
is not substituted for the phase-1 delay target. No model was fitted, wired or deployed by this
audit. The existing share/delay calibration decision and R1e prerequisites remain open.

Every input replay was checked against the completed Rocket audit's source manifest before it
was parsed. The audit used below-normal priority, one process and a 50ms pause per replay, after
the Barrel audit finished. Evidence log: `.foreman/codex_autopilot/runs/native_ability_1903.out`.
