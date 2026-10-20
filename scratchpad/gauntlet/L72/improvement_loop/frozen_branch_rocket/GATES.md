# Gates: fixed-branch Rocket diagnosis

OWNS: scratchpad/gauntlet/L72/improvement_loop/frozen_branch_rocket/**

- [x] R1: Frozen original membership, labels, public contexts and saved predictions bind before new cross-tabs.
  MANUAL: Inspect started.json hashes and source isolation; no model/optimizer imports or new inference.
- [x] R2: Producer and independent raw-array/cache recount reconcile every row, subgroup and replay with positive/corruption controls.
  CHECK: icebow/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/verify_frozen_branch_rocket_v2.py
  EXPECT: FROZEN_BRANCH_ROCKET_INDEPENDENT_V2_COMPLETE
- [x] R3: Findings, limitations and the next supported work are published without relabeling failed candidates.
  MANUAL: Review receipts and exact counts; no new-model report or deployment from this diagnostic.

Evidence: started.json/report.json/verified_v2.json and l72-frozen-branch-rocket-
audit/independent-v2 receipts pass90.29/55.88s. All54723 rows/four caches/955 Rocket
records and all per-replay groups match;6positive/10corruptions. Original verifier
stopped after repeated array inflation, nonzero256.28s receipt retained. No
producer/inference/training rerun. REVIEW.md selects the separate aim-only scope.
