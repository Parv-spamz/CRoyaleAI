# Paired late curriculum gates

OWNS: scratchpad/gauntlet/L72/improvement_loop/development_rl_3/**, icebow/data/bench/development_rl_3_20261006/**

- [x] P1: All1024initial setups and draw/projection controls bound before learning.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/development_rl_3/prepare.py
  EXPECT: LATE_CURRICULUM_PREPARED
  EVIDENCE: prepared.json;1024native setups,7positive8corruptions; l72-late-curriculum-prepare exit0/token,15.206882s. No optimizer.
- [x] T1: Both final-only16update runs complete without guards or nonfinite steps.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/development_rl_3/train.py
  EXPECT: LATE_CURRICULUM_TRAINED
  EVIDENCE: trained.json; 2048 games,32 arm-updates,512 finite Adam steps,no guard stop; l72-late-curriculum-train exit0/token,13810.484160s.
- [x] V1: Independent full training membership, native outcomes, probabilities, returns, draws and corruption checks.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/development_rl_3/verify_training.py
  EXPECT: LATE_CURRICULUM_TRAINING_VERIFIED
  EVIDENCE: training_verified.json; all native/public rows,GAE/probabilities/draws/weights reconcile;32positive17corruptions; l72-late-curriculum-training-independent exit0/token,58.893233s.
- [x] E1: Both final checkpoints evaluated once on fixed development rows.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/development_rl_3/evaluate.py
  EXPECT: LATE_CURRICULUM_EVALUATED
  EVIDENCE: evaluated.json and both arm caches;54723 fixed development rows each,finalu016only; l72-late-curriculum-eval exit0/token,152.885233s.
- [x] V2: Independent counts and both-control continuation verdict reconcile.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/development_rl_3/verify_results.py
  EXPECT: LATE_CURRICULUM_RESULTS_VERIFIED
  EVIDENCE: results_verified.json and paired replay counts; both continuation verdicts FALSE; l72-late-curriculum-results-independent exit0/token,52.114778s.
- [x] R1: Outside receipt review, report both new models once, bind delivery and deployment verdict.
  MANUAL: Review complete frozen evidence before one compound model report. No policy acceptance from development alone.
  EVIDENCE: reviewed_evidence.json/reviewed_results.json; outside review .351204s,delivery2.075860s,closeout.103685s all exit0/token. One compound report delivered3HTTP200parts,message IDs bound. Both models rejected,not deployed.
