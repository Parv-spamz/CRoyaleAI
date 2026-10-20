# Fixed descriptive metrics

Universe: original73783 contributing training rows; per-update and per-match
membership preserved, with raw noncontributing decision counts also retained.
No original expert or development labels enter this audit.

Rows contain update1..32, original match0..7/tag/side/outcome, raw decision index,
tick/end_tick, played/gate_sampled, slot/cell, original issued card/status,
saved normalized advantage, return, old value, step reward, row gamma, per-match
weight, sampled gate probability, gate-score and terminal coefficient.
WAIT rows have no invented card or physical outcome. Only played rows join
commands. Terminal reward +1/-1/0 comes from the original actual native result.

Groups: all/warmup1..5/policy6..32 crossed with all/PLAY/WAIT/Rocket and every
observed played card; original W/L/D outcomes; and policy Rocket distance bins
0..10, >10..30, >30..60, >60 seconds before termination (20 ticks/second).
These bins describe temporal credit, not phase, elixir multiplier or tactical
opportunity. Group counts do not claim independent statistical power.

Report n, distinct matches/updates, positive/negative/zero advantages, means of
advantage/absolute advantage/return/value, weighted signed/absolute advantage,
gate sampled counts/initial signed and absolute gate-score sums, accepted/refused/
unlanded/unknown command counts. Report min/median/max for remaining decisions,
terminal distance and direct terminal coefficient; no post-result thresholds.
Also report direct terminal reward contribution before batch normalization.
Every per-match and per-update group uses the same frozen definitions.

The score is the derivative direction for increasing the tempered gate logit at
the behavior policy before clipping/KL: w*A*(y-p). Positive suggests increasing
that individual logit. It is not the parameter gradient or final policy effect.
Weights are original match_weights: each nonempty match totals1/M.
Terminal coefficient analytically propagates only the terminal reward through
GAE while holding the recorded critic values fixed. Small coefficients do not
prove absent long-term learning because the critic supplies bootstrap estimates.

Preserve refused/unlanded/unknown commands and all outcomes. No reward for Rocket
frequency, no estimated hit/splash labels, no acceptance or causal benefit claim.
