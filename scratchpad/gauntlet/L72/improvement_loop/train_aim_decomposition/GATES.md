# Training aim decomposition gates

OWNS: scratchpad/gauntlet/L72/improvement_loop/TRAIN_AIM_DECOMPOSITION_PLAN.md, scratchpad/gauntlet/L72/improvement_loop/TRAIN_AIM_DECOMPOSITION_REVIEW.md, scratchpad/gauntlet/L72/improvement_loop/decompose_train_aim.py, scratchpad/gauntlet/L72/improvement_loop/verify_train_aim.py, scratchpad/gauntlet/L72/improvement_loop/train_aim_decomposition.json

- [x] A1: Exact prior training selection/checkpoints, logit reconstruction and unchanged full aim verified.
  CHECK: icebow/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/decompose_train_aim.py
  EXPECT: TRAIN_AIM_DECOMPOSITION_COMPLETE
  EVIDENCE: l72-train-aim-decomposition receipt exit 0, expected token matched; 830 original training rows, three checkpoint hashes, prior full aims match.
- [x] A2: Independent cache recount and corruption controls pass.
  CHECK: icebow/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/verify_train_aim_v3.py
  EXPECT: TRAIN_AIM_DECOMPOSITION_INDEPENDENTLY_VERIFIED
  EVIDENCE: l72-train-aim-decomposition-independent-v3 receipt exit 0 and train_aim_decomposition_verified.json. Two positives/five corruptions; all nine cohort/model comparisons match. v1/v2 precision failures preserved.
- [x] A3: Mechanism findings retain training-only, teacher-forced and no-deployment limits.
  MANUAL: Compare all controls and ablation harms, record supported next experiment without claiming a better model.
  EVIDENCE: TRAIN_AIM_DECOMPOSITION_REVIEW.md records both gains and harms, uncertain mechanism and no enabling of decoder ablations. N2 and model acceptance remain unmet.
