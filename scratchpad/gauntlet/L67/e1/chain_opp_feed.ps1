# chain_opp_feed.ps1 -- O18: feed the OPPONENT-ELIXIR ESTIMATE (or engine truth, or nothing) into the
# BoardState the policy consumes (pipeline/opp_est_audit.py's new --feed-opp-elixir/--feed-noise), and
# measure winrate over held-out ghosts. Copied from the reviewed chain_opp_est_v21.ps1 template -- same
# traps, same smoke-guard pattern, no scoring in this script (the module itself writes summary.json's
# run-level "winrate" block and prints one {"OPP_EST_AUDIT_DONE": {...}} JSON line; this chain only
# launches runs and records exit status).
#
# Traps carried from chain_split_scalars.ps1 / chain_noise_attrib.ps1 / chain_opp_confirm.ps1 /
# chain_opp_est_v2.ps1 / chain_opp_est_v21.ps1:
# never `Start-Process -Wait` (it waits for descendants and hung 23 min once) -- use -PassThru + Wait-Process -Id;
# no in-script scoring (a `2>&1` inside a -File PowerShell turned stdout into RemoteException records and
# lost the report -- score from Bash afterwards); boot only through L63/s0/_boot.ps1, never from inside a
# python process tree.
#
# Arms (all --estimator v2 --tracker):
#   1. gate_off10      entries 0:10    --feed-opp-elixir off                          (guarded)
#   2. gate_true10     entries 0:10    --feed-opp-elixir true                         (guarded)
#   3. feed_est_s1     entries 0:100   --feed-opp-elixir estimated --feed-noise live
#   4. feed_estL_s1    entries 0:100   --feed-opp-elixir estimated --feed-noise corrL --corr
#   5. gate_off10_s2   entries 100:110 --feed-opp-elixir off
#   6. gate_true10_s2  entries 100:110 --feed-opp-elixir true
#   7. feed_est_s2     entries 100:200 --feed-opp-elixir estimated --feed-noise live
# After arm 1 AND arm 2 (the two "gate" sanity arms), if that arm's summary.json is missing: Note +
# Stop-Engine + exit 2 -- the same shape as chain_opp_est_v21.ps1's smoke guard, so a broken --feed-off/
# --feed-true path (which MUST be the cheapest, best-understood arms) never burns engine time on arms 3-7.

$Repo    = 'C:\Users\benpe\ClashBot'
$Py      = "$Repo\icebow\.venv\Scripts\python.exe"
$E1      = "$Repo\scratchpad\gauntlet\L67\e1"
$A       = "$E1\opp_feed"
$Ckpt    = 'icebow\data\pipeline\s1_icebow_v6lat_s0.pt'
$Log     = "$E1\opp_feed.log"
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
  "$([DateTime]::UtcNow.ToString('s'))Z pid=$($p.Id) opp_feed $Name port=38031 out=$OutDir" | Add-Content "$E1\pids_feed.txt"
  Note "$Name launched pid $($p.Id): $($Extra -join ' ')"
  Wait-Process -Id $p.Id
  $sum = Test-Path "$OutDir\summary.json"
  Note "$Name exited code=$($p.ExitCode) summary.json exists=$sum"
  return ($p.ExitCode -eq 0)
}

function Stop-Engine {
  Note "stopping engine services + VM"
  $null = Run-Worker 'stop --stop-vm' "$E1\status_stop_feed.txt"
  Note ("stop done; qemu left={0}; free GB {1:N1}" -f @(Get-Process qemu* -ErrorAction SilentlyContinue).Count, ((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1MB))
}

Note "opp_feed start (7 arms: gate_off10, gate_true10, feed_est_s1, feed_estL_s1, gate_off10_s2, gate_true10_s2, feed_est_s2; --estimator v2 --tracker throughout)"

# 1. worker status; boot only if not already up
$st = Run-Worker 'status' "$E1\status_feed_pre.txt"
if ($st -match '"vm_ready":\s*true' -and $st -match '"services":\s*\[\s*true,\s*true\s*\]') { Note "services already up -- boot skipped" }
else {
  $bl = "$E1\boot_feed.log"
  $b = Start-Process powershell.exe -WindowStyle Hidden -PassThru -ArgumentList '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
         "$Repo\scratchpad\gauntlet\L63\s0\_boot.ps1" -RedirectStandardOutput $bl -RedirectStandardError "$E1\boot_feed.stderr.log"
  "$([DateTime]::UtcNow.ToString('s'))Z pid=$($b.Id) boot_feed" | Add-Content "$E1\pids_feed.txt"
  $t0 = Get-Date
  while (((Get-Date) - $t0).TotalMinutes -lt 45) { if ((Test-Path $bl) -and (Select-String -Path $bl -Pattern '^=== end' -Quiet)) { break }; Start-Sleep -Seconds 10 }
  $boot = if (Test-Path $bl) { Get-Content $bl -Raw } else { '' }
  if ($boot -notmatch 'exit=0') { Note "BOOT FAILED -- see boot_feed.log"; Stop-Engine; Note "ALL DONE (boot failed)"; exit 2 }
  Note ("boot ok: " + (($boot -split "`n" | Select-String 'attempt|exit=') -join ' | '))
}

# 2. liveness on 38031
$LOut = "$E1\liveness\p38031_feed"
$lp = Start-Process -FilePath $Py -ArgumentList @('-m', 'pipeline.e1_eval', '--mode', 'liveness', '--port', '38031', '--split', 'heldout',
        '--entries', '0:1', '--out', $LOut) -WorkingDirectory $Repo -WindowStyle Hidden -PassThru `
        -RedirectStandardOutput "$LOut.stdout.log" -RedirectStandardError "$LOut.stderr.log"
$null = $lp.Handle
Wait-Process -Id $lp.Id -Timeout 300 -ErrorAction SilentlyContinue
$live = if (Test-Path "$LOut.stdout.log") { Get-Content "$LOut.stdout.log" -Raw } else { '' }
if ($live -notmatch '"ok": true') { Note "LIVENESS FAILED -- see $LOut.stdout.log"; Stop-Engine; Note "ALL DONE (liveness failed)"; exit 2 }
Note "liveness ok on 38031"

# 3. arm 1 -- gate_off10: cheapest, best-understood arm (byte-identical to pre-O18 behaviour) -- must pass
# before spending any more engine time.
$null = Run-Audit 'gate_off10' "$A\gate_off10" @('--entries','0:10','--estimator','v2','--tracker','--feed-opp-elixir','off')
if (-not (Test-Path "$A\gate_off10\summary.json")) { Note "GATE_OFF10 FAILED -- skipping remaining arms"; Stop-Engine; Note "ALL DONE (gate_off10 failed)"; exit 2 }

# 4. arm 2 -- gate_true10: engine-truth opp_elixir, equivalent to e1_eval --noise-off opp_elixir.
$null = Run-Audit 'gate_true10' "$A\gate_true10" @('--entries','0:10','--estimator','v2','--tracker','--feed-opp-elixir','true')
if (-not (Test-Path "$A\gate_true10\summary.json")) { Note "GATE_TRUE10 FAILED -- skipping remaining arms"; Stop-Engine; Note "ALL DONE (gate_true10 failed)"; exit 2 }

# 5. arm 3 -- feed_est_s1: the decisive arm, live-reachable V2.1 estimate (B_tt_wl), 100 held-out ghosts.
$null = Run-Audit 'feed_est_s1' "$A\feed_est_s1" @('--entries','0:100','--estimator','v2','--tracker','--feed-opp-elixir','estimated','--feed-noise','live')

# 6. arm 4 -- feed_estL_s1: sensitivity arm, LONG correlated-degrade estimator input (B_corrL_tt_wl); the
# policy's own observation stays the standard live_view, unchanged from arm 3 (module docstring O18).
$null = Run-Audit 'feed_estL_s1' "$A\feed_estL_s1" @('--entries','0:100','--estimator','v2','--tracker','--corr','--feed-opp-elixir','estimated','--feed-noise','corrL')

# 7. arm 5 -- gate_off10_s2: second held-out slice, off arm.
$null = Run-Audit 'gate_off10_s2' "$A\gate_off10_s2" @('--entries','100:110','--estimator','v2','--tracker','--feed-opp-elixir','off')

# 8. arm 6 -- gate_true10_s2: second held-out slice, true arm.
$null = Run-Audit 'gate_true10_s2' "$A\gate_true10_s2" @('--entries','100:110','--estimator','v2','--tracker','--feed-opp-elixir','true')

# 9. arm 7 -- feed_est_s2: second held-out slice, live-reachable estimate arm (100:200).
$null = Run-Audit 'feed_est_s2' "$A\feed_est_s2" @('--entries','100:200','--estimator','v2','--tracker','--feed-opp-elixir','estimated','--feed-noise','live')

# 10. stop engine services + VM
Stop-Engine
Note "ALL DONE"
