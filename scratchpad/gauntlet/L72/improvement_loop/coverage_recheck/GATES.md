# Owner coverage recheck gates

OWNS: scratchpad/gauntlet/L72/improvement_loop/coverage_recheck/

- [x] C1: Hash-bound live and pro cohorts are scanned for observed encounters and all positive low-HP princess-tower states with missing coverage retained.
  CHECK: icebow/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/coverage_recheck/run_v2.py
  EXPECT: OWNER_COVERAGE_RECHECK_COMPLETE
- [x] C2: Independent raw-source recount and corruption fixtures match memberships, thresholds, timing, readiness and aggregate counts.
  CHECK: icebow/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/coverage_recheck/verify_v2.py
  EXPECT: OWNER_COVERAGE_RECHECK_INDEPENDENT_PASS
- [x] C3: Correct the source/finishing interpretation and identify immediately executable work separately from deployment evidence requirements.
  MANUAL: Publish measured findings and explicit data uses; no invented expert labels, damage values, safe-cycle guarantee or new-model acceptance.

Completed with v2 producer/independent receipts, two positive and nine negative
controls. v1 includes ordinary buildings in its tower counts and is rejected;
its files and the explicit nonzero rejection receipt are preserved. Read REVIEW.md.
