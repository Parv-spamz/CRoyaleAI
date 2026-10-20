# gen_v3 SIM integration

Implementation complete. Final CPU validation: **274 passed, 1 skipped, 5 deselected**, 112.44 seconds. The final run includes all added checks and the concurrent dataset.py update. Full output: sim_tests.out.

Changed production files:

- pipeline/eval_gen.py: construct from stored feature_version; shared GenRows batches unit_form and opp_past, including empty unit arrays.
- pipeline/royale_env.py: opt-in status_flags and accepted public card-play log; actual form read before command submission; landing tick and submitted engine coordinates; reset both match types before warm-up.
- pipeline/e1_view.py: preserve true unit forms through every noise switch; generated false positives have form 0; no added random draws.
- pipeline/e1_eval.py: enable adapter before reset, select features per policy in mixed matches, preserve flags through compacting, and derive forms from the same noisy/extrapolated view as tokens. History dt uses that view's tick.
- pipeline/rl_royale.py: versioned actor construction, policy/value inputs, recorded trajectory collation, pro-agreement repacking and batching; descriptive rejection of legacy pro-agreement data for v3.

search_s0.py and run_screen.py require no direct edits: both use the completed shared e1_eval entry points. The trainer subclass remains intact.

## Parity and identity

The production SelfPlaySide.prepare/gen_row path was compared against recording tagging and feature construction on an actual RoyaleSim replay, for both sides. **232 side views, 52 accepted plays, 836 unit tokens: 58 evolved and 30 hero. Exact array equality for unit_form and opp_past.** Accepted actual forms include 0, 1 and 2. See sim_parity_result.json.

Legacy checks use the previous worker's unchanged baseline snapshots plus snapshots taken before this continuation, without git. The actual rseries_r1_u0155 checkpoint was checked under versions 1 and 2: rows, heads, sampled decisions, trajectories, observation/behaviour/Python RNG states and serialized engine state remain byte-identical. Shared GenRows and RL collation/policy terms/value passes also match their pre-edit snapshots.

Additional checks cover delayed landing at tick 116, strict-before-tick history, rejected plays, reset, true/false-positive noise forms, noise RNG identity, extrapolation alignment, isolated fork logs, v1/v2/v3 mixed policies, actual S1/v3 mixes, actor weight loading, shared/trainer batch parity and pro-agreement repacking.

## CPU smokes

CUDA_VISIBLE_DEVICES was empty; torch used two CPU threads. The provided roundtrip checkpoint has synthetic integer vocabulary entries, so the permitted alternative was used: a freshly initialized tiny v3 model with gen_v1's real card vocabulary, saved under sim_smoke_20261003_120206/fresh_v3.pt. No training.

| Instrument | Matches / rows | Unit tokens | Evolved / hero | Rows with opponent plays |
|---|---:|---:|---:|---:|
| run_screen, pinned-299 subset, tau .27, forms deck | 1 / 47 | 142 | 0 / 0 | 42 |
| search_s0 plain vs frozen gen_v1, forms deck | 1 / 81 | 215 | 0 / 0 | 72 |
| Tiny v3 RL rollout, collate + gae_batch | 1 / 51 | 139 | 0 / 9 | 50 |

The ghost and reactive matches completed by engine game-over (both random-v3 losses, 0-3); neither was wall-truncated. These random-weight results are integration evidence, not policy-quality evidence. RL collation retained 19 contributing rows (12 plays); recomputed behaviour log-probabilities agree within 1e-5, and GAE advantages/returns are finite. The two full-match smokes encountered only base opponent plays; the RL smoke saw actual forms 0 and 2, and replay parity covers evolved forms. See sim_smoke_result.json and the per-match output directory.

## Validation commands

```powershell
$env:CUDA_VISIBLE_DEVICES=''
$env:OMP_NUM_THREADS='2'
$env:PYTHONDONTWRITEBYTECODE='1'
research/ext/Royale/.venv/Scripts/python.exe -m pipeline.tests.gen_v3.run_sim_tests --tb=short
```

The runner includes every gen_v3 test, test_rl_*.py, test_e1*.py, test_search_s0*.py and test_hero_abilities.py. It uses workspace temp directories because Windows mode-0700 temp directories are denied here. Two inherited E1 serialized goldens are upgraded in memory only with Unit.form=0; all old fields stay unchanged. Five historical git-show tests are deselected under the no-git instruction, with current pre-edit snapshot identity covered separately. One multiprocessing exit test is skipped only when its Windows pipe probe raises PermissionError; in-process actor construction and v3 weight loading pass.

Re-run bounded smokes, if desired:

```powershell
research/ext/Royale/.venv/Scripts/python.exe -m pipeline.tests.gen_v3.sim_smoke
```

## Requested launch commands (prepared, not executed)

Run from the repository root. Set $v3 to the trained v3 checkpoint; its stored args.feature_version must be 3. The RL command requires the completed v3 dataset with matching card_vocab. All commands below explicitly use CPU.

```powershell
$env:CUDA_VISIBLE_DEVICES=''
$py='research/ext/Royale/.venv/Scripts/python.exe'
$v3='icebow/data/pipeline/gen_v3_s0/gen_s0.pt'

# Ghost screen: all pinned 299 tags, tau .27, forms deck.
& $py scratchpad/gauntlet/L68/generalist/screen_gen/run_screen.py --ckpt $v3 --out pipeline/tests/gen_v3/launch_ghost.jsonl --split train --only-tags-from scratchpad/gauntlet/L68/generalist/lat26/screens/train_C.jsonl --tau 0.27 --seeds 0 --forms-mode deck --noise-off all --opp-elixir counter --action-delay 26 --extrapolate 26 --device cpu --threads 2 --batch 16

# Reactive plain-arm acceptance vs frozen gen_v1; 24 seeds.
& $py -m pipeline.search_s0 --gen $v3 --opp-gen icebow/data/pipeline/gen_v1_s0/gen_s0.pt --out pipeline/tests/gen_v3/launch_reactive --arms plain --opps gen --seeds 0:24 --forms-mode deck --device cpu --threads 2 --workers 1

# R1 recipe, v3 initialization and v3 pro-agreement data; no training was launched.
& $py -m pipeline.rl_royale --config scratchpad/gauntlet/L69/rl/r1_rl_royale.yaml --run gen_v3_r1 "init=$v3" proagree_data_gen=icebow/data/pipeline/gen_dataset_v3.npz league=true noise_off=all opp_elixir=counter action_delay_ticks=26 extrapolate_ticks=26 max_updates=155 'screen_seeds=[0]' league_learner_icebow_share=1.0 forms_mode=deck league_decks=scratchpad/gauntlet/L69/pool/loadable_decks.json advantage=gae gae_gamma_unit=tick gae_gamma_tick=0.99994 gae_lambda=0.95 gae_terminal_gap=false critic_warmup_updates=5 shaping=none learner_device=cpu actor_device=cpu
```

## Boundaries and concerns

No training jobs, GPU jobs, full screens/reactive runs, adb/live_play, git, agents, or dataset builds were launched. No edits were made to train_gen.py, dataset*.py, obs_contract.py, live_gen.py or icebow/data/pipeline/gen_dataset_v3.*. dataset.py changed externally during the task (after an earlier validation); the final suite was rerun against the changed workspace. Protected starting hashes are retained in protected_hashes.json.

The multiprocessing pipe test cannot be completed in this sandbox. No inference or parity failure remains. Historical git-based tests were not executed. Search coverage requested here is the plain arm; v3 mixed-model search rollout arms are outside this acceptance run.
