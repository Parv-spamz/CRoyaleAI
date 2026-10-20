# Coverage diagnosis gate

OWNS: scratchpad/gauntlet/L72/improvement_loop/late_game_readiness_coverage/**

- [x] C1: All16 saved memberships and projection fields reconcile; corruptions rejected.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/late_game_readiness_coverage/audit.py
  EXPECT: LATE_COVERAGE_DIAGNOSED
  EVIDENCE: report.json; l72-late-game-coverage0.541343s exit0/token,1positive8corruptions.
