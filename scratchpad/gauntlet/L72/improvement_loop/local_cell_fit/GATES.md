# Local cell mechanism assay gates

OWNS: scratchpad/gauntlet/L72/improvement_loop/local_cell_fit/**, icebow/data/bench/local_cell_fit_20261006/**

- [x] P1: Mapping, initial parity, roundtrip, mechanism and finite unchanged-weight backward controls pass.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/local_cell_fit/prepare.py
  EXPECT: LOCAL_CELL_FIT_PREPARED
  EVIDENCE: l72-local-cell-fit-prepare.json, exit0/token, 81.601860285s; prepared.json binds90sources, exactinitial/roundtrip/mechanism/2304mapping, finiteunchangedCPUbackward, zerooptimizer.
- [x] T1: Exactly4096 finite updates produce the quarantined final diagnostic checkpoint.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/local_cell_fit/train.py
  EXPECT: LOCAL_CELL_FIT_TRAINED
  EVIDENCE: l72-local-cell-fit-train.json, exit0/token, 717.011881113s; reviewed_results.json binds final evidence and one delivered report; diagnostic_fit FALSE.
- [x] V1: Independent training/draw/optimizer evidence passes before inference.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/local_cell_fit/verify_training.py
  EXPECT: LOCAL_CELL_FIT_TRAINING_VERIFIED
  EVIDENCE: l72-local-cell-fit-training-independent.json, exit0/token, 6.835611343s; reviewed_results.json binds final evidence and one delivered report; diagnostic_fit FALSE.
- [x] E1: Only the new final model predicts once on each fixed training orientation.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/local_cell_fit/evaluate.py
  EXPECT: LOCAL_CELL_FIT_EVALUATED
  EVIDENCE: l72-local-cell-fit-eval.json, exit0/token, 53.485715151s; reviewed_results.json binds final evidence and one delivered report; diagnostic_fit FALSE.
- [x] V2: Independent original-label counts, criteria and corruptions reconcile with cached controls.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/local_cell_fit/verify_results.py
  EXPECT: LOCAL_CELL_FIT_RESULTS_VERIFIED
  EVIDENCE: l72-local-cell-fit-results-independent.json, exit0/token, 7.800922871s; reviewed_results.json binds final evidence and one delivered report; diagnostic_fit FALSE.
- [x] R1: Review and one delivered report retain quarantine and final deployment criteria.
  MANUAL: Inspect all receipts and final results; bind exact report and delivery.
  EVIDENCE: l72-local-cell-fit-reviewed.json, exit0/token, 0.086237431s; reviewed_results.json binds final evidence and one delivered report; diagnostic_fit FALSE.
