# Saved outcome-training credit independently reconciled

October5 20:37 EDT. C1-C3 COMPLETE. Producer3.54s, independent8.64s and review.17s
exit0/token matched. All73783 contributing rows/32updates/256matches/112groups,
per-update/per-match summaries and original command joins reconcile. Five
positive/nine corrupt controls pass. No inference, backward pass, optimization,
new checkpoint, native replay, development or confirmation exposure.

Warmup:10632 rows/40matches, no policy optimization. Policy phase:63151 rows/
216matches,9433 PLAY and53718 WAIT. Original commands:9357accepted,15refused,
61unlanded,zero unknown. Every failure remains included. Policy Rocket253 rows/
139matches:252accepted,oneunlanded;135positive and118negative normalized advantages.
Those advantage signs are training signals, not correctness or tactical benefit.

Rocket decisions were9 within10 seconds of termination,31 at>10..30s,43 at
>30..60s and170 at>60s. Median Rocket lag97.75s/112 remaining contributing
rows. Direct terminal-reward coefficient under original gamma.99994/lambda.95
has median.00280814 overall; in the170 >60s Rocket rows it is.000133945.
This holds critic predictions fixed: learned bootstrap estimates can still
carry future-outcome information. It does not establish a credit bug or prove
these Rockets caused their match outcomes. Near-terminal includes the unlanded
Rocket, illustrating why reward association is not physical effectiveness.

Original per-match-weighted initial gate-logit score sums across27 updates:
PLAY -.21376972,WAIT +.11758775,net -.09618197;Rocket -.00361357. Positive would
increase an individual tempered gate logit at the behavior policy. The aggregate
is not a neural parameter gradient, actual Adam step or causal policy change.
The net negative arithmetic comes from PLAY terms; more WAIT rows alone does
not establish that their contribution pushed the gate toward waiting. Mean
saved normalized advantage PLAY -.105514/WAIT +.018529/Rocket -.094264 also
must not be substituted for probability-weighted gate-score arithmetic.

Result supports a bounded hypothesis test of full-return credit (lambda1) while
retaining the same parent, setup schedule, reward and budget. It does not prove
lambda1 will improve Rocket or gameplay. development_rl_2 separately registers
that single factor; no critic detach, loss/LR grid, tactical rules, new labels or
reward for spell frequency. Original outcome_rl_v5 stays rejected/reported once.
Final material/physical/gameplay/untouched/statistical/Q4/Q5 gates remain open.
