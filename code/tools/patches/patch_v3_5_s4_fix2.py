"""v3.5.0 S-4 fix2: exclude smoke test from coverage wrap.

test_v3_5_s1_smoke.py intentionally calls os._exit(0) to avoid
a Qt cleanup hang (see v3.4.x history).  os._exit bypasses the
atexit handlers that coverage relies on, so coverage data is
never written.  Exclude this one file from coverage wrapping.
"""
from __future__ import annotations
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
YML = REPO / ".github" / "workflows" / "check.yml"

OLD = "          coverage run --parallel-mode tests/test_v3_5_s1_smoke.py\n"
NEW = "          python tests/test_v3_5_s1_smoke.py\n"


def main() -> int:
    print("=" * 70)
    print("  patch_v3_5_s4_fix2")
    print("=" * 70)
    txt = YML.read_text(encoding="utf-8")
    n = txt.count(OLD)
    if n != 1:
        print(f"[FAIL] expected 1 occurrence, found {n}")
        sys.exit(1)
    txt = txt.replace(OLD, NEW, 1)
    YML.write_text(txt, encoding="utf-8")
    print("  unwrapped: test_v3_5_s1_smoke.py (coverage -> python)")
    print()
    print("[OK] done. Next:")
    print("     1. python -c \"import yaml; yaml.safe_load(open(r'.github/workflows/check.yml', encoding='utf-8').read()); print('YAML OK')\"")
    print("     2. cd code && python tests/test_ci_registration.py")
    print("     3. git add / commit / push")
    return 0


if __name__ == "__main__":
    sys.exit(main())