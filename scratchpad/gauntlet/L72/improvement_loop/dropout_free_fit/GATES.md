# Dropout-free fixed-set diagnostic gates

OWNS: scratchpad/gauntlet/L72/improvement_loop/dropout_free_fit/**, icebow/data/bench/dropout_free_fit_20261006/**

- [x] P1: Original sample/draw stream, exact initial evaluation outputs, dropout mechanism and finite unchanged-weight backward are qualified.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/dropout_free_fit/prepare.py
  EXPECT: DROPOUT_FREE_FIT_PREPARED
  EVIDENCE: prepared.json and l72-dropout-free-fit-prepare.json/.out; exit0/token, 90.632368s, original sample and draw equality, unchanged weights and dropout mechanism controls pass.
- [x] T1: Exactly4096 finite original-loss updates use fresh ordinary_v5 and only disable training dropout.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/dropout_free_fit/train.py
  EXPECT: DROPOUT_FREE_FIT_TRAINED
  EVIDENCE: l72-dropout-free-fit-train.json/.out; exit0/token, 665.177879s; corresponding completed result independently bound in reviewed_results.json.
- [x] V1: Independent sample/draw/log/final-state and optimizer reconciliation passes before inference.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/dropout_free_fit/verify_training.py
  EXPECT: DROPOUT_FREE_FIT_TRAINING_VERIFIED
  EVIDENCE: l72-dropout-free-fit-training-independent.json/.out; exit0/token, 6.791633s; corresponding completed result independently bound in reviewed_results.json.
- [x] E1: The final quarantined model predicts both fixed orientations once and reuses all original control caches.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/dropout_free_fit/evaluate.py
  EXPECT: DROPOUT_FREE_FIT_EVALUATED
  EVIDENCE: l72-dropout-free-fit-eval.json/.out; exit0/token, 52.743374s; corresponding completed result independently bound in reviewed_results.json.
- [x] V2: Independent original-label/mask/action/per-replay recount and malformed controls decide the original fit criteria.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/dropout_free_fit/verify_results.py
  EXPECT: DROPOUT_FREE_FIT_RESULTS_VERIFIED
  EVIDENCE: l72-dropout-free-fit-results-independent.json/.out; exit0/token, 7.602767s; corresponding completed result independently bound in reviewed_results.json.
- [x] R1: Reviewed results and one delivered diagnostic model report bind every receipt and preserve quarantine and final acceptance requirements.
  MANUAL: Inspect all artifacts/receipts, run outside evidence review, send once through the intended sender, then bind confirmed delivery.
  EVIDENCE: reviewed_evidence.json, reviewed_results.json and l72-dropout-free-fit-reviewed-evidence/discord/reviewed receipts all exit0/token. Three confirmed HTTP200 parts; exact text and message IDs bound.
