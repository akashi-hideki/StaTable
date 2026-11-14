"""patch_naming_convention.py"""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NC = ROOT / "codegen" / "naming_convention.py"
t = NC.read_text(encoding="utf-8")

def _must(old, new, label):
    global t
    if old not in t:
        raise SystemExit(f"[FAIL] {label}: not found")
    if t.count(old) != 1:
        raise SystemExit(f"[FAIL] {label}: not unique ({t.count(old)})")
    t = t.replace(old, new, 1)
    print(f"[OK] {label}")

# 1) import 追加
_must(
    "import re\nimport sys\nimport os\n",
    "import re\nimport sys\nimport os\nfrom typing import Any, Dict\n",
    "imports",
)

# 2) CONVERSION_PATTERNS 型注釈
_must(
    "    CONVERSION_PATTERNS = {\n",
    "    CONVERSION_PATTERNS: Dict[str, Dict[str, Any]] = {\n",
    "CONVERSION_PATTERNS type",
)

NC.write_text(t, encoding="utf-8")
print(f"[OK] wrote {NC}")
