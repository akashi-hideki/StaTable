#!/usr/bin/env python3
"""
P1 (Code merge / marker-based user code preservation) test suite.

Verifies:
  1.  New file (no existing content) -> generated content returned as-is
  2.  File-level marker: user code preserved across regeneration
  3.  Function-level marker: per-function user code preserved
  4.  Function marker naming (namespace vs bare, ISR)
  5.  Tail user section preserved
  6.  Multiple regeneration cycles (idempotent)
  7.  Modified/deleted markers -> graceful degradation
  8.  Integration with CCodeGenerator.save_generated_code_with_merge

Run:
  python tests/test_v2_4_p1_merge.py
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("STATABLE_DISABLE_MERMAID", "1")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ======================================================================
# Test harness
# ======================================================================
class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.skipped = 0
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

    def skip(self, name, reason=""):
        self.skipped += 1
        print(f"  [SKIP] {name}  ({reason})")

    def summary(self):
        total = self.passed + self.failed + self.skipped
        print()
        print("=" * 70)
        print(f"  TOTAL: {total}  PASSED: {self.passed}  "
              f"FAILED: {self.failed}  SKIPPED: {self.skipped}")
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
    RESULT.fail(name, f"expected to contain: {needle!r}\n"
                     f"--- got (first 400 chars) ---\n"
                     f"{haystack[:400]}\n"
                     f"-----------")
    return False


def check_not_contains(name, haystack, needle):
    if needle not in haystack:
        RESULT.ok(name)
        return True
    RESULT.fail(name, f"should NOT contain: {needle!r}")
    return False


# ======================================================================
# Fixtures
# ======================================================================
def sample_generated_file(marker_name="Test"):
    """A minimal generated file with all 3 marker types."""
    return f"""\
/**
 * @file    test_file.c
 * @brief   Test file
 */

#include <stdint.h>

/* [[STABLE_USER_CODE_START]] */
/* (file-level user area) */
/* [[STABLE_USER_CODE_END]] */

int RoleFunc_{marker_name}_DoThing(void)
{{
    int ret = 0;

    /* [[STABLE_USER_CODE_START:{marker_name}_DoThing]] */
    /* default: do nothing */
    /* [[STABLE_USER_CODE_END:{marker_name}_DoThing]] */

    return ret;
}}

int RoleFunc_{marker_name}_Other(void)
{{
    int ret = 0;

    /* [[STABLE_USER_CODE_START:{marker_name}_Other]] */
    /* default: do nothing */
    /* [[STABLE_USER_CODE_END:{marker_name}_Other]] */

    return ret;
}}

/* [[STABLE_USER_CODE_TAIL_START]] */
/* (file-tail user area) */
/* [[STABLE_USER_CODE_TAIL_END]] */
"""


def user_edited_version(marker_name="Test"):
    """The same file, edited by the user inside markers."""
    return f"""\
/**
 * @file    test_file.c
 * @brief   Test file
 */

#include <stdint.h>

/* [[STABLE_USER_CODE_START]] */
#include "my_custom_header.h"
#define MY_MAGIC 42
/* [[STABLE_USER_CODE_END]] */

int RoleFunc_{marker_name}_DoThing(void)
{{
    int ret = 0;

    /* [[STABLE_USER_CODE_START:{marker_name}_DoThing]] */
    GPIO_SetBits(GPIOA, GPIO_Pin_5);   /* <-- USER EDIT */
    ret = 1;
    /* [[STABLE_USER_CODE_END:{marker_name}_DoThing]] */

    return ret;
}}

int RoleFunc_{marker_name}_Other(void)
{{
    int ret = 0;

    /* [[STABLE_USER_CODE_START:{marker_name}_Other]] */
    /* default: do nothing */
    /* [[STABLE_USER_CODE_END:{marker_name}_Other]] */

    return ret;
}}

/* [[STABLE_USER_CODE_TAIL_START]] */
void my_helper_function(void) {{ /* <-- USER EDIT */ }}
/* [[STABLE_USER_CODE_TAIL_END]] */
"""


# ======================================================================
# 1. Basic merge: user code preserved
# ======================================================================
def test_merge_preserves_user_code():
    print("\n[1] Basic merge: user code preserved")
    from codegen.code_merger import CodeMerger

    merger = CodeMerger()
    generated = sample_generated_file("Test")
    existing = user_edited_version("Test")

    merged = merger.merge_file(generated, existing)

    check_contains("file-level user code preserved",
                   merged, "my_custom_header.h")
    check_contains("file-level #define preserved",
                   merged, "MY_MAGIC 42")
    check_contains("function-level user code preserved",
                   merged, "GPIO_SetBits")
    check_contains("tail user code preserved",
                   merged, "my_helper_function")
    # The generated structure should remain
    check_contains("generated skeleton preserved",
                   merged, "RoleFunc_Test_DoThing")


# ======================================================================
# 2. New file (no existing content)
# ======================================================================
def test_merge_new_file():
    print("\n[2] New file: generated content returned as-is")
    from codegen.code_merger import CodeMerger

    merger = CodeMerger()
    generated = sample_generated_file("New")

    # None
    merged_none = merger.merge_file(generated, None)
    check("None existing -> generated returned",
          merged_none == generated)

    # Empty string
    merged_empty = merger.merge_file(generated, "")
    check("Empty existing -> generated returned",
          merged_empty == generated)


# ======================================================================
# 3. Non-edited existing file (no-op merge)
# ======================================================================
def test_merge_unchanged():
    print("\n[3] Unchanged existing file: merge is idempotent")
    from codegen.code_merger import CodeMerger

    merger = CodeMerger()
    generated = sample_generated_file("Test")

    # Merge generated with itself
    merged1 = merger.merge_file(generated, generated)
    check("Merge with self produces stable output",
          "RoleFunc_Test_DoThing" in merged1)

    # Merge again -> should be identical
    merged2 = merger.merge_file(merged1, merged1)
    check("Second merge identical (idempotent)",
          merged1 == merged2,
          f"lengths: {len(merged1)} vs {len(merged2)}")


# ======================================================================
# 4. Function marker naming
# ======================================================================
def test_function_marker_names():
    print("\n[4] Function marker naming (namespace vs bare)")
    from codegen.code_merger import CodeMerger

    merger = CodeMerger()

    # Namespace-style: RoleFunc_Driver_Init -> Driver_Init
    generated = (
        "int RoleFunc_Driver_Init(void)\n"
        "{\n"
        "    /* [[STABLE_USER_CODE_START:Driver_Init]] */\n"
        "    /* x */\n"
        "    /* [[STABLE_USER_CODE_END:Driver_Init]] */\n"
        "    return 0;\n"
        "}\n"
    )
    existing = (
        "int RoleFunc_Driver_Init(void)\n"
        "{\n"
        "    /* [[STABLE_USER_CODE_START:Driver_Init]] */\n"
        "    /* USER: init the driver */\n"
        "    /* [[STABLE_USER_CODE_END:Driver_Init]] */\n"
        "    return 0;\n"
        "}\n"
    )
    merged = merger.merge_file(generated, existing)
    check_contains("Driver_Init marker preserved",
                   merged, "USER: init the driver")

    # Bare name: RoleFunc_Reset -> Reset
    generated2 = (
        "int RoleFunc_Reset(void)\n"
        "{\n"
        "    /* [[STABLE_USER_CODE_START:Reset]] */\n"
        "    /* x */\n"
        "    /* [[STABLE_USER_CODE_END:Reset]] */\n"
        "    return 0;\n"
        "}\n"
    )
    existing2 = (
        "int RoleFunc_Reset(void)\n"
        "{\n"
        "    /* [[STABLE_USER_CODE_START:Reset]] */\n"
        "    /* USER: reset logic */\n"
        "    /* [[STABLE_USER_CODE_END:Reset]] */\n"
        "    return 0;\n"
        "}\n"
    )
    merged2 = merger.merge_file(generated2, existing2)
    check_contains("Reset marker preserved",
                   merged2, "USER: reset logic")


# ======================================================================
# 5. Multiple regeneration cycles
# ======================================================================
def test_multiple_regenerations():
    print("\n[5] Multiple regeneration cycles (user code stays)")
    from codegen.code_merger import CodeMerger

    merger = CodeMerger()
    generated_v1 = sample_generated_file("Test")
    edited = user_edited_version("Test")

    # Cycle 1: regenerate -> preserve edit
    cycle1 = merger.merge_file(generated_v1, edited)
    check_contains("cycle 1: edit present", cycle1, "GPIO_SetBits")

    # Cycle 2: regenerate again with same generated -> still preserved
    cycle2 = merger.merge_file(generated_v1, cycle1)
    check_contains("cycle 2: edit still present",
                   cycle2, "GPIO_SetBits")

    # Cycle 3
    cycle3 = merger.merge_file(generated_v1, cycle2)
    check_contains("cycle 3: edit still present",
                   cycle3, "GPIO_SetBits")

    # File-level and tail also preserved
    check_contains("cycle 3: file-level preserved",
                   cycle3, "MY_MAGIC")
    check_contains("cycle 3: tail preserved",
                   cycle3, "my_helper_function")


# ======================================================================
# 6. Missing markers -> graceful degradation
# ======================================================================
def test_missing_markers():
    print("\n[6] Missing markers: graceful degradation")
    from codegen.code_merger import CodeMerger

    merger = CodeMerger()
    generated = sample_generated_file("Test")
    # Existing file with NO markers (old-format file)
    existing_no_markers = (
        "int RoleFunc_Test_DoThing(void)\n"
        "{\n"
        "    /* old style, no markers */\n"
        "    return 0;\n"
        "}\n"
    )
    try:
        merged = merger.merge_file(generated, existing_no_markers)
        check("merge does not crash on missing markers",
              isinstance(merged, str) and len(merged) > 0)
    except Exception as e:
        RESULT.fail("merge crashed on missing markers", str(e))
        return


# ======================================================================
# 7. Marker-mismatch (user deleted one END)
# ======================================================================
def test_marker_mismatch():
    print("\n[7] Marker mismatch: user deleted one END marker")
    from codegen.code_merger import CodeMerger

    merger = CodeMerger()
    generated = sample_generated_file("Test")
    # User deleted the END marker for Test_DoThing
    broken = (
        "int RoleFunc_Test_DoThing(void)\n"
        "{\n"
        "    /* [[STABLE_USER_CODE_START:Test_DoThing]] */\n"
        "    GPIO_SetBits(...);\n"
        "    return 0;\n"
        "}\n"
    )
    try:
        merged = merger.merge_file(generated, broken)
        check("merge does not crash on marker mismatch",
              isinstance(merged, str) and len(merged) > 0)
    except Exception as e:
        RESULT.fail("merge crashed on marker mismatch", str(e))
        return


# ======================================================================
# 8. CCodeGenerator.save_generated_code_with_merge (end-to-end)
# ======================================================================
def test_end_to_end_save_with_merge():
    print("\n[8] End-to-end: save_generated_code_with_merge")
    try:
        from codegen.c_code_generator import CCodeGenerator
        from codegen.config import CodeGenerationConfig
    except ImportError as e:
        RESULT.skip("end-to-end save_with_merge",
                    f"import failed: {e}")
        return

    from statable.state_machine import StateMachine
    from statable.model import State, Event, Transition, RoleFunction
    from statable.global_defs import GlobalDefinitions

    # Build a small state machine
    sm = StateMachine()
    sm.layer_name = "Test"
    sm.add_state(State(name="Idle"))
    sm.add_state(State(name="Active"))
    sm.add_event(Event(name="START"))
    sm.add_event(Event(name=""))
    sm.add_role_function(RoleFunction(
        name="Init", namespace="Test",
        description="", title="Init",
    ))
    sm.set_initial("Idle")
    sm.add_transition(Transition(
        source="Idle", event="START",
        target="Active", early_return=True, label="T1",
    ))

    gd = GlobalDefinitions()

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "out"
        output_dir.mkdir()

        config = CodeGenerationConfig(
            project_name="MergeTest",
            folder_structure="flat",
            output_directory=str(output_dir),
            save_with_merge=True,
        )
        gen = CCodeGenerator(config=config)
        files = gen.generate_all_layers(
            [("Test", sm)], gd,
        )
        check("generated at least 1 file", len(files) >= 1,
              f"got {len(files)}")

        # First save
        saved1 = gen.save_generated_code_with_merge(
            files, str(output_dir))
        check("first save returned files", len(saved1) >= 1)

        # Simulate user edit: find a role_functions.c file
        target = None
        for fname in saved1:
            if "role_functions" in fname and fname.endswith(".c"):
                target = Path(fname)
                break
        if target is None or not target.exists():
            RESULT.skip("user edit injection",
                        "role_functions.c not found in output")
            return

        content = target.read_text(encoding="utf-8")
        # Inject a unique user line inside the marker
        if "[[STABLE_USER_CODE_START:" in content:
            import re
            m = re.search(
                r"(/\* \[\[STABLE_USER_CODE_START:[^\]]+\]\] \*/)",
                content,
            )
            if m:
                content = content.replace(
                    m.group(1),
                    m.group(1) + "\n    /* TESTMARKER_XYZ */",
                    1,
                )
                target.write_text(content, encoding="utf-8")
                check("user edit injected", "TESTMARKER_XYZ" in content)
            else:
                RESULT.skip("user edit injection",
                            "no function marker found")
                return
        else:
            RESULT.skip("user edit injection",
                        "no STABLE_USER_CODE_START marker")
            return

        # Second save with merge -> user edit should survive
        saved2 = gen.save_generated_code_with_merge(
            files, str(output_dir))
        target2 = None
        for fname in saved2:
            if Path(fname) == target:
                target2 = Path(fname)
                break
        if target2 is None:
            RESULT.fail("second save did not return same file",
                        f"target={target}")
            return

        after = target2.read_text(encoding="utf-8")
        check_contains("user edit survived regeneration",
                       after, "TESTMARKER_XYZ")


# ======================================================================
# 9. merge_all_files (multi-file)
# ======================================================================
def test_merge_all_files():
    print("\n[9] merge_all_files (multi-file)")
    from codegen.code_merger import CodeMerger

    merger = CodeMerger()

    with tempfile.TemporaryDirectory() as tmpdir:
        existing_dir = Path(tmpdir)
        # Create two existing files with user edits
        for name in ("a.c", "b.c"):
            (existing_dir / name).write_text(
                sample_generated_file("Test")
                .replace("/* default: do nothing */",
                         f"/* USER_{name} */"),
                encoding="utf-8",
            )

        generated = {
            "a.c": sample_generated_file("Test"),
            "b.c": sample_generated_file("Test"),
        }
        merged = merger.merge_all_files(
            generated, str(existing_dir))

        check("merge_all_files returns both files",
              "a.c" in merged and "b.c" in merged)
        check_contains("a.c user code preserved",
                       merged["a.c"], "USER_a.c")
        check_contains("b.c user code preserved",
                       merged["b.c"], "USER_b.c")


# ======================================================================
# Main
# ======================================================================
def main():
    print("=" * 70)
    print("  StaTable v2.4 P1 (Code merge) test suite")
    print("=" * 70)

    test_merge_preserves_user_code()
    test_merge_new_file()
    test_merge_unchanged()
    test_function_marker_names()
    test_multiple_regenerations()
    test_missing_markers()
    test_marker_mismatch()
    test_end_to_end_save_with_merge()
    test_merge_all_files()

    ok = RESULT.summary()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()