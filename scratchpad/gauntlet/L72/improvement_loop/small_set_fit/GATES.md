# Small fixed-set fit assay gates

OWNS: scratchpad/gauntlet/L72/improvement_loop/small_set_fit/**, icebow/data/bench/small_set_fit_20261006/**

- [x] P1: Original sample labels, fixed schedule and finite unchanged-weight preparation probe reconcile.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/small_set_fit/prepare.py
  EXPECT: SMALL_SET_FIT_PREPARED
  EVIDENCE: prepared.json and l72-small-set-fit-prepare;67.421289s exit0/token.74source bindings,1024rows/798replays/524288draws,2positive6malformed controls,finite CPU backward5.726444 with exact unchanged weights and zero optimizer.
- [x] T1: Exactly 4096 finite updates produce the quarantined final assay model.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/small_set_fit/train.py
  EXPECT: SMALL_SET_FIT_TRAINED
  EVIDENCE: trained.json; l72-small-set-fit-train 707.089823s exit0/token.
- [x] V1: Independent training and corruption controls pass before final assay inference.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/small_set_fit/verify_training.py
  EXPECT: SMALL_SET_FIT_TRAINING_VERIFIED
  EVIDENCE: training_verified.json; l72-small-set-fit-training-independent 6.908803s exit0/token.
- [x] E1: The three fixed checkpoints predict once per sample orientation.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/small_set_fit/evaluate.py
  EXPECT: SMALL_SET_FIT_EVALUATED
  EVIDENCE: evaluated.json; l72-small-set-fit-eval 55.139531s exit0/token.
- [x] V2: Independent original-label, prediction, per-replay and criterion counts reconcile.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/small_set_fit/verify_results.py
  EXPECT: SMALL_SET_FIT_RESULTS_VERIFIED
  EVIDENCE: results_verified.json; l72-small-set-fit-results-independent 7.540836s exit0/token.
- [x] R1: Evidence review and one diagnostic-model report retain quarantine and all deployment floors.
  MANUAL: Inspect every receipt, final counts, exact report and confirmed delivery.
  EVIDENCE: reviewed_evidence/reviewed_results/message.md; outerreview.578288s,delivery.765301s,closeout.087099s exit0/token. Two confirmed HTTP200 messages; diagnostic criteria failed; weights quarantined.
