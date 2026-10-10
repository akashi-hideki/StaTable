"""v3.5.0 Phase 1b: annotate class-level *_TEMPLATES dicts as dict[str, Any]."""
from __future__ import annotations
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
CODEGEN = REPO / "code" / "codegen"

# Match class-level attributes like:
#     ENUM_TEMPLATES = {
#     IMPLEMENTATION_TEMPLATES = {
PATTERN = re.compile(r"^    ([A-Z][A-Z0-9_]*_TEMPLATES) = \{", re.MULTILINE)


def ensure_any_import(txt: str) -> tuple[str, bool]:
    if "from typing import Any" in txt:
        return txt, False
    # 1) `from typing import X, Y` -> add Any
    m = re.search(r"^from typing import ([^\n]+)$", txt, re.MULTILINE)
    if m:
        old = m.group(0)
        names = [n.strip() for n in m.group(1).split(",")]
        if "Any" not in names:
            names.append("Any")
            new = "from typing import " + ", ".join(sorted(set(names)))
            txt = txt.replace(old, new, 1)
            return txt, True
        return txt, False
    # 2) Insert after `import sys` or first `import `
    m = re.search(r"^import sys\s*$", txt, re.MULTILINE)
    if m:
        old = m.group(0)
        txt = txt.replace(old, old + "\nfrom typing import Any", 1)
        return txt, True
    # 3) fallback: insert right before first `class ` at column 0
    m = re.search(r"^class ", txt, re.MULTILINE)
    if m:
        i = m.start()
        txt = txt[:i] + "from typing import Any\n\n\n" + txt[i:]
        return txt, True
    return txt, False


def main() -> int:
    print("=" * 70)
    print("  patch_v3_5_6_phase1b_templates")
    print("=" * 70)

    files = sorted(CODEGEN.rglob("*.py"))
    total_annotated = 0
    total_files = 0

    for f in files:
        if "__pycache__" in str(f):
            continue
        txt = f.read_text(encoding="utf-8")
        matches = PATTERN.findall(txt)
        if not matches:
            continue

        # Annotate all matches
        new_txt = PATTERN.sub(
            lambda m: f"    {m.group(1)}: dict[str, Any] = {{",
            txt,
        )
        # Ensure Any is imported
        new_txt, added_import = ensure_any_import(new_txt)

        f.write_text(new_txt, encoding="utf-8")
        total_annotated += len(matches)
        total_files += 1
        imp = " (+Any import)" if added_import else ""
        print(f"  {f.name}: {len(matches)} dict(s){imp}")

    print(f"\n  Total: {total_annotated} dict annotations in {total_files} files")
    print()
    print("[OK] done. Next:")
    print("     cd code")
    print("     python -m mypy codegen statable statable_gui 2>&1 | Select-Object -Last 3")
    return 0


if __name__ == "__main__":
    sys.exit(main())