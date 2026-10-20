# Expert context exposure ablations

- [x] C1: Cohorts preserve expert labels and replay splits; samplers never draw held-out rows and fail on missing positive buckets.
  CHECK: icebow/.venv/Scripts/python.exe -m pytest scratchpad/gauntlet/L71/context_teaching/test_sampling.py -q
  EXPECT: passed
  Evidence: `../integration/checks/contexts-independent.json` independently reconstructs memberships/counts and checks source hashes and replay disjointness; exit0, EXPERT_CONTEXT_INDEPENDENT_VERIFY_PASS, output SHA256c958fa527db7df70c4352ac64c10c494b99760535353318a11256172a5dc8572. Integrated sampler/migration tests: `expert-context-unit.json`,12 pass. Actual v6 CPU backward: `v6-actual-smoke.json`, loss4.299795, no checkpoint saved.
- [ ] C2: Actual trained candidates and controls use fixed final-step selection, source hashes and one changed factor per comparison.
  MANUAL: Reconcile recipes, sampled-row receipts and checkpoint metadata.
  Prepared recipe: PLAN.md;34 sequential train/held-out/game jobs in run_experiments.py, dry-run verified in `../integration/checks/experiment-plan-dry-run.json`. Full training has not started; readiness is not completion.
- [ ] C3: Adopt only candidates that pass predeclared held-out/context and same-code gameplay checks; verify accepted behaviour in live telemetry.
  MANUAL: Inspect full match counts, paired metrics and deployment evidence.
