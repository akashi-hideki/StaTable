# build_monitor_gui.ps1
# Builds StaTableMonitorGUI.exe via PyInstaller.
# Output: dist\StaTableMonitorGUI.exe

$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..\..")

Write-Host "=== Checking PyInstaller ==="
if (-not (Get-Command pyinstaller -ErrorAction SilentlyContinue)) {
    Write-Host "Installing PyInstaller..."
    pip install pyinstaller
}

Write-Host "=== Building StaTableMonitorGUI.exe ==="
Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue
Remove-Item -Force *.spec -ErrorAction SilentlyContinue

pyinstaller `
    --onefile `
    --windowed `
    --name StaTableMonitorGUI `
    --paths code `
    --hidden-import serial `
    --hidden-import serial.tools.list_ports `
    --hidden-import PySide6.QtCore `
    --hidden-import PySide6.QtWidgets `
    --hidden-import PySide6.QtGui `
    code\statable_monitor_gui\entry.py

Write-Host "`n=== Result ==="
if (Test-Path dist\StaTableMonitorGUI.exe) {
    $size = (Get-Item dist\StaTableMonitorGUI.exe).Length
    Write-Host "OK: dist\StaTableMonitorGUI.exe ($([math]::Round($size/1MB,2)) MB)"
} else {
    Write-Error "Build failed: dist\StaTableMonitorGUI.exe not found"
}
