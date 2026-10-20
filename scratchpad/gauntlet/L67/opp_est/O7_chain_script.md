# O7 -- chain_opp_confirm.ps1 progress

## Step 1: context read
Read `scratchpad\gauntlet\L67\e1\chain_split_scalars.ps1` in full (105 lines). Structure:
boot-if-needed (worker status -> boot script if not up) -> liveness on 38031 -> N x Run-Eval arms
via the shared `Run-Eval` function -> Stop-Engine -> `Note "ALL DONE"`. Confirmed `Run-Eval` never
uses `Start-Process -Wait` (uses `-PassThru` + `Wait-Process -Id`), confirmed no `e1_score` anywhere
in the template (scoring is done afterwards from Bash, per its own header comment).

Confirmed `attrib_noise\ctrl_slice2` and `attrib_noise\off_scalars_slice2` exist under L67\e1
(ls'd), matching the ticket's background about a disjoint-slice control already existing at 0.47.

Nothing in the template was unclear -- proceeding without NEEDS_CONTEXT.

## Step 2: script drafted
Writing `chain_opp_confirm.ps1`, copying the template's structure and traps verbatim, changing
only: header comment, `$Log`, `$A` (kept as `$E1\attrib_split`, unchanged path per instruction --
same subfolder the template uses, arms get their own subdirs so no collision), `$Slice`, the two
status file names (`status_opp_pre.txt`/`status_stop_opp.txt`), boot log name (`boot_opp.log` +
`.stderr.log`), liveness out (`liveness\p38031_opp`), pids.txt tags (`opp_confirm`/`boot_opp`),
Note text, and the arms block (2 arms instead of 5, with `gate_slice2_10` using `--entries
100:110` distinct from the batch `$Slice` of `100:200`).

## Step 3: acceptance evidence
a. Parser check: `[System.Management.Automation.Language.Parser]::ParseFile` -> `PARSE_ERRORS: 0`.
b. `grep -n '-Wait\b'` -> only 1 hit, inside a comment line (`# Traps carried ... never
   Start-Process -Wait`), quoting the forbidden pattern to document the trap. No live
   `Start-Process -Wait` usage anywhere in the script.
c. `grep -n 'e1_score'` -> no matches.
d. `diff -u chain_split_scalars.ps1 chain_opp_confirm.ps1` run and reviewed line by line: every
   hunk falls inside header comment / `$Log` / `$Slice` / file-tag-Note names (split_scalars ->
   opp_confirm, status_split_pre -> status_opp_pre, status_stop_split -> status_stop_opp,
   boot_split -> boot_opp, p38031_split -> p38031_opp) / the arms block (5 arms -> 2 arms). `$A`
   line is byte-identical (unchanged, as permitted). `Run-Worker`, `Run-Eval`, `Stop-Engine`
   function bodies are otherwise unchanged (only the pids.txt tag string and the stop status
   filename change inside them, both allowed as file/tag names). Full diff pasted to caller.
e. Arm table:
   | name                    | entries   | --noise-off |
   |--------------------------|-----------|-------------|
   | gate_slice2_10           | 100:110   | (none)      |
   | off_opp_elixir_slice2    | 100:200   | opp_elixir  |

No unclear lines found in the template -- no NEEDS_CONTEXT triggered.
Script not run, engine not booted, nothing committed, per ticket scope.

STATUS: complete
