#!/usr/bin/env python3
"""
GUI round-trip 自動テスト（PySide6 offscreen）

main_window.py を実際にインスタンス化し、
open_project → save_project の一連の流れを自動実行して、
XML がどう変化するかを検証する。

【pytest での実行】
  pytest tests/test_gui_roundtrip.py -v
  pytest tests/test_gui_roundtrip.py -v -k isr_namespace

【CLI での実行】
  # 1 XML
  python tests/test_gui_roundtrip.py --xml specs/isr_namespace_test.xml

  # specs/ 配下の全 XML
  python tests/test_gui_roundtrip.py --all

環境変数:
  QT_QPA_PLATFORM=offscreen が自動設定される（ヘッドレス実行）
"""
import argparse
import os
import sys
import tempfile
import traceback
import xml.etree.ElementTree as ET
from pathlib import Path

# ★ Qt を offscreen モードで起動（GUI 表示なし）
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# ---- プロジェクトルート解決（tests/ から 1 階層上） ----
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

SPECS_DIR = PROJECT_ROOT / "specs"


# ============================================================
# XML 正規化（差分比較用）
# ============================================================

def normalize_xml(xml_text: str) -> str:
    try:
        return ET.canonicalize(xml_text, strip_text=True)
    except Exception:
        root = ET.fromstring(xml_text)
        return ET.tostring(root, encoding="unicode")


def diff_summary(a: str, b: str) -> dict:
    """2 つの XML の差分を要約"""
    result = {
        "identical": a == b,
        "diff_lines": [],
    }
    if a == b:
        return result

    import difflib
    diff = difflib.unified_diff(
        a.splitlines(), b.splitlines(),
        fromfile="original", tofile="gui_roundtrip", lineterm="")
    result["diff_lines"] = list(diff)
    return result


def analyze_shared_libs_diff(orig: str, new: str) -> dict:
    """SharedLibraries の差分を詳細分析"""
    orig_root = ET.fromstring(orig)
    new_root = ET.fromstring(new)

    def get_shared_libs(root):
        libs = root.find("SharedLibraries")
        if libs is None:
            return {"roles": set(), "conditions": set(), "literals": set()}
        roles = set()
        rf_lib = libs.find("RoleFunctionLibrary")
        if rf_lib is not None:
            for rf in rf_lib.findall("RoleFunction"):
                roles.add(rf.get("name", ""))
        conds = set()
        c_lib = libs.find("ConditionLibrary")
        if c_lib is not None:
            for c in c_lib.findall("Condition"):
                conds.add(c.get("name", ""))
        lits = set()
        l_lib = libs.find("LiteralLibrary")
        if l_lib is not None:
            for lit in l_lib.findall("Literal"):
                lits.add(lit.get("name", ""))
        return {"roles": roles, "conditions": conds, "literals": lits}

    orig_libs = get_shared_libs(orig_root)
    new_libs = get_shared_libs(new_root)

    return {
        "roles_added": sorted(new_libs["roles"] - orig_libs["roles"]),
        "roles_removed": sorted(orig_libs["roles"] - new_libs["roles"]),
        "conditions_added": sorted(new_libs["conditions"] - orig_libs["conditions"]),
        "conditions_removed": sorted(orig_libs["conditions"] - new_libs["conditions"]),
        "literals_added": sorted(new_libs["literals"] - orig_libs["literals"]),
        "literals_removed": sorted(orig_libs["literals"] - new_libs["literals"]),
    }


# ============================================================
# GUI round-trip 実行
# ============================================================

def gui_roundtrip_one(xml_path: Path, logger=None) -> dict:
    """
    1 XML を GUI 経由で round-trip する

    QFileDialog をモンキーパッチして、以下を自動実行:
      1. MainWindow インスタンス化
      2. open_project() → project_from_xml + 自動補完
      3. save_project() → project_to_xml
    """
    log = logger or (lambda msg: None)
    result = {
        "path": xml_path,
        "status": "SKIP",
        "summary": "",
        "details": [],
        "diff_summary": None,
        "libs_diff": None,
    }

    # ---- PySide6 のインポートと QApplication 準備 ----
    try:
        from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox
    except ImportError as e:
        result["status"] = "ERROR"
        result["summary"] = f"PySide6 not available: {e}"
        return result

    app = QApplication.instance()
    if app is None:
        app = QApplication([])

    # ---- MainWindow のインポート ----
    try:
        from statable_gui.main_window import MainWindow
    except Exception as e:
        result["status"] = "ERROR"
        result["summary"] = f"MainWindow import failed: {e}"
        result["details"].append(traceback.format_exc())
        return result

    # ---- 出力先一時ファイル ----
    tmp_file = None
    try:
        with tempfile.NamedTemporaryFile(
                "w", suffix=".xml", delete=False, encoding="utf-8") as f:
            tmp_file = f.name
    except Exception as e:
        result["status"] = "ERROR"
        result["summary"] = f"tempfile creation failed: {e}"
        return result

    # ---- QFileDialog / QMessageBox をモンキーパッチ ----
    orig_get_open = QFileDialog.getOpenFileName
    orig_get_save = QFileDialog.getSaveFileName
    orig_msg_info = QMessageBox.information
    orig_msg_warn = QMessageBox.warning
    orig_msg_crit = QMessageBox.critical

    def fake_get_open(*args, **kwargs):
        log(f"  [patch] getOpenFileName -> {xml_path}")
        return (str(xml_path), "XML files (*.xml)")

    def fake_get_save(*args, **kwargs):
        log(f"  [patch] getSaveFileName -> {tmp_file}")
        return (tmp_file, "XML files (*.xml)")

    def fake_messagebox(*args, **kwargs):
        # QMessageBox がブロックしないよう無効化
        try:
            log(f"  [patch] QMessageBox bypassed: {args[1] if len(args) > 1 else ''}")
        except Exception:
            pass
        return QMessageBox.Ok

    QFileDialog.getOpenFileName = staticmethod(fake_get_open)
    QFileDialog.getSaveFileName = staticmethod(fake_get_save)
    QMessageBox.information = staticmethod(fake_messagebox)
    QMessageBox.warning = staticmethod(fake_messagebox)
    QMessageBox.critical = staticmethod(fake_messagebox)

    mw = None
    try:
        # ---- MainWindow 生成 ----
        log("  Creating MainWindow...")
        mw = MainWindow()

        # ---- open_project ----
        log("  Calling open_project()...")
        mw.open_project()

        # ---- save_project ----
        log("  Calling save_project()...")
        mw.save_project()

        # ---- 比較 ----
        orig_text = xml_path.read_text(encoding="utf-8")
        new_text = Path(tmp_file).read_text(encoding="utf-8")

        norm_orig = normalize_xml(orig_text)
        norm_new = normalize_xml(new_text)

        result["diff_summary"] = diff_summary(norm_orig, norm_new)
        result["libs_diff"] = analyze_shared_libs_diff(norm_orig, norm_new)

        if norm_orig == norm_new:
            result["status"] = "IDENTICAL"
            result["summary"] = "GUI 経由でも完全一致"
        else:
            ld = result["libs_diff"]
            only_shared_libs = (
                not ld["roles_removed"]
                and not ld["conditions_removed"]
                and not ld["literals_removed"]
            )
            if only_shared_libs and (
                    ld["roles_added"] or ld["conditions_added"]
                    or ld["literals_added"]):
                result["status"] = "AUTO_COMPLETED"
                result["summary"] = (
                    f"GUI 経由で自動補完: "
                    f"roles+{len(ld['roles_added'])}, "
                    f"conditions+{len(ld['conditions_added'])}, "
                    f"literals+{len(ld['literals_added'])}"
                )
            else:
                result["status"] = "DIFF_DETECTED"
                result["summary"] = "自動補完以外の差分あり → 要調査"
                result["details"].append("diff (first 30 lines):")
                result["details"].extend(
                    result["diff_summary"]["diff_lines"][:30])

    except Exception as e:
        result["status"] = "ERROR"
        result["summary"] = f"exception: {e}"
        result["details"].append(traceback.format_exc())
    finally:
        # ---- モンキーパッチを復元 ----
        QFileDialog.getOpenFileName = orig_get_open
        QFileDialog.getSaveFileName = orig_get_save
        QMessageBox.information = orig_msg_info
        QMessageBox.warning = orig_msg_warn
        QMessageBox.critical = orig_msg_crit

        # ---- MainWindow を閉じる ----
        if mw is not None:
            try:
                mw.close()
                mw.deleteLater()
            except Exception:
                pass

        # ---- 一時ファイル削除 ----
        if tmp_file:
            try:
                Path(tmp_file).unlink(missing_ok=True)
            except Exception:
                pass

        # ---- イベントループを 1 回まわしてクリーンアップ ----
        try:
            app.processEvents()
        except Exception:
            pass

    return result


# ============================================================
# pytest 用テスト関数
# ============================================================

def _spec_xmls():
    """specs/ 配下の全 XML"""
    return sorted(SPECS_DIR.glob("*.xml"))


# 動的にテスト関数を生成（pytest の parametrize 相当）
#   pytest は tests/ 配下の test_*.py の test_* 関数を自動検出する
def _make_test(xml_path: Path):
    """1 XML 用の pytest テスト関数を生成"""
    def _test():
        result = gui_roundtrip_one(xml_path)
        # IDENTICAL / AUTO_COMPLETED を許容
        assert result["status"] in ("IDENTICAL", "AUTO_COMPLETED"), (
            f"{xml_path.name}: {result['status']} - {result['summary']}\n"
            + "\n".join(result["details"])
        )
    _test.__name__ = f"test_gui_roundtrip_{xml_path.stem}"
    _test.__doc__ = f"GUI round-trip: {xml_path.name}"
    return _test


# pytest 用: specs/ の XML が存在する場合のみテスト関数を登録
if _spec_xmls():
    import sys as _sys
    _this = _sys.modules[__name__]
    for _xml in _spec_xmls():
        _fn = _make_test(_xml)
        setattr(_this, _fn.__name__, _fn)


# ============================================================
# レポート出力（CLI 用）
# ============================================================

def format_report(results: list, xmls_tested: list) -> str:
    lines = ["# GUI round-trip 自動テストレポート", ""]
    lines.append(f"- 対象 XML: {len(xmls_tested)} 件")
    lines.append("")
    lines.append("## サマリ")
    lines.append("")
    lines.append("| XML | Status | 詳細 |")
    lines.append("|---|---|---|")
    for r in results:
        name = r["path"].name
        status = r["status"]
        lines.append(f"| {name} | {status} | {r['summary']} |")
    lines.append("")

    for r in results:
        lines.append(f"## {r['path'].name}")
        lines.append(f"- Status: **{r['status']}**")
        lines.append(f"- Summary: {r['summary']}")

        if r["libs_diff"]:
            ld = r["libs_diff"]
            lines.append("")
            lines.append("### SharedLibraries 差分")
            if ld["roles_added"]:
                lines.append(f"- **RoleFunctions +{len(ld['roles_added'])}**: "
                             f"{', '.join(ld['roles_added'][:5])}"
                             f"{' ...' if len(ld['roles_added']) > 5 else ''}")
            if ld["roles_removed"]:
                lines.append(f"- **RoleFunctions -{len(ld['roles_removed'])}**: "
                             f"{', '.join(ld['roles_removed'][:5])}")
            if ld["conditions_added"]:
                lines.append(f"- **Conditions +{len(ld['conditions_added'])}**: "
                             f"{', '.join(ld['conditions_added'][:5])}"
                             f"{' ...' if len(ld['conditions_added']) > 5 else ''}")
            if ld["conditions_removed"]:
                lines.append(f"- **Conditions -{len(ld['conditions_removed'])}**: "
                             f"{', '.join(ld['conditions_removed'][:5])}")
            if ld["literals_added"]:
                lines.append(f"- **Literals +{len(ld['literals_added'])}**: "
                             f"{', '.join(ld['literals_added'][:5])}")

        if r["details"]:
            lines.append("")
            lines.append("### 詳細")
            lines.append("```")
            lines.extend(r["details"])
            lines.append("```")
        lines.append("")

    lines.append("## 集計")
    lines.append("")
    statuses = {}
    for r in results:
        statuses[r["status"]] = statuses.get(r["status"], 0) + 1
    for status, count in sorted(statuses.items()):
        lines.append(f"- {status}: {count}")

    return "\n".join(lines)


# ============================================================
# CLI メイン
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="GUI round-trip 自動テスト（PySide6 offscreen）",
    )
    parser.add_argument("--xml", action="append", default=None,
                        help="テスト対象 XML（複数指定可）")
    parser.add_argument("--all", action="store_true",
                        help="specs/ 配下の全 XML をテスト")
    parser.add_argument("--report", default="gui_roundtrip_report.md",
                        help="レポート出力先")
    args = parser.parse_args()

    if args.all:
        xmls = sorted(SPECS_DIR.glob("*.xml"))
    elif args.xml:
        xmls = [Path(p).resolve() for p in args.xml]
    else:
        xmls = [SPECS_DIR / "isr_namespace_test.xml"]

    if not xmls:
        print("テスト対象が見つかりません")
        return 1

    print(f"=== GUI round-trip テスト: {len(xmls)} 件 ===")
    print(f"Qt platform: {os.environ.get('QT_QPA_PLATFORM')}")
    print()

    def _log(msg):
        print(msg)

    results = []
    for xml in xmls:
        print(f"--- {xml.name} ---")
        r = gui_roundtrip_one(xml, logger=_log)
        results.append(r)
        print(f"  → {r['status']}: {r['summary']}")
        print()

    report = format_report(results, xmls)
    Path(args.report).write_text(report, encoding="utf-8")
    print(f"レポート出力: {args.report}")

    n_err = sum(1 for r in results if r["status"] == "ERROR")
    n_diff = sum(1 for r in results if r["status"] == "DIFF_DETECTED")
    if n_err or n_diff:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())