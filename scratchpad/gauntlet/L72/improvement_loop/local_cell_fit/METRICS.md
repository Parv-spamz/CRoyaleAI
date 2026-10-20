# Prospective local-cell fit criteria

Use exactly the original small_set_fit scoring: public affordable masked card
argmax, gate>.35, original floor grid36x64 on18x32tiles, forced expert aim<=1tile,
fullPLAY=gate/card/aim. Each orientation has512PLAY,512WAIT,64ofeach8cards and
21lateRocket examples. Original labels/membership remain fixed.

Both native AND mirrored orientations must pass:
- Full PLAY >=90% of512.
- Rocket forced aim >=95% of64.
- Rocket card >=95% of64.
- Correct WAIT >=95% of512.
- All-card agreement must retain matched control512/512.
- Correct WAIT must retain matched control512/512.

This is a diagnostic mechanism criterion, never replacement acceptance. Report
the new model, matched small_set_fit control, ordinary_v5 parent and corrected
R1e on the SAME cached assay views. Original live R1e performance differs.
Include all8cards, native/mirrored counts, PLAY/WAIT, per-replay counts, and first/
last256training loss means. All views used in training; no p-value/generalization/
gameplay/physical gain claim. A failure does not prove the mechanism impossible.

Engineering requires exact initial base/gate/card/cell output and roundtrip,
correct cell-patch/offset mapping for2304cells, local-patch and query-dependence
fixtures, per-patchzero-mean, finite backward/unchangedweights/zerooptimizer in
preparation. Independently reconcile4096finiteupdate/drawlogs,524288draws,
optimizerstates and final source/tensorbindings BEFORE inference. Count the
new2048views once; do not re-infer any old control. Corruptions must be rejected.
