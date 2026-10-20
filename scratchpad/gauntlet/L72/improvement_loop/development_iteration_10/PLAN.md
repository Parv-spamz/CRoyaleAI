# Dropout-free ordinary development comparison

Registered October6 before any new preparation or optimization. The independently
verified dropout_free_fit assay passed its original criteria: fullPLAY468/474 of512,
Rocket aim64/63 of64, with512/512card andWAIT preserved in both orientations.
Original-dropout matched fit was417/418fullPLAY and51/49Rocket aim. This supports
reduced-regularization fitting of that sample, NOT development generalization.

Test ONE factor on the broader original training set: training dropout. Use the
ORIGINAL architecture and a FRESH ordinary_v5 portable checkpoint SHA
c0ba1ab910df50fdcbe1fcf4191aedd584c86fe94c5a6d3248359bda059db419.
Disable all16 nn.Dropout.p and MultiheadAttention.dropout attributes .1->0 in an
isolated loader. No local-cell branch, labels, features, card rules, losses,
optimizer changes or reward. Never load quarantined fit/rejected weights as parent.

Match the completed development_iteration_9 ordinary_extended_v5 run EXACTLY:
8000updates,batch128,seed2026100609,its1024000row draws and mirror flags,
original213995training rows,uniform replacement,50%whole-batch mirroring,
freshAdamW1e-5,wd.01,clip1,fp32,original lattice labels/loss. Independently regenerate
and compare the entire original schedule BEFORE training. Final8000only; no adaptive
budget,seed,checkpoint rescue or intermediate evaluation. All source hashes frozen.

Controls are existing ordinary_extended_v5 (matched budget) plus ordinary_v5 and
corrected-input R1e. Reuse their verified54723-row caches with no new control
inference/training. The extended control is rejected; using its cache as a control
does not restore its eligibility. Candidate name ordinary_no_dropout_v5. Parent
exposure to the inner development data remains disclosed; this is NOT untouched
confirmation. Reserved data/old validation/live bot labels remain inaccessible.

P1 validates source and original schedule bindings, malformed controls, exact
initial state/EVAL outputs, dropout configuration and finite unchanged-weight
CPU backward with0optimizer/no saved probe. Existing completed dropout mechanism
assay is reused and bound, not rerun. T1 trains once. Independent V1 BEFORE E1
reconstructs all draws/logs/final-state/96optimizerstates each8000. E1 predicts
only the NEW final checkpoint on54723development rows once. V2 independently
recounts raw labels/masks/per-replay/PLAY-WAIT statistics and compares ALL frozen
filters versus BOTH v5 and the matched extended control. No retuned threshold.

One serial chain owns common development_iteration_1 chain.lock through ALL FIVE
jobs including gaps. Fresh receipts l72-development10-*. Owner cutoff13Z; no
new updates aftercutoff. Onfailure preserve sources/outputs/receipts; no unchanged
retry. Outside evidence review and one final-model report only after all5jobs
succeed. Bind delivery and publish handoff. All final N2-N7/statistical/component/
physical/gameplay/public/Q4/Q5 gates remainOPEN. Development pass is not deployment.
STOP stays intact and there is no fallback restart.
