"""v3.5.0 Phase 1b: truthy-function + var-annotated fixes."""
from __future__ import annotations
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
CODE = REPO / "code"


def ensure_any(path: Path) -> None:
    """Ensure 'from typing import ... Any ...' exists."""
    txt = path.read_text(encoding="utf-8")
    if re.search(r"from typing import [^\n]*\bAny\b", txt):
        return
    m = re.search(r"^from typing import ([^\n]+)$", txt, re.MULTILINE)
    if m:
        names = [n.strip() for n in m.group(1).split(",") if n.strip()]
        if "Any" not in names:
            names.append("Any")
        new = "from typing import " + ", ".join(sorted(set(names)))
        txt = txt.replace(m.group(0), new, 1)
    else:
        m = re.search(r"^import sys\s*$", txt, re.MULTILINE)
        if m:
            txt = txt.replace(m.group(0), m.group(0) + "\nfrom typing import Any", 1)
        else:
            m = re.search(r"^class ", txt, re.MULTILINE)
            if m:
                i = m.start()
                txt = txt[:i] + "from typing import Any\n\n\n" + txt[i:]
    path.write_text(txt, encoding="utf-8")


def replace_in(path: Path, old: str, new: str) -> int:
    txt = path.read_text(encoding="utf-8")
    n = txt.count(old)
    if n == 0:
        return 0
    txt = txt.replace(old, new)
    path.write_text(txt, encoding="utf-8")
    return n


# ==============================================================
# truthy-function fixes (xml_io.py)
# ==============================================================
TRUTHY = [
    ("if RoleFunctionLibrary else None",
     "if RoleFunctionLibrary is not None else None"),
    ("if ConditionLibrary else None",
     "if ConditionLibrary is not None else None"),
    ("if LiteralLibrary else None",
     "if LiteralLibrary is not None else None"),
]

# ==============================================================
# var-annotated fixes (file, line, old, new)
# ==============================================================
VAR_ANN = [
    ("codegen/validate/items/base_validator.py",
     "    rules = {}", "    rules: dict[str, Any] = {}"),
    ("statable/xml_io.py",
     "    settings = {}", "    settings: dict[str, Any] = {}"),
    ("codegen/transition_generator.py",
     "        labels = set()", "        labels: set[str] = set()"),
    ("codegen/timer_generator.py",
     "        derived_timers = []", "        derived_timers: list[Any] = []"),
    ("codegen/validate/items/cell_validator.py",
     "            seen = {}", "            seen: dict[Any, Any] = {}"),
    ("codegen/validate/items/cell_validator.py",
     "            by_target = {}", "            by_target: dict[Any, Any] = {}"),
    ("codegen/validate/prompt_generator.py",
     "            actions = []", "            actions: list[Any] = []"),
    ("codegen/validate/prompt_generator.py",
     "            relations = []", "            relations: list[Any] = []"),
    ("codegen/validate/prompt_generator.py",
     "        issues = []", "        issues: list[Any] = []"),
    ("codegen/validate/items/state_validator.py",
     "        lower_names = {}", "        lower_names: dict[str, Any] = {}"),
]

def main() -> int:
    print("=" * 70)
    print("  patch_v3_5_6_phase1b_misc")
    print("=" * 70)

    # --- truthy-function ---
    xml_io = CODE / "statable" / "xml_io.py"
    truthy_total = 0
    for old, new in TRUTHY:
        n = replace_in(xml_io, old, new)
        if n:
            print(f"  truthy: xml_io.py: {n}x {old[:40]}...")
        truthy_total += n
    print(f"  truthy total: {truthy_total}")

    # --- var-annotated ---
    print()
    var_total = 0
    files_to_import = set()
    for rel, old, new in VAR_ANN:
        p = CODE / rel
        if not p.exists():
            print(f"  [SKIP] {rel}: not found")
            continue
        n = replace_in(p, old, new)
        if n == 0:
            print(f"  [SKIP] {rel}: pattern not found ({old.strip()})")
            continue
        var_total += n
        files_to_import.add(p)
        print(f"  var: {rel}: {n}x {old.strip()}")
    print(f"  var-annotated total: {var_total}")

    # --- ensure Any import in touched files ---
    print()
    for p in sorted(files_to_import):
        ensure_any(p)
        print(f"  ensured Any import: {p.relative_to(CODE)}")

    print()
    print("[OK] done. Next:")
    print("     cd code")
    print("     python -m mypy codegen statable statable_gui 2>&1 | Select-Object -Last 3")
    return 0


if __name__ == "__main__":
    sys.exit(main())