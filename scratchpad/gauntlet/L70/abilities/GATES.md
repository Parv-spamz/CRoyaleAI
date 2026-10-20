# Gates: replay ability mining

OWNS: scratchpad/gauntlet/L70/abilities/**

Scope: Mine every corpus row on CPU without changing inputs or invoking engines; report attribution uncertainty, all requested usage metrics, and replay-path evidence.

- [x] G1: Every parquet row and ability event is accounted for; every observed hero/champion has a summary.
  CHECK: python -B scratchpad/gauntlet/L70/abilities/mine_abilities.py --verify
  EXPECT: ABILITY_VERIFICATION_PASSED
  EVIDENCE: Direct authorized check; shell=direct process (launched by PowerShell); cwd=C:\Users\benpe\ClashBot; exit=0; match=True; output_sha256=dea5ee18eb55a1c62d9fc7e72bcc95b806b1802600719157361840a7f674921e; details=verification.json
- [x] G2: Attribution, repeat grouping, time boundaries, combo ordering, and coordinates pass synthetic edge cases and output invariants.
  CHECK: python -B scratchpad/gauntlet/L70/abilities/verify_cases.py
  EXPECT: ABILITY_CASES_PASSED
  EVIDENCE: Direct authorized check; shell=direct process (launched by PowerShell); cwd=C:\Users\benpe\ClashBot; exit=0; match=True; output_sha256=6e12306670e12a42dd40049ffb985bc2398be1731161d2e257e1ce1bea1c2d54; details=verification.json
- [x] G3: All requested metrics, limitations, and current replay-path file:line evidence are reviewed in the report.
  EVIDENCE: Reviewed report and JSON: all 24 abilities, requested timing/deployment/combo/repeat/crown/location metrics, short notes, ambiguity and sensitivity, current source citations; 854195 total presses reconciled.
- [x] G4: All writes stay in the declared write set and no engine, GPU, adb, live run, git, or agents are used.
  EVIDENCE: Tool-command and AST import review: writes only inside declared output directory; inputs read-only with unchanged size/mtime; no engine/project module imports, GPU, adb, live, git, or agents. Skill approval-store writes avoided to honor write set; checks executed directly.
- [x] G5: Audit records match sampled original payloads in every input file, including exact combo timing and deployment coordinates.
  CHECK: python -B scratchpad/gauntlet/L70/abilities/verify_sources.py
  EXPECT: ABILITY_SOURCE_COMPARISON_PASSED
  EVIDENCE: Direct authorized check; shell=direct process (launched by PowerShell); cwd=C:\Users\benpe\ClashBot; exit=0; match=True; output_sha256=56b99dcd5853ea1f43fb42d498f3de56b8901acbf12f3227d8cbac1ee2d5c98f; details=verification.json
