# Frozen decomposition

Use unchanged original gate>0.35 with any affordable slot, cached masked-card
argmax, and expert-forced cell distance<=1 tile. Normalized cell x=(cell%36)/36,
y=(cell//36)/64; original expert xy; tile scaling18,32. Do not round distance,
move thresholds or substitute y_cell for original expert xy. Aim is not a hit.

For each original expert PLAY row retain all three bits: fired (4), correct
affordable expert card (2), expert-forced aim within1tile (1). State7 is a full
correct PLAY; all other states are errors. WAIT rows are separate states8(correct
WAIT) and9(incorrect fire). Retain full10x10 control-to-candidate transitions,
not a single ordered failure label that hides simultaneous changes. R1e uses
the same corrected observations; primary comparator is ordinary_v5.

For all models report rows/PLAY/WAIT, called, correct card on PLAY, forced aim on
PLAY, full action, correct PLAY and correct WAIT. For candidate versus each
control report action gained/lost, PLAY gains/losses, WAIT gains/losses, changed
fire decision, changed chosen card, changed expert cell, aim gained/lost, and the
full state transition table. Preserve per-replay numerators and tables. Check
delta(action)=delta(correct PLAY)+delta(correct WAIT) exactly.

Fixed groups: all, rocket, rocket_late_overtime_clock, barrel_pro, witch,
night_witch, furnace, defensive_sequence, phase_late_overtime_clock, plus original
PLAY/WAIT partitions and every observed original expert PLAY card identity. Keep
empty groups as zero, never drop failures. Group membership and denominators are
not independent tactical opportunities. No significance or physical-benefit claim.

For ALL955 expert Rocket rows (not only changed ones), retain ID/replay/side/tick,
original card/xy, affordable-slot mask/hand identities, each model's gate
probability, chosen card, forced expert cell, continuous distance and state.
Log the primary pair's fire/card/aim change bits and gained/lost/unchanged action.
Do not infer aim for nonexpert Rocket choices: the cache lacks those cell logits.

Eight hybrid Boolean counts additionally swap control/candidate fire/card/aim
bits in all combinations (bit4/2/1 respectively). WAIT uses fire only. These
are an arithmetic decomposition of cached heads, NOT valid new policies, model
inference, counterfactual native games, or an argument to deploy head mixtures.

Reconcile unchanged action/called/card/aim totals with the already verified
results. This is a new decomposition, not a rerun of original model evaluation.
Independent checker reads original labels and caches, does not import producer
metric functions, and independently validates all955 detail records and all
group/per-replay outputs. No model acceptance thresholds are added or removed.
