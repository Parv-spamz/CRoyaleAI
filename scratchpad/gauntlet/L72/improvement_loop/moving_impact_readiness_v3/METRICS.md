# Frozen all-entity effect definitions

Units:16 synthetic roots,96 paired branches; not independent games. Every branch
has157 contiguous frames at240..396. UIDs,team,kind,card,maxHP,level and six crown
slots remain exact; all HP positive, no missing/dead-object substitution. Troops
move in WAIT; crowns retain exact position/footprint. Both WAIT curves and final
bytes match exactly, no WAIT HP changes or spells/projectiles.

For every UID and tick, incremental effect = WAIT.hp - Rocketbranch.hp. Curves
nonnegative/nondecreasing, final10frames flat; no friendly effect. Enemy crown
effects are explicitly retained, never discarded as collateral or called body
damage. Record firstpositive tick/final delta/curvehash, bodies_damaged and
crowns_damaged. Classify cast as no_damage/body_only/crown_only/body_and_crown.
Track casts damaging two bodies separately. No total-HP tactical value function.

Isolation: all native attack_phase==0, no ordinary projectile at any tick, only
the one ownRocket spell may exist after266, none at end. These constraints plus
unchanged WAIT HP isolate the single spell in this declared scope. King activation
or knockback may change statuses/positions and are preserved, not hidden.

Requested spell points derive only from rootKnight coordinates and fixed offsets;
resolvednativepoints use documented TAP_SNAP tile centers. Charge actual immediate
mana decrease at266; setup costs at180. Native inputlevels/forms/decks/seeds and
all raw bytes/JSON/source files are bound. Independent controls: baseline plus
missing/duplicate entities/frames/arms, changed HP/card/team/cost/status/aim/tick,
repeatbytehash, ordinaryprojectile/nonidleattack and mistaken crown-damage label.

No acceptance rate/CI, strategic benefit, safe cycle, new expert label or policy
training. Numerical entity/cost/time equality is exact; no new tolerance.
