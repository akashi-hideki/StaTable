"""patch_v3_5_ci_register.py"""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CY = ROOT / ".github" / "workflows" / "check.yml"

OLD = "          python tests/test_v3_5_s1_smoke.py\n"
NEW = (
    "          python tests/test_v3_5_s1_smoke.py\n"
    "          coverage run --parallel-mode "
    "tests/test_v3_5_gui_output_clean.py\n"
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
