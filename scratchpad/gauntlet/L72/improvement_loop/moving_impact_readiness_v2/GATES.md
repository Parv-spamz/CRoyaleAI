# Gates: Moving-body impact instrument

OWNS: scratchpad/gauntlet/L72/improvement_loop/moving_impact_readiness_v2/**, icebow/data/bench/moving_impact_readiness_v2_20261005/**

Scope: Qualify isolated moving-body and multiple-target impact observations without a policy.

- [ ] M1: All fixed roots and96branches have complete motion/HP/command records and matched WAIT controls.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/moving_impact_readiness_v2/collect.py
  EXPECT: MOVING_IMPACT_V2_COLLECTED
  EVIDENCE: pending
- [ ] M2: Independent effect, identity, membership and cost recount passes positive and corruption controls.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/moving_impact_readiness_v2/verify.py
  EXPECT: MOVING_IMPACT_V2_VERIFIED
  EVIDENCE: pending
- [x] M3: Receipts, findings and instrument limits are reviewed and handed off without a policy-strength claim.
  MANUAL: Bind successful receipts and report/verified hashes, preserve any failed gate, update HANDOFF.
  EVIDENCE: pending

ABANDON: M1 First-root casts damage a nearby crown, contrary to this fixture's zero-crown-effects assumption; preserve partial records and nonzero receipt.
ABANDON: M2 No complete producer report exists; independent verifier was not run.

M3 evidence: REVIEW.md, failure_diagnosis.json and l72-moving-impact-v2-collection.
Overall leaf FAILED; moving/multiple-target qualification remains incomplete.
