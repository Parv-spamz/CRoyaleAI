# Local-cell contribution gates

OWNS: scratchpad/gauntlet/L72/improvement_loop/local_cell_contribution/**, icebow/data/bench/local_cell_contribution_20261006/**

- [x] C1: Fixed-checkpoint base/residual scores and cache anchors are preserved for both orientations.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/local_cell_contribution/collect.py
  EXPECT: LOCAL_CELL_CONTRIBUTION_COLLECTED
  EVIDENCE: l72-local-cell-contribution-collect.json/.out, exit0/token, 64.119421s; reviewed.json binds receipts. See CORRECTION.md for label-descriptor limits.
- [x] V1: Independent score reconstruction, labels, per-replay counts and corruption controls pass.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/local_cell_contribution/verify.py
  EXPECT: LOCAL_CELL_CONTRIBUTION_VERIFIED
  EVIDENCE: l72-local-cell-contribution-independent.json/.out, exit0/token, 12.592147s; reviewed.json binds receipts. See CORRECTION.md for label-descriptor limits.
- [x] R1: Reviewed evidence binds both receipts and preserves failed fit criteria and quarantine.
  MANUAL: Review collected/verified original artifacts, sources and receipts; save a bound review.
  EVIDENCE: l72-local-cell-contribution-reviewed.json/.out, exit0/token, 0.592879s; reviewed.json binds receipts. See CORRECTION.md for label-descriptor limits.
