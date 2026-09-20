cd C:\Users\user\OneDrive\ドキュメント\GitHub\StaTable\code

# ============================================================
# Phase 1: 全 12 Python テストスイート
# ============================================================
Write-Host "`n========== Phase 1: All Python test suites ==========" -ForegroundColor Cyan

$fail = 0
$totalSuites = 0
Get-ChildItem tests\test_v2_2_p*.py | Sort-Object Name | ForEach-Object {
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

# ============================================================
# Phase 2: 生成 C コードの構造検証
# ============================================================
Write-Host "`n========== Phase 2: verify_generated_code ==========" -ForegroundColor Cyan
python tools\verify_generated_code.py --root output

# ============================================================
# Phase 3: cross-layer include の確認
# ============================================================
Write-Host "`n========== Phase 3: cross-layer includes ==========" -ForegroundColor Cyan

Write-Host "`n[Application/statable_transitions_Application.c]" -ForegroundColor Yellow
Select-String -Path output\Application\statable_transitions_Application.c `
    -Pattern '#include'

Write-Host "`n[Driver/statable_role_functions_Driver.c]" -ForegroundColor Yellow
Select-String -Path output\Driver\statable_role_functions_Driver.c `
    -Pattern '#include'

Write-Host "`n[Middleware/statable_transitions_Middleware.c]" -ForegroundColor Yellow
Select-String -Path output\Middleware\statable_transitions_Middleware.c `
    -Pattern '#include'

# ============================================================
# Phase 4: MISRA チェック
# ============================================================
Write-Host "`n========== Phase 4: MISRA check ==========" -ForegroundColor Cyan
python tools\run_misra_check.py --root output --out misra_report
python tools\analyze_misra_impact.py `
  --xml misra_report\cppcheck_raw.xml `
  --out misra_report\impact.md `
  --csv misra_report\impact.csv

Write-Host "`n--- summary.md ---" -ForegroundColor Yellow
Get-Content misra_report\summary.md

Write-Host "`n--- impact.csv (top 20) ---" -ForegroundColor Yellow
Get-Content misra_report\impact.csv | Select-Object -First 20

# ============================================================
# 完了
# ============================================================
Write-Host "`n========== ALL PHASES DONE ==========" -ForegroundColor Green