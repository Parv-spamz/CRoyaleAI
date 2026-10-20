$ErrorActionPreference = 'Stop'
$repoPath = 'C:\Users\benpe\ClashBot'
$workPath = Join-Path $repoPath 'scratchpad\gauntlet\L72\improvement_loop'
$pythonPath = Join-Path $repoPath 'icebow\.venv\Scripts\python.exe'
$launchPath = Join-Path $workPath 'corrected_icebow_verifier_launch.json'
if (Test-Path -LiteralPath $launchPath) { throw 'Do not duplicate verifier.' }
$argumentList = @('-u', 'scratchpad/gauntlet/L71/integration/run_check.py',
  '--name', 'l72-corrected-icebow-independent', '--expect', 'CORRECTED_ICEBOW_INDEPENDENTLY_VERIFIED',
  '--', $pythonPath, '-u', 'scratchpad/gauntlet/L72/improvement_loop/verify_reserved_icebow_corrected.py',
  '--wait-for-completion')
$frozenSources = @{}
foreach ($name in @('verify_reserved_icebow_corrected.py','verify_native_preflight.py','NATIVE_CATALOG_CORRECTION_PLAN.md')) {
  $frozenSources[$name] = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $workPath $name)).Hash.ToLower()
}
$worker = Start-Process -FilePath $pythonPath -ArgumentList $argumentList -WorkingDirectory $repoPath `
  -WindowStyle Hidden -RedirectStandardOutput (Join-Path $workPath 'corrected_icebow_verifier.out') `
  -RedirectStandardError (Join-Path $workPath 'corrected_icebow_verifier.err') -PassThru
@{started_at=(Get-Date -Format o);pid=$worker.Id;command=$argumentList;source_hashes=$frozenSources;
  purpose='Read-only independent reconciliation after new162 Icebow collection, no model/native service calls'} |
  ConvertTo-Json -Depth 5 | Set-Content -Encoding utf8 -LiteralPath $launchPath
Write-Output "CORRECTED_ICEBOW_VERIFIER_QUEUED pid=$($worker.Id)"
