"""v3.5.0 S-4: Python matrix + coverage (A-1 + A-2)."""
from __future__ import annotations
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
CODE = REPO / "code"
YML = REPO / ".github" / "workflows" / "check.yml"


def patch_pyproject():
    p = CODE / "pyproject.toml"
    txt = p.read_text(encoding="utf-8")
    old = 'dev = ["pytest>=7.0", "pycparser", "mypy>=1.10"]'
    new = 'dev = ["pytest>=7.0", "pycparser", "mypy>=1.10", "coverage>=7.0"]'
    if old in txt:
        txt = txt.replace(old, new, 1)
    elif "coverage>=" not in txt:
        print("[FAIL] dev extras pattern not found")
        sys.exit(1)
    p.write_text(txt, encoding="utf-8")
    print("  patched: pyproject.toml (coverage)")


def write_coveragerc():
    p = CODE / ".coveragerc"
    content = "[run]\nsource = statable, statable_gui, codegen\nbranch = True\nparallel = True\nomit =\n    */tests/*\n    */tools/*\n    */__pycache__/*\n    */site-packages/*\n\n[report]\nexclude_lines =\n    pragma: no cover\n    if __name__ == .__main__.:\n    raise NotImplementedError\n"
    p.write_text(content, encoding="utf-8")
    print("  wrote: code/.coveragerc")


def update_gitignore():
    p = REPO / ".gitignore"
    txt = p.read_text(encoding="utf-8")
    if ".coverage" in txt:
        print("  skipped: .gitignore already has .coverage")
        return
    txt += "\n# Coverage\n.coverage\n.coverage.*\nhtmlcov/\n"
    p.write_text(txt, encoding="utf-8")
    print("  updated: .gitignore")

def patch_check_yml():
    txt = YML.read_text(encoding="utf-8")

    old = (
        "  tests:\n"
        "    name: Unit tests\n"
        "    runs-on: ubuntu-24.04\n"
        "    needs: [syntax]\n"
        "    env:\n"
        "      QT_QPA_PLATFORM: offscreen\n"
        "      STATABLE_DISABLE_MERMAID: '1'\n"
        "      PYTHONIOENCODING: utf-8\n"
        "    steps:\n"
        "      - uses: actions/checkout@v4\n"
        "\n"
        "      - uses: actions/setup-python@v5\n"
        "        with:\n"
        "          python-version: '3.12'\n"
    )
    new = (
        "  tests:\n"
        "    name: Unit tests (py${{ matrix.python-version }})\n"
        "    runs-on: ubuntu-24.04\n"
        "    needs: [syntax]\n"
        "    strategy:\n"
        "      fail-fast: false\n"
        "      matrix:\n"
        "        python-version: ['3.10', '3.11', '3.12', '3.13']\n"
        "    env:\n"
        "      QT_QPA_PLATFORM: offscreen\n"
        "      STATABLE_DISABLE_MERMAID: '1'\n"
        "      PYTHONIOENCODING: utf-8\n"
        "    steps:\n"
        "      - uses: actions/checkout@v4\n"
        "\n"
        "      - uses: actions/setup-python@v5\n"
        "        with:\n"
        "          python-version: ${{ matrix.python-version }}\n"
    )
    if old not in txt:
        print("[FAIL] tests job header not found")
        sys.exit(1)
    txt = txt.replace(old, new, 1)

    old2 = (
        "      - name: Install PySide6 and pycparser\n"
        "        run: pip install PySide6 pycparser\n"
        "\n"
        "      - name: Run v2.2 test suites"
    )
    new2 = (
        "      - name: Install PySide6, pycparser, coverage\n"
        "        run: pip install PySide6 pycparser coverage\n"
        "\n"
        "      - name: Run v2.2 test suites"
    )
    if old2 not in txt:
        print("[FAIL] install step not found")
        sys.exit(1)
    txt = txt.replace(old2, new2, 1)

    start_marker = "  tests:\n"
    end_marker = "  # ==============================================================\n  # Job 4: Generated C code verification"
    i = txt.index(start_marker)
    j = txt.index(end_marker, i)
    section = txt[i:j]
    n = section.count("          python tests/")
    section = section.replace(
        "          python tests/",
        "          coverage run --parallel-mode tests/",
    )
    txt = txt[:i] + section + txt[j:]
    print(f"  wrapped {n} test invocations")

    coverage_steps = (
        "      - name: Combine coverage\n"
        "        if: always()\n"
        "        run: |\n"
        "          coverage combine || true\n"
        "          coverage report --show-missing --skip-covered || true\n"
        "          coverage html || true\n"
        "\n"
        "      - name: Upload coverage HTML\n"
        "        if: always()\n"
        "        uses: actions/upload-artifact@v4\n"
        "        with:\n"
        "          name: coverage-py${{ matrix.python-version }}\n"
        "          path: code/htmlcov/\n"
        "          if-no-files-found: warn\n"
        "          retention-days: 30\n"
        "\n"
    )
    txt = txt[:j] + coverage_steps + txt[j:]
    YML.write_text(txt, encoding="utf-8")
    print("  patched: check.yml")

def main() -> int:
    print("=" * 70)
    print("  patch_v3_5_s4_pymatrix_coverage")
    print("=" * 70)
    patch_pyproject()
    write_coveragerc()
    update_gitignore()
    patch_check_yml()
    print()
    print("[OK] done. Next:")
    print("     1. review diffs")
    print("     2. git add / commit / push")
    print("     3. watch CI: tests runs 4x (3.10/3.11/3.12/3.13)")
    return 0


if __name__ == "__main__":
    sys.exit(main())