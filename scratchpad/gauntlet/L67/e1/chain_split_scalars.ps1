# chain_split_scalars.ps1 -- attribution of the L67az/L67bb scalars finding across its three
# bundled --noise-off components.
#
# L67az/L67bb measured off_scalars 0.72 vs control 0.52 on held-out entries 0:100 (replicated on a
# disjoint slice, L67bb). "scalars" was a bundle of three switches; this chain unbundles it to find
# which of my_elixir, opp_elixir, king_hp carries the +20/+24pp -- pipeline.e1_eval now accepts each
# name individually (scalars remains an alias for all three together).
#
# Order: boot only if needed -> liveness -> gate_split3 (all three off together, must reproduce
#        off_scalars 0.72 if the split is bit-identical to the bundle -- a reproduction gate) ->
#        off_my_elixir -> off_opp_elixir -> off_king_hp -> ctrl_split (this batch's own control, run
#        LAST so the arms get the box first) -> stop engine + VM.
# All arms use entries 0:100 -- the slice with the existing control (0.52) and bundled-arm (0.72)
# reference numbers, so gate_split3 doubles as the reproduction check.
#
# Traps carried from chain_noise_attrib.ps1: never `Start-Process -Wait` (it waits for descendants
# and hung 23 min once) -- use -PassThru + Wait-Process -Id; no in-script scoring (a `2>&1` inside a
# -File PowerShell turned stdout into RemoteException records and lost the report -- score from Bash
# afterwards); boot only through L63/s0/_boot.ps1, never from inside a python process tree.

$Repo    = 'C:\Users\benpe\ClashBot'
$Py      = "$Repo\icebow\.venv\Scripts\python.exe"
$E1      = "$Repo\scratchpad\gauntlet\L67\e1"
$A       = "$E1\attrib_split"
$Ckpt    = 'icebow\data\pipeline\s1_icebow_v6lat_s0.pt'
$Log     = "$E1\split_scalars.log"
$Sandbox = "$Repo\research\ext\cr-native-sandbox"
$Slice   = '0:100'

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
  "$([DateTime]::UtcNow.ToString('s'))Z pid=$($p.Id) split_scalars $Name port=38031 out=$OutDir" | Add-Content "$E1\pids.txt"
  Note "$Name launched pid $($p.Id): $($Extra -join ' ')"
  Wait-Process -Id $p.Id
  $n = if (Test-Path "$OutDir\matches.jsonl") { (Get-Content "$OutDir\matches.jsonl").Count } else { 0 }
  $err = Test-Path "$OutDir\errors.jsonl"
  Note "$Name exited code=$($p.ExitCode) matches=$n errors=$err"
  return (-not $err)
}

function Stop-Engine {
  Note "stopping engine services + VM"
  $null = Run-Worker 'stop --stop-vm' "$E1\status_stop_split.txt"
  Note ("stop done; qemu left={0}; free GB {1:N1}" -f @(Get-Process qemu* -ErrorAction SilentlyContinue).Count, ((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1MB))
}

Note "split_scalars start (entries $Slice)"

# 1. worker status; boot only if not already up
$st = Run-Worker 'status' "$E1\status_split_pre.txt"
if ($st -match '"vm_ready":\s*true' -and $st -match '"services":\s*\[\s*true,\s*true\s*\]') { Note "services already up -- boot skipped" }
else {
  $bl = "$E1\boot_split.log"
  $b = Start-Process powershell.exe -WindowStyle Hidden -PassThru -ArgumentList '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
         "$Repo\scratchpad\gauntlet\L63\s0\_boot.ps1" -RedirectStandardOutput $bl -RedirectStandardError "$E1\boot_split.stderr.log"
  "$([DateTime]::UtcNow.ToString('s'))Z pid=$($b.Id) boot_split" | Add-Content "$E1\pids.txt"
  $t0 = Get-Date
  while (((Get-Date) - $t0).TotalMinutes -lt 45) { if ((Test-Path $bl) -and (Select-String -Path $bl -Pattern '^=== end' -Quiet)) { break }; Start-Sleep -Seconds 10 }
  $boot = if (Test-Path $bl) { Get-Content $bl -Raw } else { '' }
  if ($boot -notmatch 'exit=0') { Note "BOOT FAILED -- see boot_split.log"; Stop-Engine; Note "ALL DONE (boot failed)"; exit 2 }
  Note ("boot ok: " + (($boot -split "`n" | Select-String 'attempt|exit=') -join ' | '))
}

# 2. liveness on 38031
$LOut = "$E1\liveness\p38031_split"
$lp = Start-Process -FilePath $Py -ArgumentList @('-m', 'pipeline.e1_eval', '--mode', 'liveness', '--port', '38031', '--split', 'heldout',
        '--entries', '0:1', '--out', $LOut) -WorkingDirectory $Repo -WindowStyle Hidden -PassThru `
        -RedirectStandardOutput "$LOut.stdout.log" -RedirectStandardError "$LOut.stderr.log"
$null = $lp.Handle
Wait-Process -Id $lp.Id -Timeout 300 -ErrorAction SilentlyContinue
$live = if (Test-Path "$LOut.stdout.log") { Get-Content "$LOut.stdout.log" -Raw } else { '' }
if ($live -notmatch '"ok": true') { Note "LIVENESS FAILED -- see $LOut.stdout.log"; Stop-Engine; Note "ALL DONE (liveness failed)"; exit 2 }
Note "liveness ok on 38031"

# 3. gate_split3 -- all three components off together; must reproduce off_scalars 0.72 if the
#    split is bit-identical to the bundle
$null = Run-Eval 'gate_split3'    "$A\gate_split3\slot0"    @('--entries', $Slice, '--noise-off', 'my_elixir,opp_elixir,king_hp')

# 4. individual components
$null = Run-Eval 'off_my_elixir'  "$A\off_my_elixir\slot0"  @('--entries', $Slice, '--noise-off', 'my_elixir')
$null = Run-Eval 'off_opp_elixir' "$A\off_opp_elixir\slot0" @('--entries', $Slice, '--noise-off', 'opp_elixir')
$null = Run-Eval 'off_king_hp'    "$A\off_king_hp\slot0"    @('--entries', $Slice, '--noise-off', 'king_hp')

# 5. this batch's own control -- run LAST so the arms get the box first
$null = Run-Eval 'ctrl_split'     "$A\ctrl_split\slot0"     @('--entries', $Slice)

# 6. stop engine services + VM
Stop-Engine
Note "ALL DONE"
