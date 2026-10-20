# Pin the existing owner-supplied runtime; do not change packages or system policy.
$ErrorActionPreference = 'Stop'
$TaskRepo = (Resolve-Path (Join-Path $PSScriptRoot '../../../..')).Path
$NativeRepo = Join-Path $TaskRepo 'research/ext/cr-native-sandbox'
$TaskData = Join-Path $TaskRepo 'icebow/data/bench/native_confirmation_20261005/runtime'
$Report = Join-Path $PSScriptRoot 'native_host_verified.json'
if (Test-Path -LiteralPath $Report) { throw 'Fresh host verification required' }
. (Join-Path $NativeRepo 'runtime.env.ps1')
$env:CR_SANDBOX_DATA = $TaskData
$Manifest = Join-Path $TaskData 'manifest/runtime-manifest.json'
if (Test-Path -LiteralPath $Manifest) { throw 'Existing task manifest must not be overwritten' }

# This pre-existing template documents the owner's September1 Play-derived APKs.
# Every native library and the asset pack still requires the original exact hash.
$Template = Join-Path $NativeRepo 'runtime/runtime-manifest.local-template.json'
& (Join-Path $NativeRepo 'scripts/freeze_runtime.ps1') -ManifestTemplate $Template -OutputManifest $Manifest
$Badging = & (Join-Path $env:CR_SANDBOX_ANDROID_SDK 'build-tools/35.0.0/aapt.exe') dump badging $env:CR_SANDBOX_BASE_APK
if ($LASTEXITCODE -ne 0) { throw 'APK version inspection failed' }
$Package = @($Badging | Where-Object { $_ -like 'package:*' })[0]
if ($Package -notmatch "name='com.supercell.clashroyale' versionCode='150535029'") { throw 'Wrong installed runtime package' }

$DoctorPath = Join-Path $PSScriptRoot 'native_doctor_local.json'
$ShellExe = (Get-Process -Id $PID).Path
& $ShellExe -NoProfile -File (Join-Path $NativeRepo 'scripts/doctor.ps1') -Json | Set-Content -LiteralPath $DoctorPath
$DoctorExit = $LASTEXITCODE
if ($DoctorExit -ne 0) { throw 'Native hard preflight failed' }
$Acceleration = & (Join-Path $env:CR_SANDBOX_ANDROID_SDK 'emulator/emulator.exe') -accel-check 2>&1 | Out-String
$AccelerationExit = $LASTEXITCODE
if ($AccelerationExit -ne 0 -or $Acceleration -notmatch 'WHPX.*installed and usable') { throw 'Usable acceleration not verified' }
foreach ($TaskPort in @(5560,5561,37031,38031)) {
    $Listener = [Net.Sockets.TcpListener]::new([Net.IPAddress]::Loopback,$TaskPort)
    try { $Listener.Start() } finally { $Listener.Stop() }
}
$Record = [ordered]@{
    owner_local_template_sha256=(Get-FileHash -LiteralPath $Template -Algorithm SHA256).Hash.ToLowerInvariant()
    runtime_manifest=$Manifest
    runtime_manifest_sha256=(Get-FileHash -LiteralPath $Manifest -Algorithm SHA256).Hash.ToLowerInvariant()
    package=$Package
    doctor_exit=$DoctorExit
    doctor_sha256=(Get-FileHash -LiteralPath $DoctorPath -Algorithm SHA256).Hash.ToLowerInvariant()
    acceleration_exit=$AccelerationExit
    acceleration=$Acceleration.Trim()
    selected_emulator_serial='emulator-5560'
    selected_ports=@(5560,5561,37031,38031)
    started_emulator=$false
    system_policy_changed=$false
    note='Original doctor preserves upstream APK mismatch. Local owner Play-derived APKs separately version-checked and pinned; all14 native libraries and asset pack retain original exact hashes. Firmware flag is misleading under the active hypervisor. MuMu port5555 is left unchanged.'
}
$Record | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $Report
Write-Output 'NATIVE_LOCAL_HOST_VERIFIED_NOT_STARTED'
