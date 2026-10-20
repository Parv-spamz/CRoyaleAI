param([int]$PriorLauncherPid)
$ErrorActionPreference = 'Stop'
Set-Location 'C:/Users/benpe/ClashBot'
$out = 'scratchpad/gauntlet/L71/decision_options'
$prior = Get-CimInstance Win32_Process -Filter "ProcessId=$PriorLauncherPid"
if ($prior) {
    if ($prior.Name -ne 'python.exe' -or $prior.CommandLine -notlike '*decision_options/check_sampling.py*') {
        throw 'Prior PID does not belong to this diagnostic; refusing to wait on a different task.'
    }
    Write-Output 'Waiting for the original diagnostic to exit; no simultaneous diagnostic CPU workers.'
    Wait-Process -Id $PriorLauncherPid -ErrorAction SilentlyContinue
}
Copy-Item -LiteralPath "$out/report.json" -Destination "$out/report_initial_invalid_r1.json"
Write-Output 'Original diagnostic exited; starting corrected old-R1 vocabulary evaluation.'
& icebow/.venv/Scripts/python.exe -u "$out/check_sampling_v2.py"
exit $LASTEXITCODE
