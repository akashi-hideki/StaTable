#!/usr/bin/env python3
"""Find where TransitionContext_<Layer>_t is defined."""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / 'output'

# Search ALL .c/.h files
targets = ['TransitionContext_Driver_t',
           'TransitionContext_Middleware_t',
           'TransitionContext_Application_t']

for t in targets:
    print("=" * 70)
    print(f"SEARCH: {t}")
    print("=" * 70)
    found_any = False
    for f in sorted(ROOT.rglob('*')):
        if f.suffix not in ('.c', '.h'):
            continue
        text = f.read_text(encoding='utf-8', errors='replace')
        if t not in text:
            continue
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if t in line:
                found_any = True
                # Show context
                lo = max(0, i - 2)
                hi = min(len(lines), i + 3)
                print(f"\n  File: {f.relative_to(ROOT)}")
                for k in range(lo, hi):
                    marker = ">>" if k == i else "  "
                    print(f"  {marker} {k+1:4d}: {lines[k]}")
    if not found_any:
        print(f"  NOT FOUND in any .c/.h file!")
    print()

# Also show _collect_typedef_names result for each layer header
print("=" * 70)
print("  _collect_typedef_names per file")
print("=" * 70)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools.check_c_compilable import _collect_typedef_names
for f in sorted(ROOT.rglob('*.h')):
    text = f.read_text(encoding='utf-8', errors='replace')
    if 'TransitionContext' not in text:
        continue
    found = _collect_typedef_names(text)
    tc = sorted(n for n in found if 'TransitionContext' in n)
    print(f"  {f.relative_to(ROOT)}: {tc}")