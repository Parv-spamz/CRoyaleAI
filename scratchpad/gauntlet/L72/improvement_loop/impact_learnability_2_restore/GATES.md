# Gates: Saved-root representation diagnosis

OWNS: scratchpad/gauntlet/L72/improvement_loop/impact_learnability_2_restore/**

- [x] S1: All192restores retain exact native bytes and every saved JSON value; corruptions rejected.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/impact_learnability_2_restore/diagnose.py
  EXPECT: IMPACT_ROOT_RESTORE_DIAGNOSED
  EVIDENCE: l72-impact-learning2-restore-diagnosis.json; exit0/tokentrue;24.383791seconds;192positive4corruptions; report.json retains every type difference. Original gate remains failed.
