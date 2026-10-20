# Full-return RL gates

- [x] L1: Parent, identical256 prepared training setups, one-factor config and analytic full-return controls are bound before learning.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/development_rl_2/prepare.py
  EXPECT: OUTCOME_LAMBDA1_PREPARED
- [x] L2: Exactly32 finite updates and256 native games complete under the fixed recipe; only final checkpoint qualifies.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/development_rl_2/train.py
  EXPECT: OUTCOME_RL_TRAIN_COMPLETE
- [x] L3: Final-only54723 development predictions are saved with original metrics.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/development_rl_2/evaluate.py
  EXPECT: OUTCOME_RL_EVALUATED
- [x] L4: All trajectories, outcomes, probabilities, returns and frozen continuation filters independently reconcile.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/development_rl_2/verify.py
  EXPECT: OUTCOME_RL_VERIFIED
- [x] L5: Model verdict is reported once with retained delivery evidence and all final acceptance requirements preserved.
  MANUAL: Review frozen filters/receipts, send one intended Discord report, update HANDOFF.

All execution/reporting gates complete21:17 EDT. Fixed continuation verdict FAILS;
this is not model acceptance. See REVIEW.md/results_verified/reviewed_results and
l72-outcome-lambda1-{prepare,train,eval,independent,reviewed-evidence,discord,reviewed}
receipts. Report delivered once; do not rerun or resend.
