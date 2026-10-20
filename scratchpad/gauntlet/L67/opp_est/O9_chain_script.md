# O9 -- chain_opp_est_audit.ps1

Engine chain script that runs the OpponentElixirEstimator audit (`pipeline/opp_est_audit.py`, written by
another worker in parallel) over 100 held-out ghosts, entries `0:100`, port 38031, ckpt
`icebow\data\pipeline\s1_icebow_v6lat_s0.pt`, split `heldout`, seeds `0`, shard `0/1`.

Written: `C:\Users\benpe\ClashBot\scratchpad\gauntlet\L67\e1\chain_opp_est_audit.ps1`

Per the ticket, NOT run, NOT booted, NOT committed.

## CLI source of truth

Read `pipeline/opp_est_audit.py`'s `build_parser()` (lines 355-380) directly rather than trusting the
ticket's paraphrase. Its actual flags: `--port` (required), `--host`, `--ckpt` (required, Path), `--pool`,
`--split-file`, `--split` (heldout/train), `--entries`, `--seeds`, `--shard`, `--tau`, `--no-afford-mask`,
`--stall-elixir`, `--stall-seconds`, `--decide-every`, `--estimator-step`, `--device`, `--threads`,
`--timeout`, `--max-ticks`, `--out` (required, Path). No `--mode` flag exists (the module is fixed to the
live S1 policy) and no `--noise-off` flag (that belonged to `e1_eval`, not this module). The ticket's own
quoted CLI (`--port P --entries A:B --split heldout --ckpt CKPT --seeds 0 --shard 0/1 --out DIR
[--max-ticks N]`) matches this exactly -- no divergence to note.

The module writes `<out>/ticks.jsonl`, `summary.json`, `summary.md` and prints one
`{"OPP_EST_AUDIT_DONE": {...}}` JSON line at the end, confirmed at opp_est_audit.py:464-499.

## What the script does

1. `Run-Worker 'status'` -> boot via `L63\s0\_boot.ps1` only if `vm_ready`/`services` aren't already true
   (boot log `boot_oea.log` + `boot_oea.stderr.log`, pids tag `boot_oea`).
2. Liveness probe on port 38031 (`pipeline.e1_eval --mode liveness`, unchanged from the template --
   `opp_est_audit.py` has no liveness mode of its own), output `liveness\p38031_oea`.
3. One arm via `Run-Audit`: `audit_0_100` -> `$E1\opp_est\audit_0_100`, argv:
   ```
   icebow\.venv\Scripts\python.exe -m pipeline.opp_est_audit --port 38031 --split heldout ^
       --ckpt icebow\data\pipeline\s1_icebow_v6lat_s0.pt --seeds 0 --shard 0/1 ^
       --out C:\Users\benpe\ClashBot\scratchpad\gauntlet\L67\e1\opp_est\audit_0_100 --entries 0:100
   ```
   `Run-Audit` mirrors the template `Run-Eval`'s shape (Start-Process -PassThru + Wait-Process -Id, stdout/
   stderr to `$OutDir.stdout.log`/`.stderr.log`, skip if `$OutDir` non-empty, a pids.txt line, and a Note on
   exit) but checks `$OutDir\summary.json` existence instead of `matches.jsonl`/`errors.jsonl` (this module's
   output files differ from `e1_eval`'s), and does no in-script scoring of the audit's own MAE/bias numbers.
4. `Stop-Engine` (services + VM), `Note "ALL DONE"`.

## Acceptance evidence

- **Parser**: `[System.Management.Automation.Language.Parser]::ParseFile(...)` on the new script ->
  `ParseErrors: 0`.
- **No non-comment `Start-Process -Wait`**: `grep -n -i "Start-Process" ... | grep -i -- "-Wait"` matches
  only line 12, inside the header comment (the traps paragraph naming the trap itself). No executable
  `-Wait` usage; every `Start-Process` call uses `-PassThru` + a following `Wait-Process -Id`.
- **No `e1_score` / no in-script analysis**: `grep -n -i "e1_score\|score\b"` matches only comment lines 9
  and 14 (English prose "does not score", "score from Bash afterwards"). No scoring code, no reading of
  `summary.json`'s MAE/bias fields.
- **Diff vs the reviewed template** (`chain_opp_confirm.ps1`, via `diff -u`): confined to the header comment,
  variable/tag renames (`$A`, `$Log`, `status_oea_pre.txt`/`status_stop_oea.txt`, `boot_oea.*`,
  `liveness\p38031_oea`, pids tags `opp_est_audit`/`boot_oea`), the `Run-Eval` -> `Run-Audit` function body
  (module name, base argv, and the exit check swapped from `matches.jsonl`/`errors.jsonl` to
  `summary.json`), and the arm section (one `audit_0_100` arm replacing the two `attrib_split` arms). The
  `Run-Worker`, `Stop-Engine`, boot block and liveness block controlflow are otherwise byte-identical to the
  template.

## Out of scope (per ticket, not done)

- Not run, not booted, not committed.
- No changes to `pipeline/opp_est_audit.py` or any other Python file.

STATUS: complete
