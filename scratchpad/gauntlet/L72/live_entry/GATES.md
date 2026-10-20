# Manual live entry refresh

- [x] M1: Default selects the deployment pointer, explicit checkpoint wins, missing/invalid selection fails before device access, and a default-selected pointer change is observed between matches.
  CHECK: icebow/.venv/Scripts/python.exe -m pytest pipeline/tests/test_live_checkpoint.py -q
  EXPECT: passed
- [x] M2: Canonical live entry uses current public audited pilot, learned WAIT at full elixir, approved argmax options, recording/navigation/receipt paths, with no automatic external notifications.
  CHECK: icebow/.venv/Scripts/python.exe -m pytest scratchpad/gauntlet/L68/live_reader/test_live_entry.py scratchpad/gauntlet/L68/live_reader/test_live_play_clock.py scratchpad/gauntlet/L68/live_reader/test_friend_nav.py -q
  EXPECT: passed
- [x] M3: The actual default checkpoint loads and executes on archived reader frames on CPU; an archived recording renders and decodes successfully. No live match is started by verification.
  MANUAL: Inspect receipt-bound offline preflight and replay probe output, checkpoint hash, public decisions and decoded video.
- [x] M4: Retry the original sixteen blocked Rust executables unchanged and recount results.
  MANUAL: owner-rust-retry.json exit0 and OWNER_RUST_RETRY_PASS; rust_retry_owner.json:16 targets,62 pass,0 fail. Binaries unchanged.
- [x] M5: Running live session stops between matches before replacing source. Publish scoped changes, record current selection/new-model limits, and give owner a manual command.
  MANUAL: Process snapshot, scoped commit/push and HANDOFF.

M5: original live worker and supervisor exited before source replacement; STOP retained. Manual command and current-model limit are in README.md and HANDOFF; final publication is verified against origin/main before reporting. install_verified.json proves the installed source differs from the tested prepared source only by removal of its stale first comment.

M1/M2 receipt: integration/checks/manual-live-prepared.json, exit0,102 pass/2 skips. The prepared source was installed byte-for-byte; its stale header comment was then removed, with no behavior change. Canonical and compatibility CLI --check both load R1e31u0155 on CPU with tau.35, public audits and argmax choices. The two skips are unavailable old recording fixtures, not new failures.

M3 receipt: manual-live-offline-v3.json exit0/LIVE_OFFLINE_INTEGRATION_PASS.24 archived real-reader decisions match the original policy exactly; all contain public audits. Actual captured video renders with the default both overlay and decodes31 frames; the raw merge is present. Earlier probe failures were stale fixture selection (one frozen tick, then a removed September raw video); both failed receipts remain. No live-match acceptance is claimed.
