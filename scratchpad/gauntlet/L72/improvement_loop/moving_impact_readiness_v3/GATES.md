# Gates: Body and crown impact instrument

OWNS: scratchpad/gauntlet/L72/improvement_loop/moving_impact_readiness_v3/**, icebow/data/bench/moving_impact_readiness_v3_20261005/**

Scope: Qualify all-entity spell effect measurement for fixed isolated moving-body scenes.

- [ ] I1: All96branches retain complete native setup, motion, HP, cost and no-combat controls.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/moving_impact_readiness_v3/collect.py
  EXPECT: MOVING_IMPACT_V3_COLLECTED
  EVIDENCE: pending
- [ ] I2: Independent raw-frame effects, exact membership and corruption checks pass.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/moving_impact_readiness_v3/verify.py
  EXPECT: MOVING_IMPACT_V3_VERIFIED
  EVIDENCE: pending
- [x] I3: Both receipts and limitations are bound in closeout and HANDOFF.
  MANUAL: Check source/raw hashes and all reported findings; keep previous two failures and all policy gates unchanged.
  EVIDENCE: pending

ABANDON: I1 Two-body setup batches two same-team commands; collection failed before second root, preserve original receipt and partial records.
ABANDON: I2 No full report exists; independent verifier was not run.

I3 evidence: REVIEW.md and l72-moving-impact-v3-collection; leaf FAILED, no instrument qualification.
