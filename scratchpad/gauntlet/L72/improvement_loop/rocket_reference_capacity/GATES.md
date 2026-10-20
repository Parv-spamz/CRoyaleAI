# Fresh Rocket source-reference inventory gates

OWNS: scratchpad/gauntlet/L72/improvement_loop/rocket_reference_capacity/

- [x] R1: Full fixed source membership and existing label definitions are hash-bound and all original Rocket casts are accounted for without model calls.
  CHECK: icebow/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/rocket_reference_capacity/run.py
  EXPECT: ROCKET_REFERENCE_CAPACITY_COMPLETE
  EVIDENCE: started.json, references.json, report.json and l72-rocket-reference-capacity receipt (exit0/token matched). 115 selected replays, 260 casts, zero policy predictions/updates.
- [x] R2: Independent raw-source reconstruction matches every reference and aggregate; corruption controls reject altered evidence.
  CHECK: icebow/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/rocket_reference_capacity/verify.py
  EXPECT: ROCKET_REFERENCE_CAPACITY_INDEPENDENT_PASS
  EVIDENCE: verified.json and l72-rocket-reference-capacity-independent receipt (exit0/token matched). All raw references agree; one positive/nine negative controls passed.
- [x] R3: Report distinguishes source-reference counts from opportunities, independent trials, power, causal effects and model acceptance.
  MANUAL: Review source provenance and uncertainties, preserve N2-N7 open and owner farming unchanged; publish scoped evidence.
  EVIDENCE: REVIEW.md and HANDOFF October5 12:10 EDT. All landings estimated, zero labeled princess finishes not proof of absent opportunities; no acceptance or training activation.
