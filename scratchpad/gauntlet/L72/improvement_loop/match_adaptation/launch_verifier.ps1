$ErrorActionPreference = 'Stop'
$repo = 'C:/Users/benpe/ClashBot'
$here = Join-Path $repo 'scratchpad/gauntlet/L72/improvement_loop/match_adaptation'
$python = Join-Path $repo 'icebow/.venv/Scripts/python.exe'
if (Test-Path (Join-Path $here 'verifier_launch.json')) { throw 'Preserve existing verifier launch' }
$arguments = @('scratchpad/gauntlet/L71/integration/run_check.py', '--name', 'l72-match-adaptation-independent-v2', '--expect', 'MATCH_ADAPTATION_INDEPENDENT_COMPLETE', '--', 'icebow/.venv/Scripts/python.exe', 'scratchpad/gauntlet/L72/improvement_loop/match_adaptation/verify.py', '--wait')
$frozen = @{}
foreach ($name in @('verify.py','io_utils.py','METRICS.md','prepared.json','verify_preflight.json')) {
    $frozen[$name] = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $here $name)).Hash.ToLowerInvariant()
}
$process = Start-Process -FilePath $python -ArgumentList $arguments -WorkingDirectory $repo -WindowStyle Hidden -RedirectStandardOutput (Join-Path $here 'verifier.out') -RedirectStandardError (Join-Path $here 'verifier.err') -PassThru
@{ pid=$process.Id; created=(Get-Date -Format o); command=$arguments; sources=$frozen; waits_for='l72-match-adaptation-audit-v2.json successful receipt'; model_calls=$false } | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $here 'verifier_launch.json')
Write-Output ('VERIFIER_QUEUED ' + $process.Id)
