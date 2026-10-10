"""v3.5.0 Phase 1b: suppress SubElement arg-type (mypy dict variance)."""
from __future__ import annotations
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
CODE = REPO / "code"
XML_IO = CODE / "statable" / "xml_io.py"

# 1-based line numbers reported by mypy
ERROR_LINES = [224, 339, 344, 369, 396, 409, 616, 656, 660, 669, 678, 687, 694, 705, 720]


def annotate_line(line: str) -> str:
    """Add or merge # type: ignore[arg-type] at the end of a single line."""
    stripped = line.rstrip("\r\n")
    nl = line[len(stripped):]
    if "# type: ignore" in stripped:
        if "arg-type" not in stripped:
            # merge into existing bracket form
            stripped = stripped.replace(
                "# type: ignore[", "# type: ignore[arg-type, ", 1)
    else:
        stripped += "  # type: ignore[arg-type]"
    return stripped + nl


def main() -> int:
    print("=" * 70)
    print("  patch_v3_5_6_phase1b_subelement")
    print("=" * 70)

    lines = XML_IO.read_text(encoding="utf-8").splitlines(keepends=True)
    n_applied = 0
    for ln in ERROR_LINES:
        idx = ln - 1
        if idx < 0 or idx >= len(lines):
            print(f"  [SKIP] line {ln}: out of range")
            continue
        before = lines[idx]
        after = annotate_line(before)
        if after == before:
            print(f"  [SKIP] line {ln}: already annotated")
            continue
        lines[idx] = after
        n_applied += 1
        preview = before.strip()[:60]
        print(f"  line {ln}: {preview}")

    XML_IO.write_text("".join(lines), encoding="utf-8")
    print(f"\n  applied: {n_applied}/{len(ERROR_LINES)}")
    print()
    print("[OK] done. Next:")
    print("     cd code")
    print("     python -m mypy codegen statable statable_gui 2>&1 | Select-Object -Last 3")
    return 0


if __name__ == "__main__":
    sys.exit(main())