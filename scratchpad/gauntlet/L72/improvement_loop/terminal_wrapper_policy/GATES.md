# Terminal policy-driver gates

- [x] P1: All32 initial setup/form pairs match before prediction; fixed serial collection completes with source/runtime bindings and every raw record.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/terminal_wrapper_policy/collect.py
  EXPECT: TERMINAL_POLICY_COLLECTION_COMPLETE
- [x] P2: Independent exact-command/native-state/public-prefix/pending accounting passes for all16 pairs and rejects corruptions; actual fulltime coverage is explicit.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/terminal_wrapper_policy/verify.py
  EXPECT: TERMINAL_POLICY_VERIFIED
- [x] P3: Publish bounded engineering conclusion and preserve all final model gates and owner STOP.
  MANUAL: No performance/deployment claim or duplicate model report.

Completed October5 18:07 EDT; reviewed18:26 EDT. P1/P2 receipts l72-terminal-policy-collection/independent: exit0/token matched, 513.38s/70.82s. The separate l72-terminal-policy-reviewed receipt binds their output hashes, report, all32 records and frozen sources without replaying any game. P3: REVIEW.md and root HANDOFF.md preserve the engineering-only scope; no model report or live change.
