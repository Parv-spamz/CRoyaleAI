# chain_scalars_confirm.ps1 -- DISJOINT-SLICE replication of the L67az scalars finding.
#
# L67az measured off_scalars 0.72 (CI 0.63-0.81) vs control 0.52 on held-out entries 0:100.
# House rule (gauntlet section 2): a headline number is repeated on a DISJOINT slice before it is
# reported. This runs the SAME two conditions on held-out entries 100:200 -- a control and the
# scalars arm -- so the comparison is anchored on its own slice (the L67au lesson: an ablation
# chain runs its own full-n unchanged control in the same batch).
#
# Order: boot only if needed -> liveness -> ctrl_slice2 (100:200) -> off_scalars_slice2 (100:200)
#        -> stop engine + VM.
# Traps carried from chain_noise_attrib.ps1: never `Start-Process -Wait` (it waits for descendants
# and hung 23 min once) -- use -PassThru + Wait-Process -Id; no in-script scoring (a `2>&1` inside a
# -File PowerShell turned stdout into RemoteException records and lost the report -- score from Bash
# afterwards); boot only through L63/s0/_boot.ps1, never from inside a python process tree.

$Repo    = 'C:\Users\benpe\ClashBot'
$Py      = "$Repo\icebow\.venv\Scripts\python.exe"
$E1      = "$Repo\scratchpad\gauntlet\L67\e1"
$A       = "$E1\attrib_noise"
$Ckpt    = 'icebow\data\pipeline\s1_icebow_v6lat_s0.pt'
$Log     = "$E1\scalars_confirm.log"
$Sandbox = "$Repo\research\ext\cr-native-sandbox"
$Slice   = '100:200'

function Note([string]$m) { "$([DateTime]::UtcNow.ToString('s'))Z $m" | Add-Content $Log }

function Run-Worker([string]$Verb, [string]$OutFile) {
  $w = Start-Process powershell.exe -WindowStyle Hidden -PassThru -ArgumentList '-NoProfile', '-Command',
         "Set-Location '$Sandbox'; . .\runtime.env.ps1; .\.venv\Scripts\python.exe -m native_core.worker $Verb --workers 2 *> '$OutFile'"
  Wait-Process -Id $w.Id -Timeout 600 -ErrorAction SilentlyContinue
  if (Test-Path $OutFile) { return (Get-Content $OutFile -Raw) } else { return '' }
}

function Run-Eval([string]$Name, [string]$OutDir, [string[]]$Extra) {
  New-Item -ItemType Directory -Force (Split-Path $OutDir) | Out-Null
  if ((Test-Path $OutDir) -and (Get-ChildItem $OutDir -ErrorAction SilentlyContinue)) { Note "$Name output not empty -- skipping"; return $false }
  $argv = @('-m', 'pipeline.e1_eval', '--mode', 'eval', '--policy', 'live', '--ckpt', $Ckpt, '--port', '38031', '--shard', '0/1',
            '--split', 'heldout', '--seeds', '0', '--out', $OutDir) + $Extra
  $p = Start-Process -FilePath $Py -ArgumentList $argv -WorkingDirectory $Repo -WindowStyle Hidden -PassThru `
         -RedirectStandardOutput "$OutDir.stdout.log" -RedirectStandardError "$OutDir.stderr.log"
  $null = $p.Handle
  "$([DateTime]::UtcNow.ToString('s'))Z pid=$($p.Id) scalars_confirm $Name port=38031 out=$OutDir" | Add-Content "$E1\pids.txt"
  Note "$Name launched pid $($p.Id): $($Extra -join ' ')"
  Wait-Process -Id $p.Id
  $n = if (Test-Path "$OutDir\matches.jsonl") { (Get-Content "$OutDir\matches.jsonl").Count } else { 0 }
  $err = Test-Path "$OutDir\errors.jsonl"
  Note "$Name exited code=$($p.ExitCode) matches=$n errors=$err"
  return (-not $err)
}

function Stop-Engine {
  Note "stopping engine services + VM"
  $null = Run-Worker 'stop --stop-vm' "$E1\status_stop_confirm.txt"
  Note ("stop done; qemu left={0}; free GB {1:N1}" -f @(Get-Process qemu* -ErrorAction SilentlyContinue).Count, ((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1MB))
}

Note "scalars_confirm start (disjoint slice $Slice)"

# 1. worker status; boot only if not already up
$st = Run-Worker 'status' "$E1\status_confirm_pre.txt"
if ($st -match '"vm_ready":\s*true' -and $st -match '"services":\s*\[\s*true,\s*true\s*\]') { Note "services already up -- boot skipped" }
else {
  $bl = "$E1\boot_confirm.log"
  $b = Start-Process powershell.exe -WindowStyle Hidden -PassThru -ArgumentList '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
         "$Repo\scratchpad\gauntlet\L63\s0\_boot.ps1" -RedirectStandardOutput $bl -RedirectStandardError "$E1\boot_confirm.stderr.log"
  "$([DateTime]::UtcNow.ToString('s'))Z pid=$($b.Id) boot_confirm" | Add-Content "$E1\pids.txt"
  $t0 = Get-Date
  while (((Get-Date) - $t0).TotalMinutes -lt 45) { if ((Test-Path $bl) -and (Select-String -Path $bl -Pattern '^=== end' -Quiet)) { break }; Start-Sleep -Seconds 10 }
  $boot = if (Test-Path $bl) { Get-Content $bl -Raw } else { '' }
  if ($boot -notmatch 'exit=0') { Note "BOOT FAILED -- see boot_confirm.log"; Stop-Engine; Note "ALL DONE (boot failed)"; exit 2 }
  Note ("boot ok: " + (($boot -split "`n" | Select-String 'attempt|exit=') -join ' | '))
}

# 2. liveness on 38031
$LOut = "$E1\liveness\p38031_confirm"
$lp = Start-Process -FilePath $Py -ArgumentList @('-m', 'pipeline.e1_eval', '--mode', 'liveness', '--port', '38031', '--split', 'heldout',
        '--entries', '0:1', '--out', $LOut) -WorkingDirectory $Repo -WindowStyle Hidden -PassThru `
        -RedirectStandardOutput "$LOut.stdout.log" -RedirectStandardError "$LOut.stderr.log"
$null = $lp.Handle
Wait-Process -Id $lp.Id -Timeout 300 -ErrorAction SilentlyContinue
$live = if (Test-Path "$LOut.stdout.log") { Get-Content "$LOut.stdout.log" -Raw } else { '' }
if ($live -notmatch '"ok": true') { Note "LIVENESS FAILED -- see $LOut.stdout.log"; Stop-Engine; Note "ALL DONE (liveness failed)"; exit 2 }
Note "liveness ok on 38031"

# 3. control on the disjoint slice -- all noise ON, zero switches flipped
$null = Run-Eval 'ctrl_slice2' "$A\ctrl_slice2\slot0" @('--entries', $Slice)

# 4. the scalars arm on the same disjoint slice
$null = Run-Eval 'off_scalars_slice2' "$A\off_scalars_slice2\slot0" @('--entries', $Slice, '--noise-off', 'scalars')

# 5. stop engine services + VM
Stop-Engine
Note "ALL DONE"
