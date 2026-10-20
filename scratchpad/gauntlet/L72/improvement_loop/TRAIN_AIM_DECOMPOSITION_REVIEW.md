# Rocket aim has errors in both learned spatial terms

The exact previous 830 training rows and three checkpoint hashes were reused;
no new rows, held-out predictions or optimization occurred. Full predicted aims
match the earlier diagnosis. The spatial-patch, query-conditioned cell-position
and shared-bias terms reconstruct actual logits within 3.82e-6. Independent
original-label/selection/cache recount passes for all nine Rocket cohort/model
comparisons, with two positive and five corruption/precision controls.

Teacher-forced aim within two tiles of the original expert cast:

| Checkpoint | Finishing full | Finishing without position | Combo full | Combo without position |
|---|---:|---:|---:|---:|
| R1e | 13/65 | 18/65 | 140/256 | 111/256 |
| Ordinary IL | 15/65 | 16/65 | 143/256 | 127/256 |
| Rocket-exposure IL | 16/65 | 19/65 | 145/256 | 120/256 |

Even the R1e finishing increase replaces four previously correct aims with errors
while gaining nine. Removing spatial patches is worse: R1e combo aim falls to
42/256. Removing the shared cell bias leaves R1e finishing unchanged at 13/65
and only moves the Rocket-exposure arm from 16 to 17. Thus a simple bias removal
or one-term deletion does not provide a broadly useful fix.

On R1e's 52 finishing misses, the spatial term contributes the larger erroneous
preference in 24 rows and the position term in 28; shared bias in none. For the
Rocket-exposure arm, these counts are 18 and 31 among 49 misses. Full probability
mass within the expert neighborhood averages 27.90% for R1e and 28.66% for
Rocket-exposure IL. More Rocket card exposure barely improved that aim mass.

Interpretation: aim needs a learned improvement that retains both troop geometry
and tower targeting, not a forced tower preference. Towers currently enter global
scalars rather than direct unit tokens; transformed spatial patches still receive
global context. This structural fact is not proof that a particular new tower
encoding would fix the errors. Keep generic target-residual and sequence exposure
as separate controlled experiments, and consider a separately registered generic
public tower representation experiment only with its own controls after N2.
No decoder ablation is enabled, and these results do not establish a new model,
physical Rocket impact, generalization or gameplay benefit.

Independent verifier v1 failed because float32 label scaling changed two-tile
boundary membership. v2 promoted labels first but distributed multiplication
before subtraction, changing some boundary neighborhood mass through rounding.
Both sources/receipts remain preserved. v3 uses the original normalized-coordinate
subtract-then-scale convention in float64, retains the exact two-tile threshold
and passes all counts/masses/margins. The producer and original full predictions
were not changed to make verification pass.

Evidence: train_aim_decomposition.json, train_aim_decomposition_verified.json,
the bound ignored components.npz and l72-train-aim-decomposition* receipts.
