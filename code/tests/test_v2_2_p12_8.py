#!/usr/bin/env python3
"""
P12-8 (Generated C code structural test) test suite for StaTable v2.2.5.

Verifies the generated C code's structure WITHOUT a C compiler:

  1. All 24 files are generated
  2. Every file has balanced brackets
  3. Every .h has a matching include guard
  4. No `_t_t` doubled type names
  5. No duplicate typedef across files
  6. All common prototypes are declared
  7. Pre/Post actions appear in the correct cell function
  8. Section headers are valid C block comments
  9. Generated code has zero Japanese characters
 10. ISR prototypes in statable_all.h
 11. Per-layer TransitionContext_<Layer>_t typedef exists (v2.2.5 fix)

Run:
  python tests/test_v2_2_p12_8.py
"""

import os
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

XML_PATH = PROJECT_ROOT / "tests" / "data" / "v22_features_test3.xml"


# ======================================================================
# Harness
# ======================================================================
class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def ok(self, name):
        self.passed += 1
        print(f"  [PASS] {name}")

    def fail(self, name, msg=""):
        self.failed += 1
        self.errors.append((name, msg))
        print(f"  [FAIL] {name}")
        if msg:
            print(f"         {msg}")

    def summary(self):
        total = self.passed + self.failed
        print()
        print("=" * 70)
        print(f"  TOTAL: {total}  PASSED: {self.passed}  FAILED: {self.failed}")
        print("=" * 70)
        if self.errors:
            print("\nFailures:")
            for name, msg in self.errors:
                print(f"  - {name}")
                if msg:
                    print(f"      {msg}")
        return self.failed == 0


RESULT = TestResult()


def check(name, condition, msg=""):
    if condition:
        RESULT.ok(name)
    else:
        RESULT.fail(name, msg)
    return condition


def check_contains(name, haystack, needle):
    if needle in haystack:
        RESULT.ok(name)
        return True
    RESULT.fail(name, f"expected to contain: {needle!r}")
    return False


def check_not_contains(name, haystack, needle):
    if needle not in haystack:
        RESULT.ok(name)
        return True
    RESULT.fail(name, f"should NOT contain: {needle!r}")
    return False


# ======================================================================
# Generate
# ======================================================================
def generate_files():
    from codegen.c_code_generator import CCodeGenerator
    from codegen.config import CodeGenerationConfig
    from statable.xml_io import project_from_xml

    if not XML_PATH.exists():
        print(f"ERROR: {XML_PATH} not found")
        sys.exit(1)

    tabs, gd, _, _, _, ps = project_from_xml(str(XML_PATH))
    cfg = CodeGenerationConfig(**{
        k: v for k, v in ps.items()
        if hasattr(CodeGenerationConfig, k)
    })
    gen = CCodeGenerator(config=cfg)
    return gen.generate_all_layers(tabs, gd)


# ======================================================================
# Helpers
# ======================================================================
def strip_comments_and_strings(text: str) -> str:
    """Remove // and /* */ comments and string literals."""
    out = []
    i, n = 0, len(text)
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


def check_balanced(text: str) -> bool:
    cleaned = strip_comments_and_strings(text)
    for open_c, close_c in [('(', ')'), ('[', ']'), ('{', '}')]:
        depth = 0
        for ch in cleaned:
            if ch == open_c:
                depth += 1
            elif ch == close_c:
                depth -= 1
                if depth < 0:
                    return False
        if depth != 0:
            return False
    return True


# ======================================================================
# Tests
# ======================================================================
FILES = None


def test_file_count():
    print("\n[1] File count")
    check("24 files generated", len(FILES) == 24, f"got {len(FILES)}")


def test_balanced_brackets():
    print("\n[2] Balanced brackets (all files)")
    bad = []
    for fname, content in FILES.items():
        if not check_balanced(content):
            bad.append(fname)
    check("all files balanced", not bad, f"unbalanced: {bad}")


def test_include_guards():
    print("\n[3] Include guards (headers)")
    bad = []
    for fname, content in FILES.items():
        if not fname.endswith('.h'):
            continue
        ifndef = re.findall(r'^\s*#ifndef\s+(\w+)', content, re.MULTILINE)
        endif = re.findall(r'^\s*#endif', content, re.MULTILINE)
        if not ifndef or not endif:
            bad.append(fname)
    check("all headers have guards", not bad, f"missing: {bad}")


def test_no_doubled_t():
    print("\n[4] No '_t_t' doubled type names")
    pattern = re.compile(r'\b(\w+)_t_t\b')
    bad = []
    for fname, content in FILES.items():
        for m in pattern.finditer(content):
            bad.append(f"{fname}: {m.group(0)}")
    check("no doubled _t_t", not bad, f"found: {bad[:5]}")


def test_no_duplicate_typedefs():
    print("\n[5] No duplicate typedef across headers")
    typedef_re = re.compile(r'typedef\s+.*?\}\s*(\w+)\s*;', re.DOTALL)
    locations = {}
    for fname, content in FILES.items():
        if not fname.endswith('.h'):
            continue
        for m in typedef_re.finditer(content):
            locations.setdefault(m.group(1), []).append(fname)
    dups = {k: v for k, v in locations.items() if len(v) > 1}
    check("no duplicate typedefs", not dups, f"duplicates: {list(dups.keys())}")


def test_common_prototypes():
    print("\n[6] Common prototypes in statable_types_common.h")
    common = FILES.get('statable_types_common.h', '')
    for fn in ('SystemContext_Init', 'Timer_Init', 'Timer_Update'):
        check_contains(f"has {fn}", common, f"void {fn}")
def test_pre_post_in_cell():
    print("\n[7] Pre/Post cell actions in t_Init_START")
    app_c = FILES.get(
        'Application/statable_transitions_Application.c', '')

    # Match the *definition* (not the forward declaration):
    #   static STATE_Application_t t_Init_START(...)   <- forward decl (ends with ;)
    #   static STATE_Application_t t_Init_START(...)   <- definition (followed by { )
    #                                                        ... }
    # Use `[^;]*?` inside the parens to avoid crossing `;`,
    # and require `\n{` right after the closing `)`.
    m = re.search(
        r'static\s+STATE_Application_t\s+t_Init_START\s*'
        r'\([^;]*?\)\s*\n?\s*\{.*?\n\}',
        app_c, re.DOTALL)
    if not m:
        check("t_Init_START definition found", False,
              "regex did not match the function body")
        return
    body = m.group(0)

    # Sanity: the body must contain a transition marker
    if 'Transition[' not in body:
        check("t_Init_START body contains 'Transition['", False,
              f"body snippet: {body[:200]!r}")
        return
    check("t_Init_START definition found", True)

    check_contains("has App.Pre", body, "RoleFunc_App_Pre")
    check_contains("has App.Post", body, "RoleFunc_App_Post")
    i_pre = body.find("RoleFunc_App_Pre")
    i_tr = body.find("Transition[T1]")
    i_post = body.find("RoleFunc_App_Post")
    check("Pre < Transition", 0 <= i_pre < i_tr,
          f"i_pre={i_pre}, i_tr={i_tr}")
    check("Transition < Post", 0 <= i_tr < i_post,
          f"i_tr={i_tr}, i_post={i_post}")


def test_section_headers():
    print("\n[8] Section headers are valid C block comments")
    pattern_open = re.compile(
        r'/\*={10,}\s*\n\s*\*\s+[^\n]+\n\s*\*={10,}\*/', re.MULTILINE)
    for fname, content in FILES.items():
        if '/*====' not in content:
            continue
        if not pattern_open.search(content):
            check(f"{fname}: valid section header", False,
                  "found '/*====' but no closing '*====*/' pattern")
            return
    check("all section headers valid", True)


def test_no_japanese():
    print("\n[9] No Japanese characters")
    jp = re.compile(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]')
    bad = []
    for fname, content in FILES.items():
        for i, line in enumerate(content.splitlines(), 1):
            if jp.search(line):
                bad.append(f"{fname}:{i}")
    check("no Japanese", not bad, f"found: {bad[:5]}")


def test_isr_prototypes():
    print("\n[10] ISR prototypes in statable_all.h")
    all_h = FILES.get('statable_all.h', '')
    check_contains("has ISR_TIMER0 prototype",
                   all_h, "void ISR_TIMER0(void);")


def test_layer_transition_context_typedef():
    """v2.2.5 fix: TransitionContext_<Layer>_t must exist per layer."""
    print("\n[11] Per-layer TransitionContext_<Layer>_t typedef (v2.2.5)")
    for layer in ('Driver', 'Middleware', 'Application'):
        fname = f'{layer}/statable_types_{layer}.h'
        content = FILES.get(fname, '')
        check_contains(
            f"{layer}: TransitionContext_{layer}_t typedef",
            content, f"}} TransitionContext_{layer}_t;")
        check_contains(
            f"{layer}: has STATE_{layer}_t from_state",
            content, f"STATE_{layer}_t from_state;")
        check_contains(
            f"{layer}: has EVENT_{layer}_t event",
            content, f"EVENT_{layer}_t event;")


# ======================================================================
# Main
# ======================================================================
def main():
    global FILES

    print("=" * 70)
    print("  StaTable v2.2.5 P12-8 (Generated C code structure) test suite")
    print("=" * 70)

    FILES = generate_files()

    test_file_count()
    test_balanced_brackets()
    test_include_guards()
    test_no_doubled_t()
    test_no_duplicate_typedefs()
    test_common_prototypes()
    test_pre_post_in_cell()
    test_section_headers()
    test_no_japanese()
    test_isr_prototypes()
    test_layer_transition_context_typedef()

    ok = RESULT.summary()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()