# Sampled-trajectory readiness gates

- [x] R1: Eight fixed new sampled games complete with public row contracts, native outcome/form/source bindings, all-row on-policy agreement and unchanged weights after backward-only checks.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/rl_readiness/collect.py
  EXPECT: RL_READINESS_COLLECTION_COMPLETE
- [x] R2: Independent saved-record verifier reconciles every membership, mask, ratio, terminal outcome and per-tick reward identity and rejects corruptions.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/rl_readiness/verify.py
  EXPECT: RL_READINESS_VERIFIED
- [x] R3: Publish exact measured readiness and remaining learning/data/acceptance limitations before any training registration.
  MANUAL: Review both receipts, keep STOP and all final gates; no new-model report because no new model.

Completed18:57 EDT, reviewed18:59 EDT. l72-rl-readiness-collection/independent/reviewed exit0/token matched;720.29s/1.58s/.95s. Reviewed_results binds source/raw-array/report/receipt hashes. No model or optimizer update produced.
