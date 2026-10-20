# Gates: historical training sequence index

OWNS: scratchpad/gauntlet/L72/improvement_loop/defence_sequence_prep/**, scratchpad/gauntlet/L72/improvement_loop/prepare_defence_sequences.py, scratchpad/gauntlet/L72/improvement_loop/verify_defence_sequences.py, scratchpad/gauntlet/L72/improvement_loop/DEFENCE_SEQUENCE_PREP_PLAN.md, scratchpad/gauntlet/L72/improvement_loop/DEFENCE_SEQUENCE_PREP_REVIEW.md, scratchpad/gauntlet/L72/improvement_loop/defence_sequence_prepared.json, scratchpad/gauntlet/L72/improvement_loop/defence_sequence_verified.json

Scope: Produce and independently verify a training-only index that preserves all original labels and unsuccessful/non-Rocket decisions without launching training.

- [x] S1: The membership oracle accepts intact evidence and rejects membership and label corruptions.
  CHECK: icebow/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/verify_defence_sequences.py --self-test
  EXPECT: DEFENCE_SEQUENCE_CONTROLS_PASS
  EVIDENCE: l72-defence-sequence-controls.json/out; exit0, token matched; two positive checks and twelve corruptions rejected.

- [x] S2: Every indexed window exactly matches its original same-side training rows and supervision.
  CHECK: icebow/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/verify_defence_sequences.py
  EXPECT: DEFENCE_SEQUENCE_INDEPENDENTLY_VERIFIED
  EVIDENCE: l72-defence-sequence-verified.json/out; exit0, token matched; 7748 original bow labels, 126802 unique rows, eight target arrays; defence_sequence_verified.json binds exact report/source.

- [x] S3: Report distinguishes prepared historical exposure from trained improvement and retains all new-model prerequisites.
  EVIDENCE: DEFENCE_SEQUENCE_PREP_REVIEW.md and newest HANDOFF; no training or inference, trainable false, N2-N7 open, sparse/overlap/outcome limits retained.
