# Independent recount completion gates

- [x] D1: Identify every original failed assertion conjunct over the fixed saved32-update cohort, preserving exactness and per-row1e-4 threshold.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/development_rl_1_recount/diagnose.py
  EXPECT: OUTCOME_RL_RECOUNT_DIAGNOSED
- [x] D2: All remaining original row/replay assertions complete; any original failed exactness criterion remains false in the verdict.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/development_rl_1_recount/verify_completion.py
  EXPECT: OUTCOME_RL_RECOUNT_COMPLETE_WITH_FAILED_EXACTNESS
- [x] D3: Review final statistics and once-only reporting with original failures retained.
  MANUAL: No accepted deployment; original final gates unchanged.

D1 receipt11.56s exit0/token:73783 rows,all lengths/counts/per-row limits pass;
10 of32 exact summary comparisons false,max difference1.6940658945086007e-21.
D2 COMPLETE177.53s exit0/token under l72-outcome-rl-independent-v2; original exactness stays false.
D3 evidence/delivery closeouts exit0/token; reviewed_results.json binds all failures
and model report delivered ONCE1442characters/oneHTTP204. Candidate rejected.
