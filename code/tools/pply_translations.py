#!/usr/bin/env python3
"""
Apply translations from translations.json to source files.

Usage:
  # Dry run (preview changes)
  python tools/apply_translations.py --dry-run

  # Apply with backup
  python tools/apply_translations.py --apply --backup

  # Check progress (how many translated)
  python tools/apply_translations.py --progress

  # Only process specific category
  python tools/apply_translations.py --category A B --apply
"""
import argparse
import io
import json
import re
import shutil
import sys
import tokenize
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_DIRS = ["statable", "statable_gui", "codegen", "tools", "tests"]

SKIP_FILES = {
    'tools/extract_strings.py',
    'tools/apply_translations.py',
    'tools/glossary.py',
    'tools/replace_japanese.py',
    'tools/scan_japanese.py',
    'tools/scan_japanese.py',
}

JP_PATTERN = re.compile(
    r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF\uFF00-\uFFEF]+'
)


# ============================================================
# Translation application
# ============================================================

def build_replacement_map(translations: dict, categories=None) -> dict:
    """Build {japanese: english} map from translations.json."""
    result = {}
    for item in translations.get("strings", []):
        jp = item.get("japanese", "")
        en = item.get("english", "").strip()
        if not jp or not en:
            continue
        if categories and item.get("category") not in categories:
            continue
        result[jp] = en
    return result


def apply_to_token_text(text: str, replace_map: dict,
                        reverse_sorted_keys: list) -> str:
    """
    Apply replacements to a string, longest key first.
    Only replaces on exact substring boundaries.
    """
    for jp in reverse_sorted_keys:
        en = replace_map[jp]
        text = text.replace(jp, en)
    return text


def replace_in_file(path: Path, replace_map: dict,
                    dry_run: bool = True) -> dict:
    """Replace Japanese in a single file, token-safe."""
    result = {
        'path': path,
        'status': 'NO_CHANGE',
        'changed_lines': [],
        'error': None,
    }

    if not replace_map:
        return result

    try:
        source = path.read_text(encoding='utf-8')
    except Exception as e:
        result['status'] = 'ERROR'
        result['error'] = f"read failed: {e}"
        return result

    # Sort keys by length (descending) to avoid partial matches
    sorted_keys = sorted(replace_map.keys(), key=len, reverse=True)

    # Tokenize to find comment/string boundaries
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
    except Exception as e:
        result['status'] = 'ERROR'
        result['error'] = f"tokenize failed: {e}"
        return result

    # Collect replacements
    replacements = []
    for tok in tokens:
        if tok.type not in (tokenize.COMMENT, tokenize.STRING):
            continue
        original = tok.string
        replaced = apply_to_token_text(original, replace_map, sorted_keys)
        if replaced != original:
            replacements.append((tok.start, tok.end, replaced))

    if not replacements:
        return result

    # Apply replacements from last to first
    lines = source.splitlines(keepends=True)

    def pos_to_offset(lines, pos):
        row, col = pos
        return sum(len(l) for l in lines[:row - 1]) + col

    abs_replacements = []
    for start, end, new_text in replacements:
        abs_start = pos_to_offset(lines, start)
        abs_end = pos_to_offset(lines, end)
        abs_replacements.append((abs_start, abs_end, new_text))

    abs_replacements.sort(key=lambda x: -x[0])

    new_source = source
    for abs_start, abs_end, new_text in abs_replacements:
        new_source = new_source[:abs_start] + new_text + new_source[abs_end:]

    # Record changed lines
    orig_lines = source.splitlines()
    new_lines = new_source.splitlines()
    for i, (ol, nl) in enumerate(zip(orig_lines, new_lines), 1):
        if ol != nl:
            result['changed_lines'].append((i, ol, nl))

    result['status'] = 'DRY_RUN' if dry_run else 'CHANGED'

    if not dry_run:
        try:
            path.write_text(new_source, encoding='utf-8')
        except Exception as e:
            result['status'] = 'ERROR'
            result['error'] = f"write failed: {e}"

    return result


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
# Progress check
# ============================================================

def show_progress(translations: dict, source_dirs):
    """Show translation progress."""
    total = len(translations.get("strings", []))
    translated = sum(1 for s in translations.get("strings", [])
                     if s.get("english", "").strip())
    untranslated = total - translated

    print(f"=== Translation progress ===")
    print(f"Total: {total}")
    print(f"Translated: {translated} ({translated * 100 // max(total, 1)}%)")
    print(f"Untranslated: {untranslated}")
    print()

    # By category
    cat_total = {}
    cat_done = {}
    for s in translations.get("strings", []):
        cat = s.get("category", "?")
        cat_total[cat] = cat_total.get(cat, 0) + 1
        if s.get("english", "").strip():
            cat_done[cat] = cat_done.get(cat, 0) + 1

    print("By category:")
    cat_names = {
        'A': 'Generated C comments',
        'B': 'GUI text',
        'C': 'Codegen logs',
        'F': 'Sample data',
        'G': 'Test expectations',
        'H': 'Other',
    }
    for cat in sorted(cat_total.keys()):
        done = cat_done.get(cat, 0)
        total_c = cat_total[cat]
        pct = done * 100 // max(total_c, 1)
        bar = '#' * (pct // 5) + '.' * (20 - pct // 5)
        print(f"  {cat}: [{bar}] {done:4d}/{total_c:4d} ({pct:3d}%)  "
              f"{cat_names.get(cat, '')}")

    # List a few untranslated
    untranslated_items = [s for s in translations.get("strings", [])
                          if not s.get("english", "").strip()]
    if untranslated_items:
        print()
        print("Sample untranslated:")
        for s in untranslated_items[:10]:
            print(f"  {s['id']} [{s['category']}] {s['japanese'][:50]}")


# ============================================================
# Main
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Apply translations from translations.json",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--translations", default="translations.json")
    parser.add_argument("--dirs", nargs="+", default=DEFAULT_DIRS)
    parser.add_argument("--category", nargs="+", default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--backup", action="store_true")
    parser.add_argument("--progress", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--report", default="apply_report.md")
    args = parser.parse_args()

    # Load translations
    translations_path = PROJECT_ROOT / args.translations
    if not translations_path.exists():
        print(f"ERROR: {translations_path} not found")
        print("Run: python tools/extract_strings.py")
        return 1

    translations = json.loads(translations_path.read_text(encoding='utf-8'))

    # Progress mode
    if args.progress:
        show_progress(translations, args.dirs)
        return 0

    # Must specify --dry-run or --apply
    if not args.dry_run and not args.apply:
        print("ERROR: specify --dry-run, --apply, or --progress")
        return 1

    # Build replacement map
    replace_map = build_replacement_map(translations, args.category)
    print(f"=== Apply translations ===")
    print(f"Translations loaded: {len(replace_map)} entries")
    if args.category:
        print(f"Category filter: {', '.join(args.category)}")
    print(f"Mode: {'DRY-RUN' if args.dry_run else 'APPLY'}")
    print()

    if not replace_map:
        print("No translations to apply.")
        return 0

    # Backup dir
    backup_dir = None
    if args.apply and args.backup:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = PROJECT_ROOT / f"_backup_{ts}"
        backup_dir.mkdir(exist_ok=True)
        print(f"Backup dir: {backup_dir}")
        print()

    # Process files
    files = list(iter_py_files([PROJECT_ROOT / d for d in args.dirs],
                               SKIP_FILES))
    stats = {'total': len(files), 'changed': 0, 'no_change': 0, 'error': 0}
    report_lines = [
        "# Apply Translations Report",
        "",
        f"- Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- Mode: {'DRY-RUN' if args.dry_run else 'APPLY'}",
        f"- Translations: {len(replace_map)}",
        f"- Files: {len(files)}",
        "",
    ]

    for path in files:
        if args.apply and backup_dir:
            try:
                rel = path.relative_to(PROJECT_ROOT)
                backup_path = backup_dir / rel
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, backup_path)
            except Exception as e:
                print(f"WARN: backup failed for {path}: {e}")

        result = replace_in_file(path, replace_map, dry_run=(not args.apply))

        if result['status'] in ('CHANGED', 'DRY_RUN'):
            stats['changed'] += 1
            rel = path.relative_to(PROJECT_ROOT)
            print(f"[{result['status']}] {rel}: "
                  f"{len(result['changed_lines'])} lines")
            if args.verbose:
                for i, (lineno, old, new) in enumerate(result['changed_lines'][:5], 1):
                    print(f"  L{lineno}:")
                    print(f"    - {old.strip()[:80]}")
                    print(f"    + {new.strip()[:80]}")
            report_lines.append(f"## {rel}")
            report_lines.append(f"- {len(result['changed_lines'])} lines changed")
            report_lines.append("")
        elif result['status'] == 'NO_CHANGE':
            stats['no_change'] += 1
        elif result['status'] == 'ERROR':
            stats['error'] += 1
            print(f"[ERROR] {path}: {result['error']}")
            report_lines.append(f"## ERROR: {path}")
            report_lines.append(f"- {result['error']}")
            report_lines.append("")

    print()
    print("=== Summary ===")
    for k, v in stats.items():
        print(f"  {k}: {v}")

    report_lines.append("## Summary")
    report_lines.append("")
    for k, v in stats.items():
        report_lines.append(f"- {k}: {v}")
    report_lines.append("")

    report_path = PROJECT_ROOT / args.report
    report_path.write_text("\n".join(report_lines), encoding='utf-8')
    print(f"\nReport: {report_path}")

    if args.dry_run:
        print()
        print("This was a dry run. To apply, use --apply --backup")

    return 0


if __name__ == "__main__":
    sys.exit(main())