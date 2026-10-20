# E1 observation-attribution screen (L67ar/L67aq): which live-view noise component drives the S1-vs-training gap.
# Reproduces v6lat_s0's live-rule result on held-out 0:10 (gate), then an all-noise-off clean-equivalence gate on the
# same 10, then 7 single-component --noise-off arms of 100 held-out entries each (0:100, k=0). `deploying` is a
# documented no-op for this eval (engine rows lose `kind` before from_engine, e1_view.py Noise docstring) so it is
# folded into the all-off gate only, not run as its own arm.
# Order: boot only if needed -> liveness -> repro gate 10 -> all-off gate 10 -> 7 arms x 100 -> stop engine + VM.
# Traps carried from chain_e2.ps1 / L67al: never `Start-Process -Wait` (waits for descendants, hung 23 min once);
# no in-script scoring (2>&1 inside a -File PS turned stdout into RemoteException records and lost it -- the lead
# scores from Bash afterwards); boot only through L63/s0/_boot.ps1, never from inside a python process tree;
# runtime.env.ps1 is dot-sourced in a child powershell and never printed/copied; one engine client at a time on
# door 38031 only.
$Repo    = 'C:\Users\benpe\ClashBot'
Set-Location $Repo
$Py      = "$Repo\icebow\.venv\Scripts\python.exe"
$E1      = "$Repo\scratchpad\gauntlet\L67\e1"
$A       = "$E1\attrib_noise"
$Ckpt    = 'icebow\data\pipeline\s1_icebow_v6lat_s0.pt'
$Log     = "$E1\noise_attrib.log"
$Sandbox = "$Repo\research\ext\cr-native-sandbox"
$AllOff  = 'recall,false_pos,position,team,unit_hp,scalars,deploying,conf'
$Arms    = @('recall', 'false_pos', 'position', 'team', 'unit_hp', 'scalars', 'conf')

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
  "$([DateTime]::UtcNow.ToString('s'))Z pid=$($p.Id) noise_attrib $Name port=38031 out=$OutDir" | Add-Content "$E1\pids.txt"
  Note "$Name launched pid $($p.Id): ckpt $Ckpt $($Extra -join ' ')"
  Wait-Process -Id $p.Id
  $n = if (Test-Path "$OutDir\matches.jsonl") { (Get-Content "$OutDir\matches.jsonl").Count } else { 0 }
  $err = Test-Path "$OutDir\errors.jsonl"
  Note "$Name exited code=$($p.ExitCode) matches=$n errors=$err"
  return (-not $err)
}

function Stop-Engine {
  Note "stopping engine services + VM"
  $null = Run-Worker 'stop --stop-vm' "$E1\status_stop_noise.txt"
  Note ("stop done; qemu left={0}; free GB {1:N1}" -f @(Get-Process qemu* -ErrorAction SilentlyContinue).Count, ((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1MB))
}

Note "noise_attrib start"

# 1. worker status; boot only if not already up
$st = Run-Worker 'status' "$E1\status_noise_pre.txt"
if ($st -match '"vm_ready":\s*true' -and $st -match '"services":\s*\[\s*true,\s*true\s*\]') { Note "services already up -- boot skipped" }
else {
  $bl = "$E1\boot_noise.log"
  $b = Start-Process powershell.exe -WindowStyle Hidden -PassThru -ArgumentList '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
         "$Repo\scratchpad\gauntlet\L63\s0\_boot.ps1" -RedirectStandardOutput $bl -RedirectStandardError "$E1\boot_noise.stderr.log"
  "$([DateTime]::UtcNow.ToString('s'))Z pid=$($b.Id) boot_noise" | Add-Content "$E1\pids.txt"
  $t0 = Get-Date
  while (((Get-Date) - $t0).TotalMinutes -lt 45) { if ((Test-Path $bl) -and (Select-String -Path $bl -Pattern '^=== end' -Quiet)) { break }; Start-Sleep -Seconds 10 }
  $boot = if (Test-Path $bl) { Get-Content $bl -Raw } else { '' }
  if ($boot -notmatch 'exit=0') { Note "BOOT FAILED -- see boot_noise.log"; Stop-Engine; Note "ALL DONE (boot failed)"; exit 2 }
  Note ("boot ok: " + (($boot -split "`n" | Select-String 'attempt|exit=') -join ' | '))
}

# 2. liveness on 38031
$LOut = "$E1\liveness\p38031_noise"
$lp = Start-Process -FilePath $Py -ArgumentList @('-m', 'pipeline.e1_eval', '--mode', 'liveness', '--port', '38031', '--split', 'heldout',
        '--entries', '0:1', '--out', $LOut) -WorkingDirectory $Repo -WindowStyle Hidden -PassThru `
        -RedirectStandardOutput "$LOut.stdout.log" -RedirectStandardError "$LOut.stderr.log"
Wait-Process -Id $lp.Id -Timeout 300 -ErrorAction SilentlyContinue
$live = if (Test-Path "$LOut.stdout.log") { Get-Content "$LOut.stdout.log" -Raw } else { '' }
if ($live -notmatch '"ok": true') { Note "LIVENESS FAILED -- see $LOut.stdout.log"; Stop-Engine; Note "ALL DONE (liveness failed)"; exit 2 }
Note "liveness ok on 38031"

# 3. reproduction gate -- live rule, no noise change, held-out 0:10
$null = Run-Eval 'gate_live10' "$A\gate_live10\slot0" @('--entries', '0:10')

# 4. clean-equivalence gate -- all 8 noise components off, same 10 entries
$null = Run-Eval 'gate_allof10' "$A\gate_allof10\slot0" @('--entries', '0:10', '--noise-off', $AllOff)

# 5. seven single-component arms, 100 held-out entries each
foreach ($c in $Arms) {
  $null = Run-Eval "off_$c" "$A\off_$c\slot0" @('--entries', '0:100', '--noise-off', $c)
}

# 6. stop engine services + VM
Stop-Engine
Note "ALL DONE"
