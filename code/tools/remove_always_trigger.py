#!/usr/bin/env python3
"""
Remove `always` trigger (v2.2 migration).

Safe automatic replacements:
  - Default value:  trigger: str = "always"  ->  "before_transitions"
  - Explicit kw:    trigger="always"          ->  "before_transitions"

Preserved (untouched, for backward compatibility):
  - _LEGACY_TRIGGER_MAP  / migrate 系コード
  - Conditional checks like  in ("always", "before_transitions")
    (kept so that old XML data still works until fully migrated)

Reports-only (manual review needed):
  - docstring / comment mentions of "always"

Usage:
    python tools/remove_always_trigger.py --dry-run    (default)
    python tools/remove_always_trigger.py --apply
"""

import argparse
import pathlib
import re
import shutil
from datetime import datetime

PROJECT_ROOT = pathlib.Path(".")

TARGET_FILES = [
    "statable/model.py",
    "statable/sample_data.py",
    "codegen/transition_generator.py",
    "statable_gui/transition_editor_direct/actions_tab.py",
    "statable_gui/transition_editor_direct/code_widget.py",
    "tests/test_v2_2_p1.py",
    "tests/test_v2_2_p2.py",
    "tests/test_v2_2_p4a.py",
]

# Lines containing any of these substrings are NEVER auto-modified.
PRESERVE_SUBSTRINGS = (
    "_LEGACY_TRIGGER_MAP",
    "migrate_trigger",
    "legacy",
    "backward compat",
    "for compat",
    "preserve",
)

# Unambiguous auto-replacements.
AUTO_PATTERNS = [
    # Dataclass default:  trigger: str = "always"
    (re.compile(r'(trigger\s*:\s*str\s*=\s*)["\']always["\']'),
     r'\1"before_transitions"'),
    # Keyword argument:  trigger="always"
    (re.compile(r'(trigger\s*=\s*)["\']always["\']'),
     r'\1"before_transitions"'),
]

# Report-only: other mentions of "always" (strings, comments, docstrings).
REPORT_PATTERN = re.compile(r'["\']always["\']')


def make_backup(files):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = PROJECT_ROOT / f"_backup_always_{ts}"
    backup.mkdir(exist_ok=True)
    for rel in files:
        src = PROJECT_ROOT / rel
        if not src.exists():
            continue
        dst = backup / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    return backup


def should_preserve(stripped: str) -> bool:
    low = stripped.lower()
    # Comment lines are never auto-modified.
    if stripped.startswith("#"):
        return True
    for marker in PRESERVE_SUBSTRINGS:
        if marker.lower() in low:
            return True
    return False


def classify_line(line: str):
    """
    Return ('auto', new_line) if a safe replacement is possible,
    ('report', None) if only a mention exists,
    (None, None) otherwise.
    """
    stripped = line.strip()
    if should_preserve(stripped):
        return None, None

    # Try auto patterns first
    new_line = line
    changed = False
    for pat, repl in AUTO_PATTERNS:
        new_line2 = pat.sub(repl, new_line)
        if new_line2 != new_line:
            changed = True
            new_line = new_line2
    if changed:
        return "auto", new_line

    # Report-only if it mentions "always" as a quoted string
    if REPORT_PATTERN.search(line):
        return "report", None

    return None, None


def scan():
    auto_changes = []   # (rel, lineno, old, new)
    report_items = []   # (rel, lineno, line)
    for rel in TARGET_FILES:
        path = PROJECT_ROOT / rel
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for i, line in enumerate(text.splitlines(), 1):
            kind, new_line = classify_line(line)
            if kind == "auto":
                auto_changes.append((rel, i, line.rstrip(), new_line.rstrip()))
            elif kind == "report":
                report_items.append((rel, i, line.rstrip()))
    return auto_changes, report_items


def apply_changes():
    backup = make_backup(TARGET_FILES)
    modified = []
    for rel in TARGET_FILES:
        path = PROJECT_ROOT / rel
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines(keepends=True)
        new_lines = []
        file_changed = False
        for line in lines:
            kind, new_line = classify_line(line)
            if kind == "auto":
                new_lines.append(new_line)
                file_changed = True
            else:
                new_lines.append(line)
        if file_changed:
            path.write_text("".join(new_lines), encoding="utf-8")
            modified.append(rel)
    return backup, modified


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--apply", action="store_true",
                   help="Actually apply changes (default: dry-run)")
    args = p.parse_args()

    auto_changes, report_items = scan()

    print("=" * 70)
    print("  remove_always_trigger")
    print("=" * 70)

    # --- Auto-replace report ---
    if auto_changes:
        print(f"\n[AUTO] {len(auto_changes)} safe replacement(s) detected:\n")
        for rel, lineno, old, new in auto_changes:
            print(f"  {rel}:{lineno}")
            print(f"    - {old}")
            print(f"    + {new}")
    else:
        print("\n[AUTO] No automatic replacements needed.")

    # --- Report-only ---
    if report_items:
        print(f"\n[REPORT] {len(report_items)} mention(s) requiring manual review:\n")
        for rel, lineno, line in report_items:
            print(f"  {rel}:{lineno}: {line}")
        print("\n  (These are kept as-is; review only if they must be removed.)")

    print()
    print("=" * 70)

    if not args.apply:
        print("DRY-RUN mode. No files were modified.")
        print("Run with --apply to apply the automatic replacements.")
        return

    # Apply
    backup, modified = apply_changes()
    print(f"\nBackup created: {backup}")
    print(f"Modified {len(modified)} file(s):")
    for rel in modified:
        print(f"  [FIXED] {rel}")


if __name__ == "__main__":
    main()