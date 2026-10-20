# Defensive-sequence iteration gates

- [x] C1: New schedule and development masks bind the verified historical sequence index to existing disjoint inner splits without changing labels.
  CHECK: icebow/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/development_iteration_2/prepare.py
  EXPECT: DEFENCE_DEVELOPMENT_SCHEDULE_PREPARED
- [x] C2: Independent schedule/source/membership recount and leakage controls pass.
  CHECK: icebow/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/development_iteration_2/verify.py
  EXPECT: DEFENCE_DEVELOPMENT_SCHEDULE_VERIFIED
- [x] C3: Iteration1 control/results are reconciled, candidate trainer/metrics and plain-metadata roundtrip are verified before the one serial full candidate run.
  MANUAL: Fixed PLAN recipe and source binding; checkpoint-free smoke is not training; no concurrent GPU chain.
- [x] C4: Full candidate updates and independently recounted developmental outcomes are reported with all failures and original final deployment gates intact.
  MANUAL: Owner Discord model report with delivery receipt, scoped commit and handoff. No deployment from development-only results.

C3 receipt l72-development2-preflight exit0/token matched106.14s. Reuses frozen
iteration1 loader/augmentation/optimizer/loss; same original control fully
reconciled before launch. New training-only first-batch CPU smoke is not full
training and saves no checkpoint. In-memory weights-only metadata roundtrip
preserves all tensors. All original masks independently reproduced; two added
defense masks bind original labels before predictions. prelaunch.json is the
new scoped activation; historical sequence binding remains unchanged.
C4 COMPLETE October5 13:59. Full1000 finite updates, evaluation and independent
recount passed; fixed continuation criteria FAILED. Preserve rejection. All7
process receipts and paired replay summaries are in reviewed_results.json.
Model report delivered once in one HTTP204 chunk. Do not rerun this chain or
change its frozen recipe/thresholds. Final acceptance remains unmet.
