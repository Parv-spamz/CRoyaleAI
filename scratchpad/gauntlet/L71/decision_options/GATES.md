# Gates: sampling checks and Rocket area aim

OWNS: pipeline/decision_options.py, pipeline/live_gen_v2.py, pipeline/e1_eval.py, pipeline/search_s0.py, pipeline/tests/test_decision_options.py, scratchpad/gauntlet/L68/live_reader/live_play_v2.py, scratchpad/gauntlet/L71/decision_options/**, HANDOFF.md, .foreman/codex_autopilot/BLOCKERS.md

Scope: Q1 CPU teacher-forced checks on R1e u0155 and old R1 u0155; Q2 opt-in Rocket area aim integrated into SIM and an inactive candidate live entry point. Current anti-leak-off live run is preserved. Q3 GPU acceptance and deployment are subsequent work, not outcomes of this batch.

Pre-registered Q1: ratio0.5/0.7 x temperature0.7/1.0, affordable hand only, deterministic unchanged gate. Report exact expected pro-card agreement, Rocket recall/false-fire, changed decision probability and confident(top>=0.6) override. Reject agreement drops >1 percentage point or any confident override probability >1e-12 (strict zero interpretation of the brief's approximately zero requirement). No added confidence cutoff, tower-HP rule or parameter search. Report conditional card choice separately from end-to-end gated probability. Results are teacher-forced diagnostics, not win evidence.

Pre-registered Q2: Rocket only; sum learned cell probability within catalog blast radius, physical half-tile distance, zero probability outside board. Select greatest mass, then greatest local probability on exact ties, then lowest cell index. No tower preference. Default argmax remains exact. Report target coverage on held-out pro Rocket positions; this is a location agreement proxy, not confirmed live damage. One/two-Rocket finish-off behaviour remains unproven until prospective play evidence.

- [x] G1: Shared options preserve legacy decisions by default and enforce affordability, seeded sampling, batch invariance, unchanged gate and correct Rocket-area geometry in SIM and candidate live.
  CHECK: icebow/.venv/Scripts/python.exe scratchpad/gauntlet/L71/decision_options/verify_tests.py
  EXPECT: DECISION_TESTS_VERIFIED
  EVIDENCE: tests_verification.json/tests.out;58 tests; PowerShell/Python subprocess, cwd C:/Users/benpe/ClashBot, exit0, marker matched, output SHA256 b575230e8ad4dd1fbe2d850e9f319f22593937b134ce16491eb18a80b1b5fde9.
- [x] G2: Both checkpoints have complete CPU held-out sampling reports for the four frozen settings, aim diagnostics, denominators and source hashes, with independently reconciled acceptance verdicts.
  CHECK: icebow/.venv/Scripts/python.exe scratchpad/gauntlet/L71/decision_options/verify_report.py
  EXPECT: DECISION_REPORT_VERIFIED
  EVIDENCE: report_verification.json; independent metrics/geometry/counts/hashes and corruption control; PowerShell/Python subprocess, cwd C:/Users/benpe/ClashBot, exit0, marker matched, output SHA256 5794fb7fcee34f901413b708a145e50567fe1ae408b409d96b3bae22ac3d49a6.
- [x] G3: Candidate CLI/config paths are wired and documented; live entry, supervisor, checkpoint override and loaded live pilot source are unchanged; the task's scoped changes and findings are committed and pushed.
  EVIDENCE: protected source hashes verified by report_verification/curriculum_verification; CLI and reactive worker forwarding covered by58 tests and --help checks. Scoped41-file commit db62eaa pushed origin/main (exit0); no icebow/data staged, inherited edits excluded. Owner subsequently authorized GPU pause/implementation/deployment; Q3_GATES.md tracks that separate unfinished work. This ledger follow-up records the verified publication.
