$ErrorActionPreference = 'Stop'
$taskRepo = 'C:/Users/benpe/ClashBot'
$taskLeaf = Join-Path $taskRepo 'scratchpad/gauntlet/L72/improvement_loop/development_rl_3'
if (Test-Path -LiteralPath (Join-Path $taskLeaf 'launch.json')) { throw 'Already launched; inspect existing chain' }
if (Test-Path -LiteralPath (Join-Path $taskLeaf 'chain_started.json')) { throw 'Existing chain marker' }
$taskProcess = Start-Process -FilePath (Join-Path $taskRepo 'research/ext/Royale/.venv/Scripts/python.exe') -ArgumentList @('-u', (Join-Path $taskLeaf 'run_chain.py')) -WorkingDirectory $taskRepo -WindowStyle Hidden -RedirectStandardOutput (Join-Path $taskLeaf 'chain.out') -RedirectStandardError (Join-Path $taskLeaf 'chain.err') -PassThru
@{ pid = $taskProcess.Id; utc = [DateTime]::UtcNow.ToString('o'); chain = 'run_chain.py'; owner_cutoff = '2026-10-06T13:00:00Z' } | ConvertTo-Json | Set-Content -Encoding utf8 (Join-Path $taskLeaf 'launch.json')
Write-Output "CURRICULUM_LAUNCHED $($taskProcess.Id)"
