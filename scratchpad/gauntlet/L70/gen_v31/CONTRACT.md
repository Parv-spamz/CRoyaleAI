# gen_v3.1 public observation contract

New checkpoints use integer `feature_version=4` to distinguish their input shape from gen_v3 (`3`). Existing versions keep their existing paths. Live deployment is owner-only.

October 3 20:32 amendment reconciliation: the joint learned weighting must cover tower Rockets, X-Bow lane
selection, and defensive-X-Bow/Rocket-cycle contexts. The existing loss-only `rocket_context_probability`
field is retained for compatibility, but version4 preflight now requires all three context targets in its
evidence metadata. This is not a fitted classifier or a new action rule. The acceptance reporter now lists
the three X-Bow metrics as UNMEASURED alongside the five earlier missing behaviour metrics. Existing dated
reports are preserved; subsequent reports use the amended eight-metric coverage list.

October 3 21:48 reconciliation of brief commit f2075ab: additionally require defensive-Rocket,
Rocket-then-Tornado and Tornado-then-Rocket targets in the SAME loss-weight evidence. No prescribed
ordering, timing rule or preference is selected. Subsequent coverage lists11 missing behaviour metrics;
the dated8-metric reports remain preserved and are superseded only in coverage by the new amendment.
Cast-order/window/proximity proxies do not establish pulls, confirmed hits or actual elixir value hit.

October 3 15:35 source correction: native bridge `effects` is the generic nonunit list, including projectiles;
actual spell areas are in `area_effects` (jni_bridge.cpp:2099). The current re-driver discards `area_effects`.
Version 4 therefore ignores native generic `effects`, reads only explicitly recorded `area_effects`, and records
missing area coverage as `native_area_effects_unavailable`. Full training rejects it. This corrects the earlier
assumption in this contract that the native `effects` array represented spell areas. Reader v2 `effects` remains
its validated area export. No bridge, live binary, ongoing re-drive or training process was changed.

Projectile timing remains explicitly unknown where the source omits it. Position/identity adapter tests pass,
but complete semantic train/SIM/live timing and area-effect parity is NOT established by synthetic tests.

Exact body forms come from native form IDs in explicitly marked native recordings, and the same catalog IDs in reader v2. Stable body IDs retain identities. Simulation uses observed entity status flags because its card IDs have a different namespace.

Opponent history is detected from visible bodies plus spell projectiles/effects. No replay command, final opponent deck, opponent hand, next card, elixir, or deck form slot is a history input. All adapters normalize to the common observable fields. Spell identity comes from the public card catalog; troop attack projectiles are excluded. With no projectile/effect IDs in recordings, deduplication must use the same conservative temporal rules on both sides. Repeated/overlapping same-card casts can be missed; this remains a detector limitation, not hidden truth correction.

`opp_past` retains the three newest detected plays strictly before the row tick, with observed form and first-sighting location. `opp_cycle` contains up to eight most recently observed distinct cards, newest first: card, last observed form, count of subsequent detected opponent plays, seconds since last detection. Unknown cards remain padding. Counts are observations, NOT proof of card availability; missed plays, simultaneous detections, Mirror and champion cycles prevent exact hidden-hand reconstruction. No opponent evo slot is inferred.

Only public observations at or before a feature row can affect it. Side orientation and own past remain the existing contract. Training/replay and live share one detector implementation; tests cover representations, privacy mutations, repeated frames, reset, multi-object spells and projectile-to-effect/body transitions. A synthetic parity test is necessary but insufficient: a real sample and simulated acceptance path must also be checked before full training.

Replay history uses the recorded board-frame stream, excluding `play_frames` and replay commands. The re-driver normally samples in 20-tick chunks but splits a chunk at a command, so this is an irregular cadence and differs from live's faster reader. Parity means the same features for equivalent observation streams, not identical detection recall at different sampling rates.

The two opponent-elixir scalars are explicitly replaced with the shared public counter for version 4. Generic engine/dataset rows carry opponent truth in older versions; those historical training inputs need a separate owner/lead audit. The current live counter/checkpoint is not changed.

Board tokens consistently use bodies only, with deployment and body age unknown in all version-4 adapters. Full-recording waits would otherwise carry effect/deployment fields that PLAY rows lose in `_as_compact`, reintroducing the historical row-format gate shortcut. The shared history still sees spell projectiles and effects. New buff/ability/deploy fields remain outside the model pending reader validation and the owner's public-observability decisions.
