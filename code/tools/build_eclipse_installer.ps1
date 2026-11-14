# build_eclipse_installer.ps1
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

Write-Host "=== Checking PyInstaller ==="
if (-not (Get-Command pyinstaller -ErrorAction SilentlyContinue)) {
    pip install pyinstaller
}

# Kill any running EXE first (prevents qoffscreen.dll lock)
Write-Host "=== Killing running Eclipse Installer processes ==="
Get-Process "*Eclipse*Installer*" -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 1

# Force-remove both dist and build before build
Write-Host "=== Cleaning dist and build ==="
Remove-Item -Recurse -Force "dist\StaTable-Eclipse-Installer" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "build\eclipse_installer" -ErrorAction SilentlyContinue

Write-Host "=== Building StaTable-Eclipse-Installer.exe ==="
$log = "tmp_build_eclipse.log"
$err = "tmp_build_eclipse.err"

# Use cmd.exe to avoid PowerShell's NativeCommandError on stderr.
$ErrorActionPreference = "Continue"
cmd /c "pyinstaller eclipse_installer.spec --noconfirm --clean > $log 2> $err"
$rc = $LASTEXITCODE
$ErrorActionPreference = "Stop"

# Print last 10 lines of log (both files)
Write-Host "--- build log (tail) ---"
Get-Content $log -Tail 10 -ErrorAction SilentlyContinue
if ((Get-Item $err -ErrorAction SilentlyContinue).Length -gt 0) {
    Write-Host "--- stderr (tail) ---"
    Get-Content $err -Tail 10 -ErrorAction SilentlyContinue
}

if ($rc -ne 0) {
    Write-Error "PyInstaller failed (exit $rc). See $log / $err"
    exit 1
}

# Verify COLLECT succeeded
$exe      = "dist\StaTable-Eclipse-Installer\StaTable-Eclipse-Installer.exe"
$internal = "dist\StaTable-Eclipse-Installer\_internal"
$pyDll    = "$internal\python313.dll"

Write-Host "`n=== Result ==="
if (-not (Test-Path $exe))   { Write-Error "EXE not found"; exit 1 }
if (-not (Test-Path $pyDll)) { Write-Error "python313.dll missing in _internal"; exit 1 }

$size  = (Get-Item $exe).Length
$total = (Get-ChildItem "dist\StaTable-Eclipse-Installer" -Recurse | Measure-Object Length -Sum).Sum
Write-Host "OK: $exe ($([math]::Round($size/1MB,2)) MB, total $([math]::Round($total/1MB,1)) MB)"

Remove-Item $log, $err -ErrorAction SilentlyContinue
