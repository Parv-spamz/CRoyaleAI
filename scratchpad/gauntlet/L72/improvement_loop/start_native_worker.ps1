$ErrorActionPreference = 'Stop'
$TaskRoot = (Resolve-Path (Join-Path $PSScriptRoot '../../../..')).Path
. (Join-Path $TaskRoot 'research/ext/cr-native-sandbox/runtime.env.ps1')
$env:CR_SANDBOX_DATA = Join-Path $TaskRoot 'icebow/data/bench/native_confirmation_20261005/runtime'
& (Join-Path $TaskRoot 'icebow/.venv/Scripts/python.exe') -u (Join-Path $PSScriptRoot 'start_native_worker.py')
exit $LASTEXITCODE
