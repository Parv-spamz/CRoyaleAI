# Prospective descriptive measurements

Both orientations:512PLAY,64percard,21lateRocket. Count ON/OFF aim<=1tile and
exact original floor-cell target, ON versus OFF gains/losses/ties, cellchanges,
same-patch/different-patch misses. Retain row and replay denominators, per-replay
counts and all8cards. No new acceptance threshold or changed geometric tolerance.

For each row record full/base target negative log probability, target minus best
other-cell margin, and the residual logit range in the expert patch. Record the
residual contribution to target-vs-base-winner margin and the original base gap.
Aggregate mean and median for all PLAY, Rocket, lateRocket and each card. Record
mean loss-component values for the original fit's first/last256updates from its
saved logs, not new optimization or trajectory selection.

Engineering: exact saved row/label/cache joins and ON prediction identity;
exact float32 base+residual=full; all finite; fixed2304cell geometry. Independent
float64 base/residual reconstruction uses atol5e-4,rtol2e-5 against GPUfloat32
scores, declared prospectively; this does not waive any earlier exactness gate.
Recount uses saved float32 full/off arrays with float64 CE and geometry; aggregate
float summaries agree within1e-10, integer counts/perreplaycounts exact. No scoring
of private inputs, no p-values/generalization claim, no new policy or deployment.
