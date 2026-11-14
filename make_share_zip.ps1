$ErrorActionPreference = "Stop"

$Repo    = "C:\Users\user\OneDrive\ドキュメント\GitHub\StaTable"
$Staging = "C:\tmp\statable_share_v3.6.0"
$ZipTmp  = "C:\tmp\StaTable-comm-monitor-v3.6.0-share.zip"
$ZipOut  = Join-Path $Repo "StaTable-comm-monitor-v3.6.0-share.zip"

if (Test-Path $Staging) { Remove-Item -Recurse -Force $Staging }
New-Item -ItemType Directory -Force -Path $Staging | Out-Null

$Targets = @(
    "code\codegen\comm_monitor",
    "code\statable_monitor",
    "code\tests\test_v3_6_0_comm_monitor_generator.py",
    "code\docs\SPEC_COMM_MONITOR_v1_2.md",
    "code\tools\patches\patch_v3_6_0_comm_monitor.py",
    "code\tools\patches\fix_templates.py"
)

foreach ($rel in $Targets) {
    $src = Join-Path $Repo $rel
    if (-not (Test-Path $src)) {
        Write-Warning "missing: $rel"
        continue
    }
    $dst = Join-Path $Staging $rel
    New-Item -ItemType Directory -Force -Path (Split-Path $dst -Parent) | Out-Null
    Copy-Item -Path $src -Destination $dst -Recurse -Force
    Write-Host "  copied: $rel"
}

$readme = @"
# StaTable comm monitor v3.6.0 (share)

## 内容
- code/codegen/comm_monitor/   C コード生成器 (GET 専用 / ASCII のみ)
- code/statable_monitor/       PC 側 Python SDK (最小実装)
- code/tests/                  生成器のテスト (5 PASS)
- code/docs/SPEC_COMM_MONITOR_v1_2.md  仕様書
- code/tools/patches/          適用パッチ + 修正スクリプト

## 前提
- Python 3.10+

## 仕様の要点
- ASCII のみ: STX + 本文 + CR + ETX
- コマンド: PING / LIST / GET / HELP (SET なし)
- ポーリング周期: PC 制御、最小 100 ms / 既定 200 ms
- CRC なし
"@
Set-Content -Path (Join-Path $Staging "README_SHARE.md") -Value $readme -Encoding UTF8

if (Test-Path $ZipTmp) { Remove-Item -Force $ZipTmp }
Compress-Archive -Path (Join-Path $Staging "*") -DestinationPath $ZipTmp -Force
if (Test-Path $ZipOut) { Remove-Item -Force $ZipOut }
Move-Item -Path $ZipTmp -Destination $ZipOut -Force

Write-Host ""
Write-Host "Created: $ZipOut"
Write-Host ("Size: {0:N1} KB" -f ((Get-Item $ZipOut).Length / 1KB))