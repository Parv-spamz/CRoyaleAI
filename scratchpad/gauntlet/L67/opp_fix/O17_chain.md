# O17 -- chain script for V2.1 + tracker + corr, smoke arm first

New file: `scratchpad/gauntlet/L67/e1/chain_opp_est_v21.ps1`, copied from the reviewed
`chain_opp_est_v2.ps1` template. Did not run/boot/commit (out of scope for this ticket).

## Parser spellings confirmed (pipeline/opp_est_audit.py build_parser)

- line 1215: `ap.add_argument("--max-ticks", type=int, default=0, ...)`
- line 1225: `ap.add_argument("--estimator", choices=("v1", "v2", "both"), default="v1", ...)` -- `v2` is a
  valid choice.
- line 1229: `ap.add_argument("--tracker", action="store_true", ...)` -- O16(a) tracker-input condition.
- line 1233: `ap.add_argument("--corr", action="store_true", ...)` -- O16(b) SHORT/LONG correlated-noise
  conditions.

All four flags used in the two arms (`--estimator v2 --tracker --corr`, `--max-ticks 600` on the smoke
arm) match these exactly.

## Changes made vs template (named renames only + the guard)

- Header comment: purpose rewritten for V2.1 + tracker + corr, smoke-first rationale added; trap
  paragraph gains `chain_opp_est_v2.ps1` to the "traps carried from" list (text otherwise unchanged).
- `$Log`: `opp_est_v2.log` -> `opp_est_v21.log`
- pids.txt tag in `Run-Audit`: `opp_est_v2` -> `opp_est_v21`
- `Stop-Engine`'s status file: `status_stop_v2.txt` -> `status_stop_v21.txt`
- start `Note`: `"opp_est_v2 start (entries 0:100, --estimator both)"` ->
  `"opp_est_v21 start (smoke 0:2 then 0:100; --estimator v2 --tracker --corr)"`
- pre-boot status file: `status_v2_pre.txt` -> `status_v21_pre.txt`
- boot log + stderr + pids tag: `boot_v2.log` / `boot_v2.stderr.log` / `boot_v2` ->
  `boot_v21.log` / `boot_v21.stderr.log` / `boot_v21` (incl. the "BOOT FAILED" message text)
- liveness out path: `liveness\p38031_v2` -> `liveness\p38031_v21`
- Section 3 replaced with two arms in order, plus the guard between them:
  1. `$null = Run-Audit 'smoke_v21' "$A\smoke_v21" @('--entries','0:2','--max-ticks','600','--estimator','v2','--tracker','--corr')`
     `if (-not (Test-Path "$A\smoke_v21\summary.json")) { Note "SMOKE FAILED -- skipping full run"; Stop-Engine; Note "ALL DONE (smoke failed)"; exit 2 }`
  2. `$null = Run-Audit 'audit_v21_0_100' "$A\audit_v21_0_100" @('--entries','0:100','--estimator','v2','--tracker','--corr')`
  (old section numbering 3/4 shifted to 3/4/5: smoke / guard / full run / stop-engine)

Everything else (variable names `$Repo`/`$Py`/`$E1`/`$A`/`$Ckpt`/`$Sandbox`, `Note`, `Run-Worker`,
`Run-Audit`, `Stop-Engine` function bodies, the boot block's polling loop, the liveness block) is
byte-identical to the template -- confirmed by `diff` (full diff pasted in the handback report).

## Traps preserved

- No `Start-Process -Wait` call anywhere (only the comment mentions `-Wait` as the thing to avoid,
  confirmed by grep -- every actual `Start-Process` uses `-PassThru` + a separate `Wait-Process -Id`).
- No in-script scoring/analysis: the script only launches processes, checks exit codes and
  `summary.json` existence, and writes `Note` log lines -- no parsing of ticks.jsonl/summary content.
- Boot only via `L63\s0\_boot.ps1`, unchanged.

## Verification

- `[System.Management.Automation.Language.Parser]::ParseFile(...)` on the new script -> `0 parse errors`.
- `grep -n -- '-Wait'` on the new script -> 1 hit, the header comment line only, no live `-Wait` call.
- `diff chain_opp_est_v2.ps1 chain_opp_est_v21.ps1` -> confined to the items listed above.

STATUS: complete
