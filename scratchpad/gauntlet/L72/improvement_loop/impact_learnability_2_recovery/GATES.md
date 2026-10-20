# Gates: Representation-corrected effect assay recovery

OWNS: scratchpad/gauntlet/L72/improvement_loop/impact_learnability_2_recovery/**, icebow/data/bench/impact_learnability_2_20261005/r*_a*, icebow/data/bench/impact_learnability_2_20261005/r*_wait*, icebow/data/bench/impact_learnability_2_20261005/dataset.json, icebow/data/bench/impact_learnability_2_20261005/*public_*, icebow/data/bench/impact_learnability_2_20261005/draws_*

- [x] D1: All prepared roots restore exactly and produce complete qualified trajectories.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/impact_learnability_2_recovery/collect.py
  EXPECT: IMPACT_LEARNING_DATA_COLLECTED
  EVIDENCE: collected.json; l72-impact-learning2-recovery-collect: exit0/token,485.296423s
- [x] D2: All public features, labels and grouped memberships independently reconcile.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/impact_learnability_2_recovery/verify_data.py
  EXPECT: IMPACT_LEARNING_DATA_VERIFIED
  EVIDENCE: data_verified.json; l72-impact-learning2-recovery-data-independent: exit0/token,177.156634s
- [x] L1: Six models complete the original1000updates each and fixed inference.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/impact_learnability_2_recovery/train.py
  EXPECT: IMPACT_LEARNING_TRAINED
  EVIDENCE: trained.json; l72-impact-learning2-recovery-train: exit0/token,35.128636s
- [x] L2: Saved results and original continuation filters independently reconcile.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/impact_learnability_2_recovery/verify_results.py
  EXPECT: IMPACT_LEARNING_RESULTS_VERIFIED
  EVIDENCE: results_verified.json; l72-impact-learning2-recovery-results-independent: exit0/token,12.948921s. Execution/recount passed; continuation filters FAILED.
- [x] R1: Original failures, six successful receipts, reviewed results and single report delivery are handed off.
  MANUAL: Verify outside closeout, report every seed/control and limits once; do not claim a playable model or R1e superiority.
  EVIDENCE: reviewed_evidence.json and reviewed_results.json; evidence review0.255875s, Discord send1.118851s, report closeout0.106545s, all exit0/token. Three HTTP200 parts delivered ONCE.

All execution gates completed. Experimental continuation FAILED; policy not accepted or deployed. Never rerun completed jobs or resend the report.
