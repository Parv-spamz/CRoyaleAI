# Training-only Rocket aim decomposition

Extend the existing stage diagnosis without changing models or sampling rows.
Use the same hash-bound split-zero row selection and three checkpoints from
train_rocket_diagnosis.json (R1e, ordinary IL, Rocket-exposure IL). Never read
confirmation predictions, optimize weights or change live settings.

The actual cell head sums a query-conditioned spatial patch term, a
query-conditioned learned cell-position term and a shared cell bias. Record
these separately and require their sum to reconstruct the actual cell logits.
Require full-model predicted positions to match the previous diagnosis. Keep
the established expert-distance diagnostic (within two tiles), explicitly not
physical impact or gameplay success.

For the fixed finishing, combo-Rocket and ordinary-Rocket cohorts, compare the
full head with each term removed and each isolated term. Report gains AND losses
relative to full aim, expert-neighborhood probability mass and the contribution
of each term to the full prediction's margin over the best expert-neighborhood
cell. This tests a mechanism; no ablation will be enabled in play from this audit.
Spatial patches also receive transformed global context, so a spatial term is
not a pure local-unit or tower-information channel.

Save components, row IDs, original labels and membership to a hash-bound ignored
cache. Independently recompute agreement, margins, gains/losses and probability
mass with NumPy. Exercise a known positive and corrupt reconstruction/shape
controls. Preserve failures. Interpret training results without a generalization
claim; any supported learned change needs a separate registered experiment after
N2. No tactical tower preference, target override or reward-frequency rule.
