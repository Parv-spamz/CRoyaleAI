# Extended fit audit gates

OWNS: scratchpad/gauntlet/L72/improvement_loop/extended_fit_audit/**, icebow/data/bench/extended_fit_audit_20261006/**

- [x] P1: Bind both reviewed checkpoints/caches, source/labels and original draw schedule; controls pass.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/extended_fit_audit/prepare.py
  EXPECT: EXTENDED_FIT_PREPARED
  EVIDENCE: prepared.json and l72-extended-fit-prepare.json/.out;exit0/token2.674135s,81sources,2positive6bad,original1024000draws exact.
- [x] C1: Once-only training views for both fixed models, no optimization or development inference.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/extended_fit_audit/collect.py
  EXPECT: EXTENDED_FIT_COLLECTED
  EVIDENCE: collected.json and collect receipt;exit0/token463.999556s;816522views,unchangedweights,0optimizer/developmentinference.
- [x] V1: Independent raw labels, schedule, masks, scalar counts and every replay reconcile for both models.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/extended_fit_audit/verify.py
  EXPECT: EXTENDED_FIT_VERIFIED
  EVIDENCE: verified.json and independent receipt;exit0/token48.626731s;alloriginal labels/draws/perreplay counts;4positive10bad permodel.
- [x] R1: Outside review binds all three receipts and interpretations, publishes accurate handoff.
  MANUAL: Inspect artifacts and run review_extended_fit.py once via fresh l72-extended-fit-reviewed receipt.
  EVIDENCE: reviewed.json and reviewed receipt;exit0/token.615980s;all81sources/3receipts bound;both model rejections retained.
