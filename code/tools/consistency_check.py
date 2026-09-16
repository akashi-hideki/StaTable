#!/usr/bin/env python3
"""
StaTable 一貫性チェックツール (consistency_check.py) - CUI 完全版

検査内容:
  1. XML round-trip:
     - project_from_xml / project_to_xml 方式（StaTable 本実装）
     - load / save 方式（汎用フォールバック）
  2. データクラスフィールド突き合わせ: モデル定義 vs 各層の出現箇所
     - RESERVED フィールドは「予約」として明示（FAIL 扱いしない）
  3. Enum 使用箇所: model.py の Enum メンバーが他ファイルで使われているか
     - RESERVED Enum メンバーは「予約」として明示
  4. 生成 C コード整合性:
     - include guard の有無
     - statable_types_{layer}.h が common.h を include しているか
     - role_functions: 全層横断でプロトタイプの定義が存在するか
     - role_functions: 所有層（namespace prefix）の .c に定義があるか

使い方:
  # 全検査（デフォルト引数で動作）
  python tools/consistency_check.py

  # round-trip のみ
  python tools/consistency_check.py --skip-fields --skip-enums --skip-generated-c

  # 生成 C コード検査をスキップ
  python tools/consistency_check.py --skip-generated-c

終了コード:
  0 = 全 PASS（SKIP / RESERVED 含む）
  1 = 1 つ以上 FAIL / ERROR

変更履歴:
  v1.9.x: project_from_xml/project_to_xml 対応、RESERVED フィールド導入
  v1.9.y: 生成 C 検査を全層横断方式に修正（v1.6 案 A 対応）
"""

import argparse
import ast
import difflib
import importlib
import re
import sys
import tempfile
import traceback
import xml.etree.ElementTree as ET
from pathlib import Path


# ============================================================
# 予約フィールド / 予約 Enum メンバー定義（v2.0 §9.9 由来）
# ============================================================

# (クラス名, フィールド名)
RESERVED_FIELDS = {
    ("Transition", "transition_type"),   # v2.0 §9.9 #93: internal/local 未実装
    ("Transition", "action"),            # 旧互換用
}

# (Enum名, メンバー名)
RESERVED_ENUM_MEMBERS = {
    # StateType: UML 拡張状態（将来実装予定）
    ("StateType", "CONCURRENT"),
    ("StateType", "REGION"),
    ("StateType", "CHOICE"),
    ("StateType", "JUNCTION"),
    # EventKind: SIGNAL 以外のイベント種別（将来実装予定）
    ("EventKind", "CALL"),
    ("EventKind", "TIME"),
    ("EventKind", "CHANGE"),
}


# ============================================================
# ユーティリティ
# ============================================================

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def read_text(path):
    return Path(path).read_text(encoding="utf-8")


def iter_py_files(dirs):
    for d in dirs:
        p = Path(d)
        if p.is_file() and p.suffix == ".py":
            yield p
        elif p.is_dir():
            yield from p.rglob("*.py")


def normalize_xml(xml_text):
    """XML を正規化して比較しやすくする。canonicalize 優先、失敗時は tostring。"""
    try:
        return ET.canonicalize(xml_text, strip_text=True)
    except Exception:
        root = ET.fromstring(xml_text)
        return ET.tostring(root, encoding="unicode")


def diff_text(a, b, name_a="expected", name_b="actual"):
    lines_a = a.splitlines()
    lines_b = b.splitlines()
    diff = difflib.unified_diff(
        lines_a, lines_b, fromfile=name_a, tofile=name_b, lineterm=""
    )
    return "\n".join(diff)


def find_func(module, names):
    for n in names:
        if hasattr(module, n):
            return getattr(module, n)
    return None


# ============================================================
# 1. XML round-trip
# ============================================================

LOAD_NAMES = ["load", "load_from_file", "load_state_machine", "read_xml", "read"]
SAVE_NAMES = ["save", "save_to_file", "save_state_machine", "write_xml", "write"]


def _roundtrip_project(xml_path, project_from_xml, project_to_xml, logger=None):
    """project_from_xml / project_to_xml 方式の round-trip"""
    log = logger or (lambda msg: None)
    details = []
    tmp = None
    try:
        log(f"project_from_xml({xml_path.name}) ...")
        loaded = project_from_xml(str(xml_path))

        if not isinstance(loaded, tuple) or len(loaded) < 2:
            return ("ERROR",
                    f"project_from_xml の戻り値が想定外: {type(loaded)}",
                    details)

        tabs        = loaded[0]
        global_defs = loaded[1]
        role_lib    = loaded[2] if len(loaded) > 2 else None
        cond_lib    = loaded[3] if len(loaded) > 3 else None
        lit_lib     = loaded[4] if len(loaded) > 4 else None
        settings    = loaded[5] if len(loaded) > 5 else None

        with tempfile.NamedTemporaryFile(
                "w", suffix=".xml", delete=False, encoding="utf-8") as f:
            tmp = f.name

        log(f"project_to_xml(..., {Path(tmp).name}) ...")
        project_to_xml(
            tabs,
            global_defs,
            tmp,
            role_function_library=role_lib,
            condition_library=cond_lib,
            literal_library=lit_lib,
            project_settings=settings,
        )

        orig = normalize_xml(xml_path.read_text(encoding="utf-8"))
        new = normalize_xml(Path(tmp).read_text(encoding="utf-8"))
        if orig == new:
            return ("PASS", "正規化後、完全一致", details)
        else:
            details.append("round-trip 差分:")
            details.append(diff_text(orig, new, "original", "roundtrip"))
            return ("FAIL", "round-trip 差分あり", details)

    except Exception as e:
        details.append(traceback.format_exc())
        return ("ERROR", f"exception: {e}", details)
    finally:
        if tmp:
            Path(tmp).unlink(missing_ok=True)


def _roundtrip_sm(xml_path, load, save, logger=None):
    """汎用 load/save 方式（単一 StateMachine）"""
    log = logger or (lambda msg: None)
    details = []
    tmp = None
    try:
        log(f"load({xml_path.name}) ...")
        obj = load(str(xml_path))
        with tempfile.NamedTemporaryFile(
                "w", suffix=".xml", delete=False, encoding="utf-8") as f:
            tmp = f.name
        try:
            save(obj, tmp)
        except TypeError:
            save(tmp, obj)
        orig = normalize_xml(xml_path.read_text(encoding="utf-8"))
        new = normalize_xml(Path(tmp).read_text(encoding="utf-8"))
        if orig == new:
            return ("PASS", "正規化後、完全一致", details)
        else:
            details.append("round-trip 差分:")
            details.append(diff_text(orig, new, "original", "roundtrip"))
            return ("FAIL", "round-trip 差分あり", details)
    except Exception as e:
        details.append(traceback.format_exc())
        return ("ERROR", f"exception: {e}", details)
    finally:
        if tmp:
            Path(tmp).unlink(missing_ok=True)


def roundtrip_xml(root, xml_path, xml_io_path, logger=None):
    """round-trip 検査本体。API を自動判定して呼び分ける。"""
    result = {"check": "roundtrip_xml", "status": "SKIP", "summary": "", "details": []}
    xml_path = Path(xml_path)
    if not xml_path.exists():
        result["status"] = "FAIL"
        result["summary"] = f"XML file not found: {xml_path}"
        result["details"].append(str(xml_path))
        return result

    try:
        sys.path.insert(0, str(Path(root).resolve()))
        rel = Path(xml_io_path).resolve().relative_to(Path(root).resolve())
        mod_name = ".".join(rel.with_suffix("").parts)
        mod = importlib.import_module(mod_name)
    except Exception as e:
        result["status"] = "ERROR"
        result["summary"] = f"Failed to import {xml_io_path}: {e}"
        result["details"].append(traceback.format_exc())
        return result

    # API 判定: project_from_xml / project_to_xml を優先
    pf = getattr(mod, "project_from_xml", None)
    pt = getattr(mod, "project_to_xml", None)
    if callable(pf) and callable(pt):
        status, summary, details = _roundtrip_project(xml_path, pf, pt, logger)
        result["status"] = status
        result["summary"] = summary
        result["details"].extend(details)
        return result

    # フォールバック: 汎用 load/save
    load = find_func(mod, LOAD_NAMES)
    save = find_func(mod, SAVE_NAMES)
    if callable(load) and callable(save):
        status, summary, details = _roundtrip_sm(xml_path, load, save, logger)
        result["status"] = status
        result["summary"] = summary
        result["details"].extend(details)
        return result

    result["status"] = "ERROR"
    result["summary"] = (
        "対応する API が見つかりません。"
        "project_from_xml/project_to_xml または load/save が必要"
    )
    return result


# ============================================================
# 2. フィールド突き合わせ
# ============================================================

def get_dataclass_fields(model_path, class_names):
    tree = ast.parse(read_text(model_path))
    fields = {}
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name in class_names:
            fs = []
            for stmt in node.body:
                if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                    fs.append(stmt.target.id)
            fields[node.name] = fs
    return fields


def scan_fields(root, fields, scan_dirs):
    """各フィールドがどのファイルに出現するかをカウント。"""
    matrix = {cls: {f: {} for f in fs} for cls, fs in fields.items()}
    for p in iter_py_files(scan_dirs):
        try:
            text = read_text(p)
        except Exception:
            continue
        try:
            rel = str(p.relative_to(root))
        except ValueError:
            rel = str(p)
        for cls, fs in fields.items():
            for f in fs:
                patterns = [
                    rf"\.{f}\b",          # .field
                    rf"\b{f}\s*=",        # field=
                    rf"['\"]{f}['\"]",    # 'field' / "field"
                    rf"\b{f}\s*:",        # field:
                ]
                count = sum(len(re.findall(pat, text)) for pat in patterns)
                if count:
                    matrix[cls][f][rel] = count
    return matrix


# ============================================================
# 3. Enum 使用箇所
# ============================================================

def get_enums(model_path):
    tree = ast.parse(read_text(model_path))
    enums = {}
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            bases = [b.id for b in node.bases if isinstance(b, ast.Name)]
            if "Enum" in bases or "IntEnum" in bases:
                members = []
                for stmt in node.body:
                    if isinstance(stmt, ast.Assign):
                        for t in stmt.targets:
                            if isinstance(t, ast.Name):
                                members.append(t.id)
                    elif (isinstance(stmt, ast.AnnAssign)
                          and isinstance(stmt.target, ast.Name)):
                        members.append(stmt.target.id)
                enums[node.name] = members
    return enums


def scan_enums(root, enums, scan_dirs):
    usage = {e: {m: [] for m in ms} for e, ms in enums.items()}
    for p in iter_py_files(scan_dirs):
        try:
            text = read_text(p)
        except Exception:
            continue
        try:
            rel = str(p.relative_to(root))
        except ValueError:
            rel = str(p)
        for e, members in enums.items():
            for m in members:
                if re.search(rf"\b{e}\.{m}\b", text):
                    usage[e][m].append(rel)
    return usage


# ============================================================
# 4. 生成 C コード整合性
# ============================================================

def check_generated_c(root, output_dir):
    """
    生成 C コードの整合性チェック

    v1.6 案 A の設計を前提:
      - 各層 statable_role_functions_{layer}.h は
        「その層から呼べる全関数」のプロトタイプを持つ（自層 + 他層）
      - 各層 statable_role_functions_{layer}.c は
        「その層が所有する関数」の定義のみを持つ
      - よって .h と .c は完全一致しない（他層参照分があるため）

    検査方法:
      4.1  include guard の有無
      4.2  statable_types_{layer}.h が common.h を include しているか
      4.3a 全層横断で「プロトタイプはあるが定義がない関数」を検出
      4.3b 所有層（namespace prefix）の .c に定義があるかを確認
    """
    out = Path(output_dir)
    if not out.exists():
        return {"status": "SKIP",
                "summary": f"output dir not found: {out}",
                "details": []}

    details = []

    # 4.1 include guard
    for h in out.rglob("*.h"):
        text = h.read_text(encoding="utf-8", errors="ignore")
        if "#ifndef" not in text or "#define" not in text:
            details.append(f"{h.relative_to(root)}: include guard なし")

    # 4.2 statable_types_*.h は common.h を include しているか
    for h in out.rglob("statable_types_*.h"):
        if h.name == "statable_types_common.h":
            continue
        text = h.read_text(encoding="utf-8", errors="ignore")
        if "statable_types_common.h" not in text:
            details.append(f"{h.relative_to(root)}: common.h 未 include")

    # 4.3 role_functions の宣言と定義の対応（全層横断）
    all_protos = set()
    all_defs = set()
    layer_sources = {}   # layer_name -> Path

    for layer_dir in out.iterdir():
        if not layer_dir.is_dir():
            continue
        header = layer_dir / f"statable_role_functions_{layer_dir.name}.h"
        source = layer_dir / f"statable_role_functions_{layer_dir.name}.c"
        if header.exists():
            h_text = header.read_text(encoding="utf-8", errors="ignore")
            protos = set(re.findall(r"\b(RoleFunc_\w+)\s*\(", h_text))
            all_protos |= protos
        if source.exists():
            c_text = source.read_text(encoding="utf-8", errors="ignore")
            defs = set(re.findall(r"\b(RoleFunc_\w+)\s*\(", c_text))
            all_defs |= defs
            layer_sources[layer_dir.name] = source

    # 4.3a: 全層横断で定義が見つからないプロトタイプ
    missing_anywhere = all_protos - all_defs
    if missing_anywhere:
        details.append(
            f"全層横断で定義が見つからないプロトタイプ: "
            f"{sorted(missing_anywhere)}"
        )

    # 4.3b: 所有層（プレフィックス）の .c に定義があるか
    for fname in sorted(all_protos):
        owner = None
        if fname.startswith("RoleFunc_Middleware_"):
            owner = "Middleware"
        else:
            m = re.match(r"RoleFunc_(\w+?)_", fname)
            if m:
                owner = m.group(1)
        if owner and owner in layer_sources:
            c_text = layer_sources[owner].read_text(
                encoding="utf-8", errors="ignore")
            if not re.search(rf"\b{fname}\s*\(", c_text):
                details.append(
                    f"{owner}: {fname} は他層でプロトタイプされるが、"
                    f"所有層 {owner} の .c に定義なし"
                )

    return {"status": "PASS" if not details else "FAIL",
            "summary": f"検出 {len(details)} 件",
            "details": details}


# ============================================================
# メイン
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="StaTable consistency check (CUI)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--root", default=".")
    parser.add_argument("--xml", default="specs/isr_namespace_test.xml")
    parser.add_argument("--xml-io", default="statable/xml_io.py")
    parser.add_argument("--model", default="statable/model.py")
    parser.add_argument("--scan-dirs", nargs="+",
                        default=["statable", "statable_gui", "codegen"])
    parser.add_argument("--output-dir", default="output")
    parser.add_argument("--report", default="consistency_report.md")
    parser.add_argument("--skip-roundtrip", action="store_true")
    parser.add_argument("--skip-fields", action="store_true")
    parser.add_argument("--skip-enums", action="store_true")
    parser.add_argument("--skip-generated-c", action="store_true")
    parser.add_argument("--quiet", action="store_true",
                        help="レポートを標準出力に出さない")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    report_lines = ["# StaTable 一貫性チェックレポート", ""]
    fail_count = 0
    error_count = 0

    # ---- 1. round-trip ----
    if not args.skip_roundtrip:
        def _log(msg):
            eprint(f"[round-trip] {msg}")
        r = roundtrip_xml(root, root / args.xml, root / args.xml_io, logger=_log)
        report_lines.append(f"## 1. XML round-trip: {r['status']}")
        if r["summary"]:
            report_lines.append(f"- {r['summary']}")
        for d in r["details"]:
            report_lines.append("- " + d.replace("\n", "\n  "))
        report_lines.append("")
        if r["status"] == "FAIL":
            fail_count += 1
        elif r["status"] == "ERROR":
            error_count += 1

    # ---- 2. fields ----
    if not args.skip_fields:
        try:
            fields = get_dataclass_fields(
                root / args.model, ["Transition", "RoleFunction"])
            matrix = scan_fields(
                root, fields, [root / d for d in args.scan_dirs])
            report_lines.append("## 2. フィールド出現マトリクス")
            report_lines.append("")
            report_lines.append(
                "status: OK=参照あり / RESERVED=予約フィールド / MISSING=要確認")
            report_lines.append("")
            for cls, fs in fields.items():
                report_lines.append(f"### {cls}")
                report_lines.append("| field | files | status |")
                report_lines.append("|---|---|---|")
                for f in fs:
                    files = matrix[cls][f]
                    file_list = ", ".join(
                        f"{k}({v})" for k, v in files.items()) or "(none)"
                    if (cls, f) in RESERVED_FIELDS:
                        status = "RESERVED"
                    elif not files:
                        status = "MISSING"
                    else:
                        status = "OK"
                    report_lines.append(f"| {f} | {file_list} | {status} |")
                report_lines.append("")
        except Exception as e:
            report_lines.append(f"## 2. フィールドマトリクス: ERROR")
            report_lines.append(f"- {e}")
            report_lines.append("")
            error_count += 1

    # ---- 3. enums ----
    if not args.skip_enums:
        try:
            enums = get_enums(root / args.model)
            usage = scan_enums(
                root, enums, [root / d for d in args.scan_dirs])
            report_lines.append("## 3. Enum 使用箇所")
            report_lines.append("")
            report_lines.append(
                "status: OK=参照あり / RESERVED=予約メンバー / MISSING=要確認")
            report_lines.append("")
            for e, members in enums.items():
                report_lines.append(f"### {e}")
                report_lines.append("| member | referenced in | status |")
                report_lines.append("|---|---|---|")
                for m in members:
                    refs = usage[e][m]
                    ref_str = ", ".join(refs) if refs else "(none)"
                    if (e, m) in RESERVED_ENUM_MEMBERS:
                        status = "RESERVED"
                    elif not refs:
                        status = "MISSING"
                    else:
                        status = "OK"
                    report_lines.append(f"| {m} | {ref_str} | {status} |")
                report_lines.append("")
        except Exception as e:
            report_lines.append(f"## 3. Enum 使用箇所: ERROR")
            report_lines.append(f"- {e}")
            report_lines.append("")
            error_count += 1

    # ---- 4. generated C ----
    if not args.skip_generated_c:
        r = check_generated_c(root, root / args.output_dir)
        report_lines.append(f"## 4. 生成 C コード整合性: {r['status']}")
        if r["summary"]:
            report_lines.append(f"- {r['summary']}")
        for d in r["details"]:
            report_lines.append(f"- {d}")
        report_lines.append("")
        if r["status"] == "FAIL":
            fail_count += 1

    # ---- 出力 ----
    report = "\n".join(report_lines)
    Path(args.report).write_text(report, encoding="utf-8")

    if not args.quiet:
        print(report)

    print(f"\nレポート出力: {args.report}")
    print(f"結果: FAIL={fail_count}, ERROR={error_count}")

    return 0 if (fail_count == 0 and error_count == 0) else 1


if __name__ == "__main__":
    sys.exit(main())