# code/tests/test_v3_0_s4_docs.py
"""
Phase S-4 (v3.0) tests: SDK documentation + examples.

Verifies:
  - SPEC_SDK_API_ja.md has section 2.6 (CLI usage)
  - SPEC_SDK_API_en.md has section 2.6 (CLI Usage)
  - examples/quickstart.py exists and is syntactically valid
  - examples/cli_guide.md exists
  - README v3.0 section marked Released
  - README mentions pip install statable
  - .gitignore excludes examples/_output/
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
REPO = CODE.parent
sys.path.insert(0, str(CODE))

DOCS = CODE / "docs"
EXAMPLES = CODE / "examples"
README = REPO / "README.md"
GITIGNORE = REPO / ".gitignore"

TOTAL = 0
PASSED = 0
FAILED = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global TOTAL, PASSED, FAILED
    TOTAL += 1
    if cond:
        PASSED += 1
        print(f"[PASS] {name}")
    else:
        FAILED += 1
        print(f"[FAIL] {name}" + (f" -- {detail}" if detail else ""))


def main() -> int:
    print("=" * 70)
    print("  test_v3_0_s4_docs")
    print("=" * 70)

    # --- T1: SPEC_SDK_API_ja.md --------------------------------------
    ja = DOCS / "SPEC_SDK_API_ja.md"
    check("SPEC_SDK_API_ja.md exists", ja.exists(), str(ja))
    if ja.exists():
        text = ja.read_text(encoding="utf-8")
        check("JA has '### 2.6 CLI 使用法'",
              "### 2.6 CLI 使用法" in text)
        check("JA mentions 'statable-cli'",
              "statable-cli" in text)
        check("JA mentions 'pip install statable'",
              "pip install statable" in text)

    # --- T2: SPEC_SDK_API_en.md --------------------------------------
    en = DOCS / "SPEC_SDK_API_en.md"
    check("SPEC_SDK_API_en.md exists", en.exists(), str(en))
    if en.exists():
        text = en.read_text(encoding="utf-8")
        check("EN has '### 2.6 CLI Usage'",
              "### 2.6 CLI Usage" in text)
        check("EN mentions 'statable-cli'",
              "statable-cli" in text)
        check("EN mentions 'pip install statable'",
              "pip install statable" in text)

    # --- T3: examples/quickstart.py ----------------------------------
    qs = EXAMPLES / "quickstart.py"
    check("examples/quickstart.py exists", qs.exists(), str(qs))
    if qs.exists():
        src = qs.read_text(encoding="utf-8")
        try:
            ast.parse(src)
            check("quickstart.py is syntactically valid", True)
        except SyntaxError as e:
            check("quickstart.py is syntactically valid", False, repr(e))
        check("quickstart.py imports StateMachine",
              "StateMachine" in src)
        check("quickstart.py uses CCodeGenerator",
              "CCodeGenerator" in src)
        check("quickstart.py uses set_initial",
              "set_initial" in src)

    # --- T4: examples/cli_guide.md -----------------------------------
    cg = EXAMPLES / "cli_guide.md"
    check("examples/cli_guide.md exists", cg.exists(), str(cg))
    if cg.exists():
        src = cg.read_text(encoding="utf-8")
        check("cli_guide.md mentions 'statable-cli generate'",
              "statable-cli generate" in src)
        check("cli_guide.md mentions 'statable-cli validate'",
              "statable-cli validate" in src)
        check("cli_guide.md mentions exit codes table",
              "Exit Codes" in src or "終了コード" in src)

    # --- T5: README v3.0 section -------------------------------------
    check("README.md exists", README.exists(), str(README))
    if README.exists():
        text = README.read_text(encoding="utf-8")
        check("README v3.0 marked 'Released'",
              "### v3.0 (Released" in text)
        check("README mentions 'pip install statable'",
              "pip install statable" in text)
        check("README has CLI checkmark entry",
              "**CLI**" in text)
        check("README has Python SDK checkmark entry",
              "**Python SDK**" in text)

    # --- T6: .gitignore ----------------------------------------------
    check(".gitignore exists", GITIGNORE.exists(), str(GITIGNORE))
    if GITIGNORE.exists():
        text = GITIGNORE.read_text(encoding="utf-8")
        check(".gitignore has 'code/examples/_output/'",
              "code/examples/_output/" in text)

    _summary()
    return 0 if FAILED == 0 else 1


def _summary() -> None:
    print("-" * 70)
    print(f"TOTAL: {TOTAL}  PASSED: {PASSED}  FAILED: {FAILED}")
    print("=" * 70)


if __name__ == "__main__":
    sys.exit(main())
