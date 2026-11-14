"""v3.5.0 S-3: Ubuntu 26.04 CI migration prep.

Adds / modifies:
  - .github/workflows/check.yml  (pin ubuntu-24.04, add ubuntu-26.04 preview job)

Strategy:
  - Pin all existing jobs to ubuntu-24.04 to freeze the current, known-good image.
  - Add a lightweight "ubuntu-26-preview" job that runs the critical tests
    (unit tests + smoke L0-L3) on ubuntu-26.04 to catch migration issues early.

Run from repo root (StaTable/):
    python code/tools/patches/patch_v3_5_s3_ubuntu26.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
CODE = REPO / "code"

YML = REPO / ".github" / "workflows" / "check.yml"


def main() -> int:
    print("=" * 70)
    print("  patch_v3_5_s3_ubuntu26")
    print("=" * 70)

    txt = YML.read_text(encoding="utf-8")

    # --- 1. Pin every "runs-on: ubuntu-latest" to ubuntu-24.04 ---
    n_before = txt.count("runs-on: ubuntu-latest")
    txt = txt.replace("runs-on: ubuntu-latest", "runs-on: ubuntu-24.04")
    print(f"  pinned {n_before} occurrence(s) of runs-on to ubuntu-24.04")

    # --- 2. Insert ubuntu-26.04 preview job before the final job ---
    marker = (
        "  # ==============================================================\n"
        "  # Job 8: mypy check (informational, Phase 1a)"
    )
    if marker not in txt:
        print("[FAIL] insertion marker not found in check.yml")
        sys.exit(1)

    preview_job = (
        "  # ==============================================================\n"
        "  # Job 0: Ubuntu 26.04 preview (informational)\n"
        "  #\n"
        "  # ubuntu-latest migrates to Ubuntu 26.04 between 2026-10-19 and\n"
        "  # 2026-11-19.  This job runs the critical tests on the new image\n"
        "  # so regressions surface before the automatic cutover.\n"
        "  # continue-on-error is true so it never blocks the build.\n"
        "  # ==============================================================\n"
        "  ubuntu-26-preview:\n"
        "    name: Ubuntu 26.04 preview (informational)\n"
        "    runs-on: ubuntu-26.04\n"
        "    continue-on-error: true\n"
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
        "\n"
        "      - name: Install Qt system dependencies\n"
        "        run: |\n"
        "          sudo apt-get update\n"
        "          sudo apt-get install -y libegl1 libgl1 libglib2.0-0 libdbus-1-3 libxkbcommon0 libxkbcommon-x11-0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 libxcb-shape0 libxcb-xinerama0 libxcb-xfixes0 libxcb-cursor0 libfontconfig1 libfreetype6\n"
        "\n"
        "      - name: Install PySide6 and pycparser\n"
        "        run: pip install PySide6 pycparser\n"
        "\n"
        "      - name: compileall\n"
        "        run: |\n"
        "          python -m compileall -q statable statable_gui codegen\n"
        "\n"
        "      - name: Run smoke tests (levels 0-3)\n"
        "        run: |\n"
        "          python -m statable --smoke-test --smoke-level=0\n"
        "          python -m statable --smoke-test --smoke-level=1\n"
        "          python -m statable --smoke-test --smoke-level=2\n"
        "          python -m statable --smoke-test --smoke-level=3\n"
        "\n"
        "      - name: Run core test suites\n"
        "        run: |\n"
        "          python tests/test_v3_5_s1_smoke.py\n"
        "          python tests/test_v3_0_s3_cli.py\n"
        "          python tests/test_v3_0_s1_packaging.py\n"
        "          python tests/test_ci_registration.py\n"
        "          python tests/test_readme_consistency.py\n"
        "\n"
        "      - name: Upload smoke result\n"
        "        if: always()\n"
        "        uses: actions/upload-artifact@v4\n"
        "        with:\n"
        "          name: ubuntu-26-preview-report\n"
        "          path: code/logs/\n"
        "          if-no-files-found: ignore\n"
        "          retention-days: 30\n"
        "\n"
    )
    txt = txt.replace(marker, preview_job + marker, 1)
    print("  inserted: ubuntu-26-preview job")

    YML.write_text(txt, encoding="utf-8")
    print(f"  wrote: {YML.relative_to(REPO)}")

    print()
    print("[OK] done. Next:")
    print("     1. cd code")
    print("     2. Review .github/workflows/check.yml diff")
    print("     3. git add / commit / push")
    print("     4. Watch CI: ubuntu-26-preview should run and (hopefully) pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())