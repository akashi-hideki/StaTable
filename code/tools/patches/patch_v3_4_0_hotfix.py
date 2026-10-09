"""v3.4.0 hotfix: repair broken print() and README leftovers."""
from __future__ import annotations
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent.parent
CODE = ROOT / "code"


def fix_test() -> bool:
    path = CODE / "tests" / "test_v2_7_p4.py"
    if not path.exists():
        print(f"[ERR]  {path} not found")
        return False

    text = path.read_text(encoding="utf-8")

    # すでに修正済みか？
    if 'print("")' in text and 'isinstance(combo0, QComboBox)' in text:
        print("[SKIP] test_v2_7_p4.py already fixed")
        return True

    # 壊れた行: `    print("` + <改行> + `[5] ...")` を検出
    pattern = re.compile(
        r'    print\("\s*\[5\] _ActionListWidget operations"\)',
        re.DOTALL,
    )
    replacement = (
        '    print("")\n'
        '    print("[5] _ActionListWidget operations")'
    )
    new_text, n = pattern.subn(replacement, text, count=1)
    if n == 0:
        print("[WARN] broken print pattern not found")
        print("       (file may be OK already, or pattern changed)")
        return True

    path.write_text(new_text, encoding="utf-8", newline="\n")
    print(f"[OK]   fixed {path.name}: print() split into 2 lines")
    return True


def fix_readme() -> bool:
    path = ROOT / "README.md"
    if not path.exists():
        print(f"[ERR]  {path} not found")
        return False

    text = path.read_text(encoding="utf-8")
    before = text.count("1605")
    if before == 0:
        print("[SKIP] README.md: no 1605 remaining")
        return True

    text = text.replace("1605%20PASS", "1635%20PASS")
    text = text.replace("1605 PASS", "1635 PASS")
    after = text.count("1605")

    if before == after:
        print(f"[WARN] README.md: {before} occurrences of 1605 remain "
              "(unrecognized context)")
        return True

    path.write_text(text, encoding="utf-8", newline="\n")
    print(f"[OK]   fixed README.md: 1605 -> 1635 "
          f"({before - after} replaced, {after} left)")
    return True


def main() -> int:
    print("=" * 74)
    print("  v3.4.0 hotfix")
    print("=" * 74)
    ok1 = fix_test()
    ok2 = fix_readme()
    print()
    print(f"  test_v2_7_p4.py : {'OK' if ok1 else 'FAIL'}")
    print(f"  README.md       : {'OK' if ok2 else 'FAIL'}")
    print("=" * 74)
    return 0 if (ok1 and ok2) else 1


if __name__ == "__main__":
    sys.exit(main())