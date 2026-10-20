$ErrorActionPreference = 'Stop'
$TaskRoot = (Resolve-Path (Join-Path $PSScriptRoot '../../../..')).Path
$Receipt = Join-Path $PSScriptRoot 'native_data_chain_launch.json'
if (Test-Path -LiteralPath $Receipt) { throw 'Native data chain already launched; inspect existing receipt' }
$Python = Join-Path $TaskRoot 'icebow/.venv/Scripts/python.exe'
$Driver = Join-Path $PSScriptRoot 'run_native_data_chain.py'
$Launcher = Start-Process -FilePath $Python -ArgumentList @('-u', $Driver) `
    -WorkingDirectory $TaskRoot -WindowStyle Hidden `
    -RedirectStandardOutput (Join-Path $PSScriptRoot 'native_data_chain.out') `
    -RedirectStandardError (Join-Path $PSScriptRoot 'native_data_chain.err') -PassThru
@{launcher_pid=$Launcher.Id; started_at=(Get-Date).ToString('o'); driver=$Driver;
  python=$Python; purpose='Wait for existing 20-replay preflight; then fixed645-replay native CPU pilot'} |
    ConvertTo-Json | Set-Content -LiteralPath $Receipt
Get-Content -LiteralPath $Receipt
