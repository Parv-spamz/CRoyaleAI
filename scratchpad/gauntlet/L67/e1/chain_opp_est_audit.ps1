# chain_opp_est_audit.ps1 -- run the OpponentElixirEstimator audit (O8's pipeline/opp_est_audit.py) over
# 100 held-out ghosts.
#
# Purpose: measure play.py's OpponentElixirEstimator against ENGINE ground truth, under the module's three
# input conditions (A+ perfect detection incl. spells, A perfect detection units-only, B degraded live-like
# view), driven through the same S1 live policy / engine match loop e1_eval uses. Entries 0:100 of the
# heldout split (pool v1), same ckpt/port/seed/shard settings as the rest of this batch. The module itself
# writes <out>/ticks.jsonl, summary.json, summary.md and prints one {"OPP_EST_AUDIT_DONE": {...}} JSON line
# at the end -- this chain only launches it and records exit status; it does not score or interpret output.
#
# Traps carried from chain_split_scalars.ps1 / chain_noise_attrib.ps1 / chain_opp_confirm.ps1: never
# `Start-Process -Wait` (it waits for descendants and hung 23 min once) -- use -PassThru + Wait-Process -Id;
# no in-script scoring (a `2>&1` inside a -File PowerShell turned stdout into RemoteException records and
# lost the report -- score from Bash afterwards); boot only through L63/s0/_boot.ps1, never from inside a
# python process tree.

$Repo    = 'C:\Users\benpe\ClashBot'
$Py      = "$Repo\icebow\.venv\Scripts\python.exe"
$E1      = "$Repo\scratchpad\gauntlet\L67\e1"
$A       = "$E1\opp_est"
$Ckpt    = 'icebow\data\pipeline\s1_icebow_v6lat_s0.pt'
$Log     = "$E1\opp_est_audit.log"
$Sandbox = "$Repo\research\ext\cr-native-sandbox"

function Note([string]$m) { "$([DateTime]::UtcNow.ToString('s'))Z $m" | Add-Content $Log }

function Run-Worker([string]$Verb, [string]$OutFile) {
  $w = Start-Process powershell.exe -WindowStyle Hidden -PassThru -ArgumentList '-NoProfile', '-Command',
         "Set-Location '$Sandbox'; . .\runtime.env.ps1; .\.venv\Scripts\python.exe -m native_core.worker $Verb --workers 2 *> '$OutFile'"
  Wait-Process -Id $w.Id -Timeout 600 -ErrorAction SilentlyContinue
  if (Test-Path $OutFile) { return (Get-Content $OutFile -Raw) } else { return '' }
}

function Run-Audit([string]$Name, [string]$OutDir, [string[]]$Extra) {
  New-Item -ItemType Directory -Force (Split-Path $OutDir) | Out-Null
  if ((Test-Path $OutDir) -and (Get-ChildItem $OutDir -ErrorAction SilentlyContinue)) { Note "$Name output not empty -- skipping"; return $false }
  $argv = @('-m', 'pipeline.opp_est_audit', '--port', '38031', '--split', 'heldout', '--ckpt', $Ckpt,
            '--seeds', '0', '--shard', '0/1', '--out', $OutDir) + $Extra
  $p = Start-Process -FilePath $Py -ArgumentList $argv -WorkingDirectory $Repo -WindowStyle Hidden -PassThru `
         -RedirectStandardOutput "$OutDir.stdout.log" -RedirectStandardError "$OutDir.stderr.log"
  $null = $p.Handle
  "$([DateTime]::UtcNow.ToString('s'))Z pid=$($p.Id) opp_est_audit $Name port=38031 out=$OutDir" | Add-Content "$E1\pids.txt"
  Note "$Name launched pid $($p.Id): $($Extra -join ' ')"
  Wait-Process -Id $p.Id
  $sum = Test-Path "$OutDir\summary.json"
  Note "$Name exited code=$($p.ExitCode) summary.json exists=$sum"
  return ($p.ExitCode -eq 0)
}

function Stop-Engine {
  Note "stopping engine services + VM"
  $null = Run-Worker 'stop --stop-vm' "$E1\status_stop_oea.txt"
  Note ("stop done; qemu left={0}; free GB {1:N1}" -f @(Get-Process qemu* -ErrorAction SilentlyContinue).Count, ((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1MB))
}

Note "opp_est_audit start (entries 0:100)"

# 1. worker status; boot only if not already up
$st = Run-Worker 'status' "$E1\status_oea_pre.txt"
if ($st -match '"vm_ready":\s*true' -and $st -match '"services":\s*\[\s*true,\s*true\s*\]') { Note "services already up -- boot skipped" }
else {
  $bl = "$E1\boot_oea.log"
  $b = Start-Process powershell.exe -WindowStyle Hidden -PassThru -ArgumentList '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
         "$Repo\scratchpad\gauntlet\L63\s0\_boot.ps1" -RedirectStandardOutput $bl -RedirectStandardError "$E1\boot_oea.stderr.log"
  "$([DateTime]::UtcNow.ToString('s'))Z pid=$($b.Id) boot_oea" | Add-Content "$E1\pids.txt"
  $t0 = Get-Date
  while (((Get-Date) - $t0).TotalMinutes -lt 45) { if ((Test-Path $bl) -and (Select-String -Path $bl -Pattern '^=== end' -Quiet)) { break }; Start-Sleep -Seconds 10 }
  $boot = if (Test-Path $bl) { Get-Content $bl -Raw } else { '' }
  if ($boot -notmatch 'exit=0') { Note "BOOT FAILED -- see boot_oea.log"; Stop-Engine; Note "ALL DONE (boot failed)"; exit 2 }
  Note ("boot ok: " + (($boot -split "`n" | Select-String 'attempt|exit=') -join ' | '))
}

# 2. liveness on 38031
$LOut = "$E1\liveness\p38031_oea"
$lp = Start-Process -FilePath $Py -ArgumentList @('-m', 'pipeline.e1_eval', '--mode', 'liveness', '--port', '38031', '--split', 'heldout',
        '--entries', '0:1', '--out', $LOut) -WorkingDirectory $Repo -WindowStyle Hidden -PassThru `
        -RedirectStandardOutput "$LOut.stdout.log" -RedirectStandardError "$LOut.stderr.log"
$null = $lp.Handle
Wait-Process -Id $lp.Id -Timeout 300 -ErrorAction SilentlyContinue
$live = if (Test-Path "$LOut.stdout.log") { Get-Content "$LOut.stdout.log" -Raw } else { '' }
if ($live -notmatch '"ok": true') { Note "LIVENESS FAILED -- see $LOut.stdout.log"; Stop-Engine; Note "ALL DONE (liveness failed)"; exit 2 }
Note "liveness ok on 38031"

# 3. audit_0_100 -- the arm under measurement, entries 0:100
$null = Run-Audit 'audit_0_100' "$A\audit_0_100" @('--entries', '0:100')

# 4. stop engine services + VM
Stop-Engine
Note "ALL DONE"
