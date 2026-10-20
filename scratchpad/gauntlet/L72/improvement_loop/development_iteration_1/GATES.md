# Isolated development iteration gates

OWNS: scratchpad/gauntlet/L72/improvement_loop/development_iteration_1/

- [x] D1: Deterministic replay-separated training/development indices are bound to original expert labels and exclude old validation and reserved confirmation.
  CHECK: icebow/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/development_iteration_1/prepare.py
  EXPECT: DEVELOPMENT_1_DATA_PREPARED
- [x] D2: Independent source-index/count/hash recount rejects leakage and verifies the saved split.
  CHECK: icebow/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/development_iteration_1/verify.py
  EXPECT: DEVELOPMENT_1_SPLIT_VERIFIED
- [x] D3: The isolated trainer and pre-run metric manifest satisfy the fixed recipe and never evaluate old validation or confirmation.
  CHECK: icebow/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/development_iteration_1/verify_prelaunch.py
  EXPECT: DEVELOPMENT_1_PRELAUNCH_PASS
  MANUAL: Inspect the isolated trainer/evaluator paths and shared unknown-target mirroring; no old validation calls. METRICS.md fixes definitions and controls before prediction.
- [x] D4: Both full serial arms finish the registered finite updates and all paired development results are independently recounted and reported.
  MANUAL: Preserve failures and full receipts; send model reports once; no acceptance/deployment from development-only evidence.

D1/D2 successful receipts: l72-development1-data-prepared and
l72-development1-data-independent. One positive/eight corruptions pass.
213995 training rows/1573 replays,54723 development rows/405 replays;38317 old
validation pool rows excluded, zero overlap with239939 reserved groups.
D3 passed l72-development1-prelaunch, exit0/token matched,178.88s. Exact migration,
initial predictions/base dropout, canonical mirrored loss and finite backward
updates verified; neither CPU smoke saved a checkpoint. Four index corruptions
rejected, independent subgroup masks match, counter positive/four corruptions pass.
D4 COMPLETE October5 13:47 via the separately bound serialization recovery.
Original v5 training and R1e evaluation were retained; original failed v5
evaluation, sources and checkpoints remain preserved. results_verified_v2.json
reconciles both1000 finite updates and all54723 development rows per cache.
reviewed_results.json binds all15 process receipts, paired replay differences,
both reviewed model messages and successful HTTP204 deliveries. No duplication,
new model acceptance, live change or final gameplay/statistical claim.
