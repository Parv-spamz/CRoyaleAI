# Fixed expert-context experiment, October 5

Written before any full training. Owner authorizes implementation and accepted deployment. No hand-written tactical choice is added.

All arms start from R1e u0155. Each runs exactly 1,000 updates, batch128, seed20261004, AdamW weight decay0.01, base learning rate1e-5, gradient norm cap1, 50% horizontal mirroring, unchanged expert losses. Version6's new target projection/convolution uses learning rate1e-3; it starts as an exactly zero residual. Final step only; no held-out checkpoint selection, tuning or repeated seeds. Data version4 is the original public dataset; version5 is the independently verified `spawner_identity_20261005` artifact. Cohort hashes, datasets, checkpoint, source code and commands are frozen in the run manifest.

| Arm | Observation/model | Mixture | Primary one-factor comparison |
|---|---|---|---|
| v4_uniform | original | ordinary100% | untrained R1e; effect of further imitation |
| v4_rocket | original | ordinary80/opportunity10/sequence10 | v4_uniform |
| v5_uniform | corrected bodies | ordinary100% | v4_uniform |
| v5_rocket | corrected bodies | ordinary80/opportunity10/sequence10 | v5_uniform; v4_rocket isolates identity |
| v5_rocket_xbow | corrected bodies | ordinary75/opportunity10/sequence10/X-Bow5 | v5_rocket |
| v5_rocket_barrel | corrected bodies | ordinary75/opportunity10/sequence10/Barrel5 | v5_rocket |
| v6_rocket_barrel | corrected bodies + learned spatial target residual | same as preceding row | v5_rocket_barrel |
| v6_rocket_both | corrected bodies + learned spatial target residual | ordinary70/opportunity10/sequence10/X-Bow5/Barrel5 | v6_rocket_barrel |

Every mixture preserves WAIT and all expert card/cell labels. Future labels identify offline cohorts only; they never become model inputs. Version6 also preserves unknown projectile targets during mirroring, required by its explicit target mask. The identity resolver handles Witch, Furnace, **Night Witch**, huts and Tombstone. No hypothetical future spawns are inserted.

Held-out diagnostics use all38,317 Icebow validation states, with existing per-cohort denominators. Global pro-card agreement may fall by at most1 percentage point versus the primary control and untrained source. Identity adoption requires increased combined spawner action agreement and Night Witch action agreement no more than2pp below control. Context action agreement means correct WAIT, or gated correct card with aim within1 tile of the expert on PLAY; it is an imitation diagnostic, not a win estimate.

Rocket exposure must increase gated Rocket recall, include at least one correctly aimed gated finishing Rocket (the original finishing PLAY subset has10 rows), and improve both Rocket and Tornado card recall in expert Rocket-then-Tornado windows relative to its control. Report compact/spread opportunity, tower and finishing results separately. No claim of reliable finish-off or combo mastery follows from a single successful case.

X-Bow exposure must improve held-out context action agreement without lowering the useful-bow subset by more than2pp. Reduced spending alone is insufficient. Barrel exposure/architecture must improve gated correct-lane Log responses on the39 unambiguous pro-Log cases without increasing wrong-lane fired Logs, and retain global agreement. Report forced-Log aim separately; other/paired-flight rows remain visible.

All trained arms receive fresh same-code299 pinned ghost and48 reactive games (gen/S124 each, deck forms, abilitiesv2), alongside a fresh untrained R1e baseline. Adoption additionally requires ghost win-point delta>=0 versus untrained source AND primary control, reactive wins>=each comparator minus2/48, complete nontruncated matches and telemetry. Rocket-exposure adoption requires ghost Rocket share closer to the pro.058 reference and more tower Rockets than its primary control. Record actual finish-offs and combo counts separately; do not substitute expert agreement for game outcomes. Spawner and Barrel changes need no artificial Rocket-share gain merely to correct observations or placement.

Combine only supported components. Prefer the most complete arm that passes all applicable component, source and gameplay gates; if several otherwise equivalent arms pass, prefer higher ghost wins, then reactive wins, then fewer new components. A rejected arm stays disabled. After selecting an accepted learned candidate, test Rocket area aim against that exact checkpoint in a separate fixed comparison using the original Q3 win and Rocket-behaviour criteria. No filtered sampling unless its own frozen Q3 comparison passes.

Simulator matched-state support/WAIT rollouts are diagnostic only, use the same real opponent policy and later learner decisions in both branches, and charge every accepted follow-up. They are not policy inputs or training targets. Public live snapshots then permit checking actual target/body-to-decision wiring. Preserve live anti-leak OFF; SIM's existing anti-stall remains fixed and explicitly different.

One GPU process chain at a time. Training waits for the entire Q3 chain to exit, not a gap between jobs. No deployment until acceptance and source integration are verified.
