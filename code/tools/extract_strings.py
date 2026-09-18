#!/usr/bin/env python3
"""
Japanese string extraction tool (v2 - token-level).

Scans Python files and extracts whole COMMENT / STRING tokens
that contain Japanese characters into a JSON file.

Unlike v1, this tool treats each COMMENT or STRING token as a single
translation unit. This avoids fragmenting sentences into meaningless
pieces like "の" or "（".

Output format (translations.json):
  {
    "_meta": {
      "created": "2026-09-18 10:00:00",
      "source_dirs": ["statable", "statable_gui", "codegen"],
      "total_unique": 1234,
      "total_files": 119,
      "extractor": "v2-token-level"
    },
    "strings": [
      {
        "id": "s0001",
        "kind": "comment",          # "comment" | "string"
        "japanese": " タイマ変数を初期化する",
        "english": "",
        "category": "A",
        "occurrences": 15,
        "is_docstring": false,
        "prefix": "",
        "quote": "",
        "files": ["codegen/variable_generator.py", ...]
      },
      {
        "id": "s0002",
        "kind": "string",
        "japanese": "初期化に失敗しました",
        "english": "",
        "category": "B",
        "occurrences": 3,
        "is_docstring": false,
        "prefix": "",
        "quote": "\"",
        "files": ["statable_gui/main_window.py", ...]
      }
    ]
  }

Usage:
  # Extract to translations.json (tests/ and tools/ excluded)
  python tools/extract_strings.py

  # Include tests/ and tools/
  python tools/extract_strings.py --include-tests --include-tools

  # Only specific dirs
  python tools/extract_strings.py --dirs codegen

  # Only GUI display text
  python tools/extract_strings.py --category B

  # Only comments
  python tools/extract_strings.py --kinds comment
"""
import argparse
import ast
import io
import json
import re
import sys
import tokenize
from datetime import datetime
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Japanese character detection (hiragana / katakana / kanji / full-width)
JP_CHAR_RE = re.compile(
    r'[\u3040-\u309F'    # hiragana
    r'\u30A0-\u30FF'     # katakana
    r'\u4E00-\u9FFF'     # kanji
    r'\uFF00-\uFFEF'     # full-width
    r']'
)

DEFAULT_DIRS = ["statable", "statable_gui", "codegen", "tools", "tests"]

CATEGORY_RULES = [
    ("A", [
        r"codegen[/\\](?!validate[/\\]).*_generator\.py$",
        r"codegen[/\\]code_templates\.py$",
    ]),
    ("B", [r"statable_gui[/\\].*\.py$"]),
    ("C", [r"codegen[/\\].*\.py$"]),
    ("F", [
        r"statable[/\\]sample_data\.py$",
        r"codegen[/\\]sample_data\.py$",
    ]),
    ("G", [r"tests[/\\].*\.py$"]),
    ("H", [r"tools[/\\].*\.py$"]),
]

SKIP_FILES = {
    'tools/extract_strings.py',
    'tools/apply_translations.py',
    'tools/glossary.py',
    'tools/replace_japanese.py',
    'tools/scan_japanese.py',
}

CAT_ORDER = {'A': 0, 'B': 1, 'C': 2, 'D': 3, 'E': 4, 'F': 5, 'G': 6, 'H': 7}

CAT_NAMES = {
    'A': 'Generated C code comments',
    'B': 'GUI display text',
    'C': 'Codegen layer logs',
    'F': 'Sample data',
    'G': 'Test expectations',
    'H': 'Other / tools',
}


# ============================================================
# Helpers
# ============================================================

def detect_category(rel_path: str) -> str:
    norm = rel_path.replace("\\", "/")
    for cat, patterns in CATEGORY_RULES:
        for p in patterns:
            if re.search(p, norm):
                return cat
    return "H"


def has_japanese(text: str) -> bool:
    return JP_CHAR_RE.search(text) is not None


def count_japanese(text: str) -> int:
    return len(JP_CHAR_RE.findall(text))


def split_string_token(raw: str):
    """
    Split a STRING token raw text into (prefix, quote, body).

    Handles:
      - single / double quotes
      - triple quotes
      - string prefixes (f, r, b, u, rb, br, fr, rf, ...)

    Returns (prefix, quote, body).
    On failure, returns (raw, "", "").
    """
    # Anchor at start; quote is one of: triple double, triple single, single, double
    m = re.match(r'^([a-zA-Z]*)("""|\'\'\'|"|\')(.*)\2$', raw, re.DOTALL)
    if not m:
        return (raw, "", "")
    prefix, quote, body = m.group(1), m.group(2), m.group(3)
    return (prefix, quote, body)


def split_comment_token(raw: str):
    """
    Split a COMMENT token raw text into (marker, body).
    E.g. "# foo" -> ("#", " foo")
         "## bar" -> ("##", " bar")
    """
    if not raw.startswith("#"):
        return ("", raw)
    i = 0
    while i < len(raw) and raw[i] == "#":
        i += 1
    return (raw[:i], raw[i:])


def find_docstring_lines(source: str) -> set:
    """
    Return the set of 1-based line numbers where a docstring starts.

    Uses AST, which is more reliable than heuristics based on column 0.
    """
    lines = set()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return lines

    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.FunctionDef,
                                 ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        body = getattr(node, "body", None)
        if not body:
            continue
        first = body[0]
        if (isinstance(first, ast.Expr)
                and isinstance(first.value, ast.Constant)
                and isinstance(first.value.value, str)):
            lines.add(first.value.lineno)
    return lines


def iter_py_files(dirs, skip_files):
    for d in dirs:
        p = Path(d)
        if p.is_file() and p.suffix == '.py':
            yield p
        elif p.is_dir():
            for f in p.rglob('*.py'):
                try:
                    rel = str(f.relative_to(PROJECT_ROOT)).replace('\\', '/')
                except ValueError:
                    continue
                if rel in skip_files:
                    continue
                yield f


# ============================================================
# Extraction
# ============================================================

def extract_from_file(path: Path) -> dict:
    """
    Extract whole COMMENT / STRING tokens containing Japanese.

    Returns:
      {
        "comments": [ { "body": str, "raw": str, "line": int } ],
        "strings":  [ { "body": str, "raw": str, "line": int,
                        "prefix": str, "quote": str, "is_docstring": bool } ],
        "errors":   [ str ],
      }
    """
    result = {"comments": [], "strings": [], "errors": []}

    try:
        source = path.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        try:
            source = path.read_text(encoding='shift-jis')
        except Exception as e:
            result["errors"].append(f"read failed: {e}")
            return result
    except Exception as e:
        result["errors"].append(f"read failed: {e}")
        return result

    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
    except Exception as e:
        result["errors"].append(f"tokenize failed: {e}")
        return result

    docstring_lines = find_docstring_lines(source)

    for tok in tokens:
        if tok.type == tokenize.COMMENT:
            _marker, body = split_comment_token(tok.string)
            if not has_japanese(body):
                continue
            result["comments"].append({
                "body": body,
                "raw": tok.string,
                "line": tok.start[0],
            })
        elif tok.type == tokenize.STRING:
            prefix, quote, body = split_string_token(tok.string)
            if not has_japanese(body):
                continue
            is_doc = tok.start[0] in docstring_lines
            result["strings"].append({
                "body": body,
                "raw": tok.string,
                "line": tok.start[0],
                "prefix": prefix,
                "quote": quote,
                "is_docstring": is_doc,
            })

    return result


# ============================================================
# Main
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Japanese string extraction tool (token-level, v2)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--dirs", nargs="+", default=DEFAULT_DIRS,
                        help="Directories or files to scan")
    parser.add_argument("--output", default="translations.json",
                        help="Output JSON file (relative to project root)")
    parser.add_argument("--include-tests", action="store_true",
                        help="Include tests/ in scan (default: excluded)")
    parser.add_argument("--exclude-tests", action="store_true",
                        help="Explicitly exclude tests/ (default behavior)")
    parser.add_argument("--include-tools", action="store_true",
                        help="Include tools/ in scan (default: excluded)")
    parser.add_argument("--min-jp-chars", type=int, default=1,
                        help="Minimum number of Japanese characters to extract")
    parser.add_argument("--category", nargs="+", default=None,
                        help="Only these categories (A/B/C/F/G/H)")
    parser.add_argument("--kinds", nargs="+", default=["comment", "string"],
                        choices=["comment", "string"],
                        help="Which token kinds to extract")
    args = parser.parse_args()

    # ---- Resolve directory list ----
    dirs_list = list(args.dirs)

    # Remove tests/ unless explicitly included
    if "tests" in dirs_list and not args.include_tests:
        dirs_list = [d for d in dirs_list if d != "tests"]

    # Remove tools/ unless explicitly included
    if "tools" in dirs_list and not args.include_tools:
        dirs_list = [d for d in dirs_list if d != "tools"]

    dirs = [PROJECT_ROOT / d for d in dirs_list]

    # ---- Collect ----
    # key: (kind, body)
    strings_db = {}

    file_count = 0
    error_count = 0

    for path in iter_py_files(dirs, SKIP_FILES):
        file_count += 1
        extracted = extract_from_file(path)

        for err in extracted["errors"]:
            error_count += 1
            print(f"[WARN] {path}: {err}", file=sys.stderr)

        try:
            rel = str(path.relative_to(PROJECT_ROOT)).replace('\\', '/')
        except ValueError:
            rel = str(path)

        category = detect_category(rel)

        for kind, items in (("comment", extracted["comments"]),
                            ("string",  extracted["strings"])):
            if kind not in args.kinds:
                continue

            for item in items:
                body = item["body"]

                if count_japanese(body) < args.min_jp_chars:
                    continue

                key = (kind, body)
                entry = strings_db.get(key)
                if entry is None:
                    entry = {
                        "kind": kind,
                        "body": body,
                        "files": set(),
                        "occurrences": 0,
                        "category": category,
                        "is_docstring": item.get("is_docstring", False),
                        "prefix": item.get("prefix", ""),
                        "quote": item.get("quote", ""),
                    }
                    strings_db[key] = entry

                entry["files"].add(rel)
                entry["occurrences"] += 1

                # Keep the highest-priority (lowest cat_order) category
                if CAT_ORDER.get(category, 9) < CAT_ORDER.get(entry["category"], 9):
                    entry["category"] = category

                # Preserve docstring flag if any occurrence is a docstring
                if item.get("is_docstring", False):
                    entry["is_docstring"] = True

    # ---- Category filter ----
    if args.category:
        cats = set(args.category)
        strings_db = {k: v for k, v in strings_db.items() if v["category"] in cats}

    # ---- Sort ----
    sorted_items = sorted(
        strings_db.values(),
        key=lambda v: (
            CAT_ORDER.get(v["category"], 9),
            -v["occurrences"],
            -len(v["body"]),
            v["body"],
        ),
    )

    # ---- Build output ----
    output = {
        "_meta": {
            "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source_dirs": dirs_list,
            "total_unique": len(sorted_items),
            "total_files": file_count,
            "extractor": "v2-token-level",
        },
        "strings": [],
    }

    for i, info in enumerate(sorted_items, 1):
        output["strings"].append({
            "id": f"s{i:04d}",
            "kind": info["kind"],
            "japanese": info["body"],
            "english": "",
            "category": info["category"],
            "occurrences": info["occurrences"],
            "is_docstring": info["is_docstring"],
            "prefix": info["prefix"],
            "quote": info["quote"],
            "files": sorted(info["files"])[:5],
        })

    # ---- Write ----
    output_path = PROJECT_ROOT / args.output
    output_path.write_text(
        json.dumps(output, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )

    # ---- Summary ----
    cat_occ = defaultdict(int)
    cat_uniq = defaultdict(int)
    kind_occ = defaultdict(int)
    kind_uniq = defaultdict(int)

    for info in strings_db.values():
        cat_occ[info["category"]] += info["occurrences"]
        cat_uniq[info["category"]] += 1
        kind_occ[info["kind"]] += info["occurrences"]
        kind_uniq[info["kind"]] += 1

    print(f"=== Japanese string extraction (token-level, v2) ===")
    print(f"Files scanned : {file_count}")
    print(f"Read errors   : {error_count}")
    print(f"Unique strings: {len(sorted_items)}")
    print()
    print("By kind:")
    for kind in ("comment", "string"):
        if kind in kind_uniq:
            print(f"  {kind:8s}: {kind_uniq[kind]:4d} unique, "
                  f"{kind_occ[kind]:5d} occurrences")
    print()
    print("By category:")
    for cat in sorted(cat_occ.keys(), key=lambda c: CAT_ORDER.get(c, 9)):
        print(f"  {cat}: {cat_uniq[cat]:4d} unique, "
              f"{cat_occ[cat]:5d} occurrences  ({CAT_NAMES.get(cat, '')})")
    print()
    print(f"Output: {output_path}")
    print()
    print("Next steps:")
    print(f"  1. Open {args.output} and fill in the 'english' field")
    print(f"  2. Run: python tools/apply_translations.py --dry-run")
    print(f"  3. Run: python tools/apply_translations.py --apply --backup")

    return 0


if __name__ == "__main__":
    sys.exit(main())