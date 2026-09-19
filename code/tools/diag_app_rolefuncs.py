#!/usr/bin/env python3
"""
Diagnose why RoleFunc_App_* are 'missing definitions' in P12-10 Track 2.

Shows the raw bytes / lines from the actual generated .c file
and compares with what the SIG_RE regex sees.
"""

import os
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from codegen.c_code_generator import CCodeGenerator
from codegen.config import CodeGenerationConfig
from statable.xml_io import project_from_xml

XML_PATH = PROJECT_ROOT / "tests" / "data" / "v22_features_test3.xml"


def clean(t):
    t = t.replace('\r\n', '\n').replace('\r', '\n')
    t = re.sub(r'\\[ \t]*\n', '', t)
    # strip comments (v8 compatible)
    out = []; i, n = 0, len(t)
    while i < n:
        c = t[i]
        if c == '/' and i+1 < n and t[i+1] == '*':
            j = t.find('*/', i+2)
            if j == -1: i = n
            else: out.append(' '); i = j + 2
            continue
        if c == '/' and i+1 < n and t[i+1] == '/':
            j = t.find('\n', i); i = n if j == -1 else j; continue
        out.append(c); i += 1
    t = ''.join(out)
    t = re.sub(r'^[ \t]*#.*$', '', t, flags=re.MULTILINE)
    return t


SIG_RE = re.compile(
    r'(?m)^[ \t]*'
    r'(?P<prefix>(?:(?:static|extern|inline|const|volatile'
    r'|unsigned|signed|long|short)[ \t]+)*)'
    r'(?!(?:return|if|while|for|switch|do|else|goto|break|continue)\b)'
    r'(?:[A-Za-z_]\w+[ \t]+)+?'
    r'\*?[ \t]*'
    r'(?P<name>[A-Za-z_]\w*)'
    r'[ \t]*'
    r'\((?P<args>[^;{}]*)\)'
    r'\s*'
    r'(?P<end>[;{])',
)


def main():
    tabs, gd, rfl, _, _, ps = project_from_xml(str(XML_PATH))
    kwargs = {k: v for k, v in ps.items()
              if hasattr(CodeGenerationConfig, k)}
    kwargs['folder_structure'] = 'by_layer'
    cfg = CodeGenerationConfig(**kwargs)
    gen = CCodeGenerator(config=cfg)
    files = gen.generate_all_layers(tabs, gd, role_function_library=rfl)

    # Target function to investigate
    TARGET = 'RoleFunc_App_BootEntry'

    print("=" * 72)
    print(f"  Investigating: {TARGET}")
    print("=" * 72)

    # 1. Show all files containing the name
    print(f"\n[1] Files containing '{TARGET}':")
    for fname, content in files.items():
        if TARGET in content:
            hits = content.count(TARGET)
            print(f"  {fname}: {hits} occurrence(s)")

    # 2. Show raw lines from the header
    print(f"\n[2] Raw lines from {TARGET} in .h file(s):")
    for fname, content in files.items():
        if not fname.endswith('.h'):
            continue
        if TARGET not in content:
            continue
        lines = content.replace('\r\n', '\n').splitlines()
        for i, line in enumerate(lines):
            if TARGET in line:
                print(f"  [{fname}:{i+1}] {line}")
                # Show next 2 lines to see if it's declaration or definition
                for k in range(1, 3):
                    if i + k < len(lines):
                        print(f"               +{k}: {lines[i+k]}")

    # 3. Show raw lines from the .c file
    print(f"\n[3] Raw lines from {TARGET} in .c file(s):")
    for fname, content in files.items():
        if not fname.endswith('.c'):
            continue
        if TARGET not in content:
            continue
        lines = content.replace('\r\n', '\n').splitlines()
        for i, line in enumerate(lines):
            if TARGET in line:
                print(f"  [{fname}:{i+1}] {line}")
                for k in range(1, 4):
                    if i + k < len(lines):
                        print(f"               +{k}: {lines[i+k]}")

    # 4. What does clean() see?
    print(f"\n[4] After clean():")
    for fname, content in files.items():
        if TARGET not in content:
            continue
        cleaned = clean(content)
        if TARGET in cleaned:
            # Show the region around the target
            idx = cleaned.find(TARGET)
            lo = max(0, idx - 200)
            hi = min(len(cleaned), idx + 200)
            print(f"\n  [{fname}] region around '{TARGET}':")
            print("  ---")
            for line in cleaned[lo:hi].split('\n'):
                print(f"    |{line}")
            print("  ---")

    # 5. What does SIG_RE extract?
    print(f"\n[5] SIG_RE extracted symbols for '{TARGET}':")
    extracted_decl = False
    extracted_def = False
    for fname, content in files.items():
        c = clean(content)
        for m in SIG_RE.finditer(c):
            if m.group('name') == TARGET:
                end = m.group('end')
                prefix = (m.group('prefix') or '').strip()
                print(f"  [{fname}] prefix={prefix!r} end={end!r}")
                # Show the matched text
                matched = m.group(0)
                print(f"     matched text: {matched[:120]!r}")
                if end == ';':
                    extracted_decl = True
                else:
                    extracted_def = True

    print(f"\n  Summary: decl={extracted_decl}  def={extracted_def}")

    # 6. Show ALL symbols found in the .c file for reference
    print(f"\n[6] All symbols SIG_RE finds in Application .c files:")
    for fname in sorted(files.keys()):
        if 'Application' not in fname or not fname.endswith('.c'):
            continue
        c = clean(files[fname])
        defs = []
        for m in SIG_RE.finditer(c):
            if m.group('end') == '{':
                defs.append(m.group('name'))
        print(f"  [{fname}] {len(defs)} definitions:")
        for d in defs[:30]:
            print(f"    {d}")


if __name__ == "__main__":
    main()