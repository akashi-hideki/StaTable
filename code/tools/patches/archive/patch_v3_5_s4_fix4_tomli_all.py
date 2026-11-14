"""v3.5.0 S-4 fix4: tomli fallback for the remaining 3 files."""
from __future__ import annotations
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
CODE = REPO / "code"

TARGETS = [
    CODE / "tests" / "test_v3_0_g1_shared.py",
    CODE / "tests" / "test_v3_0_s2_public_api.py",
    CODE / "tests" / "test_v3_0_s3_cli.py",
]

OLD = "        import tomllib\n"
NEW = (
    "        try:\n"
    "            import tomllib\n"
    "        except ImportError:\n"
    "            import tomli as tomllib  # type: ignore[no-redef]\n"
)


def main() -> int:
    print("=" * 70)
    print("  patch_v3_5_s4_fix4_tomli_all")
    print("=" * 70)
    for p in TARGETS:
        if not p.exists():
            print(f"  [SKIP] not found: {p.name}")
            continue
        txt = p.read_text(encoding="utf-8")
        if "import tomli as tomllib" in txt:
            print(f"  [SKIP] already has fallback: {p.name}")
            continue
        n = txt.count(OLD)
        if n == 0:
            print(f"  [SKIP] pattern not found: {p.name}")
            continue
        txt = txt.replace(OLD, NEW)
        p.write_text(txt, encoding="utf-8")
        print(f"  patched: {p.name} ({n} occurrence(s))")
    print()
    print("[OK] done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())