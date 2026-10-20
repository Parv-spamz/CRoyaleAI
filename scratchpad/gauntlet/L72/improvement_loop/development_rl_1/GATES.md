# Controlled outcome-driven development gates

- [x] O1: Readiness evidence and all fixed native training setups/data/control/source bindings pass preflight; an excluded ephemeral PPO step is finite without changing parent or reading old validation.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/development_rl_1/prepare.py
  EXPECT: OUTCOME_RL_PREPARED
- [x] O2: Registered32 updates/256 games complete with valid on-policy gradients, native outcomes and final portable checkpoint.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/development_rl_1/train.py
  EXPECT: OUTCOME_RL_TRAIN_COMPLETE
- [ ] O3: Final development predictions and independent row/replay recount reconcile without threshold changes.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/development_rl_1/verify.py
  EXPECT: OUTCOME_RL_VERIFIED
- [x] O4: Review receipts, report new model once and publish verdict; only pass supports separately registered gameplay.
  MANUAL: No accepted deployment claim from development; owner STOP intact.

O1 receipt l72-outcome-rl-prepare:49.55s exit0/token matched.
O2 original attempt FAILED before first policy decision: integer/string JSON side
keys compared directly. Do not rerun this command. Recovery R1 passed34.37s with
strict form normalization; R2 carries unchanged O2/O3 learning/metric obligations
under separate driver and receipt. See ../development_rl_1_recovery/GATES.md.
O2 recovery train-v2 completed32updates/256games1898.20s exit0/token; final portable
checkpoint saved. Evaluation72.80s exit0/token. O3 original independent failed
exact summary equality2.63s; retain this failed criterion. Separate completion in
../development_rl_1_recount retains false exactness while recounting all remaining
statistics. Separate recount completed177.53s exit0/token with exactness FALSE.
ABANDON: O3 Original exact-summary criterion failed for this fixed candidate.
All remaining counts reconcile; all three Rocket policy floors independently fail.

O4 prepared closeout helper is outside both frozen leaves: ../review_outcome_rl.py.
Original chain_complete prerequisite was not met. The diagnosed separate recount
completion is bound by the revised outer helper while both failures stay explicit.
Evidence review completed under l72-outcome-rl-reviewed-evidence/OUTCOME_RL_EVIDENCE_REVIEWED.
Read its generated report_model.txt before posting ONCE with the intended sender
under l72-outcome-rl-discord/HTTP 204; then --phase delivery under
l72-outcome-rl-reviewed/OUTCOME_RL_DELIVERY_REVIEWED. The helper checks all delivery
chunks, the reviewed message/source hashes and the preserved original failure.
Evidence1.27s/delivery0.50s exit0/token; reviewed_results.json retains both failures.
Report delivered ONCE1442characters/oneHTTP204. Do not rerun or resend.
