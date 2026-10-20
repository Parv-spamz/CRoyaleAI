# Sequential setup for the body-and-crown instrument

Registered October 5, 2026, 21:55 EDT, before new collection. This successor fixes
the v3 setup batching defect. V1/v2/v3 remain failed, with original sources and
receipts preserved. No model, optimization, expert/reserved data, native-client
replay or live worker is involved.

Fixed16 roots: firing side0/1, lane0/1, level11/14, body count1/2; nested order
with seeds2026101000..1015. Both decks Rocket/Knight/Giant/Log/Tesla/IceWizard/
Tornado/Xbow, base forms, no shuffle, same declared levels for cards and crowns.
Advance180ticks. Play enemy Knight at x4.5/13.5,y4/28tiles on its own side; with
two bodies, advance ONE tick and play Giant one tile inward horizontally. Each
command is its own native step. Save requested/resolved result and before/after
state before checking success. Verify immediate per-command mana costs, allowing
natural regeneration between ticks. Then advance to absolute tick240. No direct
resource, HP or spawn edits, outcome selection, or resampling.

Six branches from exact root bytes: WAIT/repeatedWAIT/snapshot/forward2/forward4/
sideways6. Use root Knight position and fixed offsets,26tick delay, cast at266.
Forward follows enemy advance, sideways toward other lane. Spell TAP_SNAP is
floor(request/18000)*18000+9000. Troop setup resolved points are saved, not assumed
to follow spell-only snapping when native placement can resolve collisions.

Every tick240..396: all body/crown UIDs, HP, positions, footprint, status, attack
phase, spells/projectiles, crowns/outcome and mana. Save original/final bytes.
Keep v3 isolation and effect definitions: all entities alive/present; attack_phase
explicitly0; ordinary projectiles absent; only own one Rocket spell; no friendly
effect; WAIT HP unchanged; WAIT traces/finalbytes exact. Troops move in WAIT.
Incremental effects WAIT.hp-cast.hp nonnegative/nondecreasing, last10frames flat;
no active spell at end. Body-only/crown-only/both/no-damage separately counted.

Require16roots/96branches/15072frames,64accepted6elixircasts, body-hit positive,
all-entity miss positive, and two-body-hit positive. Do not change scope or offsets
after results. Failure preserves artifacts, not a parameter search. Independent
stdlib-only verifier checks membership/source/raw hashes, all setup commands,
costs, exact ticks/entities/curves and corruption controls. Outer closeout binds
receipts. No successful earlier fixture is repeated.

This qualifies a fixed synthetic measurement instrument only. Full native states
and opponent mana are outcome instrumentation, never future model inputs/teacher
features. Real-client parity, representative tactical value, safe cycling and
model improvement remain unproved. A public-only learnability comparison still
requires its own preregistered split, inputs, control, budget and decision rule.
No acceptance floor changes. Tuesday04Z cutoff unchanged.
