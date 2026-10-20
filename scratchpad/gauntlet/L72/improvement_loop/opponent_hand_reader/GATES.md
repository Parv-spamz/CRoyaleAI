# Opponent hand reader gates

OWNS: pipeline/opponent_hand.py, pipeline/tests/test_opponent_hand.py, scratchpad/gauntlet/L72/improvement_loop/opponent_hand_reader/**, icebow/data/bench/opponent_hand_reader_20261006/**

- [x] T1: Queue truth, partial knowledge, ambiguity, gaps, Mirror, abilities, reset, privacy and unchanged existing features pass.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/opponent_hand_reader/check_tests.py
  EXPECT: OPPONENT_HAND_TESTS_PASSED
  EVIDENCE: l72-opponent-hand-tests-v2.json; exit0/matched,3.968763s;18 tests; original failed fixture receipt preserved and explained in METRICS.md.
- [x] C1: Frozen eligible past-match cohort produces predictions against direct saved hands with coverage and failure accounting.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/opponent_hand_reader/collect.py
  EXPECT: OPPONENT_HAND_COLLECTED
  EVIDENCE: l72-opponent-hand-collect.json; exit0/matched,36.133480s;160replays/12696 saved-hand comparisons, collected.json.
- [x] V1: Independent raw truth, prefix/event membership and count verification rejects deliberate corrupted predictions/results.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/opponent_hand_reader/verify.py
  EXPECT: OPPONENT_HAND_VERIFIED
  EVIDENCE: l72-opponent-hand-independent.json; exit0/matched,11.357863s;verified.json,3positive8corrupt controls, every original hand/prefix/count.
- [x] R1: Reviewed measured findings, source scope, limitations and remaining model work are published with receipts.
  EVIDENCE: l72-opponent-hand-reviewed.json; exit0/matched,4.890720s;reviewed.json binds failed/successful receipts, sources, README/REVIEW/details. Scoped commit includes HANDOFF and evidence; no policy/live change.
