# Gates: narrow native form investigation

OWNS: scratchpad/gauntlet/L72/improvement_loop/NATIVE_FORM_PROBE_PLAN.md, scratchpad/gauntlet/L72/improvement_loop/NATIVE_FORM_PROBE_REVIEW.md, scratchpad/gauntlet/L72/improvement_loop/probe_native_elite_form.py, scratchpad/gauntlet/L72/improvement_loop/native_elite_form_probe.json, scratchpad/gauntlet/L72/improvement_loop/native_form_probe/**

Scope: Distinguish a catalog omission from unavailable native mechanics using bounded synthetic controls without changing production runtime or reserved replay evidence.

- [x] F1: Synthetic probe completes with exact runtime sources and a working known evolution control.
  CHECK: icebow/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/probe_native_elite_form_v3.py
  EXPECT: NATIVE_ELITE_FORM_PROBE_V3_COMPLETE
  EVIDENCE: l72-native-elite-form-probe-v3 receipt exit 0; original catalog, all three arms. v1/v2 failures preserved.

- [x] F2: Report interprets actual resolved IDs/entities and preserves all reconstruction and N2 prerequisites.
  EVIDENCE: NATIVE_FORM_PROBE_REVIEW.md; native IDs/entities inspected. Separate isolated correction plan registered before changes. No original catalog change or reconstruction qualification implied.
