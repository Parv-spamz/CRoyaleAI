# Training-only projectile-target residual diagnosis

Hold all checkpoint weights fixed. Compare the existing v5_rocket_barrel control,
v6_rocket_barrel, and v6_rocket_both on identical corrected-body training rows.
For each v6 checkpoint also measure its own residual-disabled encoding. The only
intervention skips target_patches addition to encoded patch tokens; pooled public
projectiles, global token, heads, weights and all other inputs remain unchanged.
This is a representation diagnosis, not a newly trained or deployable model.

Before any predictions, select only split0 rows in the original Icebow pool.
Use seed20261005 and at most200 replays per stratum, one random row per replay:
(1) one unambiguous enemy Barrel, affordable Log, expert same-lane Log;
(2) the same public single-Barrel condition but another expert PLAY;
(3) the same condition with expert WAIT;
(4) multiple enemy Barrels;
(5) enemy Barrel present but not an unambiguous single own-half lane target;
(6) no enemy Barrel but at least one valid public projectile target;
(7) no valid public projectile targets.
Unambiguous means target coordinates finite, x in[0,0.4)or(0.6,1], y in[0.5,1].
Keep all expert labels and actual input objects. Strata can overlap; report exact
membership and union. No final-confirmation or held-out policy inference.

Use CPU with one Torch thread and batches64. Record full teacher-forced expert
and Log aim logits, gate, legal card choice, raw labels/targets and source hashes
in ignored data. Report each stratum's forced-Log lane agreement, gated correct/
wrong-lane fired Logs on the qualified expert-Log stratum, PLAY aim agreement
within1tile, joint action agreement and paired flips. Report residual magnitude.
Unknown/no-valid-target rows must produce exactly zero residual, and gate/card
outputs must be exactly unchanged by the residual-only intervention. Retain
unknown/multiple cases without pretending their target lane is established.

Independently recount membership/split/source labels, argmax from cached logits,
all metrics and paired transitions. Deliberately corrupted memberships, logits,
gate/card invariance and reported counts must fail the verifier against a passing
fixture. Never tune thresholds or repeat selection after results. Changes between
different checkpoints also reflect different learned weights and mixtures; the
within-checkpoint ablation isolates only the inference contribution of this term.
No optimizer, checkpoint output, source/runtime/live edit or policy adoption.
N2-N7 and all fresh-cohort/statistical acceptance requirements remain open.
