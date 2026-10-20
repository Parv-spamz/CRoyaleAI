# Frozen descriptive measurements

Membership: all original development indices, 54723 rows/405 replay groups;
17192 PLAY and 37531 WAIT. Original eight labels are y_gate,y_card,y_hand_pos,
y_xy,y_wait_card,y_wait_dt,y_crowns,y_cell. Join by exact original row ID.
Primary expert Rocket mask: PLAY and original card=rocket; keep all955 rows.
Retain original Barrel primary mask and all 56 phase/past-context masks, plus
all-card PLAY and WAIT, for denominator and unchanged-output controls.

Valid projectile targets use the current model definition exactly: positive card
ID, finite x/y, both in[0,1]. Preserve invalid/unknown real objects separately.
Describe count 0/1/2plus, own-only/enemy-only/mixed (side0/1), and each observed
projectile card identity. Identity strata can overlap and do not sum to total.
Coordinates remain the public normalized observer orientation, no new transform.

Target scatter is floor(x*9),floor(y*16), clamped to[0,8]x[0,15]. The depthwise
3x3 residual can affect that patch and its eight neighbors, clipped at the board.
Support is the union for valid targets. This is POSSIBLE spatial support, not
measured residual magnitude. Full lattice cells are36x64, patch=(xcell//4,
ycell//4). Preserve whether expert cell, baseline argmax and candidate argmax
lie inside support, including NONE. A move toward a projectile target is not
necessarily useful aim. Do not treat unsupported cells as illegal.

Expert lattice target is round(x*36),round(y*64), clamped. Forced aim<=1 tile uses
Euclidean distance with x*18/y*32. Full action retains gate>.35, affordability,
correct original card and aim<=1; WAIT full action is no fired play. No threshold
changes. Count exact-cell changes, same/different-patch changes, continuous
expert-distance improvement/worsening/ties, aim success gained/lost, full action
gained/lost and per-replay count differences. Gate/card decisions retain their
original numeric differences and independently verified unchanged choices.

Cross primary Rocket transitions (better/worse/both-right/both-wrong) with
target count/side/identity, existing late-clock and narrow near-princess
descriptor, and possible support for expert/baseline/candidate targets.
Near-princess remains alive enemy slots4/5 within1tile of original expert aim,
using anchors(3.5,6.5),(14.5,6.5). It is NOT all tower opportunities or physical
hit attribution. Clock is not an explicit measured elixir multiplier.

All Rocket rows get a detailed original-label/cache/context record; other rows
remain in full counts. Include every regression and improvement, never select
success examples only. Repeated rows are not independent samples; report whole
replay paired counts, no significance/power/gameplay claim. No new inference.
