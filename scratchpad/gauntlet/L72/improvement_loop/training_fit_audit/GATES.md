# Training-fit audit gates

OWNS: scratchpad/gauntlet/L72/improvement_loop/training_fit_audit/**, icebow/data/bench/training_fit_audit_20261006/**

- [x] P1: Original checkpoint, source rows, draw orientations and scoring controls are bound.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/training_fit_audit/prepare.py
  EXPECT: TRAINING_FIT_PREPARED
  EVIDENCE: prepared.json; 68 source/input hashes,2positive6malformed scoring controls; l72-training-fit-prepare exit0/token,2.672112s. 213995native plus53310unique mirrored training views,zerooptimizer.
- [x] C1: Fresh training views are predicted once with unchanged weights and cached development reused.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/training_fit_audit/collect.py
  EXPECT: TRAINING_FIT_COLLECTED
  EVIDENCE: collected.json;267305 fresh training views,zero optimizer/development inference,weights exact; l72-training-fit-collect exit0/token,198.023819s.
- [x] V1: Independent raw-label, draw, aggregate and replay counts plus corruption controls reconcile.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/training_fit_audit/verify.py
  EXPECT: TRAINING_FIT_VERIFIED
  EVIDENCE: verified.json; all raw labels,orientations,weights,group/replay counts reconcile,4positive10corruptions; l72-training-fit-independent exit0/token,15.603543s.
- [x] R1: All receipt hashes reconcile and the written interpretation preserves diagnostic limits.
  MANUAL: Read collected and independently verified results; distinguish descriptive fit from causal mechanism and acceptance.
  EVIDENCE: reviewed.json and REVIEW.md; outside review_training_fit.py ran once,l72-training-fit-reviewed exit0/token,.355999s; no new model/acceptance/deployment.
