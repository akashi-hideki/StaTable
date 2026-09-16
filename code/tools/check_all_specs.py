#!/usr/bin/env python3
"""
specs/ 配下の全 XML で round-trip 一貫性チェックを実行

使い方:
  python tools/check_all_specs.py
"""
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SPECS_DIR    = PROJECT_ROOT / "specs"
TOOL         = PROJECT_ROOT / "tools" / "consistency_check.py"

xmls = sorted(SPECS_DIR.glob("*.xml"))
print(f"=== 対象 XML: {len(xmls)} 件 ===")

summary = []
for xml in xmls:
    rel    = f"specs/{xml.name}"
    report = f"report_{xml.stem}.md"
    print(f"\n--- {rel} ---")

    py_args = [
        sys.executable, str(TOOL),
        "--xml", rel,
        "--skip-fields",
        "--skip-enums",
        "--skip-generated-c",
        "--report", report,
        "--quiet",
    ]
    result = subprocess.run(py_args, cwd=PROJECT_ROOT, capture_output=True, text=True)

    # 標準エラー（round-trip ログ）を表示
    if result.stderr:
        for line in result.stderr.strip().splitlines():
            print(f"  {line}")

    # レポートから round-trip 結果を抽出
    report_path = PROJECT_ROOT / report
    if report_path.exists():
        content = report_path.read_text(encoding="utf-8")
        for line in content.splitlines():
            if line.startswith("## 1. XML round-trip:"):
                status = line.split(":")[-1].strip()
                summary.append((xml.name, status))
                mark = "✅" if status == "PASS" else "❌"
                print(f"  round-trip: {mark} {status}")
                break
    else:
        summary.append((xml.name, "NO_REPORT"))
        print(f"  ❌ レポート未生成")

print("\n=== サマリ ===")
print(f"{'XML':40s} {'Status':10s}")
print("-" * 52)
for name, status in summary:
    print(f"{name:40s} {status:10s}")

pass_count = sum(1 for _, s in summary if s == "PASS")
total = len(summary)
print(f"\nPASS: {pass_count} / {total}")

sys.exit(0 if pass_count == total else 1)