# Gates: Corrected placement-effect learnability

OWNS: scratchpad/gauntlet/L72/improvement_loop/impact_learnability_2/**, icebow/data/bench/impact_learnability_2_20261005/**

- [x] P1: Every root setup is saved before full trajectory collection.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/impact_learnability_2/prepare.py
  EXPECT: IMPACT_LEARNING_ROOTS_PREPARED
  EVIDENCE: l72-impact-learning2-prepare.json;124.150114s;exit0/tokentrue;192roots288commands;prepared.json.
- [x] P2: All192root setups and288commands independently reconcile, with corruption controls.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/impact_learnability_2/verify_preparation.py
  EXPECT: IMPACT_LEARNING_ROOTS_VERIFIED
  EVIDENCE: l72-impact-learning2-preparation-independent.json;3.468902s;exit0/tokentrue;192positive7corruptions;preparation_verified.json.
- [ ] D1: All prepared roots produce complete qualified raw branches and public rows.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/impact_learnability_2/collect.py
  EXPECT: IMPACT_LEARNING_DATA_COLLECTED
  EVIDENCE: pending
- [ ] D2: Independent raw effects, public projection and grouped split pass controls.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/impact_learnability_2/verify_data.py
  EXPECT: IMPACT_LEARNING_DATA_VERIFIED
  EVIDENCE: pending
- [ ] L1: Six auxiliary predictors finish all1000updates and fixed inference.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/impact_learnability_2/train.py
  EXPECT: IMPACT_LEARNING_TRAINED
  EVIDENCE: pending
- [ ] L2: Independent probabilities, original metrics and filters reconcile.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/impact_learnability_2/verify_results.py
  EXPECT: IMPACT_LEARNING_RESULTS_VERIFIED
  EVIDENCE: pending
- [ ] R1: Reviewed evidence, exact report and single delivery are handed off without claiming policy superiority.
  MANUAL: Inspect all six receipts and independent results, report once with every seed/control and limits, preserve delivery.
  EVIDENCE: pending

ABANDON: D1 Original collection failed at r000 restore equality before any trajectory;6.559501s exit1/tokenfalse. Original receipt/source preserved. Separate restore diagnosis and registered recovery do not retroactively pass this gate.
ABANDON: D2 Original chain stopped before complete data; successor checks live in impact_learnability_2_recovery.
ABANDON: L1 Original chain performed no optimization; successor owns separately bound training.
ABANDON: L2 No original model results exist.
ABANDON: R1 Original failure handed off; any future auxiliary-model report belongs to independently completed recovery and must be sent only once.
