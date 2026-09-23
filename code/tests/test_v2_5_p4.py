#!/usr/bin/env python3
"""StaTable v2.6 / R-10 (all (void) suppressions in user marker) test suite.

Verifies:
  - from_state / event / transition_id / ctx (or ctx->data.*) (void)
    lines are emitted INSIDE the user-code marker
  - Declarations remain OUTSIDE the marker
  - Merge preserves user-deleted (void) lines across regeneration
  - Idempotency

Run:
  python tests/test_v2_5_p4.py
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


def make_gd_empty():
    from statable.global_defs import GlobalDefinitions
    gd = GlobalDefinitions()
    gd.variables = []
    return gd


def make_gen():
    from codegen.role_function_generator import RoleFunctionGenerator
    gen = RoleFunctionGenerator()
    gen.set_layer("Middleware")
    return gen


# ======================================================================
# [1] _generate_local_transition_members: no (void)
# ======================================================================
def test_transition_members_no_suppress():
    print("\n[1] _generate_local_transition_members (no (void))")

    gen = make_gen()
    out = gen._generate_local_transition_members()

    check("has from_state decl",
          "STATE_Middleware_t from_state" in out, f"got:\n{out}")
    check("has event decl",
          "EVENT_Middleware_t event" in out, f"got:\n{out}")
    check("has null guard",
          "if (transition != NULL)" in out, f"got:\n{out}")
    check("no (void)from_state",
          "(void)from_state" not in out, f"got:\n{out}")
    check("no (void)event",
          "(void)event" not in out, f"got:\n{out}")


# ======================================================================
# [2] _generate_local_transition_id: no (void)
# ======================================================================
def test_transition_id_no_suppress():
    print("\n[2] _generate_local_transition_id (no (void))")

    gen = make_gen()
    rf = make_role()
    out = gen._generate_local_transition_id(rf, has_call_sites=False)

    check("has transition_id decl",
          "const uint16_t transition_id" in out, f"got:\n{out}")
    check("no (void)transition_id",
          "(void)transition_id" not in out, f"got:\n{out}")


# ======================================================================
# [3] _generate_local_data_suppress: covers all
# ======================================================================
def test_suppress_block_with_data():
    print("\n[3] _generate_local_data_suppress (with data pointers)")

    gen = make_gen()
    gd = make_gd()
    out = gen._generate_local_data_suppress(gd, include_transition_id=True)

    check("has (void)from_state", "(void)from_state" in out, f"got:\n{out}")
    check("has (void)event", "(void)event" in out, f"got:\n{out}")
    check("has (void)transition_id",
          "(void)transition_id" in out, f"got:\n{out}")
    check("has (void)balance", "(void)balance" in out, f"got:\n{out}")
    check("has (void)price", "(void)price" in out, f"got:\n{out}")
    check("has (void)stock", "(void)stock" in out, f"got:\n{out}")
    check("no (void)ctx (has data pointers)",
          "(void)ctx" not in out, f"got:\n{out}")


def test_suppress_block_without_data():
    print("\n[3b] _generate_local_data_suppress (no data pointers)")

    gen = make_gen()
    gd = make_gd_empty()
    out = gen._generate_local_data_suppress(gd, include_transition_id=True)

    check("has (void)from_state", "(void)from_state" in out, f"got:\n{out}")
    check("has (void)event", "(void)event" in out, f"got:\n{out}")
    check("has (void)transition_id",
          "(void)transition_id" in out, f"got:\n{out}")
    check("has (void)ctx", "(void)ctx" in out, f"got:\n{out}")
    check("no (void)balance",
          "(void)balance" not in out, f"got:\n{out}")


def test_suppress_block_no_transition_id():
    print("\n[3c] _generate_local_data_suppress (no transition_id)")

    gen = make_gen()
    gd = make_gd()
    out = gen._generate_local_data_suppress(gd, include_transition_id=False)

    check("has (void)from_state", "(void)from_state" in out, f"got:\n{out}")
    check("has (void)event", "(void)event" in out, f"got:\n{out}")
    check("no (void)transition_id",
          "(void)transition_id" not in out, f"got:\n{out}")


# ======================================================================
# [4] generate_implementation: all (void) inside marker
# ======================================================================
def test_implementation_layout():
    print("\n[4] generate_implementation layout")

    gen = make_gen()
    gd = make_gd()
    rf = make_role()

    out = gen.generate_implementation(
        rf, global_defs=gd, call_sites=[], include_transition_id=True,
    )

    i_decl = out.find("STATE_Middleware_t from_state")
    i_id_decl = out.find("const uint16_t transition_id")
    i_marker_start = out.find(
        "STABLE_USER_CODE_START:Middleware_AccumulatePayment")
    i_void_from = out.find("(void)from_state")
    i_void_event = out.find("(void)event")
    i_void_tid = out.find("(void)transition_id")
    i_void_balance = out.find("(void)balance")
    i_marker_end = out.find(
        "STABLE_USER_CODE_END:Middleware_AccumulatePayment")

    check("from_state decl before marker",
          0 < i_decl < i_marker_start,
          f"indices: decl={i_decl}, start={i_marker_start}")

    check("transition_id decl before marker",
          0 < i_id_decl < i_marker_start,
          f"indices: id_decl={i_id_decl}, start={i_marker_start}")

    check("(void)from_state inside marker",
          i_marker_start < i_void_from < i_marker_end,
          f"indices: start={i_marker_start}, "
          f"void={i_void_from}, end={i_marker_end}")

    check("(void)event inside marker",
          i_marker_start < i_void_event < i_marker_end,
          f"indices: start={i_marker_start}, "
          f"void={i_void_event}, end={i_marker_end}")

    check("(void)transition_id inside marker",
          i_marker_start < i_void_tid < i_marker_end,
          f"indices: start={i_marker_start}, "
          f"void={i_void_tid}, end={i_marker_end}")

    check("(void)balance inside marker",
          i_marker_start < i_void_balance < i_marker_end,
          f"indices: start={i_marker_start}, "
          f"void={i_void_balance}, end={i_marker_end}")

    # No (void) lines before the marker
    prefix = out[:i_marker_start]
    check("no (void)from_state before marker",
          "(void)from_state" not in prefix)
    check("no (void)event before marker",
          "(void)event" not in prefix)
    check("no (void)transition_id before marker",
          "(void)transition_id" not in prefix)


# ======================================================================
# [5] Merge preserves user-deleted (void) lines
# ======================================================================
def test_merge_preserves_deletion():
    print("\n[5] Merge preserves user-deleted (void) lines")

    from codegen.code_merger import CodeMerger
    gen = make_gen()
    gd = make_gd()
    rf = make_role()

    generated = gen.generate_implementation(
        rf, global_defs=gd, call_sites=[], include_transition_id=True,
    )
    check("first generation has (void)from_state",
          "(void)from_state" in generated)
    check("first generation has (void)balance",
          "(void)balance" in generated)

    user_edited = generated.replace(
        "    (void)from_state;   /* suppress unused warning */\n", "")
    user_edited = user_edited.replace(
        "    (void)balance;   /* suppress unused warning */\n", "")
    check("user edit removed (void)from_state",
          "(void)from_state" not in user_edited)
    check("user edit removed (void)balance",
          "(void)balance" not in user_edited)

    merger = CodeMerger()
    merged = merger.merge_file(generated, user_edited)

    check("merge preserved (void)from_state deletion",
          "(void)from_state" not in merged,
          f"merged still contains (void)from_state")
    check("merge preserved (void)balance deletion",
          "(void)balance" not in merged,
          f"merged still contains (void)balance")
    check("merge kept (void)event",
          "(void)event" in merged)
    check("merge kept (void)transition_id",
          "(void)transition_id" in merged)
    check("merge kept (void)price",
          "(void)price" in merged)


# ======================================================================
# [6] Merge idempotent
# ======================================================================
def test_merge_idempotent():
    print("\n[6] Merge is idempotent (no user edits)")

    from codegen.code_merger import CodeMerger
    gen = make_gen()
    gd = make_gd()
    rf = make_role()

    generated = gen.generate_implementation(
        rf, global_defs=gd, call_sites=[], include_transition_id=True,
    )

    merger = CodeMerger()
    merged1 = merger.merge_file(generated, generated)
    merged2 = merger.merge_file(generated, merged1)

    check("merge with self produces stable output",
          "(void)from_state" in merged1)
    check("second merge identical (idempotent)",
          merged1 == merged2,
          f"len(merged1)={len(merged1)}, len(merged2)={len(merged2)}")


# ======================================================================
# Main
# ======================================================================
def main():
    print("=" * 70)
    print("  StaTable v2.6 / R-10 (all (void) suppressions in user marker)")
    print("=" * 70)

    test_transition_members_no_suppress()
    test_transition_id_no_suppress()
    test_suppress_block_with_data()
    test_suppress_block_without_data()
    test_suppress_block_no_transition_id()
    test_implementation_layout()
    test_merge_preserves_deletion()
    test_merge_idempotent()

    ok = R.summary()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()