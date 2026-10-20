# Owner 2026-09-26: keep gen_v1lat26_s0 training running, but stop it if the battery reaches 6%.
# Polls every 30 s; stops ONLY the training process (pid passed in); exits when training ends on its own.
param([int]$TrainPid = 20336, [int]$Threshold = 6)
$log = Join-Path $PSScriptRoot "battery_guard.log"
function Log($m) { Add-Content -Path $log -Value "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $m" }
Log "guard started: training pid $TrainPid, stop at <= $Threshold%"
while ($true) {
    $p = Get-Process -Id $TrainPid -ErrorAction SilentlyContinue
    if (-not $p) { Log "training process gone (finished or stopped) -> guard exits"; break }
    $b = (Get-CimInstance Win32_Battery | Select-Object -First 1).EstimatedChargeRemaining
    if ($null -ne $b -and $b -le $Threshold) {
        Stop-Process -Id $TrainPid -Force
        Log "battery $b% <= $Threshold% -> STOPPED training pid $TrainPid (best-epoch checkpoint stays in icebow/data/pipeline/gen_v1lat26_s0)"
        break
    }
    Start-Sleep -Seconds 30
}
