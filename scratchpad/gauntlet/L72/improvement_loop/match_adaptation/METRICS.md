# Frozen descriptive metrics, October 5 14:43 EDT

No selection by outcome, prediction, low HP, cast Rocket or successful X-Bow.
All 268718 fixed inner rows remain: 213995 training and 54723 development.
Preparation binds sorted IDs, original labels, native sources, existing labels
and three already-verified development prediction caches. No model/optimizer.

Row joins: original PLAY uses its unique accepted non-ability command matched
by side/tick/card/normalized aim and its play_index pre-play frame. WAIT uses
the exact compact frame tick. Reject ambiguous joins; never use a later frame.
Compare joined tower fractions against original scalar slots where known. Raw
native king HP is an outcome annotation, not newly authorized policy input.

Clock spans in ticks at 20 Hz: [0,2400), [2400,3600), [3600,4800), [4800,infinity).
Name these single-clock, double-regulation-clock, early-overtime-clock and late-
overtime-clock. They follow the existing adapter/pinned calibration's normal
rules. Historical frames do not explicitly record elixir multiplier/game mode;
keep observed_multiplier unknown. Do not claim measured 1x/2x/3x from clock alone.

Require six explicit crown-tower entries (side/type/lane), finite HP/max HP,
positive maxima and no duplicates. Ordinary buildings never count. Standing
means HP>0. Crown score is opposing princess losses, or three if opposing king
is down. Report crowns separately. Raw margin=min(own standing crown HP)-
min(enemy standing crown HP); exact sign ahead/equal/behind, no tuned band.
Missing/terminal sides are unknown. Also retain princess-only raw and crown
fraction minima separately. High enemy-princess HP means all standing enemy
princess towers exceed1500 HP, a descriptive cut inherited from the owner audit,
not a target, damage forecast or Rocket condition.

Public revealed cards: accepted opposing non-ability commands strictly BEFORE
the row tick. Their identities are observed history; neither future full deck
nor hidden resources enter history. Same-tick events are excluded conservatively.
Describe Barrel/Witch/Night Witch/Furnace encounters using these revealed names.

Prior offensive placement uses the already-calibrated historical X-Bow label;
it is attack-capable geometry, NOT an observed lock. Native compact entities have
nine columns without target/attack state and projectile objects lack shooter
identity; direct hit events are null. Lock and attributed X-Bow damage therefore
stay UNKNOWN in this corpus, even when towers lose HP. No geometric proxy may
be renamed blocked/successful lock.

For a causal lifetime proxy, link an offensive command to exactly one newly
appearing native Xbow entity of the same side and EXACT recorded placement,
within10 ticks after casting. Use entity ID and contiguous lifetime generation;
missing IDs, gaps>10 ticks, ambiguous births or missing end stay unknown. A
disappearance becomes known only after the first absent frame, strictly before
the decision. Label the most recent prior offensive bow as none, ongoing,
ended_enemy_princess_hp_drop, ended_no_enemy_princess_hp_drop or unknown. HP drop
is concurrent observational damage from any source. It is not a lock label.
No use of eventual end/drop until observed. Count all prior offensive commands
as0/1/2plus independently of outcome linkage.

At10/30/60 seconds (30 primary), find the latest compact frame at/before the
endpoint, within10 ticks, with no intervening compact gaps>10. Retain missing/
terminal truncation as unknown; do not shorten to terminal and call it full.
Include accepted command costs on [decision_tick, endpoint_tick], including
abilities and the initial action. Any missing cost makes both spending totals
unknown. Retain own remaining elixir, each side's left/right princess HP drop,
raw crown margin change, crowns and terminal outcome/source crown-match flag.
These are expert-trajectory associations, not policy counterfactuals or exact
Rocket damage. Terminal winner is recorded, tiebreak cause is unknown without
an explicit reason; a late terminal tick alone is not proof of a tiebreak.

Aggregate by split and clock; clock×equal-crowns×margin sign; clock×last-bow
proxy; prior count; revealed family; high-princess-HP status. Keep per-replay
numerators/denominators for comparisons. Expert PLAY/WAIT/Rocket/X-Bow and native
grade mismatch groups all retained. Reuse cached R1e, ordinary_v5 and ordinary_v6
development gate/card/full-action flags with the original .35/one-tile definition.
No model tower-target logits are cached for nonexpert Rocket choices: count such
choices, but do not invent their aim or useful-impact outcome. No significance,
causal or acceptance claim from repeated rows. No training threshold selected here.
