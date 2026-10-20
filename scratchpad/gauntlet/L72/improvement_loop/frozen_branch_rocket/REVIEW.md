# Fixed projectile branch cannot address most remaining Rocket misses

October5 17:33 EDT. R1-R3 complete. Producer90.29s and corrected independent
verifier55.88s exit0/token matched. All54723 rows, four cached models, subgroups,
per-replay counts and955 detailed Rocket records reconcile. Six positive/ten
corruption controls pass. No new predictions, optimizer, simulator or checkpoint.
Preserve the original stopped verifier/nonzero receipt256.28s; the correction
only loads compressed arrays once. See VERIFIER_CORRECTION.md and verified_v2.json.

Primary comparison ordinary_v5 versus frozen_base_projectile_v6:

| Rocket context | Rows / replay groups | Aim successes before / after | Changed cells | Aim gains / losses |
|---|---:|---:|---:|---:|
| All expert Rockets |955 /336|292 /290|15|1 /3|
| No valid projectile target |607 /295|196 /196|0|0 /0|
| One valid target |262 /181|70 /67|10|0 /3|
| Multiple valid targets |86 /74|26 /27|5|1 /0|
| Own targets only |165 /136|41 /39|9|0 /2|
| Enemy targets only |126 /100|40 /39|3|0 /1|
| Mixed sides |57 /51|15 /16|3|1 /0|

The no-target group contains411 of665 remaining aim misses. The module's
mathematically zero residual there and unchanged cached aims show that further
training ONLY this branch cannot repair those examples. Of955 expert aims,
only93 lie inside the union of possible3x3 target-patch support. That is possible
support, not measured feature magnitude, and it is not physical hit geometry.

All15 changed Rocket cells switch patches; six get closer to the expert aim,
nine farther. One aim success is gained and three lost in four distinct replay
groups. The losses coincide with an own X-Bow projectile, an own Log and an enemy
Wizard projectile; the gain has own X-Bow/enemy Bowler projectiles. These sparse
contexts do not establish a card-family effect or justify a handwritten mask.
Two losses move away from the residual's possible support, consistent with
relative patch suppression; this does not identify the actual learned logits.
Full Rocket actions fall77->76, with one loss and no gain. Late forced aim62->61;
late full action stays22/320. Preserve the rejected model verdict.

The narrow near-princess descriptor contains42 ROCKET rows/29 replay groups,
aim5/fullaction2 unchanged; only two expert cells have possible support. The
earlier43-row near-princess total included one other-card PLAY row. Neither
descriptor is all tower opportunities, damage-lead cycling, splash hits or a
physical-impact attribution. One improvement crosses the original one-tile
floating-point boundary (distance1.0000000000001137 to near-zero); keep that
literal definition and continuous distances, do not enlarge the threshold.

Across all36739 no-valid-target states, expert aim, Log aim and action decisions
are unchanged. Across all17192 PLAY rows,252 expert cells change, all between
patches; aim gains49/losses22 and full-action gains32/losses10. WAIT actions stay
unchanged. Primary Barrel has12 gained full actions/no loss (20->32/63), consistent
with the useful component found previously. This is no new gameplay validation.

The source already conditions aim on card/form through query; do not claim this
feature was absent. Choose a separate trainability experiment: keep all encoder
and timing/card parameters frozen while allowing existing global aim query,
cell_key, cell_emb and cell_bias to learn along with the same projectile module.
This is development_iteration_8, starting again from ordinary_v5, with original
data/loss/draws and stronger Rocket materiality requirements. No failed trained
weights, hand-coded card conditions or mixture/loss recipes are combined. Final
untouched/component/gameplay/statistical/Q4/Q5 requirements remain open.
