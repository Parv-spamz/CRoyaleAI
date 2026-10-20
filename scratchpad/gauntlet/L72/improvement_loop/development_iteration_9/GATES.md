# Additional ordinary imitation gates

OWNS: scratchpad/gauntlet/L72/improvement_loop/development_iteration_9/**, icebow/data/bench/development_iteration_9_20261006/**

- [x] P1: Frozen training-only schedule and new-driver controls reconcile.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/development_iteration_9/prepare.py
  EXPECT: ORDINARY_EXTENDED_PREPARED
  EVIDENCE: prepared.json;80source/input hashes,1024000draws/212145unique rows,2positive6malformed controls,finite new-driver backward probe with exact unchanged weights and zero optimizer updates; l72-development9-prepare74.417735s exit0/token.
- [x] T1: Exactly8000 finite updates produce only the final candidate under frozen bindings.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/development_iteration_9/train.py
  EXPECT: ORDINARY_EXTENDED_TRAINED
  EVIDENCE: trained.json;8000finiteupdates/finalcheckpoint only;l72-development9-train1334.245839s exit0/token.
- [x] V1: Independent training evidence and corruption controls reconcile before development inference.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/development_iteration_9/verify_training.py
  EXPECT: ORDINARY_EXTENDED_TRAINING_VERIFIED
  EVIDENCE: training_verified.json;1024000draws,96optimizer parameter states each8000steps,finite changed weights,1positive8corruptions;l72-development9-training-independent3.870191s exit0/token.
- [x] E1: The final candidate predicts once on the registered development rows.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/development_iteration_9/evaluate.py
  EXPECT: ORDINARY_EXTENDED_EVALUATED
  EVIDENCE: evaluated.json;54723final-only predictions;l72-development9-eval79.887351s exit0/token.
- [x] V2: Independent counts, controls and every continuation verdict reconcile.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/development_iteration_9/verify_results.py
  EXPECT: ORDINARY_EXTENDED_RESULTS_VERIFIED
  EVIDENCE: results_verified.json;all original raw labels/masks/per-replay counts and2positive10corruptions reconcile;all Rocket material floors fail;l72-development9-results-independent68.626868s exit0/token.
- [x] R1: Evidence review and the single model report are bound with an accurate deployment verdict.
  MANUAL: Inspect every receipt, final counts, message and confirmed delivery; preserve all final floors.
  EVIDENCE: reviewed_evidence/reviewed_results/message.md;outside evidence.763362s,delivery.916176s,closeout.095654s all exit0/token. Two HTTP200parts delivered once;candidate rejected/notdeployed.
