# Acceptance scorer review, October 5 03:00 EDT

Read before all candidate results were available. This review does not change the
frozen recipe, thresholds, training data or held-out cohorts. The running worktree
and its scorer remain unchanged.

`context_teaching/score_experiments.py` verifies source/input/output hashes,
receipts, all 1,000 finite training updates, recipe/initialization, prediction
hashes, cohort counts, 299 ghost pins and 48 reactive games. It enforces source
and primary-control global agreement and gameplay gates, with an extra
v5_rocket versus v4_rocket gameplay comparison. A partial report cannot nominate
a candidate. Independent prediction recount is still required after the chain.

The output is provisional for two reasons:

1. PLAN.md says Rocket-exposure gameplay must move Rocket share toward 0.058
   and increase tower Rockets versus the primary control. The scorer uses the
   ordinary-mixture control (v4_uniform or v5_uniform) for every Rocket arm.
   These controls coincide only for v4_rocket and v5_rocket. For a combined
   candidate, final review must also check the literal primary-control
   comparison in PLAN.md; retain the existing ordinary-control requirement too.
   Do not replace either with a more favorable comparison. Input/Barrel
   corrections do not independently require an invented Rocket improvement,
   but an accepted combined Rocket-exposure claim must meet its declared gates.
2. The scorer checks each combined arm's diagnostics but does not prove every
   included component through its one-factor comparison. For example, later
   version-5/6 arms compare spawner agreement to v4_rocket, and v6_rocket_both
   compares Barrel outcomes to v5_rocket_barrel. Those aggregate checks do not
   isolate the identity, spatial residual or extra X-Bow exposure. Review the
   registered one-factor rows and component support explicitly before combining
   or attributing improvements. Do not deploy solely from provisional_selection.

Keep a final matrix of each candidate, applicable component comparisons,
source/primary gameplay, ordinary/primary Rocket behavior, exact denominators
and every rejection. Reject an unsupported combined candidate; do not tune or
relax the frozen plan. A supported simpler arm may remain eligible under its own
declared gates. Report finish-offs and both combo orders separately from wins.

The simulator update adds a second provenance requirement: any deployment
candidate must retain applicable source, primary and component controls in
fresh same-code comparisons on the updated runtime. Existing frozen old-engine
results cannot be paired with the new engine. Rocket area aim, if considered
after accepting a learned candidate, needs its separately declared comparison.

This is a static code/plan review, not a candidate verdict. Independent cache
recounts, actual gameplay, final component adjudication and live verification
remain open.
