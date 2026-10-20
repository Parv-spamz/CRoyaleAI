# Frozen diagnostic measurements

Eight caches:512PLAY each,64/card,21late Rocket,439PLAY replay groups per cache.
Report allPLAY,all8cards,Rocket,lateRocket with exact counts and per-replay counts:
original continuous aim<=1tile; floor vs lattice exact target; same/other target
patch misses; label changes; near-boundary distances (descriptive only, no waiver).

Two saved logit archives: ON/OFF argmax unchanged, target CE and target-minus-best
other margin using actual lattice labels; direct residual target-vs-OFF-winner,
OFF-winner target gap, expert-patch residual span. Compare old floor calculations
without overwriting them. Independent float summaries abs<=1e-10, integers and
joins exact. Label mapping must agree exactly with existing cell_label(grid=lattice).

Positive controls include full native/mirrored arrays and synthetic half-integer,
edge and jitter cases; malformed controls must reject wrong grid, target, original
row/label/choice joins, NaN score and altered summaries. All weights and files
remain unchanged; zero inference/backward/optimizer. No p-values or generalized
performance claims, no acceptance-floor substitutions.
