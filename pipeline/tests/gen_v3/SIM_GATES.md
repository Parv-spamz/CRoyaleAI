# Gates: gen_v3 SIM continuation

OWNS: pipeline/eval_gen.py, pipeline/royale_env.py, pipeline/e1_view.py, pipeline/rl_royale.py, pipeline/e1_eval.py, pipeline/search_s0.py, scratchpad/gauntlet/L68/generalist/screen_gen/run_screen.py, pipeline/tests/gen_v3/**

Scope: Complete versioned SIM features without training, GPU, live play, git, agents, or edits outside the write set.

- [x] G1: Production SIM and training features agree, including forms and public history; noise and extrapolation preserve alignment.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider pipeline/tests/gen_v3/test_sim_contract.py pipeline/tests/gen_v3/test_sim_integration.py
  EXPECT: (?m)^15 passed(?:,| in )
  EVIDENCE: PowerShell at repository root, CPU only, exit 0; sim_integration.out reports 15 passed. Also reverified by final combined suite. sim_parity_result.json: 232 side views, exact forms and history.
- [x] G2: Legacy snapshots and the active rseries checkpoint remain byte identical, including RNG states.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider pipeline/tests/gen_v3/test_legacy.py pipeline/tests/gen_v3/test_sim_legacy.py
  EXPECT: (?m)^8 passed(?:,| in )
  EVIDENCE: All eight legacy tests passed inside final combined suite (PowerShell, repository root, exit 0). Actual rseries checkpoint, v1/v2, raw and serialized engine/RNG state; previous snapshot hashes verified.
- [x] G3: One ghost match, one plain reactive match against gen_v1, and tiny RL collate/GAE run on CPU with measured features.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe -m pipeline.tests.gen_v3.sim_smoke
  EXPECT: SIM_SMOKE_OK
  EVIDENCE: sim_smoke.out ends SIM_SMOKE_OK; artifacts independently verified with exit 0 / SMOKE_ARTIFACTS_VERIFIED. Exactly one completed ghost and reactive match, no truncation; RL 19 contributing rows, finite GAE. PowerShell emitted NativeCommandError for a Python warning despite completion; no inference exception occurred.
- [x] G4: Requested CPU suites executed with explicit no-git exclusions and environment skips; all executable checks pass.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe -m pipeline.tests.gen_v3.run_sim_tests
  EXPECT: SIM_TESTS_OK
  EVIDENCE: Final PowerShell run at repository root, exit 0 / SIM_TESTS_OK: 274 passed, 1 Windows pipe skip, 5 historical git-show deselections. All current source changes and the external dataset.py change included. sim_tests.out.
- [x] G5: Reviewed scope, commands and evidence; no prohibited actions or edits.
  EVIDENCE: Five production files changed; all remaining writes are tests/evidence in gen_v3. Protected starting hashes retained. train_gen, dataset_gen, obs_contract and live_gen unchanged; dataset.py changed externally at 12:11:01, before the final validation. No training jobs, full screens, GPU, live client, git or agents.

Result: 5 met, 0 unmet, 0 abandoned implementation gates. The multiprocessing shutdown test remains environment-blocked; historical git tests are excluded by the task constraint.
