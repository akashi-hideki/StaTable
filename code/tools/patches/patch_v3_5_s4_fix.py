"""v3.5.0 S-4 fix: correct check.yml patch + register coverage pattern."""
from __future__ import annotations
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
CODE = REPO / "code"
YML = REPO / ".github" / "workflows" / "check.yml"
TEST_REG = CODE / "tests" / "test_ci_registration.py"


def patch_test_ci_registration():
    txt = TEST_REG.read_text(encoding="utf-8")
    old = 'return set(re.findall(r"python\\s+tests[\\\\/](test_\\w+\\.py)", text))'
    new = (
        '# Matches:  python tests/test_xxx.py\n'
        '    #           python tests\\\\test_xxx.py\n'
        '    #           coverage run --parallel-mode tests/test_xxx.py\n'
        '    return set(re.findall(\n'
        '        r"(?:python|coverage\\s+run(?:\\s+--parallel-mode)?)\\s+tests[\\\\/](test_\\w+\\.py)",\n'
        '        text,\n'
        '    ))'
    )
    if old not in txt:
        print("[FAIL] test_ci_registration.py pattern not found")
        sys.exit(1)
    txt = txt.replace(old, new, 1)
    TEST_REG.write_text(txt, encoding="utf-8")
    print("  patched: test_ci_registration.py")

def patch_check_yml():
    txt = YML.read_text(encoding="utf-8")

    # --- 1) Matrix + install step ---
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

    # --- 2) Insert coverage_steps FIRST (before any length change) ---
    end_marker = (
        "\n\n  # ==============================================================\n"
        "  # Job 4: Generated C code verification"
    )
    if end_marker not in txt:
        print("[FAIL] Job 4 marker not found")
        sys.exit(1)

    coverage_steps = (
        "\n"
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
    )
    txt = txt.replace(end_marker, coverage_steps + end_marker, 1)
    print("  inserted: coverage_steps (before Job 4 marker)")

    # --- 3) Now replace 'python tests/' inside the tests job only ---
    start_marker = "  tests:\n"
    end_marker2 = (
        "  # ==============================================================\n"
        "  # Job 4: Generated C code verification"
    )
    i = txt.index(start_marker)
    j = txt.index(end_marker2, i)
    section = txt[i:j]
    n = section.count("          python tests/")
    section = section.replace(
        "          python tests/",
        "          coverage run --parallel-mode tests/",
    )
    txt = txt[:i] + section + txt[j:]
    print(f"  wrapped {n} test invocations")

    YML.write_text(txt, encoding="utf-8")
    print("  patched: check.yml")


def main() -> int:
    print("=" * 70)
    print("  patch_v3_5_s4_fix")
    print("=" * 70)
    patch_test_ci_registration()
    patch_check_yml()
    print()
    print("[OK] done. Next:")
    print("     1. cd code && python tests/test_ci_registration.py")
    print("     2. python -c \"import yaml; yaml.safe_load(open(r'../.github/workflows/check.yml', encoding='utf-8').read()); print('YAML OK')\"")
    print("     3. git add / commit / push")
    return 0


if __name__ == "__main__":
    sys.exit(main())