# Prelaunch metric and execution contract

All evaluation uses the fixed54723 inner-development rows only. These historical
examples were seen by parent R1e; results do not prove unseen generalization.
R1e is evaluated on the SAME corrected-v5 observations as both trained arms,
using a weight-identical v4-to-v5 migration. Do not call it unchanged live-input
R1e. Final live/generalization comparisons still require their separate gates.

No sampling or area aim: affordable-hand argmax, gate sigmoid>0.35. Affordability
is the existing public own-elixir floor(sc[3]*10+0.001) and pinned card costs.
Action agreement is correct WAIT, or called correct expert card with expert-card
cell argmax within1 tile (normalized subtract then float64 scale by18,32).
Report original expert PLAY card agreement and all-row action agreement, counts
and per-replay numerators/denominators. Exact cells, gate probabilities, masked
card logits and forced Log cell predictions are retained for independent recount.

Witch, Night Witch and Furnace masks use their ORIGINAL enemy token identity,
fixed across arms; separately report corrected-parent-present and child-only
subgroups. Original source may have mislabeled children; this limitation persists.
Barrel: exactly one enemy public Barrel, target finite and x in[0,1],y in[.5,1],
x<.4 or x>.6, affordable Log in hand. Primary expert rows also have PLAY Log
with expert aim on that target's lane. Report fired correct/wrong, no-fire,
forced Log lane and full action counts. Retain other-PLAY, WAIT, multiple,
ambiguous and no-Barrel strata. No damage/landing claim from aim agreement.
Rocket expert rows receive gate/card/within1/within2 tile diagnostics and existing
finish/combo flags, explicitly narrow historical labels. No low-HP-state label
is converted into an expert Rocket action. Spawner and Barrel denominators are
frozen before prediction in prelaunch.json; missing strata are inconclusive.

Continuation filter remains PLAN.md: v6 improves correct gated Barrel responses
without increasing wrong lanes versus ordinary_v5, card agreement loss<=0.5pp,
and no action point regression in each spawner family. This is a developmental
filter, not final acceptance, a p-value claim or permission to deploy. All R1e
comparisons are reported, including failures. Candidate final-step only.

Shared augmentation clarification before optimization: pipeline.train_gen.losses
previously preserves unknown projectile x only for v6, but mirrors it for v5.
Both new arms use the same v6 unknown-coordinate convention applied externally,
then the ORIGINAL unmodified loss with mirror=False. Known positions, labels,
ordinary tokens/scalars/history follow the original mirror_gen. This removes a
preprocessing confound; no loss weight, target or runtime action rule changes.
Verify equality with the original v6 mirrored loss and both arms' equal initial
outputs/dropout stream. Record this shared preprocessing in every run.

Save the full1000x128 row draw schedule and1000 mirror bits before launch. Both
arms must consume exactly it; reset torch seed20261005 after construction. Use
fp32, no AMP or scheduler, fixed optimizer/clip/budget from PLAN. Training reads
only saved training rows; evaluation reads only saved development rows. Smoke
uses CPU, saves no checkpoint, and is never counted as full training. All imported
pipeline Python sources, local scripts, model/data/cost inputs and runtime are
hash-bound before launch. New RL is a separate updated-runtime experiment.
