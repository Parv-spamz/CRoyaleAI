# Validation commands

Run from C:/Users/benpe/ClashBot in PowerShell. All inference and simulation is CPU-only.

```powershell
$env:OMP_NUM_THREADS='2'
$env:PYTHONDONTWRITEBYTECODE='1'
icebow/.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider -p no:tmpdir pipeline/tests/gen_v3/test_contract.py pipeline/tests/gen_v3/test_legacy.py pipeline/tests/test_obs_contract.py pipeline/tests/test_live_mem.py pipeline/tests/test_live_gen_afford.py pipeline/tests/test_opp_elixir_count.py pipeline/tests/test_model_gen.py pipeline/tests/test_e1_eval_gen.py -k 'not checkpoint_roundtrip_and_eval_gen_reproduces and not detects_by_gen_key'
```

71 passed, 2 deselected. The excluded training round-trip would run training, which is forbidden. The other excluded test uses a Windows temporary-directory creation path denied by this environment; the new fixed-path round-trip and actual rseries checkpoint tests cover loading without it.

```powershell
research/ext/Royale/.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider -p no:tmpdir pipeline/tests/gen_v3/test_sim_contract.py
```

1 passed. Real RoyaleSim replay; both sides; actual accepted forms compared with per-card cycle reconstruction; board forms and opponent history compared against recording features. This is adapter evidence, not completed production SIM/RL integration.

```powershell
icebow/.venv/Scripts/python.exe -m pipeline.tests.gen_v3.smoke
```

50/50 replays, 0 failed; 12,448 rows, 50,440 tokens. Rebuilt after the tagging-statistics fix. No full build.

Initial test runs hit Windows PermissionError in pytest temporary-directory creation. Tests now use a fixed checkpoint artifact under this directory and disable pytest's tmpdir/cache plugins. All selected tests pass.
