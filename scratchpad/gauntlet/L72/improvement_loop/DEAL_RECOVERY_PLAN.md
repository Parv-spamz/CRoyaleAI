# Native opening-hand recovery, October 5

Evidence: all three excluded fresh exact-Icebow/Witch records use the driver's
documented canonical-order fallback after one side's deal-position probe fails.
Training pilot records independently contain the same condition: 13 of 209,
all excluded. The fallback can also discard a valid arrangement for the other
side. This is reconstruction failure, not evidence about model skill.

D1: Audit all 183 unused exact-Icebow metadata groups for actual opposing Barrel
and Witch decks, and all 807 existing collection records for fallback status,
first rejection and source/command provenance. No native execution or policy
predictions. Original splits and exclusions remain unchanged.

D2: Implement an isolated generic opening-deal resolver, without changing the
original replay driver, native package, engine, source commands or catalog. Use
only original per-side card sequences, the existing enumerated legal initial
hand/queue assignments and native tick-zero hand/cycle positions. Deterministically
try measured deck permutations, preserving each card's original form/level. No
card-specific rule. Permit at most 64 native reset probes per replay; record all
attempts and fail closed if no arrangement supports both original sequences.
Never choose based on crowns, eventual win, damage or model output. Do not set
hands, force accepted plays, delay/skip commands, or change the random seed.

Construct the isolated driver from the hash-bound original with exactly the
fallback block replaced and a final tick-zero deal verification inserted. Reuse
the original entire command-driving/recording/grading path. Verify the patch
surface and reject source drift. Synthetic controls must cover coupled side
positions, repeated permutations, unachievable deals, changed forms and bounded
failure. A native candidate is not usable merely because its opening is legal.

D3: Before any fresh-confirmation recovery, test all 13 training fallback cases
in original tag order and three previously usable training controls in tag order.
Repeat every case. Use unchanged full command/public-field/crown/termination and
determinism checks; preserve every failure. Require all selected original usable
controls to retain their original log/grade/final and canonical public frames.
Independently recount logs against immutable CSVs and verify opening/queue
consistency. Record reset budgets and hashes. No confirmation retry or training
is authorized by this leaf alone: separately freeze a recovery batch only after
reviewing these training controls and implementation evidence.

All old collections remain immutable. A successful repair permits a separately
identified reconstruction attempt; it never retroactively waives an old failure.
N2 still needs adequate exact-deck cohorts, opportunity denominators and frozen
power/multiplicity/design. No successor model or Discord model report here.
