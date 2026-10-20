# Cached RL diagnostic gates

- [x] D1: Fixed identities and original labels are bound; producer completes the full row-state, PLAY/WAIT and head decomposition without inference.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/rl_failure_audit/audit.py
  EXPECT: RL_FAILURE_AUDIT_COMPLETE
- [x] D2: Independent original-label/cache recount matches every aggregate, per-replay transition and Rocket detail; positive and corruption controls pass.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/rl_failure_audit/verify.py
  EXPECT: RL_FAILURE_AUDIT_VERIFIED
- [x] D3: Published review binds completed receipts and measured decomposition while preserving the candidate rejection and deployment gates.
  MANUAL: Bind successful receipts/source/output hashes, preserve failures if any, update HANDOFF and continuation. No duplicate model report or live restart.

D1/D2 receipts130.45s/11.41s exit0/token;54723rows/405replays/19groups/955Rocket
records independently match,2positive8corruptions. D3 review0.55s exit0/token;
reviewed.json plus separate Windows source-binding supplement preserve receipts.
REVIEW.md reports WAIT gains and PLAY losses separately; no accepted model.
