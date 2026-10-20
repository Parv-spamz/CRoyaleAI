# chain_opp_feed_v6aug.ps1 -- O20: re-run the O18 feed experiment (pipeline.opp_est_audit's
# --feed-opp-elixir/--feed-noise) against the checkpoint that is ACTUALLY DEPLOYED LIVE, v6aug_s1
# (icebow\data\pipeline\s1_icebow_v6aug_s1.pt), rather than v6lat_s0 used by every prior arm in this
# series (chain_opp_feed.ps1). v6aug_s1 was trained on DEGRADED rows (opp_elixir None) rather than
# clean ones, so its feed-estimated behaviour is not assumed to match v6lat_s0's and needs its own
# measurement. Copied from the reviewed chain_opp_feed.ps1 (itself copied from chain_opp_est_v21.ps1)
# -- same structure, traps and guard pattern; only the checkpoint, output paths and arm list differ.
#
# Gate rationale: the gate_v6aug_off10 arm (--feed-opp-elixir off, byte-identical to pre-O18
# behaviour) on the FIRST 10 heldout entries must reproduce the existing control run
# attrib\e2_v6aug_s1_tau027\slot0 (100 heldout entries, tau 0.27, winrate 0.74 = 74/100 -- see
# score_attrib_e2_v6aug_s1_tau027.json). That run used pipeline.e1_eval (--mode eval --policy live),
# a different module, with matching seeds=0/shard=0/1/split=heldout/tau=0.27; opp_est_audit.py imports
# TAU_LIVE=0.27 from e1_eval.py as its own --tau default (pipeline\opp_est_audit.py:1446, importing
# pipeline\e1_eval.py:60), and its --seeds/--shard/--split argparse defaults are "0"/"0/1"/"heldout"
# (pipeline\opp_est_audit.py:1442-1445) -- all unspecified here, so this run inherits the same values
# as the anchor run. Reproducing 0.74 on the first 10 entries is what licenses using that already-run
# 100-match run as the control anchor instead of spending another 100 control matches on this
# checkpoint. Arm 2 (feed_est_v6aug_s1) is the actual measurement: the live-reachable V2 tracker
# estimate fed into the policy's BoardState, 100 held-out ghosts.
#
# Traps carried from chain_split_scalars.ps1 / chain_noise_attrib.ps1 / chain_opp_confirm.ps1 /
# chain_opp_est_v2.ps1 / chain_opp_est_v21.ps1 / chain_opp_feed.ps1:
# never `Start-Process -Wait` (it waits for descendants and hung 23 min once) -- use -PassThru + Wait-Process -Id;
# no in-script scoring (a `2>&1` inside a -File PowerShell turned stdout into RemoteException records and
# lost the report -- score from Bash afterwards); boot only through L63/s0/_boot.ps1, never from inside a
# python process tree.
#
# Arms (both --estimator v2 --tracker):
#   1. gate_v6aug_off10   entries 0:10   --feed-opp-elixir off                          (guarded)
#   2. feed_est_v6aug_s1  entries 0:100  --feed-opp-elixir estimated --feed-noise live
# After arm 1, if its summary.json is missing: Note + Stop-Engine + exit 2 -- the same shape as
# chain_opp_feed.ps1's smoke guard, so a broken --feed-off path never burns engine time on arm 2.
#
# NOTE (deviation from chain_opp_feed.ps1, in-scope): the pids log is renamed pids_feed_v6aug.txt
# (chain_opp_feed.ps1 uses pids_feed.txt) so this chain's pid records never interleave with a
# concurrently-running chain_opp_feed.ps1's own pids_feed.txt.

$Repo    = 'C:\Users\benpe\ClashBot'
$Py      = "$Repo\icebow\.venv\Scripts\python.exe"
$E1      = "$Repo\scratchpad\gauntlet\L67\e1"
$A       = "$E1\opp_feed_v6aug"
$Ckpt    = 'icebow\data\pipeline\s1_icebow_v6aug_s1.pt'
$Log     = "$E1\opp_feed_v6aug.log"
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
  "$([DateTime]::UtcNow.ToString('s'))Z pid=$($p.Id) opp_feed_v6aug $Name port=38031 out=$OutDir" | Add-Content "$E1\pids_feed_v6aug.txt"
  Note "$Name launched pid $($p.Id): $($Extra -join ' ')"
  Wait-Process -Id $p.Id
  $sum = Test-Path "$OutDir\summary.json"
  Note "$Name exited code=$($p.ExitCode) summary.json exists=$sum"
  return ($p.ExitCode -eq 0)
}

function Stop-Engine {
  Note "stopping engine services + VM"
  $null = Run-Worker 'stop --stop-vm' "$E1\status_stop_v6aug.txt"
  Note ("stop done; qemu left={0}; free GB {1:N1}" -f @(Get-Process qemu* -ErrorAction SilentlyContinue).Count, ((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1MB))
}

Note "opp_feed_v6aug start (gate 0:10 then 0:100 estimated; ckpt v6aug_s1)"

# 1. worker status; boot only if not already up
$st = Run-Worker 'status' "$E1\status_v6aug_pre.txt"
if ($st -match '"vm_ready":\s*true' -and $st -match '"services":\s*\[\s*true,\s*true\s*\]') { Note "services already up -- boot skipped" }
else {
  $bl = "$E1\boot_v6aug.log"
  $b = Start-Process powershell.exe -WindowStyle Hidden -PassThru -ArgumentList '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
         "$Repo\scratchpad\gauntlet\L63\s0\_boot.ps1" -RedirectStandardOutput $bl -RedirectStandardError "$E1\boot_v6aug.stderr.log"
  "$([DateTime]::UtcNow.ToString('s'))Z pid=$($b.Id) boot_v6aug" | Add-Content "$E1\pids_feed_v6aug.txt"
  $t0 = Get-Date
  while (((Get-Date) - $t0).TotalMinutes -lt 45) { if ((Test-Path $bl) -and (Select-String -Path $bl -Pattern '^=== end' -Quiet)) { break }; Start-Sleep -Seconds 10 }
  $boot = if (Test-Path $bl) { Get-Content $bl -Raw } else { '' }
  if ($boot -notmatch 'exit=0') { Note "BOOT FAILED -- see boot_v6aug.log"; Stop-Engine; Note "ALL DONE (boot failed)"; exit 2 }
  Note ("boot ok: " + (($boot -split "`n" | Select-String 'attempt|exit=') -join ' | '))
}

# 2. liveness on 38031
$LOut = "$E1\liveness\p38031_v6aug"
$lp = Start-Process -FilePath $Py -ArgumentList @('-m', 'pipeline.e1_eval', '--mode', 'liveness', '--port', '38031', '--split', 'heldout',
        '--entries', '0:1', '--out', $LOut) -WorkingDirectory $Repo -WindowStyle Hidden -PassThru `
        -RedirectStandardOutput "$LOut.stdout.log" -RedirectStandardError "$LOut.stderr.log"
$null = $lp.Handle
Wait-Process -Id $lp.Id -Timeout 300 -ErrorAction SilentlyContinue
$live = if (Test-Path "$LOut.stdout.log") { Get-Content "$LOut.stdout.log" -Raw } else { '' }
if ($live -notmatch '"ok": true') { Note "LIVENESS FAILED -- see $LOut.stdout.log"; Stop-Engine; Note "ALL DONE (liveness failed)"; exit 2 }
Note "liveness ok on 38031"

# 3. arm 1 -- gate_v6aug_off10: cheapest, best-understood arm (byte-identical to pre-O18 behaviour);
# must reproduce attrib\e2_v6aug_s1_tau027\slot0 (0.74, 74/100) on these first 10 entries before
# spending any more engine time.
$null = Run-Audit 'gate_v6aug_off10' "$A\gate_v6aug_off10" @('--entries','0:10','--estimator','v2','--tracker','--feed-opp-elixir','off')
if (-not (Test-Path "$A\gate_v6aug_off10\summary.json")) { Note "GATE_V6AUG_OFF10 FAILED -- skipping remaining arms"; Stop-Engine; Note "ALL DONE (gate_v6aug_off10 failed)"; exit 2 }

# 4. arm 2 -- feed_est_v6aug_s1: the decisive arm, live-reachable V2.1 estimate (B_tt_wl), 100 held-out ghosts.
$null = Run-Audit 'feed_est_v6aug_s1' "$A\feed_est_v6aug_s1" @('--entries','0:100','--estimator','v2','--tracker','--feed-opp-elixir','estimated','--feed-noise','live')

# 5. stop engine services + VM
Stop-Engine
Note "ALL DONE"
