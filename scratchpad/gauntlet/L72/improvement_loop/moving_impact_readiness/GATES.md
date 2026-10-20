# Gates: Moving-body impact instrument

OWNS: scratchpad/gauntlet/L72/improvement_loop/moving_impact_readiness/**, icebow/data/bench/moving_impact_readiness_20261005/**

Scope: Qualify isolated moving-body and multiple-target impact observations without a policy.

- [ ] M1: All fixed roots and96branches have complete motion/HP/command records and matched WAIT controls.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/moving_impact_readiness/collect.py
  EXPECT: MOVING_IMPACT_COLLECTED
  EVIDENCE: See REVIEW.md and l72-moving-impact-collection failure receipt; no success claimed.
- [ ] M2: Independent effect, identity, membership and cost recount passes positive and corruption controls.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/moving_impact_readiness/verify.py
  EXPECT: MOVING_IMPACT_VERIFIED
  EVIDENCE: See REVIEW.md and l72-moving-impact-collection failure receipt; no success claimed.
- [x] M3: Receipts, findings and instrument limits are reviewed and handed off without a policy-strength claim.
  MANUAL: Bind successful receipts and report/verified hashes, preserve any failed gate, update HANDOFF.
  EVIDENCE: See REVIEW.md and l72-moving-impact-collection failure receipt; no success claimed.

ABANDON: M1 Original fixed window includes ordinary tower shots; raw output and nonzero receipt preserved.
ABANDON: M2 No complete qualifying producer report exists; independent verifier was not run.
