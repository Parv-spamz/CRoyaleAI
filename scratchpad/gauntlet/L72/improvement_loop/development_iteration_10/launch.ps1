$ErrorActionPreference = 'Stop'
$repo = 'C:/Users/benpe/ClashBot'
$leaf = "$repo/scratchpad/gauntlet/L72/improvement_loop/development_iteration_10"
if (Test-Path -LiteralPath "$leaf/launch.json") { throw 'Already launched' }
if (Test-Path -LiteralPath "$leaf/chain_started.json") { throw 'Chain already started' }
$python = "$repo/research/ext/Royale/.venv/Scripts/python.exe"
$proc = Start-Process -FilePath $python -ArgumentList @('-u', "$leaf/run_chain.py") -WorkingDirectory $repo -WindowStyle Hidden -RedirectStandardOutput "$leaf/chain.out" -RedirectStandardError "$leaf/chain.err" -PassThru
@{ pid=$proc.Id; utc=[DateTime]::UtcNow.ToString('o') } | ConvertTo-Json | Set-Content -LiteralPath "$leaf/launch.json" -Encoding utf8
