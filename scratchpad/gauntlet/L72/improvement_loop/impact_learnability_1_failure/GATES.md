# Gates: Original setup failure diagnosis

OWNS: scratchpad/gauntlet/L72/improvement_loop/impact_learnability_1_failure/**

- [x] F1: Saved failed command, source hashes, original receipt and partial inventory reconcile.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/impact_learnability_1_failure/diagnose.py
  EXPECT: IMPACT_LEARNING_FAILURE_BOUND
  EVIDENCE: l72-impact-learning1-failure-diagnosis.json; exit0/tokentrue;25.208837seconds; report.json/inventory.json;1positive4corruptions. Original collection gate remains failed.
