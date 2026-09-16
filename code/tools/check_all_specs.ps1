# tools/check_all_specs.ps1
# specs/ 配下の全 XML で一貫性チェックを実行（round-trip のみ）

$ErrorActionPreference = "Continue"
$ProjectRoot = "C:\Users\user\OneDrive\ドキュメント\GitHub\StaTable\code"
$SpecsDir = Join-Path $ProjectRoot "specs"
$Tool = Join-Path $ProjectRoot "tools\consistency_check.py"

Set-Location $ProjectRoot

$xmls = Get-ChildItem -Path $SpecsDir -Filter "*.xml"
Write-Host "=== 対象 XML: $($xmls.Count) 件 ===" -ForegroundColor Cyan

$summary = @()

foreach ($xml in $xmls) {
    $rel = "specs/$($xml.Name)"
    $report = "report_$($xml.BaseName).md"

    Write-Host ""
    Write-Host "--- $rel ---" -ForegroundColor Yellow

    # 引数を配列で渡す（-- の誤解釈を回避）
    $args = @(
        $Tool,
        "--xml", $rel,
        "--skip-fields",
        "--skip-enums",
        "--skip-generated-c",
        "--report", $report,
        "--quiet"
    )
    & python $args

    # レポートから round-trip 結果を抽出
    if (Test-Path $report) {
        $content = Get-Content $report -Raw
        if ($content -match "## 1\. XML round-trip: (\w+)") {
            $status = $Matches[1]
            $summary += [PSCustomObject]@{
                XML    = $xml.Name
                Status = $status
            }
            $color = if ($status -eq "PASS") { "Green" } else { "Red" }
            Write-Host "  round-trip: $status" -ForegroundColor $color
        }
    }
}

Write-Host ""
Write-Host "=== サマリ ===" -ForegroundColor Cyan
$summary | Format-Table -AutoSize

$passCount = ($summary | Where-Object { $_.Status -eq "PASS" }).Count
$totalCount = $summary.Count
Write-Host ""
$color = if ($passCount -eq $totalCount) { "Green" } else { "Yellow" }
Write-Host "PASS: $passCount / $totalCount" -ForegroundColor $color