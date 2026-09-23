#!/usr/bin/env python3
"""
P12-10 Comprehensive validation for StaTable v2.2.5 (v8).

Primary target: by_layer (the only configuration used in production).

Tracks:
  Track 1: Real C syntax parsing (pycparser)  -- by_layer only
  Track 2: Symbol table validation            -- all structures
  Track 3: folder_structure coverage          -- file generation checks

Run:  python tests/test_v2_2_p12_10.py
"""

import os
import re
import sys
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

XML_PATH = PROJECT_ROOT / "tests" / "data" / "v22_features_test3.xml"


# ======================================================================
# Harness
# ======================================================================
class Result:
    def __init__(self):
        self.passed = 0; self.failed = 0; self.skipped = 0; self.errors = []

    def ok(self, n): self.passed += 1; print(f"  [PASS] {n}")
    def fail(self, n, msg=""):
        self.failed += 1; self.errors.append((n, msg))
        print(f"  [FAIL] {n}")
        if msg:
            for line in str(msg).splitlines():
                print(f"         {line}")
    def skip(self, n, r=""):
        self.skipped += 1; print(f"  [SKIP] {n}")
        if r: print(f"         {r}")

    def summary(self):
        t = self.passed + self.failed + self.skipped
        print()
        print("=" * 70)
        print(f"  TOTAL: {t}  PASSED: {self.passed}  "
              f"FAILED: {self.failed}  SKIPPED: {self.skipped}")
        print("=" * 70)
        if self.errors:
            print("\nFailures:")
            for n, _ in self.errors: print(f"  - {n}")
        return self.failed == 0


R = Result()
def check(name, cond, msg=""):
    if cond: R.ok(name); return True
    R.fail(name, msg); return False


# ======================================================================
# Text utilities
# ======================================================================
def normalize_newlines(t):
    return t.replace('\r\n', '\n').replace('\r', '\n')

def join_line_continuations(t):
    return re.sub(r'\\[ \t]*\n', '', t)

def strip_comments(t):
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
        if c == '"':
            out.append(c); i += 1
            while i < n:
                out.append(t[i])
                if t[i] == '\\' and i+1 < n:
                    out.append(t[i+1]); i += 2; continue
                if t[i] == '"': i += 1; break
                i += 1
            continue
        out.append(c); i += 1
    return ''.join(out)

def strip_preprocessor(t):
    return re.sub(r'^[ \t]*#.*$', '', t, flags=re.MULTILINE)

def clean(t):
    t = normalize_newlines(t)
    t = join_line_continuations(t)
    t = strip_comments(t)
    t = strip_preprocessor(t)
    return t


# ======================================================================
# Track 2 - symbol extraction
# ======================================================================
C_KEYWORDS = {
    'return','if','while','for','switch','case','do','else','goto','break',
    'continue','sizeof','typedef','struct','union','enum','extern','static',
    'inline','const','volatile','unsigned','signed','long','short','void',
    'int','char','float','double',
}
NOISE_NAMES = {'func', 'fn', 'cb', 'cbk', 'user'}

# v8: \s* between ) and ;/{ allows newline (e.g. `)\n{`)
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


def extract_symbols(files):
    S = {'decls': defaultdict(set), 'defs': defaultdict(set)}
    for fname, content in files.items():
        c = clean(content)
        for m in SIG_RE.finditer(c):
            name = m.group('name')
            if name in C_KEYWORDS or name in NOISE_NAMES or len(name) < 3:
                continue
            prefix = (m.group('prefix') or '').strip()
            is_static = 'static' in prefix
            if m.group('end') == ';':
                S['decls'][name].add((fname, is_static))
            else:
                S['defs'][name].add((fname, is_static))
    return S


def check_symbols(S, files, structure):
    print(f"\n--- [{structure}] Track 2: Symbol table ---")

    # 1. Functions declared in headers must be defined
    header_decls = {n for n, entries in S['decls'].items()
                    if any(f.endswith('.h') for f, _ in entries)}
    defined_names = set(S['defs'].keys())
    missing = sorted(header_decls - defined_names)
    check(f"[{structure}] all header-declared funcs have definitions",
          not missing,
          f"missing {len(missing)}: {missing[:8]}")

    # 2. Duplicate NON-static definitions
    dup = []
    for n, entries in S['defs'].items():
        c_entries = [(f, s) for f, s in entries if f.endswith('.c')]
        if len(c_entries) <= 1: continue
        if all(s for _, s in c_entries): continue
        files_set = sorted({f for f, _ in c_entries})
        if len(files_set) > 1:
            dup.append((n, files_set))
    check(f"[{structure}] no duplicate non-static definitions",
          not dup, f"{len(dup)}: {dup[:3]}")

    # 3. No noise identifiers
    check(f"[{structure}] no noise identifiers in symbols",
          'func' not in S['defs'] and 'func' not in S['decls'])


# ======================================================================
# Track 1 - pycparser (by_layer only)
# ======================================================================
FAKE_HEADERS = """
typedef unsigned char uint8_t;
typedef unsigned short uint16_t;
typedef unsigned int uint32_t;
typedef unsigned long long uint64_t;
typedef signed char int8_t;
typedef short int16_t;
typedef int int32_t;
typedef long long int64_t;
typedef unsigned int size_t;
typedef _Bool bool;
"""

HEADER_ORDER = [
    'statable_types_common.h',
    'statable_types_Driver.h',
    'statable_types_Middleware.h',
    'statable_types_Application.h',
    'statable_role_functions_Driver.h',
    'statable_role_functions_Middleware.h',
    'statable_role_functions_Application.h',
    'statable_transitions_Driver.h',
    'statable_transitions_Middleware.h',
    'statable_transitions_Application.h',
    'osal.h',
]


def _sort_headers(paths):
    def key(p):
        base = os.path.basename(p)
        try:
            return (0, HEADER_ORDER.index(base))
        except ValueError:
            return (1, base)
    return sorted(paths, key=key)


def _preprocess_for_pycparser(fname, files):
    seen_content = set()
    header_block = []
    for h in _sort_headers([f for f in files if f.endswith('.h')]):
        content = clean(files[h])
        if content in seen_content:
            continue
        seen_content.add(content)
        header_block.append(content)

    c_src = files[fname]
    c_src = re.sub(r'^[ \t]*#include.*$', '', c_src, flags=re.MULTILINE)
    c_src = clean(c_src)
    c_src = re.sub(r'\bFIRE_EVENT\s*\([^()]*\)', '((void)0)', c_src)

    return FAKE_HEADERS + '\n'.join(header_block) + '\n\n' + c_src


def _dump_context(src, msg):
    m = re.search(r':(\d+):(\d+):', msg)
    if not m:
        return msg.splitlines()[0] if msg else ""
    line = int(m.group(1))
    src_lines = src.splitlines()
    lo = max(0, line - 4); hi = min(len(src_lines), line + 3)
    out = []
    for k in range(lo, hi):
        marker = ">>" if k + 1 == line else "  "
        out.append(f"  {marker} {k+1:4d}: {src_lines[k][:90]}")
    return '\n'.join(out)


def try_pycparser(files, structure):
    try:
        from pycparser import c_parser
    except ImportError:
        return False

    parser = c_parser.CParser()
    failures = []
    for fname in sorted(files):
        if not fname.endswith('.c'):
            continue
        # [R-13 follow-up] Skip OSAL implementations.  They use
        # GNU inline asm ("cpsid i" / "cpsie i" for ARM Cortex-M)
        # which pycparser cannot parse.  osal*.c are already
        # covered by verify_c_syntax.py (gcc + arm) and
        # verify_arm_link.py (real ARM link).
        if os.path.basename(fname).startswith('osal'):
            continue
        src = _preprocess_for_pycparser(fname, files)
        try:
            parser.parse(src, filename=fname)
        except Exception as e:
            msg = str(e).splitlines()[0] if str(e) else repr(e)
            failures.append((fname, msg, _dump_context(src, msg)))

    detail = ""
    if failures:
        f, m, ctx = failures[0]
        detail = f"\n  first failure: {f}\n  {m}\n{ctx}"

    check(f"[{structure}] pycparser: all .c files parse",
          not failures,
          f"{len(failures)} file(s) failed{detail}")
    return True


def heuristic_lint(files, structure):
    unbal = []
    for fname, content in files.items():
        c = strip_comments(join_line_continuations(normalize_newlines(content)))
        ok = True
        for o, cl in [('(', ')'), ('[', ']'), ('{', '}')]:
            d = 0
            for ch in c:
                if ch == o: d += 1
                elif ch == cl:
                    d -= 1
                    if d < 0: ok = False; break
            if d != 0: ok = False
            if not ok: break
        if not ok: unbal.append(fname)
    check(f"[{structure}] all files brace-balanced",
          not unbal, f"unbalanced: {unbal}")


# ======================================================================
# Track 3 - folder_structure coverage
# ======================================================================
def load_xml():
    from statable.xml_io import project_from_xml
    return project_from_xml(str(XML_PATH))


def _generate(tabs, gd, rfl, structure):
    from codegen.c_code_generator import CCodeGenerator
    from codegen.config import CodeGenerationConfig
    _, _, _, _, _, ps = load_xml()
    kwargs = {k: v for k, v in ps.items()
              if hasattr(CodeGenerationConfig, k)}
    kwargs['folder_structure'] = structure
    cfg = CodeGenerationConfig(**kwargs)
    gen = CCodeGenerator(config=cfg)
    return gen.generate_all_layers(tabs, gd, role_function_library=rfl)


def generate_single_tab(structure):
    """flat / by_type: single tab only, no library."""
    tabs, gd, _, _, _, _ = load_xml()
    sm = tabs[0][1]
    sm.layer_name = ''
    return _generate([('', sm)], gd, None, structure)


def generate_by_layer():
    """by_layer: full multi-layer data (production config)."""
    tabs, gd, rfl, _, _, _ = load_xml()
    return _generate(tabs, gd, rfl, 'by_layer')


def check_includes_resolve(files, structure):
    basenames = {os.path.basename(f) for f in files}
    rel_paths = set(files.keys())
    unresolved = []
    for fname, content in files.items():
        src_dir = os.path.dirname(fname)
        for m in re.finditer(r'^\s*#include\s+"([^"]+)"', content, re.MULTILINE):
            inc = m.group(1)
            cand = (os.path.normpath(os.path.join(src_dir, inc)).replace('\\', '/')
                    if src_dir else inc)
            if cand in rel_paths or inc in rel_paths: continue
            if os.path.basename(inc) in basenames: continue
            unresolved.append(f'{fname}: "{inc}"')
    check(f"[{structure}] local #include directives resolve",
          not unresolved,
          "unresolved:\n" + "\n".join(unresolved[:5]))


# ======================================================================
# Test drivers
# ======================================================================
def run_full(structure, files, key_files):
    """Full: Track 3 + Track 2 + Track 1."""
    check(f"[{structure}] files generated", len(files) > 0, f"got {len(files)}")
    for kf in key_files:
        check(f"[{structure}] has {kf}", kf in files)
    check_includes_resolve(files, structure)

    S = extract_symbols(files)
    check_symbols(S, files, structure)

    print(f"\n--- [{structure}] Track 1: C syntax ---")
    if not try_pycparser(files, structure):
        R.skip(f"[{structure}] pycparser unavailable")
    heuristic_lint(files, structure)


def run_light(structure, files, key_files):
    """Light: Track 3 + Track 2 only. Skip pycparser (not production config)."""
    check(f"[{structure}] files generated", len(files) > 0, f"got {len(files)}")
    for kf in key_files:
        check(f"[{structure}] has {kf}", kf in files)
    check_includes_resolve(files, structure)

    S = extract_symbols(files)
    check_symbols(S, files, structure)

    print(f"\n--- [{structure}] Track 1: C syntax ---")
    R.skip(f"[{structure}] pycparser",
           "flat/by_type are not the production configuration")
    heuristic_lint(files, structure)


def test_flat():
    print("\n" + "=" * 70)
    print("  STRUCTURE: flat (informational - not production)")
    print("=" * 70)
    try:
        files = generate_single_tab('flat')
    except Exception as e:
        check("[flat] generation succeeded", False, repr(e)); return
    run_light('flat', files, [
        'statable_types.h', 'statable_transitions.c',
        'statable_role_functions.c', 'statable_all.h'])


def test_by_type():
    print("\n" + "=" * 70)
    print("  STRUCTURE: by_type (informational - not production)")
    print("=" * 70)
    try:
        files = generate_single_tab('by_type')
    except Exception as e:
        check("[by_type] generation succeeded", False, repr(e)); return
    keys = list(files.keys())
    run_light('by_type', files, keys[:3])


def test_by_layer():
    print("\n" + "=" * 70)
    print("  STRUCTURE: by_layer (PRODUCTION)")
    print("=" * 70)
    try:
        files = generate_by_layer()
    except Exception as e:
        check("[by_layer] generation succeeded", False, repr(e)); return
    run_full('by_layer', files, [
        'Driver/statable_types_Driver.h',
        'Application/statable_transitions_Application.c',
        'statable_all.h'])


# ======================================================================
def main():
    print("=" * 70)
    print("  StaTable v2.2.5 P12-10 v8 (Tracks 1-3)")
    print("=" * 70)

    try:
        import pycparser  # noqa
        print("\n  pycparser: AVAILABLE")
    except ImportError:
        print("\n  pycparser: NOT INSTALLED")

    test_flat()
    test_by_type()
    test_by_layer()

    sys.exit(0 if R.summary() else 1)


if __name__ == "__main__":
    main()