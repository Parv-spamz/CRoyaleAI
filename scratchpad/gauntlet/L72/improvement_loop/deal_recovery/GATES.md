# Gates: isolated native opening-hand recovery

OWNS: scratchpad/gauntlet/L72/improvement_loop/deal_recovery/**, scratchpad/gauntlet/L72/improvement_loop/DEAL_RECOVERY_PLAN.md, scratchpad/gauntlet/L72/improvement_loop/DEAL_RECOVERY_REVIEW.md

Scope: Prove a source-faithful generic reconstruction repair on training records before a separately registered confirmation recovery.

- [x] D1: Immutable metadata and existing records establish complete fallback and missing-deck coverage counts.
  CHECK: icebow/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/deal_recovery/audit.py
  EXPECT: DEAL_RECOVERY_SOURCE_AUDIT_PASS
  EVIDENCE: l72-deal-recovery-source-audit.json/out; exit0 and token; 807 native records, 183 exact-Icebow metadata groups, zero opposing Barrel decks, thirteen training fallbacks.

- [x] D2: Isolated solver rejects illegal or altered deals and terminates within its fixed budget.
  CHECK: icebow/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/deal_recovery/solver.py --self-test
  EXPECT: DEAL_RECOVERY_SOLVER_CONTROLS_PASS
  EVIDENCE: l72-deal-recovery-solver-controls.json/out; two positives/six negatives. v3 wrapper restricts solver to 61 plus three inherited resets; independent-v4 verifies captured budget, unresolved history and preserved forms. Earlier cap-accounting error retained.

- [x] D3: Native training trials and independent recount retain all original commands and failures with deterministic repeats and unchanged successful controls.
  CHECK: icebow/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/deal_recovery/verify_v4.py
  EXPECT: DEAL_RECOVERY_TRAINING_INDEPENDENT_PASS
  EVIDENCE: l72-deal-recovery-training-v3 and independent-v4 receipts; exit0/token. Seven of thirteen former failures recovered, three original controls unchanged, all sixteen repeats match. Four unresolved and two other failed captures remain excluded. l72-deal-recovery-recount-controls adds two positive/seven negative oracle checks.

- [x] D4: Report preserves original exclusions and forbids new-model or confirmation acceptance from training-only reconstruction.
  EVIDENCE: DEAL_RECOVERY_REVIEW.md and newest HANDOFF retain failures, precise harness corrections, zero new model/predictions and unresolved N2-N7. The separate reserved recovery is source reconstruction with its own frozen plan/jobs/gates.
