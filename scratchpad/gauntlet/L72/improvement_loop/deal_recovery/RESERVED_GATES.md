# Gates: reserved native deal recovery

OWNS: scratchpad/gauntlet/L72/improvement_loop/deal_recovery/reserved_*.json, scratchpad/gauntlet/L72/improvement_loop/deal_recovery/run_reserved.py, scratchpad/gauntlet/L72/improvement_loop/deal_recovery/verify_reserved.py, scratchpad/gauntlet/L72/improvement_loop/deal_recovery/RESERVED_*.md

Scope: Reconstruct the complete fixed 65 reserved fallback cases with unchanged source commands and criteria, preserving all failed attempts.

- [x] R1: Frozen jobs include every non-training fallback exactly once with unchanged original identity and input hashes.
  CHECK: icebow/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/deal_recovery/verify_reserved.py --jobs-only
  EXPECT: RESERVED_DEAL_JOBS_VERIFIED
  EVIDENCE: l72-deal-recovery-reserved-jobs.json/out; exit0 and token; all65 cases (12development/53confirmation), original splits/forms/commands/seed/level; training proof and plan hashes bound.

- [x] R2: All selected captures and repeats finish with source/runtime provenance and explicit success or exclusion.
  CHECK: icebow/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/deal_recovery/verify_reserved.py
  EXPECT: RESERVED_DEAL_RECOVERY_INDEPENDENT_PASS
  EVIDENCE: reserved_complete.json/reserved_verified.json; l72-deal-recovery-reserved and reserved-independent receipts exit0/matched. All65 cases and repeats finish;32 newly usable,33 remain excluded; sources/runtime/commands and normalized frames checked. No original archive changes.

- [x] R3: Report distinguishes new verified reconstruction yield from model acceptance and preserves N2 gaps.
  EVIDENCE: RESERVED_RECOVERY_REVIEW.md and recovered_capacity/REVIEW.md distinguish source cast counts from qualified opportunities and retain N2-N7, zero model predictions and no new training/model/deployment.
