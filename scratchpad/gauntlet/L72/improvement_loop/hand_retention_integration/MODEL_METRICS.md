# Prospective learned representation and integration qualification

Architecture tag public_hand_belief_v1, base feature_version=5 and explicit
hand_belief_version=1. Fresh tensor-identical ordinary_v5 portable parent only.
Card embeddings plus five public per-card belief scalars feed a shared MLP and
masked mean/max pooling. A second MLP combines that pool, existing global board
representation and five quality flags. Its zero-initialized final layer adds a
learned residual to the global representation used by every existing action head.
No card counter table, rule, mask, priority or reward is added.

Matched control uses the SAME architecture/parameters/initialization but masks
the new hand tokens and quality flags to a constant untrusted/unknown input.
This separates the added information from simply adding trainable capacity.
Both start output-identical to v5. Original v5 remains a separately cached control.

Qualification before learning: all initial base tensors and every output/head
and original loss exact on 128 training rows in both orientations; finite backward
gradients without optimizer or weight change; strict metadata/state/shape failures;
in-memory roundtrip; nonzero diagnostic branch demonstrates feature sensitivity,
blank-control invariance, card-order invariance and live-row causality/privacy.
The diagnostic perturbation is unsaved and never a policy/training parent.

New opt-in live companion supplies the same public tokens from the normal memory
PublicObserver, records their uncertainty in the public audit and resets with the
normal match observer. Existing live files/processes stay unchanged while the owner
is playing. Companion entry reuses canonical CLI/actions in its own new process;
it never launches itself. No hidden opponent hand/deck/next/elixir is consumed.

Separate training metrics must freeze paired seed/draws/optimizer/budget, final-only
selection and ALL original component/material protection floors before optimization.
This qualification alone establishes neither profitable retention nor better play.
