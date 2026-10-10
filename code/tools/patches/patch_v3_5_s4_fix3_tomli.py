"""v3.5.0 S-4 fix3: tomllib fallback for Python 3.10 + tomli dep."""
from __future__ import annotations
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
CODE = REPO / "code"
PYPROJECT = CODE / "pyproject.toml"
YML = REPO / ".github" / "workflows" / "check.yml"

# Files to rewrite (direct `import tomllib` -> try/except fallback)
TARGETS = [
    CODE / "tests" / "test_v3_0_s1_packaging.py",
]


def patch_targets():
    for p in TARGETS:
        if not p.exists():
            print(f"  [SKIP] not found: {p.name}")
            continue
        txt = p.read_text(encoding="utf-8")
        # Skip if already using fallback
        if "tomli" in txt and "except ImportError" in txt:
            print(f"  [SKIP] already has fallback: {p.name}")
            continue
        # Case: bare `import tomllib` on its own line
        old = "import tomllib\n"
        new = (
            "try:\n"
            "    import tomllib  # Python 3.11+\n"
            "except ImportError:  # Python 3.10\n"
            "    import tomli as tomllib  # type: ignore[no-redef]\n"
        )
        if old not in txt:
            print(f"  [SKIP] pattern not found: {p.name}")
            continue
        txt = txt.replace(old, new, 1)
        p.write_text(txt, encoding="utf-8")
        print(f"  patched: {p.relative_to(REPO)}")


def patch_pyproject():
    txt = PYPROJECT.read_text(encoding="utf-8")
    # Look for the dev extras block
    m = re.search(r'dev = \[(.*?)\]', txt, re.DOTALL)
    if not m:
        print("[FAIL] dev extras not found in pyproject.toml")
        sys.exit(1)
    block = m.group(0)
    if "tomli" in block:
        print("  [SKIP] tomli already in dev extras")
        return
    new_block = block.rstrip("]").rstrip()
    # Insert before closing bracket
    new_block = new_block + ', "tomli>=2.0; python_version < \'3.11\'"]'
    txt = txt.replace(block, new_block, 1)
    PYPROJECT.write_text(txt, encoding="utf-8")
    print("  patched: pyproject.toml (dev extras += tomli)")


def patch_check_yml():
    txt = YML.read_text(encoding="utf-8")
    old = "        run: pip install PySide6 pycparser coverage\n"
    new = "        run: pip install PySide6 pycparser coverage tomli\n"
    n = txt.count(old)
    if n == 0:
        # already patched?
        if "coverage tomli" in txt:
            print("  [SKIP] check.yml already has tomli")
            return
        print("[FAIL] install line not found in check.yml")
        sys.exit(1)
    txt = txt.replace(old, new)
    YML.write_text(txt, encoding="utf-8")
    print(f"  patched: check.yml (install += tomli, {n} occurrence(s))")

def main() -> int:
    print("=" * 70)
    print("  patch_v3_5_s4_fix3_tomli")
    print("=" * 70)
    patch_targets()
    patch_pyproject()
    patch_check_yml()
    print()
    print("[OK] done. Next:")
    print("     1. python -c \"import yaml; yaml.safe_load(open(r'.github/workflows/check.yml', encoding='utf-8').read()); print('YAML OK')\"")
    print("     2. cd code && python tests/test_ci_registration.py")
    print("     3. git diff (review)")
    print("     4. git add / commit / push")
    return 0


if __name__ == "__main__":
    sys.exit(main())