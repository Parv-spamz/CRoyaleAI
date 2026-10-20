# Explicit module loading for independent recount

October5 17:44 EDT. The v2 wrapper failed its module identity assertion before
loading data: experiment.py prepends iteration1 to sys.path, so a bare import
recount selected iteration1's namesake. Preserve v2 source and failed receipt
(exit1,1.83s). The identity assertion prevented the wrong recount from running.

The separate outer recount_development8_v3.py loads the original iteration8
recount.py by exact absolute file path with importlib. All original source and
metrics remain unchanged. It binds both failed receipts/outputs, both correction
records, v2 source, its own source and the reused extra_masks helper. No earlier
successful job is repeated. This supersedes only R1's execution command in
RECOUNT_COMPLETION.md, whose initial timestamp rounded up to17:44 EDT.

- [ ] R1: Original trial8 recount completes, with all labels/caches/filters intact.
  CHECK: icebow/.venv/Scripts/python.exe scratchpad/gauntlet/L72/improvement_loop/recount_development8_v3.py
  EXPECT: AIM_HEADS_RECOUNT_V3_COMPLETE
- [ ] R2: Original and v2 failures remain visible in reviewed receipts and handoff.
  MANUAL: No inference, optimization, tolerance, threshold or original source edits.
