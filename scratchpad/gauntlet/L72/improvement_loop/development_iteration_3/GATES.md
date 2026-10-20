# Rocket aim-loss gates

- [x] A1: Fixed ordinary schedule/control and original labels/splits are bound; weight1 reproduces old loss/gradients, added loss only trains expert Rocket cell targets, metadata roundtrip and finite CPU smoke pass.
  CHECK: icebow/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/development_iteration_3/preflight.py
  EXPECT: ROCKET_AIM_PREFLIGHT_COMPLETE
- [x] A2: Exactly1000 finite updates and the fixed final candidate evaluation finish serially, without reserved/old validation access.
  MANUAL: Inspect train/eval receipts, source/runtime/row fingerprints and full logs; no smoke as training.
- [x] A3: Independent cache/raw-label/per-replay recount and fixed filters reviewed, model report delivered once, failures preserved and scoped handoff published.
  MANUAL: Apply PLAN/METRICS literally. No acceptance or deployment from development-only results.

A1 receipt l72-development3-preflight exit0/token matched129.91s. Exact default
loss/gradient equality, unchanged non-cell terms, non-Rocket zero extra gradient,
positive Rocket extra gradient, no-Rocket/WAIT exclusions, metadata roundtrip and
independent masks pass. Training-only CPU smoke loss5.9850544929504395 has two
original expert Rockets, no saved checkpoint and no development predictions.
A2/A3 COMPLETE. Chain finished14:12:16 EDT, all receipts exit0/token matched.
results_verified.json and reviewed_results.json bind1000 finite updates, all54723
predictions, replay deltas and the once-delivered HTTP204 model report. The fixed
continuation filter FAILS Rocket aim/action materiality and Furnace protection.
Completed experiment does not mean accepted candidate. Do not rerun or edit
the frozen training/evaluation sources/PLAN/METRICS.
