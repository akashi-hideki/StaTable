#!/usr/bin/env python3
"""StaTable v2.5 P3 (user-editable (void) suppression) test suite.

Verifies:
  - The ctx->data (void) suppression block is emitted INSIDE the
    user-code marker (not in the auto-generated region)
  - Declaration-only version of _generate_local_data_pointers
  - Merge preserves user-deleted (void) lines across regeneration

API note:
  CodeMerger.merge_file(generated_content, existing_content)
    - generated_content : freshly generated text
    - existing_content  : previous file content (may be None)
    - returns           : merged text

Run:
  python tests/test_v2_5_p3.py
"""

import os
import sys
from pathlib import Path

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


R = TestResult()


def check(name, cond, msg=""):
    if cond:
        R.ok(name)
    else:
        R.fail(name, msg)
    return cond


# ======================================================================
# Fixtures
# ======================================================================
def make_role():
    from statable.model import RoleFunction
    return RoleFunction(
        name="AccumulatePayment", namespace="Middleware",
        title="Accumulate payment", description="Add coin to balance",
    )


def make_gd():
    from statable.global_defs import GlobalDefinitions, SystemVariable
    gd = GlobalDefinitions()
    gd.variables = [
        SystemVariable(name="balance", type="uint32_t", group="System"),
        SystemVariable(name="price", type="uint32_t", group="System"),
        SystemVariable(name="stock", type="uint8_t", group="System"),
    ]
    return gd


def make_gen():
    from codegen.role_function_generator import RoleFunctionGenerator
    gen = RoleFunctionGenerator()
    gen.set_layer("Middleware")
    return gen


# ======================================================================
# [1] _generate_local_data_decls: declarations only, no (void)
# ======================================================================
def test_decls_only():
    print("\n[1] _generate_local_data_decls")

    gen = make_gen()
    gd = make_gd()
    out = gen._generate_local_data_decls(gd)

    check("has local_data_header",
          "local pointer to ctx->data" in out, f"got:\n{out}")
    check("has balance declaration",
          "&ctx->data.balance" in out, f"got:\n{out}")
    check("has price declaration",
          "&ctx->data.price" in out, f"got:\n{out}")
    check("has stock declaration",
          "&ctx->data.stock" in out, f"got:\n{out}")
    check("no (void)balance",
          "(void)balance" not in out, f"got:\n{out}")
    check("no (void)price",
          "(void)price" not in out, f"got:\n{out}")
    check("no suppress unused warning comment",
          "suppress unused warning" not in out, f"got:\n{out}")


# ======================================================================
# [2] _generate_local_data_suppress: only (void) lines + header
# ======================================================================
def test_suppress_only():
    print("\n[2] _generate_local_data_suppress")

    gen = make_gen()
    gd = make_gd()
    out = gen._generate_local_data_suppress(gd)

    check("has explanatory comment",
          "auto-generated: unused-variable suppression" in out,
          f"got:\n{out}")
    check("has Delete hint",
          "Delete each (void) line" in out, f"got:\n{out}")
    check("has (void)balance", "(void)balance" in out, f"got:\n{out}")
    check("has (void)price", "(void)price" in out, f"got:\n{out}")
    check("has (void)stock", "(void)stock" in out, f"got:\n{out}")
    check("no declaration",
          "&ctx->data.balance" not in out, f"got:\n{out}")


# ======================================================================
# [3] _generate_local_data_pointers (legacy wrapper) delegates to _decls
# ======================================================================
def test_legacy_wrapper():
    print("\n[3] _generate_local_data_pointers (legacy wrapper)")

    gen = make_gen()
    gd = make_gd()
    out = gen._generate_local_data_pointers(gd)

    check("has balance declaration (legacy still works)",
          "&ctx->data.balance" in out, f"got:\n{out}")
    check("legacy wrapper no longer emits (void)balance",
          "(void)balance" not in out, f"got:\n{out}")


# ======================================================================
# [4] generate_implementation: (void) inside user marker
# ======================================================================
def test_implementation_layout():
    print("\n[4] generate_implementation layout")

    gen = make_gen()
    gd = make_gd()
    rf = make_role()

    out = gen.generate_implementation(
        rf, global_defs=gd, call_sites=[], include_transition_id=False,
    )

    i_decl = out.find("&ctx->data.balance")
    i_marker_start = out.find(
        "STABLE_USER_CODE_START:Middleware_AccumulatePayment")
    i_suppress_comment = out.find(
        "auto-generated: unused-variable suppression")
    i_void_balance = out.find("(void)balance")
    i_marker_end = out.find(
        "STABLE_USER_CODE_END:Middleware_AccumulatePayment")

    check("declaration before user marker",
          0 < i_decl < i_marker_start,
          f"indices: decl={i_decl}, start={i_marker_start}")

    check("suppress comment inside marker",
          i_marker_start < i_suppress_comment < i_marker_end,
          f"indices: start={i_marker_start}, "
          f"comment={i_suppress_comment}, end={i_marker_end}")

    check("(void)balance inside marker",
          i_marker_start < i_void_balance < i_marker_end,
          f"indices: start={i_marker_start}, "
          f"void={i_void_balance}, end={i_marker_end}")

    check("no (void)balance before marker",
          "(void)balance" not in out[:i_marker_start],
          f"prefix:\n{out[:i_marker_start]}")


# ======================================================================
# [5] Merge preserves user-deleted (void) lines
# ======================================================================
def test_merge_preserves_deletion():
    print("\n[5] Merge preserves user-deleted (void) lines")

    from codegen.code_merger import CodeMerger
    gen = make_gen()
    gd = make_gd()
    rf = make_role()

    # Step 1: first-generation output (with (void)balance)
    generated = gen.generate_implementation(
        rf, global_defs=gd, call_sites=[], include_transition_id=False,
    )
    check("first generation has (void)balance",
          "(void)balance" in generated)

    # Step 2: simulate user deletion of the (void)balance line
    user_edited = generated.replace(
        "    (void)balance;   /* suppress unused warning */\n", "")
    check("user edit removed (void)balance",
          "(void)balance" not in user_edited)

    # Step 3: merge regenerated version with user-edited content.
    #   API: merge_file(generated_content, existing_content)
    merger = CodeMerger()
    merged = merger.merge_file(generated, user_edited)

    # Step 4: user deletion should be preserved
    check("merge preserved user deletion",
          "(void)balance" not in merged,
          f"merged still contains (void)balance:\n"
          f"{merged[:1500]}")

    # (void)price should still be present (not deleted by user)
    check("merge kept other (void) lines",
          "(void)price" in merged,
          f"merged missing (void)price")


# ======================================================================
# [6] Merge is idempotent when nothing changed
# ======================================================================
def test_merge_idempotent():
    print("\n[6] Merge is idempotent (no user edits)")

    from codegen.code_merger import CodeMerger
    gen = make_gen()
    gd = make_gd()
    rf = make_role()

    generated = gen.generate_implementation(
        rf, global_defs=gd, call_sites=[], include_transition_id=False,
    )

    merger = CodeMerger()
    merged1 = merger.merge_file(generated, generated)
    merged2 = merger.merge_file(generated, merged1)

    check("merge with self produces stable output",
          "(void)balance" in merged1)
    check("second merge identical (idempotent)",
          merged1 == merged2,
          f"len(merged1)={len(merged1)}, len(merged2)={len(merged2)}")


# ======================================================================
# Main
# ======================================================================
def main():
    print("=" * 70)
    print("  StaTable v2.5 P3 (user-editable (void) suppression)")
    print("=" * 70)

    test_decls_only()
    test_suppress_only()
    test_legacy_wrapper()
    test_implementation_layout()
    test_merge_preserves_deletion()
    test_merge_idempotent()

    ok = R.summary()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()