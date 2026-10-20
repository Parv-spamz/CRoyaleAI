# O6 — chain_split_scalars.ps1 progress

## 1. Context read
- Read `scratchpad/gauntlet/L67/e1/chain_scalars_confirm.ps1` in full (94 lines). No unclear
  lines — proceeding without NEEDS_CONTEXT.
- Template structure: header comment -> vars ($Repo,$Py,$E1,$A,$Ckpt,$Log,$Sandbox,$Slice) ->
  Note/Run-Worker/Run-Eval/Stop-Engine functions -> start Note -> boot-if-needed block ->
  liveness block -> 2 eval arms (ctrl_slice2, off_scalars_slice2) -> Stop-Engine -> "ALL DONE".

## 2. Scope decisions (for the diff to stay inside acceptance (d))
Changed: header comment; `$Log`; `$A`; `$Slice` value; the two `status_*` filenames passed to
Run-Worker (pre-check + inside Stop-Engine); `$bl` boot log path; boot's stderr sibling
(`boot_split.stderr.log`, grouped under "boot file names" alongside `$bl`, same pattern as
Run-Eval's stdout/stderr pair); `$LOut` liveness path; the arms block (5 arms replacing 2).

Left untouched (verbatim, flagged below rather than guessed into scope):
- pids.txt tag literals `scalars_confirm` (Run-Eval) and `boot_confirm` (boot block) — these are
  content strings inside a shared file, not "file names" per acceptance (d)'s bucket list.
- `Note "scalars_confirm start (disjoint slice $Slice)"` — same reasoning; `$Slice` still renders
  correctly at runtime (0:100), only the surrounding label text is stale.
Flagging these two as a concern in the handback rather than editing them, since editing would add
a diff region acceptance (d) does not list.

## 3. Script written
`scratchpad/gauntlet/L67/e1/chain_split_scalars.ps1` — written, not run.

## 4. Verification
a. Parser check: `[System.Management.Automation.Language.Parser]::ParseFile(...)` -> ParseErrors=0.
b. `Select-String -Pattern 'Start-Process[^#]*-Wait\b'` (non-comment lines) -> no matches.
c. `Select-String -Pattern 'e1_score'` -> no matches.
d. Diff vs template: changed regions are exactly header comment, `$A`, `$Log`, `$Slice`,
   `status_stop_split.txt` / `status_split_pre.txt`, `$bl`/boot_split.log + boot_split.stderr.log,
   `$LOut`, and the arms block (2 arms -> 5, renumbered comments 3-6). No other lines touched.
e. Arm table:

   | name            | --noise-off value              |
   |-----------------|---------------------------------|
   | gate_split3     | my_elixir,opp_elixir,king_hp   |
   | off_my_elixir   | my_elixir                      |
   | off_opp_elixir  | opp_elixir                     |
   | off_king_hp     | king_hp                        |
   | ctrl_split      | (none)                          |

## 5. Concerns (disclosed, not acted on — outside the named diff buckets)
- pids.txt tag literals left as template text: `scalars_confirm` (Run-Eval line) and
  `boot_confirm` (boot pids.txt line) — harmless, just a stale label in a shared log file.
- `Note "scalars_confirm start (disjoint slice $Slice)"` left verbatim; `$Slice` renders as
  `0:100` correctly, but the surrounding wording ("scalars_confirm", "disjoint slice") is stale.

STATUS: complete

## Attempt 2 — rename the three stale label strings

Edited `chain_split_scalars.ps1`, exactly these three content strings, nothing else:

| line | before | after |
|------|--------|-------|
| 47 (Run-Eval pids.txt tag) | `pid=$($p.Id) scalars_confirm $Name port=38031 out=$OutDir` | `pid=$($p.Id) split_scalars $Name port=38031 out=$OutDir` |
| 71 (boot pids.txt tag) | `pid=$($b.Id) boot_confirm` | `pid=$($b.Id) boot_split` |
| 62 (start Note) | `Note "scalars_confirm start (disjoint slice $Slice)"` | `Note "split_scalars start (entries $Slice)"` |

File is untracked/new (no prior commit), so `git diff` / `git diff --no-index` has no baseline to
compare against (`git status --short` confirms `??`). Verified the change is scoped to exactly
these three lines via targeted grep instead:
- `Select-String -Pattern 'scalars_confirm|boot_confirm'` -> 0 matches (old strings fully gone).
- `Select-String -Pattern 'split_scalars \$Name|split_scalars start|boot_split"'` -> exactly 1
  match each, at lines 47, 62, 71 respectively — matching the table above, nowhere else.

Re-ran the three required checks after the edits:
a. Parser: `[System.Management.Automation.Language.Parser]::ParseFile(...)` -> ParseErrors=0.
b. `Select-String -Pattern 'Start-Process[^#]*-Wait\b'` on non-comment lines -> no matches.
c. `Select-String -Pattern 'e1_score'` -> no matches.

No other lines touched. Script not run, not committed. Same write set as attempt 1.

STATUS: complete
