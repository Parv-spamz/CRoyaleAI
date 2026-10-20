# Readiness measures

All64 initial/final state hashes, forms, actual terminal winner/crowns/tick,
full and late decision/contributing counts, early-empty games, sampled PLAY/WAIT,
remaining time and contributing decisions to terminal, public history retention,
unchanged parameters, finite gradients and zero optimizer updates.

For every late contributing row, recompute unchanged-policy joint probability;
all finite and abs(expm1(recomputed - original)) <1e-4. Log canonical NumPy maximum.
Per match reward +1/-1/0 from native outcome only; gamma_tick.99994, terminal gap
preserved. Independent backward recurrence validates GAE for lambda.95 and1.
Full-batch late-row raw advantages/returns must equal late-view raw values EXACTLY.
Independent recomputation summary tolerance1e-12 is prospective; array membership,
features/actions/probabilities/native byte hashes/source bindings remain exact.

For exact recurrence comparison, use the same saved full-batch critic values in
both recurrences. Separately recompute late-only values and measure their batch
shape numerical difference, requiring max absolute difference<1e-5. This is
prospective engineering tolerance on this diagnostic only; raw recurrence
equality stays exact and earlier experiments' exact-output failures stay failed.

Late equal-match row weights:1/(number of nonempty late matches * that match's
contributing row count). Normalized advantages are calculated over all late rows.
First min(256,late rows) fixed backward probe, actor and critic separate. Require
finite nonzero gradients and identical every checkpoint tensor; no optimizer.

Coverage minimum4 nonempty late matches and256 late contributing rows. Do not
infer strategic opportunity, physical trade, Rocket lead/cycle/finish quality,
R1e superiority or statistical significance from this engineering minimum.
