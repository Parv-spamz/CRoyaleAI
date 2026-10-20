# Gates: corrected-feature defense sequence binding

OWNS: scratchpad/gauntlet/L72/improvement_loop/defence_crosswalk/**, scratchpad/gauntlet/L72/improvement_loop/bind_defence_sequences.py, scratchpad/gauntlet/L72/improvement_loop/verify_defence_binding.py, scratchpad/gauntlet/L72/improvement_loop/DEFENCE_CROSSWALK_PLAN.md, scratchpad/gauntlet/L72/improvement_loop/DEFENCE_CROSSWALK_REVIEW.md, scratchpad/gauntlet/L72/improvement_loop/defence_crosswalk_bound.json, scratchpad/gauntlet/L72/improvement_loop/defence_crosswalk_verified.json

Scope: Preserve the completed historical training sequence index on the exact corrected dataset without training or authorizing release.

- [x] B1: Independent binding oracle accepts intact mappings and rejects corruption.
  CHECK: icebow/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/verify_defence_binding.py --self-test
  EXPECT: DEFENCE_BINDING_CONTROLS_PASS
  EVIDENCE: l72-defence-crosswalk-controls.json/out; exit0 and expected token; two positive checks and 21 rejected corruptions.

- [x] B2: Corrected dataset references preserve original training identity, all supervision and complete sequence membership.
  CHECK: icebow/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/verify_defence_binding.py
  EXPECT: DEFENCE_BINDING_INDEPENDENT_PASS
  EVIDENCE: l72-defence-crosswalk-bound.json/out and l72-defence-crosswalk-independent.json/out; exit0 and expected tokens. defence_crosswalk_verified.json binds exact report/source; all 7748 windows, 268718 pool rows and eight target arrays preserved.

- [x] B3: Published binding remains disabled with no model, predictions or waived fresh-data prerequisites.
  EVIDENCE: DEFENCE_CROSSWALK_REVIEW.md and newest HANDOFF; manifest trainable=false, activation=none, training_launched=false, predictions_run=false; N2-N7 remain open.
