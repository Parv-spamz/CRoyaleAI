$ErrorActionPreference = 'Stop'
$repoPath = 'C:\Users\benpe\ClashBot'
$workPath = Join-Path $repoPath 'scratchpad\gauntlet\L72\improvement_loop'
$pythonPath = Join-Path $repoPath 'icebow\.venv\Scripts\python.exe'
$launchPath = Join-Path $workPath 'pilot_reconciliation_launch.json'
if (Test-Path -LiteralPath $launchPath) { throw 'Preserve original launch; do not duplicate verifier.' }
$argumentList = @('-u', 'scratchpad/gauntlet/L71/integration/run_check.py',
  '--name', 'l72-reserved-pilot-independent', '--expect', 'RESERVED_PILOT_INDEPENDENTLY_VERIFIED',
  '--', $pythonPath, '-u', 'scratchpad/gauntlet/L72/improvement_loop/verify_reserved_pilot.py',
  '--wait-for-completion')
$frozenSources = @{}
foreach ($name in @('verify_reserved_pilot.py', 'verify_native_preflight.py', 'PILOT_RECONCILIATION_PLAN.md')) {
  $frozenSources[$name] = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $workPath $name)).Hash.ToLower()
}
$worker = Start-Process -FilePath $pythonPath -ArgumentList $argumentList -WorkingDirectory $repoPath `
  -WindowStyle Hidden -RedirectStandardOutput (Join-Path $workPath 'pilot_reconciliation.out') `
  -RedirectStandardError (Join-Path $workPath 'pilot_reconciliation.err') -PassThru
@{started_at=(Get-Date -Format o);pid=$worker.Id;command=$argumentList;source_hashes=$frozenSources;
  purpose='Read-only independent reconciliation after existing645 collection; no model or native service calls'} |
  ConvertTo-Json -Depth 5 | Set-Content -Encoding utf8 -LiteralPath $launchPath
Write-Output "PILOT_RECONCILIATION_QUEUED pid=$($worker.Id)"
