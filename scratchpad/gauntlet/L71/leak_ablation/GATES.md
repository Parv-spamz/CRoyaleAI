# R1e live anti-leak ablation

Owner authorized disabling the hardcoded anti-leak rule and redeploying the same R1e checkpoint on 2026-10-04. This is a live observation experiment, not a claim of improved match performance.

- [x] G1: The opt-in flag disables forced spending; default behaviour and normal learned plays remain unchanged.
  CHECK: icebow/.venv/Scripts/python.exe scratchpad/gauntlet/L71/leak_ablation/verify_switch.py
  EXPECT: ANTI_LEAK_SWITCH_VERIFIED
  EVIDENCE: verification.json; PowerShell/Python direct subprocess in C:/Users/benpe/ClashBot, exit0, marker matched; output SHA256 5bd1484da59cd95aba9598e0da0b728a0cb12d36a886444873013900250b1e54. Replays497 real attempts: default497, disabled485; positive control12 forced suppressions. CLI help and bash -n pass.
- [x] G2: The old run exits between matches, and one replacement run loads R1e u0155 with anti-leak disabled and confirms an ordinary play.
  EVIDENCE: deployment.json/processes_after_start.json. Old four PIDs absent after clean STOP exit21:48:07, supervisor done21:48:08; launch refused duplicates. First match21:51:10 start anti_leak=false, same checkpoint hash, tau0.35; runtime snapshot7 attempts/7 confirmed/0 forced. Python5424 is child of venv37388; bash entries form one ancestor chain.
- [x] G3: Record the experiment boundary, owner authorization, checks and restart configuration in HANDOFF, commit and push only this batch.
  EVIDENCE: commit3356087 pushed origin/main (f11419b..3356087, exit0). Scoped10-file diff reviewed; no icebow/data staged. HANDOFF top/sections3,5,6 updated; only this task's authorization appended to the BLOCKERS index blob, preserving inherited worktree changes. This final ledger-only follow-up records that verified push.
