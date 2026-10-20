# Goblin Barrel target and pre-emptive Log

- [x] B1: Trace native target, observer orientation, look-ahead and model Log placement with saved witnesses; distinguish transform errors from policy errors.
  MANUAL: Inspect exact-coordinate audit and held-out policy/counterfactual measurements; unavailable historical live flight data remains explicit.
  Evidence: native_audit.json/paired_flights.json:7040 observations,14080 orientation/lookahead checks,0 unexplained far targets; r1e_policy.json/r1e_fullshot_policy.json:11/39 wrong-lane fired Logs, target-only0/95 and whole-flight1/95 lane changes. reader_archive.json:3 observed Barrel shots in3631 coherent saved frames; actual landing unverified. Reader inventory receipt: `../integration/checks/barrel-reader-archive.json`, exit0/matched/hash recorded.
- [x] B2: Write an evidence-based proposal, implement it and verify both observer sides, both lanes and unknown-target handling without forcing Log actions.
  MANUAL: Inspect proposal, code and independent checks.
  Evidence: PROPOSAL.md; integrated version6 generic spatial target residual, Barrel exposure cohort, optional public decision audit. `integrated-regression.json`90 tests and `expert-context-unit.json`12 tests pass, including unknown/padded/multiple flights, real source output parity and reader privacy. No full learned candidate is accepted yet; B3 stays open.
- [ ] B3: Accepted candidate is measured under identical gameplay conditions and live logs verify target-to-action wiring.
  MANUAL: Inspect paired game receipts and deployment telemetry.
