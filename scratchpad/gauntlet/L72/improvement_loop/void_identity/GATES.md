# Gates: Void identity and native cost

OWNS: scratchpad/gauntlet/L72/improvement_loop/void_identity/

- [x] V1: Pinned spell/catalog/localization establish the same card identity and retain original asset hashes.
  CHECK: icebow/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/void_identity/audit.py
  EXPECT: VOID_PINNED_IDENTITY_VERIFIED
  EVIDENCE: audit.json; successful l72-void-pinned-identity receipt.
- [x] V2: Native DarkMagic cost/identity, deterministic repeat and known Arrows control independently reconcile.
  CHECK: icebow/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/void_identity/verify.py
  EXPECT: VOID_NATIVE_COST_INDEPENDENT_PASS
  EVIDENCE: verified.json; successful l72-void-native-independent receipt; one positive/seven corruptions. Original l72-void-native-cost comparator failure remains preserved.
- [x] V3: Report distinguishes verified identity/cost from full mechanics parity and fresh replay/model acceptance.
  MANUAL: Review native receipts and all preserved limitations before separately registering any source reconstruction.
  EVIDENCE: REVIEW.md and ORACLE_CORRECTION.md; no full mechanics-parity or policy-performance claim.
