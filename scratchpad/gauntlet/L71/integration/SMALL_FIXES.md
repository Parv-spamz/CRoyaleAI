# Q5 acceptance, recorded before the fix

The existing preflight20.npz declares version4 but contains no own_ability array. The mapped and in-memory loaders both preserve that absence; model version4 requires the field. This is a stale test fixture, not evidence that mmap dropped an array. Generate the fixture with the current dataset builder from the existing native sample. Verify all archive arrays and batches match, then verify weighted mirrored loss and every populated gradient match and are finite. No production loader/model change or fabricated missing-ability defaults.

The supervisor is stopped. Add the existing "new checkpoint deployed" event to last_stop()'s pattern. Verify shell syntax and that extracting the function and applying it to a local synthetic log returns the latest checkpoint switch. No launch, game input or network message is part of this check.

Both fixes are outside the running experiment source manifest. They do not justify changing any candidate acceptance threshold.

Verified: checks/dataset-spool-current-contract.json records2 passed, exit0, output SHA25654c6863df5fbae1767b85327e0b31054d7550bb9786ada42e9004149e8bb90ee. checks/supervisor-reason.json records exit0 and SUPERVISOR_CHECKPOINT_REASON_PASS, SHA2560d5e25312dc5ce67b185be004e57aca2847c62f734a3948f411f960d80e21f59. The supervisor was not launched by either check.
