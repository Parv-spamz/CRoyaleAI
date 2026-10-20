# Gates: initial Q0 live comparison

OWNS: scratchpad/gauntlet/L71/live_comparison/**

Scope: A repeatable CPU-only comparison of existing R1e and old R1 live matches, with per-match checkpoint attribution, explicit coverage and unknowns, source-prefix provenance, and no live changes. Q1-Q5 remain the subsequent queue.

- [x] G1: Checkpoint attribution, outcome joins, Wilson intervals, censored records and confirmed-play counting pass adversarial fixtures.
  CHECK: icebow/.venv/Scripts/python.exe scratchpad/gauntlet/L71/live_comparison/test_compare.py
  EXPECT: LIVE_COMPARISON_TESTS_PASSED
  EVIDENCE: verification.json test_compare.py; PowerShell direct subprocess, cwd C:/Users/benpe/ClashBot, icebow venv, exit 0, marker matched, 10 tests; output SHA256 46dbab832a0fd0a12caac4a881bcb10403ba186c520b0243ed5973b2235afe86.

- [x] G2: The saved report reconciles to its frozen source prefixes and rejects a corrupted report.
  CHECK: icebow/.venv/Scripts/python.exe scratchpad/gauntlet/L71/live_comparison/verify_report.py
  EXPECT: LIVE_COMPARISON_VERIFIED
  EVIDENCE: verification.json verify_report.py; PowerShell direct subprocess, cwd C:/Users/benpe/ClashBot, icebow venv, exit 0, marker matched; output SHA256 d8b2b1a565d4616381ad7fca631403421e1f04205e492ce8c323c35cbdd24dff. Source prefixes independently verified; corrupted win count rejected.

- [x] G3: Live checkpoint, supervisor and live source hashes remain unchanged by this batch; documentation records measured coverage and remaining gaps.
  EVIDENCE: report.json protected_sha256 checked by verify_report.py; git diff on live_play.py/run_live.sh empty, CKPT_OVERRIDE remains R1e u0155. HANDOFF 2026-10-04 21:31 records outcomes, denominators, unavailable metrics and Q1/Q2 next. Only new offline reporting files and documentation edited.
