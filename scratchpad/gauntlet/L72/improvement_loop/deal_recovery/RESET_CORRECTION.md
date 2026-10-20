# Reset contract correction before training trials

The first isolated attempt failed before issuing any replay command: the new
wrapper incorrectly asserted native reset tick zero. Existing original native
records and NativeRoyaleEnv.reset show this service returns its bootstrapped
observation at tick 10 even with warmup_steps=0. This was not a failed card play,
solver-budget result or change to the native runtime.

Preserve driver_patch.py, run_training.py, verify.py, started.json/progress.json,
the first empty ignored output directory and l72-deal-recovery-training receipt.
No first-attempt replay is usable. Version 2 changes only this wrapper assertion
to require the original per-replay tick_after_reset, which must equal 10, and
uses distinct files/directories/receipts. The solver, 64-reset cap, selected
training cases, source commands, native state, criteria and repeats are unchanged.
The final reset must still match that original bootstrap tick before any command.
References to tick-zero in the initial plan mean the pre-command opening state;
the precise native clock value is ten. No timestamp is changed or normalized.
