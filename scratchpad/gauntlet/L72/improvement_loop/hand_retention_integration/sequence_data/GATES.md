# Sequence gates

OWNS: scratchpad/gauntlet/L72/improvement_loop/hand_retention_integration/sequence_data/**

- [x] C1: Every allowed original row has causal public features and separately stored response-window descriptors.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/hand_retention_integration/sequence_data/collect.py
  EXPECT: HAND_SEQUENCE_COLLECTED
  EVIDENCE: reviewed.json binds collected/verified/chain_complete and all three exit0/token receipts.
- [x] V1: Independent reconstruction and corruptions verify all rows, labels, features and response windows.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/hand_retention_integration/sequence_data/verify.py
  EXPECT: HAND_SEQUENCE_VERIFIED
  EVIDENCE: reviewed.json binds collected/verified/chain_complete and all three exit0/token receipts.

- [x] P1: Independent scalar reference agrees on positive event/window fixtures before collection.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/hand_retention_integration/sequence_data/preflight.py
  EXPECT: HAND_SEQUENCE_PREFLIGHT
  EVIDENCE: reviewed.json binds collected/verified/chain_complete and all three exit0/token receipts.
