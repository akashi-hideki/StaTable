"""patch_v3_5_readme_full_aggregation_v2.py"""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TRC = ROOT / "tests" / "test_readme_consistency.py"

def _must(text, old, new, label):
    if old not in text:
        raise SystemExit(f"[FAIL] {label}: anchor not found")
    if text.count(old) != 1:
        raise SystemExit(f"[FAIL] {label}: not unique")
    return text.replace(old, new, 1)

t = TRC.read_text(encoding="utf-8")
orig = t

# 1) PYTHONUNBUFFERED=1
t = _must(
    t,
    '    env.setdefault("PYTHONIOENCODING", "utf-8")\n',
    '    env.setdefault("PYTHONIOENCODING", "utf-8")\n'
    '    # [v3.5.0] Some tests call os._exit(0); without\n'
    '    # unbuffered stdout their TOTAL: line is lost.\n'
    '    env["PYTHONUNBUFFERED"] = "1"\n',
    "PYTHONUNBUFFERED",
)

# 2) Extend fallback with "Result: N PASS / M FAIL"
old_fb = (
    '        else:\n'
    '            # Fallback: some tests may print differently\n'
    '            p = re.search(r"TOTAL:\\s*(\\d+)\\s+PASSED:\\s*(\\d+)\\s+FAILED:\\s*(\\d+)", out)\n'
    '            if p:\n'
    '                total_pass += int(p.group(2))\n'
    '                total_fail += int(p.group(3))\n'
)
new_fb = (
    '        else:\n'
    '            # Fallback 1: "TOTAL: N PASSED: P FAILED: F"\n'
    '            p = re.search(r"TOTAL:\\s*(\\d+)\\s+PASSED:\\s*(\\d+)\\s+FAILED:\\s*(\\d+)", out)\n'
    '            if p:\n'
    '                total_pass += int(p.group(2))\n'
    '                total_fail += int(p.group(3))\n'
    '            else:\n'
    '                # Fallback 2: "Result: N PASS / M FAIL"\n'
    '                r2 = re.search(\n'
    '                    r"Result:\\s*(\\d+)\\s+PASS\\s*/\\s*(\\d+)\\s+FAIL",\n'
    '                    out)\n'
    '                if r2:\n'
    '                    total_pass += int(r2.group(1))\n'
    '                    total_fail += int(r2.group(2))\n'
)
t = _must(t, old_fb, new_fb, "fallback regex")

if t == orig:
    raise SystemExit("[FAIL] no changes")

TRC.write_text(t, encoding="utf-8")
print(f"[OK] {TRC}")
