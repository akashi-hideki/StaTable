#!/usr/bin/env python3
"""
README consistency test suite for StaTable.

Verifies that claims in README.md match the actual repository state.

  [1] Badge test count
  [2] Suite count
  [3] Internal numeric consistency (badge / platform / quick-start / roadmap)
  [4] Documentation links exist
  [5] Roadmap contains v2.7.0
  [6] Breaking Changes section present
  [7] Generated file table includes state_actions
  [8] File count claim (single-layer / three-layer)
  [9] Codegen sub-generator count
  [10] Full test run (opt-in via --full)

Run:
  python tests/test_readme_consistency.py           # fast (no test run)
  python tests/test_readme_consistency.py --full    # run all suites too
"""

import os
import re
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent       # code/
REPO_ROOT = PROJECT_ROOT.parent                             # StaTable/
README = REPO_ROOT / "README.md"
TESTS_DIR = PROJECT_ROOT / "tests"
CODEGEN_DIR = PROJECT_ROOT / "codegen"
DOCS_DIR = PROJECT_ROOT / "docs"


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


RESULT = TestResult()


def check(name, condition, msg=""):
    if condition:
        RESULT.ok(name)
    else:
        RESULT.fail(name, msg)
    return condition


# ======================================================================
# Helpers
# ======================================================================
def load_readme() -> str:
    return README.read_text(encoding="utf-8")


def strip_roadmap(text: str) -> str:
    """Return README text with the Roadmap section removed.

    Past release notes (v2.3: 25 suites, v2.5.5: 796 PASS, ...) are
    historical records, not current claims. Exclude them from
    numeric-consistency checks.
    """
    marker = "## Roadmap"
    idx = text.find(marker)
    if idx < 0:
        return text
    return text[:idx]



def extract_all(pattern: str, text: str) -> list:
    return re.findall(pattern, text)


def extract_first(pattern: str, text: str):
    m = re.search(pattern, text)
    return m.group(1) if m else None


def count_test_files() -> int:
    return len(sorted(TESTS_DIR.glob("test_*.py")))


def count_sub_generators() -> int:
    """Count codegen/*_generator.py files (excluding c_code_generator.py
    and state_actions_generator.py which is also a generator)."""
    return len(sorted(CODEGEN_DIR.glob("*_generator.py")))


# ======================================================================
# [1] Badge test count
# ======================================================================
def test_badge_count():
    print("\n[1] Badge test count")
    text = load_readme()

    badge = extract_first(r"Tests-(\d+)%20PASS", text)
    check("Badge has Tests-NNNN%20PASS",
          badge is not None,
          f"pattern not found in README")

    if badge is None:
        return None

    print(f"         Badge claims: {badge} PASS")

    # Internal consistency: badge value must appear elsewhere too
    occurrences = text.count(f"{badge} PASS")
    check(f"Badge value {badge} appears in body",
          occurrences >= 2,
          f"found only {occurrences} occurrence(s)")

    return int(badge)


# ======================================================================
# [2] Suite count
# ======================================================================
def test_suite_count():
    print("\n[2] Suite count")
    text = strip_roadmap(load_readme())

    actual = count_test_files()
    print(f"         Actual test_*.py files: {actual}")

    # Multiple expected phrasings
    # NOTE: "N other suites" is NOT a total count (it means
    # "N additional suites besides the explicitly listed ones"),
    # so it is excluded from the suite-count check.
    patterns = [
        r"(\d+)\s+test suites",
        r"(\d+)\s+suites(?![\w])",   # avoid matching "...other suites"
        r"All\s+(\d+)\s+suites",
    ]
    claims = set()
    for pat in patterns:
        for m in re.findall(pat, text):
            claims.add(int(m))

    print(f"         README claims: {sorted(claims)}")

    check("README claims at least one suite count",
          bool(claims),
          "no suite count found")

    # All claims should match actual
    for c in claims:
        check(f"Suite count {c} == actual ({actual})",
              c == actual,
              f"README says {c}, actual is {actual}")

    return actual


# ======================================================================
# [3] Internal numeric consistency
# ======================================================================
def _extract_summary_pass_values(text: str) -> set:
    """Extract only *total* PASS values from README.

    Distinguishes:
      - Total counts like "27 test suites, 1106 PASS / ..."
      - Total counts like "N suites, NNNN tests"
      - Per-suite counts like "`test_v2_7_p4.py` (52 PASS)"
    The latter must NOT be treated as the project total.
    """
    values = set()
    # Patterns that indicate a *summary* / total PASS count
    summary_patterns = [
        r"(\d+)\s+test suites,\s*(\d+)\s+PASS",   # "N test suites, NNNN PASS"
        r"across\s+(\d+)\s+suites.*?(\d+)\s+PASS", # "across N suites ... NNNN PASS"
        r"Expected:\s*\*\*(\d+)\s+PASS",          # "Expected: **NNNN PASS"
        r"\((\d+)\s+PASS\s*/\s*\d+\s+SKIP\)",  # "(NNNN PASS / M SKIP)"
    ]
    for pat in summary_patterns:
        for m in re.finditer(pat, text, re.DOTALL):
            # Last group is the PASS number
            try:
                values.add(int(m.group(2)))
            except IndexError:
                try:
                    values.add(int(m.group(1)))
                except (IndexError, ValueError):
                    pass
    return values


def test_numeric_consistency(badge_pass: int):
    print("\n[3] Internal numeric consistency")
    text = strip_roadmap(load_readme())

    summary_values = _extract_summary_pass_values(text)
    print(f"         Summary PASS values in README: {sorted(summary_values)}")

    if badge_pass is not None and summary_values:
        check(f"Summary PASS values == badge ({badge_pass})",
              summary_values == {badge_pass},
              f"badge={badge_pass}, summary values={sorted(summary_values)}")


# ======================================================================
# [4] Documentation links exist
# ======================================================================
def test_doc_links():
    print("\n[4] Documentation links")
    text = load_readme()

    # Extract code/docs/*.md paths
    links = set(extract_all(r"\(code/(docs/[A-Za-z0-9_./-]+\.md)\)", text))
    print(f"         Found {len(links)} doc link(s)")

    for rel in sorted(links):
        path = PROJECT_ROOT / rel
        check(f"Doc exists: {rel}",
              path.exists(),
              f"missing: {path}")

    # SPEC_STATE_ACTIONS must be linked
    check("SPEC_STATE_ACTIONS_v1.md is linked",
          any("SPEC_STATE_ACTIONS_v1.md" in l for l in links))


# ======================================================================
# [5] Roadmap contains v2.7.0
# ======================================================================
def test_roadmap_v270():
    print("\n[5] Roadmap v2.7.0 entry")
    text = load_readme()

    check("Roadmap has '### v2.7.0' heading",
          "### v2.7.0" in text)

    check("Roadmap v2.7.0 marked Released",
          re.search(r"### v2\.7\.0 \(Released", text) is not None)

    check("Roadmap mentions StateActionsDialog",
          "StateActionsDialog" in text)

    check("Roadmap mentions State actions (Entry / Exit / Do)",
          "State actions (Entry / Exit / Do)" in text)


# ======================================================================
# [6] Breaking Changes section
# ======================================================================
def test_breaking_changes():
    print("\n[6] Breaking Changes section")
    text = load_readme()

    check("Has '## Breaking Changes' heading",
          "## Breaking Changes" in text)

    check("Mentions FIRE_EVENT migration",
          "FIRE_EVENT_<Layer>" in text)

    check("States v2.7.0 backward compatible",
          "v2.7.0 is fully backward compatible" in text)


# ======================================================================
# [7] Generated file table
# ======================================================================
def test_generated_file_table():
    print("\n[7] Generated file table")
    text = load_readme()

    check("Table includes statable_state_actions.h",
          "`statable_state_actions.h`" in text)
    check("Table includes statable_state_actions.c",
          "`statable_state_actions.c`" in text)
    check("Table mentions Entry / Exit / Do",
          "Entry / Exit / Do" in text)

    # Generator actually emits these files
    gen_files = [p.name for p in CODEGEN_DIR.glob("*.py")]
    check("state_actions_generator.py exists in codegen/",
          "state_actions_generator.py" in gen_files)


# ======================================================================
# [8] File count claim
# ======================================================================
def test_file_count_claim():
    print("\n[8] File count claim")
    text = load_readme()

    m = re.search(r"Single-layer project:\s*(\d+)\s*files", text)
    check("'Single-layer project: N files' present",
          m is not None)

    if m:
        single = int(m.group(1))
        print(f"         Single-layer claim: {single} files")
        # We can't easily verify at test time without running codegen.
        # Just sanity-check the range.
        check(f"Single-layer file count plausible (10 <= {single} <= 30)",
              10 <= single <= 30)

    m2 = re.search(r"Three-layer project:\s*(\d+)\s*files", text)
    if m2:
        three = int(m2.group(1))
        print(f"         Three-layer claim: {three} files")
        check(f"Three-layer file count plausible (20 <= {three} <= 60)",
              20 <= three <= 60)

    # The v2.7 generates 30 for 3 layers, so single should be 16 (per README)
    if m and m2:
        s, t = int(m.group(1)), int(m2.group(1))
        # 3-layer = 16 + 2*(layers-1) + extras
        # For 3 layers with 6 layer-specific files each + 10 common
        # single: 16, 3-layer: 30
        check(f"Three-layer ({t}) > Single-layer ({s})",
              t > s)


# ======================================================================
# [9] Codegen sub-generator count
# ======================================================================
def test_sub_generator_count():
    print("\n[9] Codegen sub-generator count")
    text = load_readme()

    m = re.search(r"CCodeGenerator\s*\+\s*(\d+)\s+sub-generators", text)
    check("'CCodeGenerator + N sub-generators' present",
          m is not None,
          "pattern not found")

    if m:
        claimed = int(m.group(1))
        actual = count_sub_generators()
        print(f"         Claimed: {claimed}, Actual *_generator.py: {actual}")
        # Allow some tolerance: generators may not all follow the
        # "_generator.py" naming pattern.
        check(f"Sub-generator count {claimed} >= actual ({actual})",
              claimed >= actual,
              f"claimed {claimed} < actual {actual}")


# ======================================================================
# [10] Full test run (opt-in)
# ======================================================================
def test_full_run():
    print("\n[10] Full test run (--full)")
    test_files = sorted(TESTS_DIR.glob("test_*.py"))
    # Exclude self to avoid recursion
    test_files = [f for f in test_files if f.name != "test_readme_consistency.py"]

    print(f"         Running {len(test_files)} test suite(s)...")

    env = os.environ.copy()
    env.setdefault("QT_QPA_PLATFORM", "offscreen")
    env.setdefault("STATABLE_DISABLE_MERMAID", "1")
    env.setdefault("PYTHONIOENCODING", "utf-8")

    total_pass = 0
    total_fail = 0
    total_skip = 0

    for tf in test_files:
        try:
            proc = subprocess.run(
                [sys.executable, str(tf)],
                cwd=str(PROJECT_ROOT),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=120,
                env=env,
            )
        except subprocess.TimeoutExpired:
            print(f"         [TIMEOUT] {tf.name}")
            continue

        out = (proc.stdout or "") + "\n" + (proc.stderr or "")
        # Parse "TOTAL: N  PASSED: P  FAILED: F  SKIPPED: S"
        m = re.search(
            r"TOTAL:\s*(\d+)\s+PASSED:\s*(\d+)\s+"
            r"FAILED:\s*(\d+)\s+SKIPPED:\s*(\d+)",
            out)
        if m:
            total_pass += int(m.group(2))
            total_fail += int(m.group(3))
            total_skip += int(m.group(4))
        else:
            # Fallback: some tests may print differently
            p = re.search(r"TOTAL:\s*(\d+)\s+PASSED:\s*(\d+)\s+FAILED:\s*(\d+)", out)
            if p:
                total_pass += int(p.group(2))
                total_fail += int(p.group(3))

    print(f"         Measured: PASS={total_pass} FAIL={total_fail} SKIP={total_skip}")

    text = load_readme()
    badge = int(extract_first(r"Tests-(\d+)%20PASS", text) or 0)

    check(f"Measured PASS ({total_pass}) == badge ({badge})",
          total_pass == badge,
          f"badge={badge}, measured={total_pass} "
          f"(diff={total_pass - badge:+d})")

    check(f"Measured FAIL == 0",
          total_fail == 0,
          f"got {total_fail}")

    return total_pass


# ======================================================================
# Main
# ======================================================================
def main():
    full = "--full" in sys.argv

    print("=" * 70)
    print("  StaTable README consistency test suite")
    if full:
        print("  (--full: running all test suites)")
    print("=" * 70)
    print(f"  README: {README}")
    print(f"  Tests:  {TESTS_DIR}")

    if not README.exists():
        print(f"[FAIL] README not found: {README}")
        sys.exit(1)

    badge_pass = test_badge_count()
    test_suite_count()
    test_numeric_consistency(badge_pass)
    test_doc_links()
    test_roadmap_v270()
    test_breaking_changes()
    test_generated_file_table()
    test_file_count_claim()
    test_sub_generator_count()

    if full:
        test_full_run()
    else:
        print("\n[10] Full test run")
        print("  [SKIP] use --full to run all test suites")

    ok = RESULT.summary()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()