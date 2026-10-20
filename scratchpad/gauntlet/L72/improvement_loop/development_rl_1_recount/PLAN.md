# Complete failed independent outcome-RL recount without weakening a check

Registered October5 after observing the original verifier stop at verify.py line27.
Preserve original verifier/outer wrapper, failed output and nonzero receipt.
Training32 updates/256 games and evaluation54723 rows already succeeded. They
must not be repeated. No new policy inference, optimization or evidence cohort.

D1 diagnoses each conjunct of the failed assertion using the saved rollout and
contract arrays: contract lengths, contributing row count and exact equality of
logged versus independently computed maximum probability-ratio deviation. Keep
every update's original value, independent value, difference and exact verdict.
Do not assume a floating-point cause until the differences are measured. The
original per-row ratio limit1e-4 stays unchanged; no numerical tolerance is added.

D2 may complete the unchanged original row/replay/model-metric recount only if
lengths/counts and all per-row finite/ratio checks pass. The exact summary-equality
assertion becomes a recorded FALSE filter rather than preventing the remaining
statistics from being computed. It remains a failed criterion in the overall
verdict. Every other original assertion, label, mask, threshold and fixed final
checkpoint stays unchanged. If another assertion fails, preserve it and diagnose
before a separate correction; never edit an executed frozen source in place.

D3 independently binds completed statistics and all original failures, then
reports the new model once via the intended sender as NOT ACCEPTED. A failed
exactness filter must be disclosed even if all policy-metric point filters pass.
No model acceptance/deployment or model-strength claim from training outcomes.

Scope is this new leaf plus outer helpers; original development_rl_1 and recovery
Python/PLAN/METRICS remain frozen. No reserved/old-validation/live-label access.
