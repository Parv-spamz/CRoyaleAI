$ErrorActionPreference = 'Stop'
$repoPath = 'C:\Users\benpe\ClashBot'
$workPath = Join-Path $repoPath 'scratchpad\gauntlet\L72\improvement_loop'
$pythonPath = Join-Path $repoPath 'icebow\.venv\Scripts\python.exe'
$launchPath = Join-Path $workPath 'corrected_icebow_launch.json'
if (Test-Path -LiteralPath $launchPath) { throw 'Do not duplicate this collection.' }
if ((Get-Date) -ge [datetime]'2026-10-06') { throw 'Tuesday cutoff; preserve handoff.' }
$conflicts = Get-CimInstance Win32_Process | Where-Object {
  $_.Name -eq 'python.exe' -and $_.CommandLine -match 'collect_reserved|capture_native_preflight|probe_native_elite_form|run_native_data_chain'
}
if ($conflicts) { throw 'A native worker client or chain already exists.' }
$argumentList = @('-u', 'scratchpad/gauntlet/L71/integration/run_check.py',
  '--name', 'l72-corrected-icebow-collection', '--expect', 'CORRECTED_ICEBOW_COLLECTION_COMPLETE',
  '--', $pythonPath, '-u', 'scratchpad/gauntlet/L72/improvement_loop/collect_reserved_icebow_corrected.py')
$frozenSources = @{}
foreach ($name in @('collect_reserved_icebow_corrected.py','native_catalog_overlay.py',
  'native_catalog_corrected.json','NATIVE_CATALOG_CORRECTION_PLAN.md','reserved_icebow_corrected_prepared.json')) {
  $frozenSources[$name] = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $workPath $name)).Hash.ToLower()
}
$worker = Start-Process -FilePath $pythonPath -ArgumentList $argumentList -WorkingDirectory $repoPath `
  -WindowStyle Hidden -RedirectStandardOutput (Join-Path $workPath 'corrected_icebow_collection.out') `
  -RedirectStandardError (Join-Path $workPath 'corrected_icebow_collection.err') -PassThru
@{started_at=(Get-Date -Format o);pid=$worker.Id;command=$argumentList;source_hashes=$frozenSources;
  purpose='162 newly compatible original-form reserved Icebow replays, one CPU native worker, no model calls'} |
  ConvertTo-Json -Depth 5 | Set-Content -Encoding utf8 -LiteralPath $launchPath
Write-Output "CORRECTED_ICEBOW_COLLECTION_STARTED pid=$($worker.Id)"
