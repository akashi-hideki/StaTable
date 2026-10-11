"""patch_ci_register_v3_5_3.py"""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CY = ROOT / ".github" / "workflows" / "check.yml"

OLD = "          coverage run --parallel-mode tests/test_v3_5_1_eclipse_installer.py\n"
NEW = (
    OLD
    + "          coverage run --parallel-mode "
    + "tests/test_v3_5_3_eclipse_installer_deep.py\n"
)

t = CY.read_text(encoding="utf-8")
if NEW.strip() in t:
    print("[SKIP] already registered")
else:
    n = t.count(OLD)
    if n != 1:
        raise SystemExit(f"[FAIL] anchor count={n}")
    CY.write_text(t.replace(OLD, NEW, 1), encoding="utf-8")
    print(f"[OK] {CY}")
