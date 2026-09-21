# Move to the code/ directory (script is in code/tools/)
$CodeDir = Split-Path -Parent $PSScriptRoot
Set-Location $CodeDir

# ============================================================
# Phase 1: All Python test suites (v2.2 + v2.3)
# ============================================================
Write-Host "`n========== Phase 1: All Python test suites ==========" -ForegroundColor Cyan

$fail = 0
$totalSuites = 0
Get-ChildItem tests\test_v2_*.py | Sort-Object Name | ForEach-Object {
    $totalSuites++
    Write-Host "`n--- $($_.Name) ---" -ForegroundColor Yellow
    python $_.FullName
    if ($LASTEXITCODE -ne 0) {
        Write-Host "FAILED: $($_.Name)" -ForegroundColor Red
        $fail++
    }
}

Write-Host "`n========== Phase 1 result ==========" -ForegroundColor Cyan
Write-Host "Suites: $totalSuites, Failed: $fail" `
    -ForegroundColor $(if ($fail -eq 0) {'Green'} else {'Red'})

# ... 以下、Phase 2-4 は既存のまま ...