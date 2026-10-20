# Training residual diagnosis gates

OWNS: scratchpad/gauntlet/L72/improvement_loop/barrel_residual/

- [x] B1: Fixed split0 replay-stratified rows, original labels and unchanged checkpoint weights are bound before inference.
  CHECK: icebow/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/barrel_residual/run.py
  EXPECT: TRAIN_BARREL_RESIDUAL_COMPLETE
  EVIDENCE: selection.json and report.json; successful l72-training-barrel-residual receipt. 789 training rows, 489 replay groups, three existing checkpoints/five conditions; zero optimizer updates.
- [x] B2: Independent source/cache recount and positive/negative controls verify metrics and residual-only invariants.
  CHECK: icebow/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/barrel_residual/verify.py
  EXPECT: TRAIN_BARREL_RESIDUAL_INDEPENDENT_PASS
  EVIDENCE: verified.json and successful l72-training-barrel-residual-independent receipt; one positive/eight corruption controls, all membership/logit/label/count checks agree; all 200 no-valid-target rows unchanged.
- [x] B3: Report separates representation effects from unseen-data, landing, gameplay and new-model acceptance claims.
  MANUAL: Review actual paired counts and limitations; preserve failed original candidates and N2 prerequisites.
  EVIDENCE: REVIEW.md and HANDOFF 11:49 EDT. Original candidates remain rejected; no live or model deployment change; N2-N7 stay open.
