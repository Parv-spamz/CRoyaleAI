# Exact input collision audit gates

OWNS: scratchpad/gauntlet/L72/improvement_loop/input_collision_audit/**, icebow/data/bench/input_collision_audit_20261006/**

- [x] C1: Freeze input sources and original native training membership, check controls and collect strict public hashes once.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/input_collision_audit/collect.py
  EXPECT: INPUT_COLLISIONS_COLLECTED
  EVIDENCE: l72-input-collisions-collect.json; exit0/matched,90.860224s; collected.json.
- [x] V1: Independently reconstruct every input and original label, reconcile all groups and reject malformed evidence.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/input_collision_audit/verify.py
  EXPECT: INPUT_COLLISIONS_VERIFIED
  EVIDENCE: l72-input-collisions-independent.json; exit0/matched,96.157929s; verified.json,2positive7negative.
- [x] R1: All receipt/source/result hashes match; the published interpretation states narrow scope and unchanged rejections.
  MANUAL: Run outside review_input_collisions.py once after successful C1/V1 and inspect reviewed evidence.
  EVIDENCE: l72-input-collisions-reviewed.json; exit0/matched,0.606283s; reviewed.json and REVIEW.md.
