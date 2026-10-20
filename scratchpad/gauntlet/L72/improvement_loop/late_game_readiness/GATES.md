# Late-game readiness gates

OWNS: scratchpad/gauntlet/L72/improvement_loop/late_game_readiness/**, icebow/data/bench/late_game_readiness_20261005/**

- [ ] C1:16 full games, exact late views, probability/GAE/backward checks, zero updates.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/late_game_readiness/collect.py
  EXPECT: LATE_GAME_READINESS_COLLECTED
  EVIDENCE: FAILED l72-late-game-readiness-collection,104.688055s exit1/tokenfalse;16games completed,4late games/91rows<256. Original source and all records preserved.
- [ ] V1: Independent complete membership, rewards, history, weights and corruption checks.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/late_game_readiness/verify.py
  EXPECT: LATE_GAME_READINESS_VERIFIED
  EVIDENCE: ABANDONED for this failed fixed cohort; no verifier run.
- [ ] R1: Outside review binds both receipts, source/output hashes and next verdict.
  MANUAL: Complete after independent results. Readiness is not model improvement.
  EVIDENCE: ABANDONED. Separate late_game_readiness_coverage records capacity only; no readiness pass.
