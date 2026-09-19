#!/usr/bin/env python3
"""
Locate which codegen module emits statable_types_<Layer>.h
and where TransitionContext_<Layer>_t should be added.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CODEGEN = ROOT / 'codegen'

print("=" * 72)
print("  Diagnostic: locate the emitter of statable_types_<Layer>.h")
print("=" * 72)

# ----------------------------------------------------------------------
# 1. Find files referencing 'statable_types' filename
# ----------------------------------------------------------------------
print("\n[1] Files referencing 'statable_types' as a filename")
print("-" * 72)
for f in sorted(CODEGEN.rglob('*.py')):
    text = f.read_text(encoding='utf-8', errors='replace')
    hits = []
    for m in re.finditer(r'statable_types', text):
        line_no = text[:m.start()].count('\n') + 1
        line = text.splitlines()[line_no - 1].strip()
        hits.append((line_no, line))
    if hits:
        print(f"\n  {f.relative_to(ROOT)}")
        for ln, line in hits[:8]:
            print(f"    L{ln}: {line}")

# ----------------------------------------------------------------------
# 2. Find files that mention 'STATE_' enum generation
# ----------------------------------------------------------------------
print("\n[2] Files generating STATE_<Layer>_ or EVENT_<Layer>_ enums")
print("-" * 72)
for f in sorted(CODEGEN.rglob('*.py')):
    text = f.read_text(encoding='utf-8', errors='replace')
    if 'STATE_' in text and ('enum' in text.lower() or 'typedef' in text.lower()):
        # Count occurrences
        n_state = text.count('STATE_')
        n_event = text.count('EVENT_')
        n_typedef = text.count('typedef')
        print(f"  {f.relative_to(ROOT)}: STATE_={n_state}, EVENT_={n_event}, typedef={n_typedef}")

# ----------------------------------------------------------------------
# 3. Find files that mention 'TransitionContext'
# ----------------------------------------------------------------------
print("\n[3] Files mentioning 'TransitionContext'")
print("-" * 72)
for f in sorted(CODEGEN.rglob('*.py')):
    text = f.read_text(encoding='utf-8', errors='replace')
    if 'TransitionContext' in text:
        lines = text.splitlines()
        print(f"\n  {f.relative_to(ROOT)}")
        for i, line in enumerate(lines, 1):
            if 'TransitionContext' in line:
                print(f"    L{i}: {line.strip()}")

# ----------------------------------------------------------------------
# 4. Find functions that produce 'statable_types' header body
# ----------------------------------------------------------------------
print("\n[4] Functions emitting the type header")
print("-" * 72)
for f in sorted(CODEGEN.rglob('*.py')):
    text = f.read_text(encoding='utf-8', errors='replace')
    # Look for function defs near "statable_types" or "Layer-specific"
    for m in re.finditer(
            r'def\s+(\w+)\s*\([^)]*\)[^:]*:',
            text, re.DOTALL):
        func_name = m.group(1)
        # Get the function body (until next def at same indent)
        start = m.end()
        # find next 'def ' at column 0 or 4
        next_def = re.search(r'\n(?=def |    def )', text[start:])
        end = start + next_def.start() if next_def else len(text)
        body = text[start:end]
        if 'statable_types' in body or ('STATE_' in body and 'typedef enum' in body):
            line_no = text[:m.start()].count('\n') + 1
            print(f"  {f.relative_to(ROOT)}: {func_name}() at L{line_no}")

# ----------------------------------------------------------------------
# 5. Search for where TransitionContext_t (common) is emitted
# ----------------------------------------------------------------------
print("\n[5] Where is TransitionContext_t (common) emitted?")
print("-" * 72)
for f in sorted(CODEGEN.rglob('*.py')):
    text = f.read_text(encoding='utf-8', errors='replace')
    if 'TransitionContext_t' in text or 'Generic transition context' in text:
        for i, line in enumerate(text.splitlines(), 1):
            if 'TransitionContext_t' in line or 'Generic transition context' in line:
                print(f"  {f.relative_to(ROOT)}:L{i}: {line.strip()}")

# ----------------------------------------------------------------------
# 6. Check generated header for comparison
# ----------------------------------------------------------------------
print("\n[6] Compare: what's IN the generated header vs. what's expected")
print("-" * 72)
h = ROOT / 'output' / 'Application' / 'statable_types_Application.h'
if h.exists():
    text = h.read_text(encoding='utf-8')
    has_state = 'STATE_Application_t' in text
    has_event = 'EVENT_Application_t' in text
    has_ctx = 'TransitionContext_Application_t' in text
    print(f"  STATE_Application_t: {'YES' if has_state else 'NO'}")
    print(f"  EVENT_Application_t: {'YES' if has_event else 'NO'}")
    print(f"  TransitionContext_Application_t: {'YES' if has_ctx else 'NO'}  ← should be YES")
else:
    print(f"  {h} not found")

# ----------------------------------------------------------------------
# 7. Summary
# ----------------------------------------------------------------------
print("\n" + "=" * 72)
print("  SUMMARY: Share these files for the fix")
print("=" * 72)
candidates = set()
for f in sorted(CODEGEN.rglob('*.py')):
    text = f.read_text(encoding='utf-8', errors='replace')
    score = 0
    if 'statable_types' in text: score += 3
    if 'STATE_' in text and 'typedef enum' in text: score += 2
    if 'EVENT_' in text and 'typedef enum' in text: score += 1
    if 'TransitionContext' in text: score += 2
    if score >= 3:
        candidates.add((score, f.relative_to(ROOT)))

for score, path in sorted(candidates, reverse=True):
    print(f"  score={score}: {path}")