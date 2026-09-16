#!/usr/bin/env python3
"""
specs/ 配下の XML を新形式に一括変換

動作:
  1. 各 XML を project_from_xml で読込
  2. project_to_xml で新形式として保存
  3. 元ファイルは .bak として退避

使い方:
  # ドライラン（変更内容を確認のみ、ファイル書き換えなし）
  python tools/upgrade_specs.py --dry-run

  # 本実行（バックアップ作成 + 書き換え）
  python tools/upgrade_specs.py

  # 特定ファイルのみ
  python tools/upgrade_specs.py --xml specs/multi_layer_test.xml
"""
import argparse
import shutil
import sys
import traceback
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

SPECS_DIR = PROJECT_ROOT / "specs"


def upgrade_one(xml_path: Path, dry_run: bool = False) -> dict:
    """1 ファイルを新形式に変換"""
    result = {
        "path": xml_path,
        "status": "SKIP",
        "summary": "",
        "bytes_before": xml_path.stat().st_size,
        "bytes_after": 0,
    }

    try:
        from statable.xml_io import project_from_xml, project_to_xml

        # 読込
        loaded = project_from_xml(str(xml_path))
        tabs, global_defs = loaded[0], loaded[1]
        role_lib = loaded[2] if len(loaded) > 2 else None
        cond_lib = loaded[3] if len(loaded) > 3 else None
        lit_lib  = loaded[4] if len(loaded) > 4 else None
        settings = loaded[5] if len(loaded) > 5 else None

        if dry_run:
            # ドライラン: 一時ファイルに書き出して差分サイズのみ確認
            import tempfile
            with tempfile.NamedTemporaryFile(
                    "w", suffix=".xml", delete=False, encoding="utf-8") as f:
                tmp = f.name
            project_to_xml(
                tabs, global_defs, tmp,
                role_function_library=role_lib,
                condition_library=cond_lib,
                literal_library=lit_lib,
                project_settings=settings,
            )
            result["bytes_after"] = Path(tmp).stat().st_size
            Path(tmp).unlink(missing_ok=True)
            result["status"] = "DRY_RUN"
            result["summary"] = "変更内容を確認（ファイル未変更）"
        else:
            # 本実行: バックアップ → 上書き保存
            backup = xml_path.with_suffix(xml_path.suffix + ".bak")
            shutil.copy2(xml_path, backup)

            project_to_xml(
                tabs, global_defs, str(xml_path),
                role_function_library=role_lib,
                condition_library=cond_lib,
                literal_library=lit_lib,
                project_settings=settings,
            )
            result["bytes_after"] = xml_path.stat().st_size
            result["status"] = "UPGRADED"
            result["summary"] = f"バックアップ: {backup.name}"

    except Exception as e:
        result["status"] = "ERROR"
        result["summary"] = f"{e}"
        result["traceback"] = traceback.format_exc()

    return result


def main():
    parser = argparse.ArgumentParser(
        description="specs/ 配下の XML を新形式に変換",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--xml", action="append", default=None,
                        help="個別ファイル指定（複数可）。未指定なら specs/*.xml すべて")
    parser.add_argument("--dry-run", action="store_true",
                        help="ファイルを書き換えず、サイズ差分のみ確認")
    args = parser.parse_args()

    if args.xml:
        xmls = [Path(p).resolve() for p in args.xml]
    else:
        xmls = sorted(SPECS_DIR.glob("*.xml"))

    if not xmls:
        print("対象 XML が見つかりません")
        return 1

    print(f"=== 対象 XML: {len(xmls)} 件 ===")
    if args.dry_run:
        print("【ドライラン: ファイルは書き換えません】")
    print()

    results = []
    for xml in xmls:
        print(f"--- {xml.name} ---")
        r = upgrade_one(xml, dry_run=args.dry_run)
        results.append(r)

        before = r["bytes_before"]
        after  = r["bytes_after"]
        diff = after - before if after else 0
        diff_str = f"(+{diff})" if diff >= 0 else f"({diff})"

        if r["status"] == "UPGRADED":
            print(f"  ✅ UPGRADED  {before} → {after} bytes  {diff_str}")
            print(f"     {r['summary']}")
        elif r["status"] == "DRY_RUN":
            print(f"  📋 DRY_RUN   {before} → {after} bytes  {diff_str}")
        elif r["status"] == "ERROR":
            print(f"  ❌ ERROR     {r['summary']}")
            if "traceback" in r:
                for line in r["traceback"].splitlines():
                    print(f"     {line}")
        print()

    # サマリ
    print("=== サマリ ===")
    for r in results:
        name = r["path"].name
        status = r["status"]
        if r["bytes_after"]:
            diff = r["bytes_after"] - r["bytes_before"]
            print(f"  {name:40s} {status:10s} ({diff:+d} bytes)")
        else:
            print(f"  {name:40s} {status:10s}")

    n_upgraded = sum(1 for r in results if r["status"] == "UPGRADED")
    n_dry = sum(1 for r in results if r["status"] == "DRY_RUN")
    n_err = sum(1 for r in results if r["status"] == "ERROR")

    print()
    if args.dry_run:
        print(f"ドライラン完了: {n_dry} 件")
    else:
        print(f"変換完了: {n_upgraded} 件 / エラー {n_err} 件")

    return 0 if n_err == 0 else 1


if __name__ == "__main__":
    sys.exit(main())