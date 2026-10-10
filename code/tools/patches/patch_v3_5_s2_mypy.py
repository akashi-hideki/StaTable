"""v3.5.0 S-2: mypy foundation (Phase 1a).

Adds / modifies:
  - code/pyproject.toml               (add mypy to dev extras + [tool.mypy])
  - .github/workflows/check.yml       (add mypy-check job, informational)

Run from repo root (StaTable/):
    python code/tools/patches/patch_v3_5_s2_mypy.py
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
CODE = REPO / "code"


def patch(path: Path, old: str, new: str) -> None:
    txt = path.read_text(encoding="utf-8")
    if old not in txt:
        print(f"[FAIL] pattern not found in {path.relative_to(REPO)}")
        print("----- expected (first 500 chars) -----")
        print(old[:500])
        sys.exit(1)
    txt = txt.replace(old, new, 1)
    path.write_text(txt, encoding="utf-8")
    print(f"  patched: {path.relative_to(REPO)}")


def append_if_missing(path: Path, marker: str, content: str) -> None:
    txt = path.read_text(encoding="utf-8")
    if marker in txt:
        print(f"  skipped (already present): {path.relative_to(REPO)}")
        return
    if not txt.endswith("\n"):
        txt += "\n"
    txt += content
    path.write_text(txt, encoding="utf-8")
    print(f"  appended: {path.relative_to(REPO)}")


def main() -> int:
    print("=" * 70)
    print("  patch_v3_5_s2_mypy (Phase 1a)")
    print("=" * 70)

    # --- 1. pyproject.toml ---
    pyproject = CODE / "pyproject.toml"

    # 1a. dev extras に mypy を追加
    patch(
        pyproject,
        'dev = ["pytest>=7.0", "pycparser"]',
        'dev = ["pytest>=7.0", "pycparser", "mypy>=1.10"]',
    )

    # 1b. [tool.mypy] セクションを末尾に追加
    mypy_section = '''
[tool.mypy]
python_version = "3.10"
warn_unused_configs = true
ignore_missing_imports = true
follow_imports = "silent"
check_untyped_defs = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
# Phase 1a: keep untyped defs allowed for gradual adoption.
disallow_untyped_defs = false
disallow_incomplete_defs = false
strict_optional = true

# Exclude tests and patch scripts (Phase 1a scope).
exclude = [
    "^tests/",
    "^tools/patches/",
    "^__pycache__/",
]

# Per-module overrides to silence known-noisy modules until Phase 1c.
[[tool.mypy.overrides]]
module = [
    "PySide6.*",
    "pycparser.*",
]
ignore_missing_imports = true
'''
    append_if_missing(pyproject, "[tool.mypy]", mypy_section)

    # --- 2. .github/workflows/check.yml ---
    yml = REPO / ".github" / "workflows" / "check.yml"

    # 2a. mypy-check ジョブを追加 (ARM link verification の直前)
    mypy_job = '''  # ==============================================================
  # Job 8: mypy check (informational, Phase 1a)
  #
  # Introduces static type checking.  continue-on-error is true
  # so the first runs only *report* errors and never block the
  # build.  Once the error count is driven to zero, this flips
  # to blocking and the config gets stricter (Phase 1b/1c).
  #
  # The report is uploaded as an artifact for inspection.
  # ==============================================================
  mypy-check:
    name: mypy check (informational)
    runs-on: ubuntu-latest
    needs: [syntax]
    continue-on-error: true
    env:
      PYTHONIOENCODING: utf-8
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install mypy
        run: pip install mypy

      - name: Run mypy
        run: |
          mypy statable statable_gui codegen \\
            2>&1 | tee mypy_report.txt || true

      - name: Show summary (tail)
        if: always()
        run: |
          echo "----- mypy_report.txt (last 40 lines) -----"
          tail -n 40 mypy_report.txt || true

      - name: Upload mypy report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: mypy-report
          path: code/mypy_report.txt
          if-no-files-found: warn
          retention-days: 30

'''
    # ARM link verification ジョブの前に挿入
    marker = "  # ==============================================================\n"
    marker += "  # Job 7: ARM link verification (framework links, no hardware)"
    if marker not in yml.read_text(encoding="utf-8"):
        print("[FAIL] insertion marker for mypy job not found in check.yml")
        sys.exit(1)
    patch(yml, marker, mypy_job + marker)

    print()
    print("[OK] patch applied. Next steps:")
    print("     1. cd code")
    print("     2. pip install mypy")
    print("     3. mypy statable statable_gui codegen  (see current errors)")
    print("     4. git add / commit / push")
    return 0


if __name__ == "__main__":
    sys.exit(main())