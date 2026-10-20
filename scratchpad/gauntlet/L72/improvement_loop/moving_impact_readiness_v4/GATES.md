# Gates: Sequential-setup impact instrument

OWNS: scratchpad/gauntlet/L72/improvement_loop/moving_impact_readiness_v4/**, icebow/data/bench/moving_impact_readiness_v4_20261005/**

Scope: Qualify all-entity spell effect measurement in fixed isolated moving-body scenes.

- [x] I1: All96branches retain sequential setup, complete native effects and no-combat controls.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/moving_impact_readiness_v4/collect.py
  EXPECT: MOVING_IMPACT_V4_COLLECTED
  EVIDENCE: l72-moving-impact-v4-collection.json, report.json; exit0/token true
- [x] I2: Independent membership, effect and setup recount passes positive and corruption controls.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/moving_impact_readiness_v4/verify.py
  EXPECT: MOVING_IMPACT_V4_VERIFIED
  EVIDENCE: l72-moving-impact-v4-independent.json, verified.json; exit0/token true;16positive17corruptions
- [x] I3: Receipts, limitations and original failed attempts are bound in closeout and HANDOFF.
  MANUAL: Verify hashes and reported findings; preserve every policy acceptance gate.
  EVIDENCE: reviewed.json, REVIEW.md and l72-moving-impact-v4-reviewed.json; exit0/token true
