# Reserved-pilot independent checks

- [x] P1: Recount oracle rejects corrupted command/grade/repeat evidence.
  MANUAL: Run verify_reserved_pilot.py --self-test under run_check; require zero exit and RESERVED_PILOT_RECOUNT_CONTROLS_PASS. Preserve command/output receipt.
- [x] P2: Read-only integration checks ten completed training recordings.
  MANUAL: Run verify_reserved_pilot.py --training-smoke under run_check; require zero exit and RESERVED_PILOT_TRAINING_SMOKE_PASS. This cannot close P3 or N2.
- [x] P3: Entire fixed collection reconciles independently after its final receipt.
  MANUAL: Run verify_reserved_pilot.py under run_check; require zero exit and RESERVED_PILOT_INDEPENDENTLY_VERIFIED. Inspect all645 membership decisions, source command recounts, all scheduled repeats or explicit source exclusions, immutable hashes and exact aggregate comparisons.
- [x] P4: Publish usable-yield limits and remaining N2 prerequisites.
  MANUAL: Review independent summary and update HANDOFF. Do not label reconstruction/deck counts as tactical opportunities or statistically adequate confirmation.

Evidence: l72-pilot-recount-current-controls and l72-pilot-recount-final-smoke receipts. Original membership schema failure is retained in l72-pilot-recount-training-smoke and verify_reserved_pilot_v1.py. Full P3 now passes: l72-reserved-pilot-independent and its hash-bound reserved_pilot_independent.json. P4: PILOT_FINAL_REVIEW.md and current HANDOFF. N2 remains open.
