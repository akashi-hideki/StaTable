#!/usr/bin/env python3
"""
verify_translation.py — 翻訳適用後の検証ツール（自己完結・依存なし）

【目的】
  apply_translations.py 実行後、ソースをアップロードせずに
  ローカルで以下の検証を一括実行し、問題点のみを報告する。

【検証項目】
  1. Python 構文チェック（AST parse）— 置換で壊れていないか
  2. 日本語残存チェック（COMMENT/STRING トークン単位・カテゴリ別）
  3. 重要プレースホルダ保持チェック（s1214 / s1216）
  4. STABLE_USER_CODE / [[...]] マーカー保護チェック
  5. エスケープ保持チェック（\\n 二文字 vs 実改行）
  6. 最新 _backup_* との差分サマリ

【使い方】
  # 全検証（既定）
  python tools/verify_translation.py

  # H カテゴリの日本語残存を許容（意図的に日本語のまま残す場合）
  python tools/verify_translation.py --allow-ja H

  # レポートを JSON でも出力
  python tools/verify_translation.py --json verify_report.json

  # 構文チェックだけ
  python tools/verify_translation.py --only syntax

【終了コード】
  0 = 問題なし
  1 = 問題あり（詳細は stdout を参照）
"""
import argparse
import ast
import io
import json
import re
import sys
import tokenize
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DIRS = ["statable", "statable_gui", "codegen"]

# 日本語（ひらがな / カタカナ / 漢字 / 全角）
JP_RE = re.compile(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF\uFF00-\uFFEF]')

CATEGORY_RULES = [
    ("A", [r"codegen[/\\](?!validate[/\\]).*_generator\.py$",
           r"codegen[/\\]code_templates\.py$"]),
    ("B", [r"statable_gui[/\\].*\.py$"]),
    ("C", [r"codegen[/\\].*\.py$"]),
    ("F", [r"statable[/\\]sample_data\.py$",
           r"codegen[/\\]sample_data\.py$"]),
    ("H", [r"statable[/\\].*\.py$"]),
]

# s1216 の必須プレースホルダ
PROMPT_PLACEHOLDERS = [
    "codegen/validate/data/prompt_templates.py",
    ["{example}", "{data}", "{action_definitions}", "{validation_points}"],
]

# STABLE_USER_CODE 系マーカー
MARKER_PATTERNS = [
    "STABLE_USER_CODE_START",
    "STABLE_USER_CODE_END",
    "STABLE_USER_CODE_TAIL_START",
    "STABLE_USER_CODE_TAIL_END",
]


def detect_category(rel: str) -> str:
    norm = rel.replace("\\", "/")
    for cat, pats in CATEGORY_RULES:
        for p in pats:
            if re.search(p, norm):
                return cat
    return "?"


def iter_py_files(dirs):
    for d in dirs:
        p = PROJECT_ROOT / d
        if not p.exists():
            continue
        for f in p.rglob("*.py"):
            yield f


# ============================================================
# Check 1: 構文チェック
# ============================================================

def check_syntax(files):
    errors = []
    ok = 0
    for f in files:
        try:
            src = f.read_text(encoding="utf-8")
        except Exception as e:
            errors.append((str(f.relative_to(PROJECT_ROOT)), f"read: {e}"))
            continue
        try:
            ast.parse(src)
            ok += 1
        except SyntaxError as e:
            errors.append((
                str(f.relative_to(PROJECT_ROOT)),
                f"SyntaxError L{e.lineno}: {e.msg}",
            ))
        except Exception as e:
            errors.append((str(f.relative_to(PROJECT_ROOT)), f"parse: {e}"))
    return ok, errors


# ============================================================
# Check 2: 日本語残存チェック
# ============================================================

def check_residual_japanese(files, allow_cats):
    by_cat = defaultdict(lambda: {"lines": 0, "files": set(), "details": []})
    for f in files:
        rel = str(f.relative_to(PROJECT_ROOT)).replace("\\", "/")
        cat = detect_category(rel)
        if cat in allow_cats:
            continue
        try:
            src = f.read_text(encoding="utf-8")
            tokens = list(tokenize.generate_tokens(io.StringIO(src).readline))
        except Exception:
            continue
        for tok in tokens:
            if tok.type not in (tokenize.COMMENT, tokenize.STRING):
                continue
            if not JP_RE.search(tok.string):
                continue
            by_cat[cat]["lines"] += 1
            by_cat[cat]["files"].add(rel)
            if len(by_cat[cat]["details"]) < 15:
                snippet = tok.string.replace("\n", "\\n")[:90]
                by_cat[cat]["details"].append(
                    (rel, tok.start[0], tok.type == tokenize.COMMENT, snippet)
                )
    return by_cat


# ============================================================
# Check 3: プレースホルダ保持チェック
# ============================================================

def check_placeholders():
    path, required = PROMPT_PLACEHOLDERS
    target = PROJECT_ROOT / path
    result = {"path": path, "ok": [], "missing": []}
    if not target.exists():
        result["missing"] = [f"<file not found: {path}>"]
        return result
    src = target.read_text(encoding="utf-8")
    for ph in required:
        if ph in src:
            result["ok"].append(ph)
        else:
            result["missing"].append(ph)
    return result


# ============================================================
# Check 4: STABLE_USER_CODE マーカー保護
# ============================================================

def check_markers(files):
    found = defaultdict(int)
    for f in files:
        try:
            src = f.read_text(encoding="utf-8")
        except Exception:
            continue
        for m in MARKER_PATTERNS:
            found[m] += src.count(m)
    return dict(found)


# ============================================================
# Check 5: エスケープ保持チェック
# ============================================================

def check_escapes(translations_path):
    """
    translations.json 内で、japanese に C-style '\\n'（2文字）を含むのに
    english 側で実改行になっている／消失しているエントリを検出。
    """
    p = PROJECT_ROOT / translations_path
    if not p.exists():
        return {"path": str(p), "mismatches": [], "checked": 0}
    data = json.loads(p.read_text(encoding="utf-8"))
    mismatches = []
    checked = 0
    for entry in data.get("strings", []):
        jp = entry.get("japanese", "")
        en = entry.get("english", "")
        if not jp or not en:
            continue
        # japanese が C-style \n のみ（実改行なし）かつ english に実改行がある
        if "\\n" in jp and "\n" not in jp and "\n" in en:
            mismatches.append((entry["id"], "real newline in english"))
            continue
        # japanese に \n があるのに english に \n も実改行もない
        if "\\n" in jp and "\\n" not in en and "\n" not in en:
            mismatches.append((entry["id"], "\\n lost in english"))
            continue
        checked += 1
    return {"path": str(p), "mismatches": mismatches, "checked": checked}


# ============================================================
# Check 6: バックアップ差分サマリ
# ============================================================

def check_backup_diff():
    backups = sorted(PROJECT_ROOT.glob("_backup_*"),
                     key=lambda x: x.name, reverse=True)
    if not backups:
        return None
    latest = backups[0]
    changed = 0
    total = 0
    syntax_broken = []
    for f in latest.rglob("*.py"):
        rel = f.relative_to(latest)
        current = PROJECT_ROOT / rel
        total += 1
        if not current.exists():
            continue
        try:
            a = f.read_text(encoding="utf-8")
            b = current.read_text(encoding="utf-8")
        except Exception:
            continue
        if a != b:
            changed += 1
            try:
                ast.parse(b)
            except SyntaxError as e:
                syntax_broken.append((str(rel), f"L{e.lineno}: {e.msg}"))
    return {
        "backup": latest.name,
        "total": total,
        "changed": changed,
        "syntax_broken": syntax_broken,
    }


# ============================================================
# Report
# ============================================================

def print_report(results, allow_cats):
    print("=== Translation Verification Report ===\n")

    # 1. Syntax
    r = results["syntax"]
    print(f"[1/6] Python syntax check")
    print(f"  OK: {r['ok']}, Errors: {len(r['errors'])}")
    for path, msg in r["errors"][:20]:
        print(f"    \u2717 {path}: {msg}")
    print()

    # 2. Residual Japanese
    r = results["residual"]
    print(f"[2/6] Residual Japanese (allow: {', '.join(sorted(allow_cats)) or 'none'})")
    if not r:
        print("  No residual Japanese detected.")
    else:
        total_lines = sum(v["lines"] for v in r.values())
        total_files = len({f for v in r.values() for f in v["files"]})
        print(f"  Total: {total_lines} tokens in {total_files} files")
        for cat in sorted(r.keys()):
            v = r[cat]
            print(f"    {cat}: {v['lines']} tokens / {len(v['files'])} files")
        print()
        for cat in sorted(r.keys()):
            print(f"  --- Category {cat} ---")
            for path, line, is_comment, snippet in r[cat]["details"]:
                kind = "C" if is_comment else "S"
                print(f"    [{kind}] {path}:{line}")
                print(f"         {snippet}")
            if len(r[cat]["details"]) >= 15:
                print(f"    ... (showing first 15)")
            print()

    # 3. Placeholders
    r = results["placeholders"]
    print(f"[3/6] Critical placeholders — {r['path']}")
    for ph in r["ok"]:
        print(f"  \u2713 {ph}")
    for ph in r["missing"]:
        print(f"  \u2717 MISSING: {ph}")
    print()

    # 4. Markers
    r = results["markers"]
    print(f"[4/6] STABLE_USER_CODE markers")
    for m in MARKER_PATTERNS:
        print(f"  {m}: {r.get(m, 0)}")
    print()

    # 5. Escapes
    r = results["escapes"]
    print(f"[5/6] Escape integrity — {r['path']}")
    print(f"  Checked: {r['checked']}, Mismatches: {len(r['mismatches'])}")
    for sid, reason in r["mismatches"][:20]:
        print(f"    \u2717 {sid}: {reason}")
    print()

    # 6. Backup diff
    r = results["backup"]
    print(f"[6/6] Backup diff")
    if r is None:
        print("  No _backup_* directory found (skip).")
    else:
        print(f"  Backup: {r['backup']}")
        print(f"  Files changed: {r['changed']} / {r['total']}")
        if r["syntax_broken"]:
            print(f"  \u2717 Syntax broken after change: {len(r['syntax_broken'])}")
            for path, msg in r["syntax_broken"][:10]:
                print(f"      {path}: {msg}")
        else:
            print(f"  \u2713 No syntax breakage detected in changed files.")
    print()

    # Overall
    issues = (
        len(results["syntax"]["errors"])
        + sum(v["lines"] for v in results["residual"].values())
        + len(results["placeholders"]["missing"])
        + len(results["escapes"]["mismatches"])
        + (len(results["backup"]["syntax_broken"])
           if results["backup"] else 0)
    )
    print(f"=== Overall: {issues} issue(s) ===")
    return issues


# ============================================================
# Main
# ============================================================

def main():
    p = argparse.ArgumentParser(
        description="Verify translation results without uploading sources.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--dirs", nargs="+", default=DEFAULT_DIRS)
    p.add_argument("--allow-ja", nargs="+", default=[],
                   help="Allow residual Japanese in these categories (e.g. H)")
    p.add_argument("--json", default=None,
                   help="Write JSON report to this path")
    p.add_argument("--only", choices=["syntax", "residual", "placeholders",
                                      "markers", "escapes", "backup"],
                   default=None)
    p.add_argument("--translations", default="translations.json")
    args = p.parse_args()

    files = list(iter_py_files(args.dirs))
    allow_cats = set(args.allow_ja)

    results = {}
    only = args.only

    if only in (None, "syntax"):
        ok, err = check_syntax(files)
        results["syntax"] = {"ok": ok, "errors": err}
    else:
        results["syntax"] = {"ok": 0, "errors": []}

    if only in (None, "residual"):
        results["residual"] = check_residual_japanese(files, allow_cats)
    else:
        results["residual"] = {}

    if only in (None, "placeholders"):
        results["placeholders"] = check_placeholders()
    else:
        results["placeholders"] = {"path": "", "ok": [], "missing": []}

    if only in (None, "markers"):
        results["markers"] = check_markers(files)
    else:
        results["markers"] = {}

    if only in (None, "escapes"):
        results["escapes"] = check_escapes(args.translations)
    else:
        results["escapes"] = {"path": "", "checked": 0, "mismatches": []}

    if only in (None, "backup"):
        results["backup"] = check_backup_diff()
    else:
        results["backup"] = None

    # Convert set() to sorted list for JSON
    serial = {
        "syntax": results["syntax"],
        "residual": {
            cat: {"lines": v["lines"],
                  "files": sorted(v["files"]),
                  "details": v["details"]}
            for cat, v in results["residual"].items()
        },
        "placeholders": results["placeholders"],
        "markers": results["markers"],
        "escapes": results["escapes"],
        "backup": results["backup"],
    }

    issues = print_report(results, allow_cats)

    if args.json:
        out = PROJECT_ROOT / args.json
        out.write_text(
            json.dumps(serial, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"\nJSON report: {out}")

    return 0 if issues == 0 else 1


if __name__ == "__main__":
    sys.exit(main())