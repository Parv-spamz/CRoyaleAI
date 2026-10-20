# O14 -- one-arm chain script for the side-by-side estimator run

Wrote `scratchpad/gauntlet/L67/e1/chain_opp_est_v2.ps1`, copied from the reviewed template
`chain_opp_est_audit.ps1`, changing only:

- header comment (filename line + purpose: V1 vs V2 estimator on the same 100 ghosts and the
  same det stream; conditions A+/A/A_wl/B per variant)
- `$Log` -> `opp_est_v2.log`
- status files: `status_v2_pre.txt` (worker status pre-check), `status_stop_v2.txt` (Stop-Engine)
- boot log: `boot_v2.log` / `boot_v2.stderr.log`; pids.txt tag `boot_v2`
- liveness out prefix: `liveness\p38031_v2`
- pids.txt tag for the audit process: `opp_est_v2`
- start Note: `opp_est_v2 start (entries 0:100, --estimator both)`
- the arm: `Run-Audit 'audit_v2_0_100' "$A\audit_v2_0_100" @('--entries','0:100','--estimator','both')`
  (and its preceding numbered comment, updated to name the new arm + flag)

Confirmed `--estimator` spelling against `pipeline/opp_est_audit.py`'s `build_parser`:
`ap.add_argument("--estimator", choices=("v1", "v2", "both"), default="v1", ...)` (line 931) --
`both` is exact.

Did NOT run, boot, or commit anything, per ticket.

## Verification

- Parse check (no execution): `[System.Management.Automation.Language.Parser]::ParseFile(...)`
  on the new script -> `PARSE_OK errors=0`.
- `grep -n -- '-Wait'` on the new script: only hit is inside the traps comment (line 11,
  `Start-Process -Wait` referenced as the thing to avoid); no non-comment `-Wait` usage anywhere
  in the script body.
- `grep -niE 'score|analy'`: both hits are inside comments (purpose paragraph "it does not score
  or interpret output"; traps paragraph "score from Bash afterwards") -- no in-script scoring
  code.
- `diff -u chain_opp_est_audit.ps1 chain_opp_est_v2.ps1`: confined to the named changes above
  (header comment, `$Log`, pids.txt tags `opp_est_v2`/`boot_v2`, `status_v2_pre.txt`,
  `status_stop_v2.txt`, `boot_v2.log`/`.stderr.log`, `liveness\p38031_v2`, start Note, the
  `audit_v2_0_100` arm line and its comment). Full diff pasted below.

```diff
--- chain_opp_est_audit.ps1
+++ chain_opp_est_v2.ps1
@@ -1,12 +1,11 @@
-# chain_opp_est_audit.ps1 -- run the OpponentElixirEstimator audit (O8's pipeline/opp_est_audit.py) over
+# chain_opp_est_v2.ps1 -- run the OpponentElixirEstimator audit (O8's pipeline/opp_est_audit.py) over
 # 100 held-out ghosts.
 #
-# Purpose: measure play.py's OpponentElixirEstimator against ENGINE ground truth, under the module's three
-# input conditions (A+ perfect detection incl. spells, A perfect detection units-only, B degraded live-like
-# view), driven through the same S1 live policy / engine match loop e1_eval uses. Entries 0:100 of the
-# heldout split (pool v1), same ckpt/port/seed/shard settings as the rest of this batch. The module itself
-# writes <out>/ticks.jsonl, summary.json, summary.md and prints one {"OPP_EST_AUDIT_DONE": {...}} JSON line
-# at the end -- this chain only launches it and records exit status; it does not score or interpret output.
+# Purpose: V1 vs V2 estimator on the same 100 ghosts and the same det stream; conditions A+/A/A_wl/B per
+# variant. Entries 0:100 of the heldout split (pool v1), same ckpt/port/seed/shard settings as the rest of
+# this batch. The module itself writes <out>/ticks.jsonl, summary.json, summary.md and prints one
+# {"OPP_EST_AUDIT_DONE": {...}} JSON line at the end -- this chain only launches it and records exit
+# status; it does not score or interpret output.
 #
 # Traps carried from chain_split_scalars.ps1 / chain_noise_attrib.ps1 / chain_opp_confirm.ps1: never
 # `Start-Process -Wait` (it waits for descendants and hung 23 min once) -- use -PassThru + Wait-Process -Id;
@@ -19,7 +18,7 @@
 $E1      = "$Repo\scratchpad\gauntlet\L67\e1"
 $A       = "$E1\opp_est"
 $Ckpt    = 'icebow\data\pipeline\s1_icebow_v6lat_s0.pt'
-$Log     = "$E1\opp_est_audit.log"
+$Log     = "$E1\opp_est_v2.log"
 $Sandbox = "$Repo\research\ext\cr-native-sandbox"
 
 function Note([string]$m) { "$([DateTime]::UtcNow.ToString('s'))Z $m" | Add-Content $Log }
@@ -39,7 +38,7 @@
   $p = Start-Process -FilePath $Py -ArgumentList $argv -WorkingDirectory $Repo -WindowStyle Hidden -PassThru `
          -RedirectStandardOutput "$OutDir.stdout.log" -RedirectStandardError "$OutDir.stderr.log"
   $null = $p.Handle
-  "$([DateTime]::UtcNow.ToString('s'))Z pid=$($p.Id) opp_est_audit $Name port=38031 out=$OutDir" | Add-Content "$E1\pids.txt"
+  "$([DateTime]::UtcNow.ToString('s'))Z pid=$($p.Id) opp_est_v2 $Name port=38031 out=$OutDir" | Add-Content "$E1\pids.txt"
   Note "$Name launched pid $($p.Id): $($Extra -join ' ')"
   Wait-Process -Id $p.Id
   $sum = Test-Path "$OutDir\summary.json"
@@ -49,29 +48,29 @@
 
 function Stop-Engine {
   Note "stopping engine services + VM"
-  $null = Run-Worker 'stop --stop-vm' "$E1\status_stop_oea.txt"
+  $null = Run-Worker 'stop --stop-vm' "$E1\status_stop_v2.txt"
   Note ("stop done; qemu left={0}; free GB {1:N1}" -f @(Get-Process qemu* -ErrorAction SilentlyContinue).Count, ((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1MB))
 }
 
-Note "opp_est_audit start (entries 0:100)"
+Note "opp_est_v2 start (entries 0:100, --estimator both)"
 
 # 1. worker status; boot only if not already up
-$st = Run-Worker 'status' "$E1\status_oea_pre.txt"
+$st = Run-Worker 'status' "$E1\status_v2_pre.txt"
 if ($st -match '"vm_ready":\s*true' -and $st -match '"services":\s*\[\s*true,\s*true\s*\]') { Note "services already up -- boot skipped" }
 else {
-  $bl = "$E1\boot_oea.log"
+  $bl = "$E1\boot_v2.log"
   $b = Start-Process powershell.exe -WindowStyle Hidden -PassThru -ArgumentList '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
-         "$Repo\scratchpad\gauntlet\L63\s0\_boot.ps1" -RedirectStandardOutput $bl -RedirectStandardError "$E1\boot_oea.stderr.log"
-  "$([DateTime]::UtcNow.ToString('s'))Z pid=$($b.Id) boot_oea" | Add-Content "$E1\pids.txt"
+         "$Repo\scratchpad\gauntlet\L63\s0\_boot.ps1" -RedirectStandardOutput $bl -RedirectStandardError "$E1\boot_v2.stderr.log"
+  "$([DateTime]::UtcNow.ToString('s'))Z pid=$($b.Id) boot_v2" | Add-Content "$E1\pids.txt"
   $t0 = Get-Date
   while (((Get-Date) - $t0).TotalMinutes -lt 45) { if ((Test-Path $bl) -and (Select-String -Path $bl -Pattern '^=== end' -Quiet)) { break }; Start-Sleep -Seconds 10 }
   $boot = if (Test-Path $bl) { Get-Content $bl -Raw } else { '' }
-  if ($boot -notmatch 'exit=0') { Note "BOOT FAILED -- see boot_oea.log"; Stop-Engine; Note "ALL DONE (boot failed)"; exit 2 }
+  if ($boot -notmatch 'exit=0') { Note "BOOT FAILED -- see boot_v2.log"; Stop-Engine; Note "ALL DONE (boot failed)"; exit 2 }
   Note ("boot ok: " + (($boot -split "`n" | Select-String 'attempt|exit=') -join ' | '))
 }
 
 # 2. liveness on 38031
-$LOut = "$E1\liveness\p38031_oea"
+$LOut = "$E1\liveness\p38031_v2"
 $lp = Start-Process -FilePath $Py -ArgumentList @('-m', 'pipeline.e1_eval', '--mode', 'liveness', '--port', '38031', '--split', 'heldout',
         '--entries', '0:1', '--out', $LOut) -WorkingDirectory $Repo -WindowStyle Hidden -PassThru `
         -RedirectStandardOutput "$LOut.stdout.log" -RedirectStandardError "$LOut.stderr.log"
@@ -81,8 +80,8 @@
 if ($live -notmatch '"ok": true') { Note "LIVENESS FAILED -- see $LOut.stdout.log"; Stop-Engine; Note "ALL DONE (liveness failed)"; exit 2 }
 Note "liveness ok on 38031"
 
-# 3. audit_0_100 -- the arm under measurement, entries 0:100
-$null = Run-Audit 'audit_0_100' "$A\audit_0_100" @('--entries', '0:100')
+# 3. audit_v2_0_100 -- the arm under measurement, entries 0:100, --estimator both
+$null = Run-Audit 'audit_v2_0_100' "$A\audit_v2_0_100" @('--entries', '0:100', '--estimator', 'both')
 
 # 4. stop engine services + VM
 Stop-Engine
```

## Arm line

```powershell
$null = Run-Audit 'audit_v2_0_100' "$A\audit_v2_0_100" @('--entries', '0:100', '--estimator', 'both')
```

STATUS: complete
