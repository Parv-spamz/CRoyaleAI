$ErrorActionPreference = 'Stop'
$repoRoot = 'C:\Users\benpe\ClashBot'
$experimentDir = Join-Path $repoRoot 'scratchpad\gauntlet\L72\improvement_loop\development_iteration_7'
$launchFile = Join-Path $experimentDir 'launch.json'
if ((Test-Path -LiteralPath $launchFile) -or (Test-Path -LiteralPath (Join-Path $experimentDir 'chain_started.json'))) { throw 'Existing launch: inspect, never duplicate.' }
$preflight = Get-Content -LiteralPath (Join-Path $experimentDir 'prelaunch.json') -Raw | ConvertFrom-Json
$receipt = Get-Content -LiteralPath (Join-Path $repoRoot 'scratchpad\gauntlet\L71\integration\checks\l72-development7-preflight.json') -Raw | ConvertFrom-Json
if (-not $preflight.complete -or -not $preflight.optimizer_allowed -or $receipt.exit_code -ne 0 -or -not $receipt.matched) { throw 'Unmet preflight' }
$conflicts = @(Get-CimInstance Win32_Process | Where-Object {
    $_.Name -match '^python(w)?\.exe$' -and $_.CommandLine -match 'ClashBot|pipeline\.|development_iteration' -and
    $_.CommandLine -match 'run_chain\.py|resume_chain\.py|train_expert_context|train_gen|train_rocket_curriculum|pipeline\.rl_royale|pipeline\.search_s0|run_screen\.py|resume_verified_chain|run_experiments\.py|development_iteration_.*/train\.py'
})
if ($conflicts.Count) { throw ('Existing chain: ' + (($conflicts | Select-Object -ExpandProperty ProcessId) -join ',')) }
$gpuApps = @(& nvidia-smi --query-compute-apps=pid,process_name --format=csv,noheader)
if ($LASTEXITCODE -ne 0) { throw 'GPU inspection failed' }
if ($gpuApps | Where-Object { $_ -match 'python(w)?\.exe|demo_gradio' }) { throw 'Existing Python GPU process' }
$pythonExe = Join-Path $repoRoot 'icebow\.venv\Scripts\python.exe'
$driver = Join-Path $experimentDir 'run_chain.py'
$process = Start-Process -FilePath $pythonExe -ArgumentList @('-u', $driver) -WorkingDirectory $repoRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $experimentDir 'chain.out') -RedirectStandardError (Join-Path $experimentDir 'chain.err') -PassThru
@{ launcher_pid=$process.Id; started_at=(Get-Date -Format o); driver=$driver; python=$pythonExe; prelaunch_sha256=(Get-FileHash -LiteralPath (Join-Path $experimentDir 'prelaunch.json') -Algorithm SHA256).Hash.ToLowerInvariant(); serial=$true; live_settings_changed=$false; existing_live_stop_preserved=$true } | ConvertTo-Json | Set-Content -LiteralPath $launchFile
Write-Output ('FROZEN_PROJECTILE_LAUNCHED ' + $process.Id)
