# Training-only stage diagnosis, October5

`diagnose_train_rocket.py` asserts split0, selects830 rows with fixed seed20261005, records source/context/checkpoint hashes, and evaluates R1e plus ordinary-IL and Rocket-exposure controls on CPU. `train_rocket_diagnosis.json` contains per-row predictions, full denominators and probability mass. Receipt `L71/integration/checks/train-rocket-diagnosis.json` is exit0/PASS. This is development diagnosis, not generalization, new training or acceptance.

On65 finishing-Rocket expert plays from65 training replays:

| Checkpoint | Gate passes | Correct card | Expert-forced aim within2 tiles | Gated correct card and aim |
|---|---:|---:|---:|---:|
| R1e |59|4|13|2|
| ordinary IL |60|15|15|3|
| Rocket IL |61|38|16|10|

The gate is usually open. Exposure primarily improves card choice; conditional placement changes much less. Finishing aim remains poor even on these training examples. The fixed128,000 sampling draws expose finishing-Rocket plays only31 times in expectation under uniform and76 under the Rocket mixture, despite65 distinct expert examples. These are probability-derived expectations, not observed sample counts.

On256 sampled combo Tornado plays, gate passes113/122/131, correct-card counts162/182/195 and gated aimed responses31/40/46 respectively. Combo timing/gating also warrants separate diagnosis. On256 combo Rocket plays, the Rocket arm improves gated aimed responses28->105 but teacher-forced aim only140->145. Full row tables remain available.

Next: audit untouched replay-separated confirmation data and declare successor comparisons before training. Diagnose cell losses and target representation on train/development; isolate one-factor aiming, rare-situation exposure and generic projectile-target residual changes. Preserve ordinary-IL controls and actual gameplay gates. Expert-cast distance is not simulated impact, and replay-derived finishing labels never become future-information inputs. Do not tune on the inspected L71 holdout or equate more Rockets with better gameplay.

The original frozen chain stopped between jobs after29/34 receipts because an owner-started live worker was present. Once that session and rendering exited, normal resume at05:38:49 failed before jobs because main was legitimately integrated after Q3; its old source comparison cannot be rerun against current main. RESUME.md and resume_verified_chain.py preserve the captured Q3 verification against the published hash and independently recheck all completed receipts/outputs plus current frozen worktree sources/inputs. Verification and corruption controls pass. The separate resume launched05:43:08 (launcher44060); read chain_resume_verified.out/.err and resume_verified_launch.json here. All original source/results and failed launch logs remain unchanged. Do not duplicate jobs.
