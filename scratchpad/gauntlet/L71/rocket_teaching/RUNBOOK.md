# Rocket curriculum: prepared, not trained or deployed

The original learned six-context probability scales a row's loss by `1 + (weight-1)*p`. Rare-combo probabilities are tiny (existing held-out combo mean about .00014), so a nominal 4x maximum is not 4x exposure to observed combo sequences. This experiment changes **training row sampling only**, while preserving expert cards, timing, coordinates and WAIT targets.

The public annotation uses the owner's >=9 elixir, >=2 troops, HP > two Logs and post-Rocket HP <10% of maximum criteria. Level11 catalog damage is Rocket1484/Log268. Costs count once per causally attributed deployment. Compact groups fit Rocket's two-tile centre-coverage disk; spread groups fit Tornado's5.5-tile disk but not Rocket's. Unsupported forms, shields/pull immunity, child bodies and ambiguous births are excluded. These are conservative opportunity cohorts, not proof a pull will complete before impact. No detector threshold is used to force a live play.

The fixed mixture is **80% ordinary Icebow training rows, 10% qualifying opportunity rows, 10% complete expert Rocket windows** (2s lead-in through1s after impact). Windows preserve Rocket -> Tornado order, waits, other defences, tower finishes and recorded repeated Rockets. Existing v4 public unit positions, own past plays, projectiles/TTI and effect tokens are the model inputs. The unchanged card/gate/cell heads learn when and where to act; there is no combo macro and no runtime requirement to cast Tornado after Rocket. Rocket-only area aim remains a separate inference option; Tornado location/timing remains learned.

Built from2,262 replay sources:268,718 train rows and38,317 held-out rows, replay-disjoint. Training cohorts:2,281 opportunity rows (1,143WAIT);16,226 Rocket-window rows (8,869WAIT);1,697 combo-window rows containing457 Rockets and457 Tornados. Held-out combo windows contain69 of each action. The masks and hashes live in ignored `icebow/data/bench/rocket_teaching_20261004/`; tracked `report.json` contains the reconciled summary. Unsupported/ambiguous exclusions are reported, not silently treated as proven negatives.

Preparation checks: boundary/geometry/cost/privacy/split/sampling/checkpoint tests; a real R1e CPU forward/backward using actual public training rows; independent count/window/hash reconciliation. The smoke saves **no checkpoint**, is not a learning-result claim and is not deployed. The checkpoint layout is unchanged and loads through existing model/SIM/candidate live loaders.

## GPU experiment, fixed before outcomes

First finish Q3 inference acceptance in `../decision_options/RUNBOOK.md` for both R1e and old R1. The current live worker owns the GPU; no competing job has been launched. The owner chooses when to pause live at a match boundary.

Then two arms start from the exact same R1e u0155 checkpoint: uniform Icebow sampling control and the fixed curriculum. Both use seed20261004,1000steps,batch128,AdamW lr1e-5,weight_decay.01,gradient_clip1,50%mirroring,existing imitation losses. Save the final step only; no selection or tuning on held-out results. The only arm difference is row sampling. This is imitation fine-tuning, not a new RL reward or PPO run.

```powershell
# Run sequentially during an exclusive GPU window. Fresh output directories required.
icebow/.venv/Scripts/python.exe -m pipeline.train_rocket_curriculum --data icebow/data/pipeline/gen_dataset_v31_public.npz --curriculum icebow/data/bench/rocket_teaching_20261004 --init-ckpt icebow/data/bench/rl_royale/rseries_r1e31/rseries_r1e31_u0155.pt --out icebow/data/bench/rocket_teaching_uniform --arm uniform --device cuda
icebow/.venv/Scripts/python.exe -m pipeline.train_rocket_curriculum --data icebow/data/pipeline/gen_dataset_v31_public.npz --curriculum icebow/data/bench/rocket_teaching_20261004 --init-ckpt icebow/data/bench/rl_royale/rseries_r1e31/rseries_r1e31_u0155.pt --out icebow/data/bench/rocket_teaching_candidate --arm curriculum --device cuda
```

Re-run held-out card/gate/aim diagnostics, including285 geometric opportunity rows,69 combo sequences and10 observed finishing Rockets. Measure both actions and timing in prospective play, not only teacher-forced Rocket recall. Compare original R1e, uniform fine-tune and curriculum using the SAME inference options/code: pinned299 ghost, reactive gen/S124each, public behaviour telemetry. Deployment requires nonnegative paired ghost point estimate, no more than2/48 reactive wins lost, and Rocket/tower/defensive/combo use moving toward the pro baselines without increased waste. Reject a usage increase accompanied by lower win value. Geometry alone never establishes a combo success.

After measured acceptance, publish the exact candidate checkpoint/options and live decision. Candidate `live_play_v2.py` already supports unchanged architecture, optional filtered selection, Rocket area aim and `--no-anti-leak`; active supervisor remains on the original script. Verify match-start checkpoint/options/seed and accepted plays after any authorized switch. Never describe a prepared recipe or unit test as live deployment.

## Remaining queue

See QUEUE.md: spawner investigation/proposal first after Rocket work, then dead-lane X-Bow support-spending investigation. Neither requested investigation authorizes a tactical hardcoded policy.
