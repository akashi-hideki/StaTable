<#
.SYNOPSIS
    StaTable: 予約フィールド（role function signature / State.do）の
    GUI 編集箇所を全数調査する。

.DESCRIPTION
    v3.7 で SettingsPanel から以下を削除した:
      - RoleFunction: return_type / arg1_type / arg1_name
                     / arg2_type / arg2_name
      - State:        do

    しかし、他のダイアログ（RoleFunctionDialog, ActionEditDialog など）が
    まだこれらのフィールドを編集可能なまま残している可能性がある。
    本スクリプトは全 Python ファイルを走査し、以下を報告する:

      1. 各予約フィールドが出現するファイル・行・コンテキスト
      2. GUI レイヤ（statable_gui/）での編集・表示箇所
      3. ダイアログ内の QLineEdit / QComboBox 等の生成箇所との相関
      4. コード生成（codegen/）での実際の使用有無

.PARAMETER Root
    プロジェクトの code/ ディレクトリ (default: カレント)

.PARAMETER ShowContext
    マッチ行の前後 N 行を表示 (default: 2)

.PARAMETER GuiOnly
    statable_gui/ 配下のみを対象にする

.EXAMPLE
    .\find_reserved_field_editors.ps1
    .\find_reserved_field_editors.ps1 -GuiOnly
    .\find_reserved_field_editors.ps1 -Root C:\path\to\code -ShowContext 3
#>

param(
    [string]$Root = ".",
    [int]$ShowContext = 2,
    [switch]$GuiOnly
)

$ErrorActionPreference = "Stop"

# ----------------------------------------------------------------------
# 設定
# ----------------------------------------------------------------------
$ReservedFields = @(
    @{ Name = "return_type";  Regex = '\breturn_type\b' },
    @{ Name = "arg1_type";    Regex = '\barg1_type\b' },
    @{ Name = "arg1_name";    Regex = '\barg1_name\b' },
    @{ Name = "arg2_type";    Regex = '\barg2_type\b' },
    @{ Name = "arg2_name";    Regex = '\barg2_name\b' },
    @{ Name = "State.do";     Regex = '\.do\b|\bdo\s*[:=]' }
)

# 探索対象ディレクトリ
if ($GuiOnly) {
    $SearchDirs = @("statable_gui")
} else {
    $SearchDirs = @("statable", "statable_gui", "codegen", "tests", "tools")
}

# 除外パターン（出力ログ等）
$ExcludePatterns = @(
    '\\output\\',
    '\\misra_report\\',
    '__pycache__',
    '\.pyc$'
)

# ----------------------------------------------------------------------
# ヘルパー
# ----------------------------------------------------------------------
function Write-Section {
    param([string]$Title, [ConsoleColor]$Color = "Cyan")
    Write-Host ""
    Write-Host ("=" * 78) -ForegroundColor $Color
    Write-Host "  $Title" -ForegroundColor $Color
    Write-Host ("=" * 78) -ForegroundColor $Color
}

function Test-Excluded {
    param([string]$Path)
    foreach ($p in $ExcludePatterns) {
        if ($Path -match $p) { return $true }
    }
    return $false
}

function Get-PythonFiles {
    param([string[]]$Dirs)
    $files = @()
    foreach ($d in $Dirs) {
        $full = Join-Path $Root $d
        if (Test-Path $full) {
            $files += Get-ChildItem -Path $full -Recurse -Filter "*.py" -File |
                Where-Object { -not (Test-Excluded $_.FullName) }
        }
    }
    return $files
}

# ----------------------------------------------------------------------
# 開始
# ----------------------------------------------------------------------
Write-Section "StaTable: Reserved-field editor search"
Write-Host "  Root        : $((Resolve-Path $Root).Path)"
Write-Host "  Search dirs : $($SearchDirs -join ', ')"
Write-Host "  GuiOnly     : $GuiOnly"
Write-Host "  Context     : $ShowContext lines"

$files = Get-PythonFiles -Dirs $SearchDirs
Write-Host "  Python files: $($files.Count)"
Write-Host ""

if ($files.Count -eq 0) {
    Write-Host "[ERROR] No Python files found. Check -Root." -ForegroundColor Red
    exit 1
}

# ----------------------------------------------------------------------
# 1. 予約フィールドごとの全出現箇所
# ----------------------------------------------------------------------
Write-Section "1. All occurrences of reserved fields" "Yellow"

$summary = @{}   # fieldName -> count
foreach ($field in $ReservedFields) {
    $summary[$field.Name] = 0
}

foreach ($field in $ReservedFields) {
    Write-Host ""
    Write-Host "--- $($field.Name) ---" -ForegroundColor Yellow

    $hits = @()
    foreach ($f in $files) {
        $rel = $f.FullName.Substring((Resolve-Path $Root).Path.Length + 1)
        $matches = Select-String -Path $f.FullName -Pattern $field.Regex `
            -Context $ShowContext, $ShowContext -ErrorAction SilentlyContinue
        if ($matches) {
            foreach ($m in $matches) {
                $hits += [PSCustomObject]@{
                    File    = $rel
                    Line    = $m.LineNumber
                    Text    = $m.Line.Trim()
                    Context = $m.Context
                }
                $summary[$field.Name]++
            }
        }
    }

    if ($hits.Count -eq 0) {
        Write-Host "  (no hits)" -ForegroundColor DarkGray
        continue
    }

    # ファイルごとにグループ化
    $byFile = $hits | Group-Object File | Sort-Object Name
    foreach ($g in $byFile) {
        Write-Host "  $($g.Name)" -ForegroundColor White
        foreach ($h in $g.Group) {
            Write-Host ("    L{0,-5}  {1}" -f $h.Line, $h.Text) -ForegroundColor Gray
        }
    }
}

# ----------------------------------------------------------------------
# 2. GUI レイヤでの編集可能性（QLineEdit / QComboBox / QSpinBox）
# ----------------------------------------------------------------------
Write-Section "2. GUI editors potentially bound to reserved fields" "Yellow"

# ダイアログ系ファイルを探索
$guiFiles = $files | Where-Object {
    $_.FullName -match 'statable_gui'
}

Write-Host "  GUI files: $($guiFiles.Count)"
Write-Host ""

$editorFiles = @()
foreach ($f in $guiFiles) {
    $rel = $f.FullName.Substring((Resolve-Path $Root).Path.Length + 1)

    # ダイアログ/編集UI の兆候
    $hasDialog = Select-String -Path $f.FullName `
        -Pattern 'QDialog|QLineEdit|QComboBox|QSpinBox|QFormLayout' `
        -Quiet
    if (-not $hasDialog) { continue }

    # 予約フィールドへの言及
    $fieldHits = @()
    foreach ($field in $ReservedFields) {
        $m = Select-String -Path $f.FullName -Pattern $field.Regex `
            -ErrorAction SilentlyContinue
        if ($m) {
            $fieldHits += [PSCustomObject]@{
                Field = $field.Name
                Count = $m.Count
                Lines = ($m | ForEach-Object { $_.LineNumber }) -join ','
            }
        }
    }

    if ($fieldHits.Count -gt 0) {
        $editorFiles += [PSCustomObject]@{
            File   = $rel
            Fields = $fieldHits
        }
    }
}

if ($editorFiles.Count -eq 0) {
    Write-Host "  [OK] No GUI dialog references any reserved field." -ForegroundColor Green
} else {
    Write-Host "  [WARN] The following GUI files reference reserved fields:" -ForegroundColor Red
    foreach ($e in $editorFiles) {
        Write-Host ""
        Write-Host "  >> $($e.File)" -ForegroundColor Red
        foreach ($fh in $e.Fields) {
            Write-Host ("       {0,-12} hits={1}  lines={2}" `
                -f $fh.Field, $fh.Count, $fh.Lines) -ForegroundColor Yellow
        }
    }
}

# ----------------------------------------------------------------------
# 3. 特に重要なダイアログの個別チェック
# ----------------------------------------------------------------------
Write-Section "3. Key dialog inspection" "Yellow"

$KeyDialogs = @(
    "statable_gui\role_function_dialog.py",
    "statable_gui\libcntrl\role_function_edit_dialog.py",
    "statable_gui\action_edit_dialog.py",
    "statable_gui\widgets.py",
    "statable_gui\main_window.py"
)

foreach ($d in $KeyDialogs) {
    $path = Join-Path $Root $d
    if (-not (Test-Path $path)) {
        Write-Host "  [MISSING] $d" -ForegroundColor DarkGray
        continue
    }
    Write-Host ""
    Write-Host "  >> $d" -ForegroundColor White

    foreach ($field in $ReservedFields) {
        $m = Select-String -Path $path -Pattern $field.Regex `
            -ErrorAction SilentlyContinue
        if ($m) {
            Write-Host "     [HIT] $($field.Name):" -ForegroundColor Yellow
            foreach ($x in $m) {
                Write-Host ("           L{0,-5} {1}" `
                    -f $x.LineNumber, $x.Line.Trim()) -ForegroundColor Gray
            }
        }
    }
}

# ----------------------------------------------------------------------
# 4. codegen での実際の使用（無使用の確認）
# ----------------------------------------------------------------------
Write-Section "4. Code generation usage (should be NONE)" "Yellow"

$codegenDir = Join-Path $Root "codegen"
if (Test-Path $codegenDir) {
    $codegenFiles = Get-ChildItem -Path $codegenDir -Recurse `
        -Filter "*.py" -File | Where-Object { -not (Test-Excluded $_.FullName) }

    foreach ($field in $ReservedFields) {
        $total = 0
        $hitFiles = @()
        foreach ($f in $codegenFiles) {
            $m = Select-String -Path $f.FullName -Pattern $field.Regex `
                -ErrorAction SilentlyContinue
            if ($m) {
                $total += $m.Count
                $rel = $f.FullName.Substring((Resolve-Path $Root).Path.Length + 1)
                $hitFiles += $rel
            }
        }
        if ($total -eq 0) {
            Write-Host ("  [OK]   {0,-12} not used in codegen" `
                -f $field.Name) -ForegroundColor Green
        } else {
            Write-Host ("  [WARN] {0,-12} used {1} time(s) in: {2}" `
                -f $field.Name, $total, ($hitFiles -join ', ')) -ForegroundColor Red
        }
    }
} else {
    Write-Host "  [SKIP] codegen/ not found" -ForegroundColor DarkGray
}

# ----------------------------------------------------------------------
# 5. XML I/O での保持確認
# ----------------------------------------------------------------------
Write-Section "5. XML I/O preservation (should be ALL PRESENT)" "Yellow"

$xmlio = Join-Path $Root "statable\xml_io.py"
if (Test-Path $xmlio) {
    foreach ($field in $ReservedFields) {
        $m = Select-String -Path $xmlio -Pattern $field.Regex `
            -ErrorAction SilentlyContinue
        if ($m) {
            Write-Host ("  [OK]   {0,-12} preserved ({1} refs)" `
                -f $field.Name, $m.Count) -ForegroundColor Green
        } else {
            Write-Host ("  [WARN] {0,-12} not found in xml_io.py" `
                -f $field.Name) -ForegroundColor Red
        }
    }
} else {
    Write-Host "  [SKIP] statable/xml_io.py not found" -ForegroundColor DarkGray
}

# ----------------------------------------------------------------------
# 6. サマリ
# ----------------------------------------------------------------------
Write-Section "Summary" "Cyan"

Write-Host ""
Write-Host "  Reserved field occurrences (all dirs):" -ForegroundColor White
foreach ($k in $summary.Keys | Sort-Object) {
    Write-Host ("    {0,-12} {1,4}" -f $k, $summary[$k])
}

Write-Host ""
if ($editorFiles.Count -gt 0) {
    Write-Host "  [ACTION REQUIRED]" -ForegroundColor Red
    Write-Host "  The following GUI files still reference reserved fields:" -ForegroundColor Red
    foreach ($e in $editorFiles) {
        Write-Host "    - $($e.File)" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "  Review each file and decide whether to remove the" -ForegroundColor Yellow
    Write-Host "  UI editors for those fields (or leave them, if they" -ForegroundColor Yellow
    Write-Host "  are intentional for the shared library)." -ForegroundColor Yellow
} else {
    Write-Host "  [OK] No GUI file references reserved fields." -ForegroundColor Green
}

Write-Host ""
Write-Host "Done." -ForegroundColor Cyan