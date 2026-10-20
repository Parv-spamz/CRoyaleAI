# O20 -- chain script for the v6aug variant of the feed experiment

## What was built
New file: `scratchpad/gauntlet/L67/e1/chain_opp_feed_v6aug.ps1`, copied from the reviewed,
currently-running `scratchpad/gauntlet/L67/e1/chain_opp_feed.ps1`, same structure/traps/guard
pattern, with the checkpoint switched to the LIVE-deployed one and cut down to the two arms the
ticket specified. Not run. Engine not touched. Nothing committed.

## Checkpoint confirmation
```
$ ls -la icebow/data/pipeline/s1_icebow_v6aug_s1.pt
-rw-r--r-- 1 benpe 197609 5108845 Sep  8 04:03 icebow/data/pipeline/s1_icebow_v6aug_s1.pt
```
File exists on disk.

## $Ckpt line (verbatim)
```
$Ckpt    = 'icebow\data\pipeline\s1_icebow_v6aug_s1.pt'
```

## Both arm lines (verbatim)
```
$null = Run-Audit 'gate_v6aug_off10' "$A\gate_v6aug_off10" @('--entries','0:10','--estimator','v2','--tracker','--feed-opp-elixir','off')
...
$null = Run-Audit 'feed_est_v6aug_s1' "$A\feed_est_v6aug_s1" @('--entries','0:100','--estimator','v2','--tracker','--feed-opp-elixir','estimated','--feed-noise','live')
```
Guard between them (verbatim):
```
if (-not (Test-Path "$A\gate_v6aug_off10\summary.json")) { Note "GATE_V6AUG_OFF10 FAILED -- skipping remaining arms"; Stop-Engine; Note "ALL DONE (gate_v6aug_off10 failed)"; exit 2 }
```

## --ckpt flag / defaults confirmation (from pipeline/opp_est_audit.py build_parser, line 1435+)
- `ap.add_argument("--ckpt", type=Path, required=True, ...)` (line 1439) -- `--ckpt` is the exact flag, unchanged.
- `ap.add_argument("--tau", type=float, default=TAU_LIVE)` (line 1446); `TAU_LIVE = 0.27` is defined
  in `pipeline/e1_eval.py:60` and imported into opp_est_audit.py at line 281. So the template's
  UNSPECIFIED `--tau` already defaults to 0.27 -- correct, since `attrib/e2_v6aug_s1_tau027/slot0`
  (the anchor run) used tau 0.27 (confirmed from its `run.json`: `"tau": "0.27"`). No `--tau` flag
  needed in the new script (matches chain_opp_feed.ps1's own omission of `--tau`).
- `--seeds` default `"0"`, `--shard` default `"0/1"`, `--split` default `"heldout"` (lines 1442-1445)
  -- all match the anchor run's `run.json` (`"seeds": "0"`, `"shard": "0/1"`, `"split": "heldout"`)
  and are left unspecified in the new script exactly as in chain_opp_feed.ps1, so this run inherits
  the same values as the anchor run.
- Anchor run's actual numbers (from `score_attrib_e2_v6aug_s1_tau027.json`):
  `{"matches": 100, "winrate": 0.74, "ci": [0.65, 0.82]}` -- 74/100. Documented in the new script's
  header as the value gate_v6aug_off10 (on its first 10 entries) must reproduce.
- Caveat: the anchor run was produced by `pipeline.e1_eval` (`--mode eval --policy live`), not
  `pipeline.opp_est_audit` -- a different module, same tau/seeds/shard/split. This is stated
  explicitly in the new script's header comment as the basis for the gate's reproduction claim
  (untested until the gate is actually run -- this ticket does not run it).

## Diff against chain_opp_feed.ps1
Full diff generated with `diff -u chain_opp_feed.ps1 chain_opp_feed_v6aug.ps1` (pasted to the
foreman in-line in this task's chat transcript; reproducible any time by re-running that diff).
Confined to:
- header comment (O20 purpose, gate-reproduction rationale, trimmed arm list, one added NOTE)
- `$A`, `$Ckpt`, `$Log` variable values
- `pids_feed.txt` -> `pids_feed_v6aug.txt` (see deviation below), tag strings `opp_feed`/`boot_feed`
  -> `opp_feed_v6aug`/`boot_v6aug`
- `status_feed_pre.txt` -> `status_v6aug_pre.txt`, `status_stop_feed.txt` -> `status_stop_v6aug.txt`
- `boot_feed.log`/`.stderr.log` -> `boot_v6aug.log`/`.stderr.log`
- `liveness\p38031_feed` -> `liveness\p38031_v6aug`
- start `Note` string
- arms 2 ("gate_true10"), 4 ("feed_estL_s1"), 5-7 (the two "_s2" gates + "feed_est_s2") removed;
  remaining two arms renamed `gate_v6aug_off10` / `feed_est_v6aug_s1`, guard re-pointed at
  `gate_v6aug_off10\summary.json`
No other lines differ: `Run-Worker`, `Run-Audit`, `Stop-Engine` function bodies, the boot-skip
check, the liveness call, and the trap comments are otherwise byte-identical to chain_opp_feed.ps1.

## Deviation (in-scope, noted per contract)
Renamed the pids log `pids_feed.txt` -> `pids_feed_v6aug.txt` (not explicitly named in the ticket's
rename list). Reason: chain_opp_feed.ps1 is currently running and appends to
`scratchpad/gauntlet/L67/e1/pids_feed.txt`; giving the new script the same pids filename would
interleave two chains' pid records in one file. This is a filename choice only -- no change to
either script's logic, structure, or guard pattern. Called out here for visibility.

## Acceptance checks run
1. **PowerShell parser, 0 errors**:
   ```
   [System.Management.Automation.Language.Parser]::ParseFile(...) -> ErrorCount=0
   ```
2. **No non-comment `Start-Process -Wait`**: `grep -n "\-Wait\b" chain_opp_feed_v6aug.ps1` matches
   only the trap comment line (`# never \`Start-Process -Wait\` ...`); no executable `-Wait` usage.
3. **No in-script scoring**: script only launches processes, writes Note lines, and checks
   `Test-Path ... summary.json` -- same as chain_opp_feed.ps1, no score/winrate computation added.
4. **Checkpoint file exists on disk**: confirmed above (`ls -la`, 5,108,845 bytes, dated Sep 8 04:03).
5. **Two arms only, both `--estimator v2 --tracker`**: confirmed by reading the file back -- lines
   for `gate_v6aug_off10` and `feed_est_v6aug_s1` both carry `'--estimator','v2','--tracker'`.

## What was NOT done (per ticket instruction)
- Script not executed.
- Engine/worker not started, stopped, or queried.
- No commit made; no file outside the two-file write set touched.

STATUS: complete
