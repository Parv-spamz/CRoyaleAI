# Spawner correction acceptance

- [x] S1: Exact catalog body identity covers Witch, Furnace, Night Witch and the audited huts/Tombstone, including ordinary child forms and conservative unknowns.
  CHECK: icebow/.venv/Scripts/python.exe -m pytest scratchpad/gauntlet/L71/spawners/test_body_identity.py -q
  EXPECT: passed
  Evidence: prototype_checks.json records the exact command, cwd, exit, matched output and SHA-256; 13 tests plus the three-card repeated-wave SIM probe pass. This is prototype evidence, not live deployment.
- [x] S2: Every changed training token is backed by a reproduced original public row; expert labels and replay splits remain unchanged.
  MANUAL: Inspect reconstruction receipt and independently compare original/corrected arrays and hashes.
  Evidence: final `spawner_identity_20261005` artifact;484437 affected rows reproduced,357425 rows/885918 class tokens/232491 forms changed. Night Witch152004 tokens. `../integration/checks/spawner-final-data.json` records exit0 and matched SPAWNER_DATASET_VERIFY_PASS; output SHA2563d8c9c2b68a5374a6406c00f9c932db67057a80652e50cd013ad0b8964041c5e.
- [x] S3: Opt-in contract is shared by dataset, SIM and live, with legacy parity and actual checkpoint loading verified.
  MANUAL: Inspect isolated-worktree integration; main Q3 sources remain frozen.
  Evidence: `../integration/checks/integrated-regression.json`90 tests/4 subtests; `expert-context-unit.json`12 tests including real R1e zero-residual parity and v5/v6 loading. Both exit0 with matched counts and hashed outputs. This gate is code/contract verification, not learning or live acceptance.
- [ ] S4: Trained correction passes held-out and same-code gameplay acceptance and is verified in the authorized live deployment.
  MANUAL: Inspect training/control, full evaluation receipts and deployed startup/confirmed-play logs.
