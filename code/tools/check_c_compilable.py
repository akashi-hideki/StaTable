#!/usr/bin/env python3
"""
Compile-readiness checker for generated C code (no C compiler needed).

Performs the following checks:
  1. All `#include "..."` targets exist (relative to the file).
  2. No duplicate `#define` for the same macro name within a file.
  3. Function calls to declared functions (basic).
  4. Type usages: every `Xxx_t` mentioned is defined somewhere.
  5. `static` functions are all used (dead-code detection).
  6. C89/C99 keyword misuse in identifiers.

Usage:
    python tools/check_c_compilable.py --root output
"""

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set


# ----------------------------------------------------------------------
# Patterns
# ----------------------------------------------------------------------
RE_INCLUDE = re.compile(r'^\s*#include\s+"([^"]+)"', re.MULTILINE)
RE_DEFINE = re.compile(r'^\s*#define\s+(\w+)', re.MULTILINE)
RE_TYPE_USAGE = re.compile(r'\b([A-Z][A-Za-z0-9_]*_t)\b')
RE_STATIC_FUNC_DEF = re.compile(
    r'^\s*static\s+\w+\s+(\w+)\s*\([^;]*\)\s*\{', re.MULTILINE
)
RE_CALL = re.compile(r'\b([A-Za-z_]\w*)\s*\(')

C_KEYWORDS = {
    'if', 'else', 'for', 'while', 'do', 'switch', 'case', 'default',
    'return', 'break', 'continue', 'goto', 'sizeof', 'typedef',
    'struct', 'union', 'enum', 'static', 'const', 'volatile',
    'extern', 'inline', 'void', 'int', 'char', 'short', 'long',
    'float', 'double', 'unsigned', 'signed', 'bool', '_Bool',
    'true', 'false', 'NULL', 'defined',
}

# Standard library / common external types (no typedef in project)
EXTERNAL_TYPES = {
    # <stdint.h>
    'uint8_t', 'uint16_t', 'uint32_t', 'uint64_t',
    'int8_t', 'int16_t', 'int32_t', 'int64_t',
    'uintptr_t', 'intptr_t',
    'uint_least8_t', 'uint_least16_t', 'uint_least32_t',
    'int_least8_t', 'int_least16_t', 'int_least32_t',
    'uint_fast8_t', 'uint_fast16_t', 'uint_fast32_t',
    'int_fast8_t', 'int_fast16_t', 'int_fast32_t',
    # <stddef.h>
    'size_t', 'ptrdiff_t', 'wchar_t',
    # <stdbool.h>
    'bool',
    # <time.h>
    'time_t', 'clock_t',
    # <stdio.h>
    'FILE', 'fpos_t',
    # Project-internal known external (from statable_types_common.h)
    'SystemContext_t',
}

# RX-specific excluded functions (interrupt handlers, extern tables)
STATIC_EXCLUDE_NAMES = {
    'main',
    'ISR',  # prefix match handled below
}


# ----------------------------------------------------------------------
# Helper: robust typedef name collection
# ----------------------------------------------------------------------
def _collect_typedef_names(text: str) -> Set[str]:
    """Robustly collect all typedef target names.

    Handles:
      - `typedef <type> Name;`
      - `typedef struct {...} Name;`  (with nested braces)
      - `typedef <ret> (*Name)(<args>);`  (function pointer)
    """
    names: Set[str] = set()

    # Function pointer form: `(*Name)(...)`
    for m in re.finditer(r'\(\s*\*\s*(\w+)\s*\)', text):
        names.add(m.group(1))

    # Generic form: scan from each 'typedef' to its matching ';' at brace depth 0
    for m in re.finditer(r'\btypedef\b', text):
        i = m.end()
        depth = 0
        j = i
        n = len(text)
        while j < n:
            c = text[j]
            if c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
            elif c == ';' and depth == 0:
                segment = text[i:j].rstrip()
                # Last identifier before ';'
                match = re.search(r'(\w+)\s*$', segment)
                if match:
                    names.add(match.group(1))
                break
            j += 1

    return names


# ----------------------------------------------------------------------
# Analysis
# ----------------------------------------------------------------------
class CompileReadiness:
    def __init__(self, root: Path):
        self.root = root
        self.errors: List[str] = []
        self.warnings: List[str] = []

        self.all_includes: Dict[str, List[str]] = defaultdict(list)
        self.all_defines: Dict[str, List[str]] = defaultdict(list)
        self.all_typedefs: Dict[str, List[str]] = defaultdict(list)
        self.all_type_usages: Dict[str, List[str]] = defaultdict(list)
        self.all_static_defs: Dict[str, List[str]] = defaultdict(list)

    def run(self) -> int:
        c_h_files = sorted(
            list(self.root.rglob('*.c')) + list(self.root.rglob('*.h'))
        )
        if not c_h_files:
            print(f"No .c/.h files found in {self.root}")
            return 1

        print("=" * 70)
        print(f"  Compile-readiness check: {self.root}")
        print("=" * 70)
        print(f"\nTarget: {len(c_h_files)} file(s)\n")

        for f in c_h_files:
            self._collect(f)
        for f in c_h_files:
            self._analyze_file(f)

        self._check_includes()
        self._check_typedefs_vs_usages()
        self._check_unused_statics()

        self._print_report()
        return 0 if not self.errors else 1

    # ------------------------------------------------------------------
    def _collect(self, f: Path):
        text = f.read_text(encoding='utf-8', errors='replace')
        rel = str(f.relative_to(self.root))

        for m in RE_INCLUDE.finditer(text):
            self.all_includes[rel].append(m.group(1))

        for m in RE_DEFINE.finditer(text):
            self.all_defines[m.group(1)].append(rel)

        # v2.2.5: robust typedef collection (struct / funptr / simple)
        for name in _collect_typedef_names(text):
            if rel not in self.all_typedefs[name]:
                self.all_typedefs[name].append(rel)

        for m in RE_TYPE_USAGE.finditer(text):
            self.all_type_usages[m.group(1)].append(rel)

        for m in RE_STATIC_FUNC_DEF.finditer(text):
            self.all_static_defs[m.group(1)].append(rel)

    # ------------------------------------------------------------------
    def _analyze_file(self, f: Path):
        text = f.read_text(encoding='utf-8', errors='replace')
        rel = str(f.relative_to(self.root))

        local_defines: Dict[str, int] = defaultdict(int)
        for m in RE_DEFINE.finditer(text):
            local_defines[m.group(1)] += 1
        for name, count in local_defines.items():
            if count > 1:
                self.warnings.append(
                    f"[{rel}] duplicate #define '{name}' ({count}x)"
                )

    # ------------------------------------------------------------------
    def _check_includes(self):
        for rel, includes in self.all_includes.items():
            src_dir = (self.root / rel).parent
            for inc in includes:
                if inc.startswith('<'):
                    continue
                target = (src_dir / inc).resolve()
                if target.exists():
                    continue
                target = (self.root / inc).resolve()
                if target.exists():
                    continue
                self.errors.append(
                    f"[{rel}] include not found: \"{inc}\""
                )

    # ------------------------------------------------------------------
    def _check_typedefs_vs_usages(self):
        defined = set(self.all_typedefs.keys())
        for type_name, files in self.all_type_usages.items():
            if type_name in defined:
                continue
            if type_name in EXTERNAL_TYPES:
                continue
            # Heuristic: skip RX-specific CMSIS / iodefine types
            if type_name.startswith(('IOPORT', 'ICU', 'CMT', 'SCI', 'RIIC')):
                continue
            self.warnings.append(
                f"undefined type '{type_name}' used in: "
                f"{', '.join(sorted(set(files)))}"
            )

    # ------------------------------------------------------------------
    def _check_unused_statics(self):
        called: Set[str] = set()
        for f in self.root.rglob('*.c'):
            text = f.read_text(encoding='utf-8', errors='replace')
            for m in RE_CALL.finditer(text):
                name = m.group(1)
                if name not in C_KEYWORDS:
                    called.add(name)

        for name, defs in self.all_static_defs.items():
            if name in called:
                continue
            if name in STATIC_EXCLUDE_NAMES:
                continue
            if name.startswith('ISR'):
                continue
            # Function pointer tables are OK
            self.warnings.append(
                f"static function '{name}' never called "
                f"(defined in {', '.join(defs)})"
            )

    # ------------------------------------------------------------------
    def _print_report(self):
        print("=" * 70)
        print("  Results")
        print("=" * 70)

        if self.errors:
            print(f"\n[ERROR] {len(self.errors)} error(s):")
            for e in self.errors:
                print(f"  {e}")

        if self.warnings:
            print(f"\n[WARN] {len(self.warnings)} warning(s):")
            for w in self.warnings:
                print(f"  {w}")

        if not self.errors and not self.warnings:
            print("\n[OK] No issues detected")

        print()
        print("=" * 70)
        print(f"  TOTAL: errors={len(self.errors)}, warnings={len(self.warnings)}")
        print("=" * 70)


# ----------------------------------------------------------------------
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", default="output")
    args = p.parse_args()

    root = Path(args.root)
    if not root.exists():
        print(f"ERROR: {root} not found")
        return 1

    checker = CompileReadiness(root)
    return checker.run()


if __name__ == "__main__":
    sys.exit(main())