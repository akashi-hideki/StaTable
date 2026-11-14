"""fix_test_idempotency.py"""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEST = ROOT / "tests" / "test_v3_5_3_eclipse_installer_deep.py"
t = TEST.read_text(encoding="utf-8")

old = '''    res1 = install(opts)
    res2 = install(opts)
    check("2-3 idempotent: 1st no errors", not res1.errors)
    check("2-3 idempotent: 2nd no errors", not res2.errors)
    check("2-3 idempotent: same # installed",
          len(res1.installed) == len(res2.installed))
    check("2-3 idempotent: scaffolding skipped (>= 1)",
          len(res2.skipped) >= 1)
'''

new = '''    res1 = install(opts)
    res2 = install(opts)
    check("2-3 idempotent: 1st no errors", not res1.errors)
    check("2-3 idempotent: 2nd no errors", not res2.errors)
    # 1st install: everything fresh (installed = all)
    # 2nd install: generated C overwritten (installed), scaffolding
    #   skipped (overwrite_scaffolding=False default)
    check("2-3 idempotent: 2nd has fewer installed",
          len(res2.installed) < len(res1.installed))
    check("2-3 idempotent: 2nd skipped scaffolding (>= 1)",
          len(res2.skipped) >= 1)
    check("2-3 idempotent: 2nd installed + skipped == 1st installed",
          len(res2.installed) + len(res2.skipped) == len(res1.installed))
'''

if old not in t:
    raise SystemExit("[FAIL] anchor not found")
t = t.replace(old, new, 1)
TEST.write_text(t, encoding="utf-8")
print(f"[OK] {TEST}")
