# Shared gradient diagnosis gates

- [x] G1: All27 fixed policy-phase checkpoints yield finite saved component gradients with unchanged weights and exact detached-path controls.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/rl_gradient_audit/collect.py
  EXPECT: RL_GRADIENT_COLLECTED
- [x] G2: Independent vector recount reconciles all27 memberships, tensor and total norms/dots; positive and corruption controls pass.
  CHECK: research/ext/Royale/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/rl_gradient_audit/verify.py
  EXPECT: RL_GRADIENT_VERIFIED
- [x] G3: Published review distinguishes measured gradient interaction from unproved causal performance and preserves rejection/final gates.
  MANUAL: Review source/raw-vector/process receipts, update handoff; no optimizer or new model claim.
