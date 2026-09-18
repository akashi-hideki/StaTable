#!/usr/bin/env python3
"""
extract_residuals.py — 翻訳適用後に残った日本語だけを再抽出

apply_translations.py 実行後のソースを走査し、
COMMENT / STRING トークン内に残存する日本語を検出して
新しいバッチファイル residuals.json として出力する。

【分類】
  A) 既存 translations.json に japanese がある → マッチ失敗バグ
  B) 存在しない → 新規文字列（本来のターゲット）

【使い方】
  python tools/extract_residuals.py
  python tools/extract_residuals.py --output batch10.json
  python tools/extract_residuals.py --min-jp 2   # 2文字以上のみ
"""
import argparse
import io
import json
import re
import sys
import tokenize
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DIRS = ["statable", "statable_gui", "codegen"]

JP_RE = re.compile(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF\uFF00-\uFFEF]')

SKIP_FILES = {
    'tools/extract_strings.py', 'tools/apply_translations.py',
    'tools/apply_batch.py', 'tools/glossary.py',
    'tools/replace_japanese.py', 'tools/scan_japanese.py',
    'tools/verify_translation.py', 'tools/extract_residuals.py',
    'tools/fix_translations.py',
}


def split_string_token(raw):
    m = re.match(r'^([a-zA-Z]*)("""|\'\'\'|"|\')(.*)\2$', raw, re.DOTALL)
    if not m:
        return (raw, "", "")
    return (m.group(1), m.group(2), m.group(3))


def split_comment_token(raw):
    if not raw.startswith("#"):
        return ("", raw)
    i = 0
    while i < len(raw) and raw[i] == "#":
        i += 1
    return (raw[:i], raw[i:])


def iter_py_files(dirs):
    for d in dirs:
        p = PROJECT_ROOT / d
        if not p.exists():
            continue
        for f in p.rglob("*.py"):
            try:
                rel = str(f.relative_to(PROJECT_ROOT)).replace("\\", "/")
            except ValueError:
                continue
            if rel in SKIP_FILES:
                continue
            yield f


def extract(files):
    """Return { (kind, body): { ... } } for all residual Japanese tokens."""
    db = {}
    for f in files:
        try:
            rel = str(f.relative_to(PROJECT_ROOT)).replace("\\", "/")
            src = f.read_text(encoding="utf-8")
            tokens = list(tokenize.generate_tokens(io.StringIO(src).readline))
        except Exception:
            continue

        for tok in tokens:
            if tok.type == tokenize.COMMENT:
                marker, body = split_comment_token(tok.string)
                if not JP_RE.search(body):
                    continue
                key = ("comment", body)
                if key not in db:
                    db[key] = {
                        "kind": "comment", "japanese": body,
                        "files": set(), "occurrences": 0, "example": (rel, tok.start[0]),
                    }
                db[key]["files"].add(rel)
                db[key]["occurrences"] += 1

            elif tok.type == tokenize.STRING:
                prefix, quote, body = split_string_token(tok.string)
                if not JP_RE.search(body):
                    continue
                key = ("string", body)
                if key not in db:
                    db[key] = {
                        "kind": "string", "japanese": body,
                        "prefix": prefix, "quote": quote,
                        "files": set(), "occurrences": 0, "example": (rel, tok.start[0]),
                    }
                db[key]["files"].add(rel)
                db[key]["occurrences"] += 1

    return db


def main():
    p = argparse.ArgumentParser(description="Extract residual Japanese strings.")
    p.add_argument("--dirs", nargs="+", default=DEFAULT_DIRS)
    p.add_argument("--translations", default="translations.json")
    p.add_argument("--output", default="residuals.json")
    p.add_argument("--min-jp", type=int, default=1)
    args = p.parse_args()

    # Load existing translations
    existing_jp = set()
    tp = PROJECT_ROOT / args.translations
    if tp.exists():
        data = json.loads(tp.read_text(encoding="utf-8"))
        for e in data.get("strings", []):
            existing_jp.add(e.get("japanese", ""))

    files = list(iter_py_files(args.dirs))
    db = extract(files)

    # Counters
    matched_bug = []   # in translations but not replaced
    new_strings = []   # not in translations

    for (kind, body), info in db.items():
        n_jp = len(JP_RE.findall(body))
        if n_jp < args.min_jp:
            continue
        if body in existing_jp:
            info["category"] = "MATCH_FAILED"
            matched_bug.append(info)
        else:
            info["category"] = "NEW"
            new_strings.append(info)

    # Sort: NEW first by occurrences descending
    new_strings.sort(key=lambda x: (-x["occurrences"], -len(x["japanese"]), x["japanese"]))
    matched_bug.sort(key=lambda x: (-x["occurrences"], -len(x["japanese"]), x["japanese"]))

    # Build output
    out = {
        "_meta": {
            "description": "Residual Japanese strings after apply_translations",
            "source_dirs": args.dirs,
            "total_files": len(files),
            "new_strings": len(new_strings),
            "match_failed": len(matched_bug),
        },
        "strings": [],
    }

    next_id = 1661
    for info in new_strings:
        entry = {
            "id": f"s{next_id:04d}",
            "kind": info["kind"],
            "japanese": info["japanese"],
            "english": "",
            "category": "NEW",
            "occurrences": info["occurrences"],
            "files": sorted(info["files"])[:5],
        }
        if info["kind"] == "string":
            entry["prefix"] = info.get("prefix", "")
            entry["quote"] = info.get("quote", "")
        out["strings"].append(entry)
        next_id += 1

    for info in matched_bug:
        entry = {
            "id": f"s{next_id:04d}",
            "kind": info["kind"],
            "japanese": info["japanese"],
            "english": "",
            "category": "MATCH_FAILED",
            "occurrences": info["occurrences"],
            "files": sorted(info["files"])[:5],
            "example": f"{info['example'][0]}:{info['example'][1]}",
        }
        out["strings"].append(entry)
        next_id += 1

    out_path = PROJECT_ROOT / args.output
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    # Report
    print(f"=== Residual Japanese extraction ===")
    print(f"Files scanned   : {len(files)}")
    print(f"NEW strings     : {len(new_strings)}  <- need translation")
    print(f"MATCH_FAILED    : {len(matched_bug)}  <- in translations.json but not applied")
    print(f"Output          : {out_path}")
    print()

    if new_strings:
        print(f"--- NEW strings (top 30 of {len(new_strings)}) ---")
        for info in new_strings[:30]:
            jp = info["japanese"].replace("\n", "\\n")[:90]
            tag = "S" if info["kind"] == "string" else "C"
            print(f"  [{tag}] x{info['occurrences']:2d}  {jp}")
        if len(new_strings) > 30:
            print(f"  ... and {len(new_strings) - 30} more")
        print()

    if matched_bug:
        print(f"--- MATCH_FAILED (all {len(matched_bug)}) ---")
        for info in matched_bug:
            jp = info["japanese"].replace("\n", "\\n")[:90]
            ex = info["example"]
            print(f"  {ex[0]}:{ex[1]}")
            print(f"    {jp}")
        print()

    return 0


if __name__ == "__main__":
    sys.exit(main())