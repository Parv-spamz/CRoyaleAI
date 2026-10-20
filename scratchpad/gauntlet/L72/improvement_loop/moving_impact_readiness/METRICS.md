# Frozen moving impact measurements

Unit is one synthetic root and its six branches, not independent games.
Exact ticks240..446 inclusive:26ticks command delay plus180post-arrivalticks.
Track entities by exact UID and unchanged team/kind/card_id/max_hp. Require six
unique crown slots and the exact one/two original troop identities throughout.
No vanished-object inference. Coordinates and HP are integer native units.
One tile is18000 native units. Record target/attack phase as observation where
reported, not inferred from geometry. Record complete spell/projectile fields.

For each troop/tower/tick, effect = WAIT.hp - branch.hp. Keep per-object curves,
first positive effect tick, final effect, and total bodies affected. Require
WAIT HP unchanged and all crown HP unchanged in all branches; only the injected
Rocket can inflict damage in the accepted isolated scope. Effects nonnegative,
nondecreasing and stable for final10frames; no active spells/projectiles at end.
Troop motion is root-to-final squared displacement in WAIT, plus full trajectories;
the root position is used for fixed fixture aims, never future target position.
Sideways and forward offsets are categorical fixture arms, not tuned thresholds.

Record actual resolved command status/card/tick/aim and immediate mana charge;
do not infer cost from later mana differences. Repeated WAIT must have exact
entity/spell/projectile/player frames and final serialized engine bytes. All
original setup commands/levels/forms/seeds bound. Independent corruption controls
cover membership, missing frame/body, reused UID/wrong card/team, altered HP,
command delay/aim/refusal/cost, repeated final hash, and reported effect.

Synthetic hit/miss/multi-hit controls qualify observation only. No success rate,
confidence interval, policy choice, safe-cycle or live-client benefit is claimed.
