#!/usr/bin/env python3
"""
Verify generated C code without a C compiler.

Checks:
  1. Bracket / brace / paren balance
  2. Include guard correctness (matching #ifndef / #define / #endif)
  3. Function declaration vs definition consistency
     (declarations searched across .c AND .h)
  4. Duplicate typedef / enum / struct detection
  5. Japanese character residual check
  6. Known-issue detection (nested group, custom type)

Usage:
    cd <project-root>
    python tools/verify_generated_code.py --root output
    python tools/verify_generated_code.py --root output --verbose
"""

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple


# ======================================================================
# Data
# ======================================================================
class FileReport:
    def __init__(self, path: Path):
        self.path = path
        self.errors: List[str] = []
        self.warnings: List[str] = []

    @property
    def name(self) -> str:
        return str(self.path)

    def has_errors(self) -> bool:
        return bool(self.errors)


# ======================================================================
# 1. Bracket / brace / paren balance
# ======================================================================
def strip_comments_and_strings(text: str) -> str:
    out = []
    i = 0
    n = len(text)
    while i < n:
        c = text[i]
        if c == '/' and i + 1 < n and text[i + 1] == '/':
            j = text.find('\n', i)
            if j == -1:
                break
            i = j
            continue
        if c == '/' and i + 1 < n and text[i + 1] == '*':
            j = text.find('*/', i + 2)
            if j == -1:
                break
            i = j + 2
            continue
        if c == '"':
            i += 1
            while i < n:
                if text[i] == '\\':
                    i += 2
                    continue
                if text[i] == '"':
                    i += 1
                    break
                i += 1
            continue
        if c == "'":
            i += 1
            while i < n:
                if text[i] == '\\':
                    i += 2
                    continue
                if text[i] == "'":
                    i += 1
                    break
                i += 1
            continue
        out.append(c)
        i += 1
    return ''.join(out)


def check_balance(text: str, path: str) -> Tuple[List[str], List[str]]:
    errors = []
    warnings = []
    cleaned = strip_comments_and_strings(text)
    pairs = [('(', ')'), ('[', ']'), ('{', '}')]
    for open_c, close_c in pairs:
        depth = 0
        for i, ch in enumerate(cleaned):
            if ch == open_c:
                depth += 1
            elif ch == close_c:
                depth -= 1
                if depth < 0:
                    errors.append(
                        f"Unbalanced '{close_c}' at offset {i} in {path}")
                    break
        if depth > 0:
            errors.append(
                f"Unclosed '{open_c}' (depth={depth}) in {path}")
    return errors, warnings


# ======================================================================
# 2. Include guard check
# ======================================================================
def check_include_guard(text: str, path: str) -> Tuple[List[str], List[str]]:
    errors = []
    warnings = []
    if not path.endswith('.h'):
        return errors, warnings

    ifndef = re.findall(r'^\s*#ifndef\s+(\w+)', text, re.MULTILINE)
    define = re.findall(r'^\s*#define\s+(\w+)', text, re.MULTILINE)
    endif = re.findall(r'^\s*#endif', text, re.MULTILINE)

    # Allow additional #ifndef for feature flags (e.g. MAX_CONSECUTIVE_PENDING_EVENTS).
    # Only the first #ifndef is expected to be the include guard.
    if not ifndef:
        warnings.append(f"No #ifndef found in {path}")
    if not endif:
        warnings.append(f"No #endif found in {path}")

    if ifndef and define:
        if ifndef[0] != define[0]:
            errors.append(
                f"Include guard mismatch in {path}: "
                f"#ifndef {ifndef[0]} vs first #define {define[0]}")
    return errors, warnings


# ======================================================================
# 3. Function decl vs def (across .c AND .h)
# ======================================================================
_RET_TYPES = (
    r'(?:void|int|bool|char|short|long|float|double|'
    r'uint\d+_t|int\d+_t|size_t|'
    r'[A-Z]\w*_t|STATE_\w+_t|EVENT_\w+_t|FLAG_t|'
    r'SystemContext_t)'
)

FUNC_DECL_RE = re.compile(
    r'^\s*(?:extern\s+)?(?:static\s+)?(?:inline\s+)?'
    + _RET_TYPES +
    r'\s+\*?\s*(\w+)\s*\([^;{]*\)\s*;',
    re.MULTILINE
)
FUNC_DEF_RE = re.compile(
    r'^\s*(?:static\s+)?(?:inline\s+)?'
    + _RET_TYPES +
    r'\s+\*?\s*(\w+)\s*\([^;{]*\)\s*\{',
    re.MULTILINE
)

# Exclude macros / keywords that look like declarations.
_EXCLUDE_NAMES = {
    'if', 'else', 'for', 'while', 'do', 'switch', 'case',
    'sizeof', 'return', 'define', 'ifndef', 'include',
}


def collect_decls_defs(root: Path
                       ) -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
    """Collect declarations (from .c AND .h) and definitions (from .c)."""
    decls: Dict[str, List[str]] = defaultdict(list)
    defs: Dict[str, List[str]] = defaultdict(list)

    for path in sorted(root.rglob('*.h')):
        text = path.read_text(encoding='utf-8', errors='replace')
        for m in FUNC_DECL_RE.finditer(text):
            name = m.group(1)
            if name in _EXCLUDE_NAMES:
                continue
            decls[name].append(str(path))

    for path in sorted(root.rglob('*.c')):
        text = path.read_text(encoding='utf-8', errors='replace')
        # Forward declarations inside .c
        for m in FUNC_DECL_RE.finditer(text):
            name = m.group(1)
            if name in _EXCLUDE_NAMES:
                continue
            decls[name].append(str(path))
        # Definitions
        for m in FUNC_DEF_RE.finditer(text):
            name = m.group(1)
            if name in _EXCLUDE_NAMES:
                continue
            defs[name].append(str(path))

    return decls, defs


# ======================================================================
# 4. Duplicate typedef
# ======================================================================
TYPEDEF_RE = re.compile(r'typedef\s+.*?\}\s*(\w+)\s*;', re.DOTALL)


def check_duplicate_typedefs(root: Path) -> Tuple[List[str], List[str]]:
    errors = []
    warnings = []
    type_locations: Dict[str, List[str]] = defaultdict(list)
    for path in sorted(root.rglob('*.h')):
        text = path.read_text(encoding='utf-8', errors='replace')
        for m in TYPEDEF_RE.finditer(text):
            type_locations[m.group(1)].append(str(path))
    for tname, locs in type_locations.items():
        if len(locs) > 1:
            warnings.append(
                f"Duplicate typedef '{tname}' in: {', '.join(locs)}")
    return errors, warnings


# ======================================================================
# 5. Japanese character check
# ======================================================================
JP_RE = re.compile(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]')


def check_japanese(root: Path) -> List[str]:
    found = []
    for path in sorted(root.rglob('*')):
        if path.is_dir():
            continue
        if path.suffix not in ('.c', '.h'):
            continue
        text = path.read_text(encoding='utf-8', errors='replace')
        for i, line in enumerate(text.splitlines(), 1):
            if JP_RE.search(line):
                found.append(f"{path}:{i}: {line.strip()[:80]}")
    return found


# ======================================================================
# 6. Known-issue detection
# ======================================================================
def check_nested_duplicate(root: Path) -> List[str]:
    """Detect duplicate transition blocks inside one cell function."""
    issues = []
    for path in sorted(root.rglob('statable_transitions_*.c')):
        text = path.read_text(encoding='utf-8', errors='replace')
        # Find each cell function body (static ... t_xxx(...) { ... })
        for m in re.finditer(
            r'static\s+\w+\s+t_\w+\s*\([^)]*\)\s*\{(.*?)\n\}',
            text, re.DOTALL
        ):
            body = m.group(1)
            labels = re.findall(r'Transition\[(\w+)\]', body)
            seen = set()
            dup = []
            for lbl in labels:
                if lbl in seen:
                    dup.append(lbl)
                seen.add(lbl)
            if dup:
                issues.append(
                    f"{path}: duplicate transition block(s) {dup} in one cell")
    return issues


def check_custom_t_doubling(root: Path) -> List[str]:
    """Detect '_t_t' doubled typedef names."""
    issues = []
    pattern = re.compile(r'\b(\w+)_t_t\b')
    for path in sorted(root.rglob('*.h')):
        text = path.read_text(encoding='utf-8', errors='replace')
        for m in pattern.finditer(text):
            issues.append(
                f"{path}: doubled '_t_t' typedef: '{m.group(0)}'")
    return issues


# ======================================================================
# Main
# ======================================================================
def analyze_file(path: Path) -> FileReport:
    report = FileReport(path)
    text = path.read_text(encoding='utf-8', errors='replace')

    errs, warns = check_balance(text, str(path))
    report.errors.extend(errs)
    report.warnings.extend(warns)

    errs, warns = check_include_guard(text, str(path))
    report.errors.extend(errs)
    report.warnings.extend(warns)

    return report


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", default="output")
    p.add_argument("--verbose", action="store_true")
    args = p.parse_args()

    root = Path(args.root)
    if not root.exists():
        print(f"ERROR: {root} not found")
        return 1

    print("=" * 70)
    print(f"  Verify generated C code: {root}")
    print("=" * 70)

    files = sorted(root.rglob('*.c')) + sorted(root.rglob('*.h'))
    print(f"\nTarget: {len(files)} file(s)\n")

    all_errors = 0
    all_warnings = 0

    # --- 1. Per-file checks ---
    for f in files:
        rep = analyze_file(f)
        if rep.has_errors() or rep.warnings:
            print(f"--- {f.relative_to(root)} ---")
            for e in rep.errors:
                print(f"  [ERROR] {e}")
                all_errors += 1
            for w in rep.warnings:
                print(f"  [WARN]  {w}")
                all_warnings += 1

    print()
    print("=" * 70)
    print("  Cross-file checks")
    print("=" * 70)

    # --- 2. Decl vs Def (across .c AND .h) ---
    decls, defs = collect_decls_defs(root)
    undefined = []
    for fn in defs:
        if fn in decls:
            continue
        # skip known acceptable cases (main etc.)
        if fn in ('main',):
            continue
        undefined.append(fn)

    if undefined:
        print(f"\n[WARN] Functions defined but not declared:")
        for f in sorted(undefined):
            print(f"  {f}  ({defs[f][0]})")
        all_warnings += len(undefined)
    else:
        print("\n[OK] All defined functions have a declaration")

    # --- 3. Duplicate typedefs ---
    _, dup_warnings = check_duplicate_typedefs(root)
    if dup_warnings:
        print(f"\n[WARN] Duplicate typedefs:")
        for w in dup_warnings[:10]:
            print(f"  {w}")
        all_warnings += len(dup_warnings)
    else:
        print("[OK] No duplicate typedefs")

    # --- 4. Japanese ---
    jp = check_japanese(root)
    if jp:
        print(f"\n[ERROR] Japanese characters found ({len(jp)}):")
        for j in jp[:20]:
            print(f"  {j}")
        all_errors += len(jp)
    else:
        print("\n[OK] No Japanese characters")

    # --- 5. Nested group duplicate ---
    p3 = check_nested_duplicate(root)
    if p3:
        print(f"\n[ERROR] Nested group duplicate detected:")
        for i in p3:
            print(f"  {i}")
        all_errors += len(p3)
    else:
        print("[OK] No nested group duplicate")

    # --- 6. Custom type _t_t ---
    p7 = check_custom_t_doubling(root)
    if p7:
        print(f"\n[ERROR] Custom type _t_t doubled:")
        for i in p7:
            print(f"  {i}")
        all_errors += len(p7)
    else:
        print("[OK] No doubled _t_t typedefs")

    print()
    print("=" * 70)
    print(f"  TOTAL: errors={all_errors}, warnings={all_warnings}")
    print("=" * 70)

    return 0 if all_errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())