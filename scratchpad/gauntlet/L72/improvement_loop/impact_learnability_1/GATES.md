# Gates: Public placement-effect learnability

OWNS: scratchpad/gauntlet/L72/improvement_loop/impact_learnability_1/**, icebow/data/bench/impact_learnability_1_20261005/**

- [ ] D1: Frozen192roots produce all qualified raw branches and public rows.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/impact_learnability_1/collect.py
  EXPECT: IMPACT_LEARNING_DATA_COLLECTED
  EVIDENCE: pending

ABANDON: D1 Original collection failed at root152 setup with status7 NO_DEPLOY; l72-impact-learning1-collect exit1/tokenfalse. Original source and152completed roots preserved, not independently qualified.
ABANDON: D2 No complete data artifact; original collection cannot qualify.
ABANDON: L1 No optimizer launched after failed collection.
ABANDON: L2 No trained model/probabilities exist.
ABANDON: R1 No auxiliary models produced to report. Failure documented in sibling impact_learnability_1_failure and HANDOFF; do not send a model report.
- [ ] D2: Independent raw effects, public projection and grouped split pass controls.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/impact_learnability_1/verify_data.py
  EXPECT: IMPACT_LEARNING_DATA_VERIFIED
  EVIDENCE: pending
- [ ] L1: Both predictors complete all three paired1000-update seeds and fixed development inference.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/impact_learnability_1/train.py
  EXPECT: IMPACT_LEARNING_TRAINED
  EVIDENCE: pending
- [ ] L2: Independent probabilities/metrics/filters reconcile without selecting a new recipe.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/impact_learnability_1/verify_results.py
  EXPECT: IMPACT_LEARNING_RESULTS_VERIFIED
  EVIDENCE: pending
- [ ] R1: Findings, original verdict, limitations and one Discord delivery are bound and handed off.
  MANUAL: Inspect every receipt and final result; report auxiliary model versus control without implying a comparable R1e policy score or deployment.
  EVIDENCE: pending
