# Imitation gradient audit gates

OWNS: scratchpad/gauntlet/L72/improvement_loop/il_gradient_audit/**, icebow/data/bench/il_gradient_audit_20261006/**

- [x] C1: Collect all32 fixed model/batch gradients with original losses, unchanged weights and controls.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/il_gradient_audit/collect.py
  EXPECT: IL_GRADIENT_COLLECTED
  EVIDENCE: l72-il-gradient-collect.json; exit0/matched,160.699687s; collected.json,32records.
- [x] V1: Independently reconcile original draws and labels, all vector reductions and corruption controls.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/il_gradient_audit/verify.py
  EXPECT: IL_GRADIENT_VERIFIED
  EVIDENCE: l72-il-gradient-independent.json; exit0/matched,24.850928s; verified.json,3positive7negative.
- [x] R1: All receipts and bindings reconcile and interpretation preserves limitations and model rejections.
  MANUAL: Inspect both successful stages, run outside once-only review and publish qualified results.
  EVIDENCE: l72-il-gradient-reviewed.json; exit0/matched,0.644249s; reviewed.json,REVIEW.md,DETAILS.md.
