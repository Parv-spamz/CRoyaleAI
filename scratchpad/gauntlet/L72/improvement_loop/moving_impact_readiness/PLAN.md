# Moving-body impact instrument

Registered October 5, 2026, 21:30 EDT, before collection. Extend the qualified
stationary crown instrument to moving bodies and multiple targets. This is a
model-free engineering test, not training, expert labels, or policy acceptance.
The previous stationary fixtures and all completed model jobs remain untouched.

Freeze sixteen synthetic roots: firing side 0/1, lane left/right, card/tower
level 11/14, and opponent body set Knight / Knight+Giant. Both decks contain
Rocket, Knight, Giant, Log, Tesla, IceWizard, Tornado, Xbow in that order, base
forms, no shuffle. Seeds 2026100700..715 in side/lane/level/body-count order.
Advance from reset to tick180; deploy opposing Knight at x4.5/13.5 tiles and
y4/28 tiles on its own half. For the two-body fixture also deploy Giant one
tile inward horizontally at the same y. Save command results and actual costs.
Advance60ticks to root240, allowing the troops to move naturally. No direct
entity creation, HP/elixir modification, resampling or outcome-based selection.

Each exact serialized root has six branches: WAIT, repeated WAIT, Rocket at
the Knight's root position, two/four tiles farther along its forward direction,
and six tiles sideways toward the other lane. Fixture positions are controls,
not a proposed policy rule, learned label or reward. Commands arrive26ticks
after root; record every tick from root through180ticks after arrival. No other
actions/abilities. Preserve all entities, spell/projectile objects, crowns,
mana, accepted commands and root/final bytes. No model input or policy exists.

Require bodies to stay present throughout this nonlethal isolated assay; missing
or dead objects cause a failure rather than silently counting their HP as zero.
WAIT bodies must move, keep full HP, and cause no crown HP change. Accepted
Rocket cost must equal the catalog cost immediately. Attribute body damage only
through paired per-UID HP difference in these isolated no-combat scenes. Preserve
movement/knockback differences; equality after damage is not required. Both
WAIT branches must match exactly. A positive body-hit control and miss control
are required, and at least one two-body branch must damage both bodies before
multiple-target measurement can be called qualified. Arm outcomes are descriptive;
do not choose or change offsets after seeing results.

M1 collect96branches once under pinned updated MAIN runtime with source hashes.
M2 separately verify raw frames, complete membership, identities, commands/costs,
effect curves, no-combat controls, duplicate traces/bytes and corruption tests.
M3 bind receipts and report what qualified and what did not. No emulator replay,
existing expert/confirmation data, model prediction, optimizer or live change.
No Discord model report is due. Native-client parity and useful tactical value
remain unproved. Any future joint-targeting learnability run needs a separate
prospective contract; this instrument does not waive any prior floor or verdict.
