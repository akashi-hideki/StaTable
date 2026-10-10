"""Fix README.md SPEC_STATE_ACTIONS references.

Changes:
  1. Line 36: "See ..." -> EN + ZH links only (per user request)
  2. Line 501 (doc table): expand to EN / ZH / JA rows
     (JA kept because test_readme_consistency.py requires
      SPEC_STATE_ACTIONS_v1_ja.md to be linked)
"""
from __future__ import annotations
import sys
from pathlib import Path

README = Path(__file__).resolve().parent.parent.parent.parent / "README.md"


OLD_SEE = (
    "See [SPEC_STATE_ACTIONS_v1.md]"
    "(code/docs/SPEC_STATE_ACTIONS_v1.md) for details."
)
NEW_SEE = (
    "See [SPEC_STATE_ACTIONS_v1_en.md]"
    "(code/docs/SPEC_STATE_ACTIONS_v1_en.md) or\n"
    "[SPEC_STATE_ACTIONS_v1_zh.md]"
    "(code/docs/SPEC_STATE_ACTIONS_v1_zh.md) for details."
)

OLD_ROW = (
    "| [SPEC_STATE_ACTIONS_v1.md](code/docs/SPEC_STATE_ACTIONS_v1.md) "
    "| English | **v2.7** State actions (Entry/Exit/Do) specification |"
)
NEW_ROW = (
    "| [SPEC_STATE_ACTIONS_v1_en.md](code/docs/SPEC_STATE_ACTIONS_v1_en.md) "
    "| English | **v2.7** State actions (Entry/Exit/Do) specification |\n"
    "| [SPEC_STATE_ACTIONS_v1_zh.md](code/docs/SPEC_STATE_ACTIONS_v1_zh.md) "
    "| 中文 | **v2.7** State actions (Entry/Exit/Do) specification |\n"
    "| [SPEC_STATE_ACTIONS_v1_ja.md](code/docs/SPEC_STATE_ACTIONS_v1_ja.md) "
    "| 日本語 | **v2.7** State actions (Entry/Exit/Do) specification |"
)


def main() -> int:
    if not README.exists():
        print(f"[ERR] {README} not found")
        return 1

    text = README.read_text(encoding="utf-8")
    orig = text
    changes = 0

    # 1. "See ..." line
    if NEW_SEE.split("\n")[0] in text:
        print("[SKIP] 'See ...' line already updated")
    elif OLD_SEE in text:
        text = text.replace(OLD_SEE, NEW_SEE, 1)
        print("[OK]   'See ...' line -> EN + ZH (no JA)")
        changes += 1
    else:
        print("[WARN] 'See ...' pattern not found; check manually")

    # 2. Doc table row
    if NEW_ROW.split("\n")[0] in text:
        print("[SKIP] Doc table row already expanded")
    elif OLD_ROW in text:
        text = text.replace(OLD_ROW, NEW_ROW, 1)
        print("[OK]   Doc table row -> EN / ZH / JA")
        changes += 1
    else:
        print("[WARN] Doc table row pattern not found; check manually")

    if text == orig:
        print("[SKIP] nothing changed")
        return 0

    README.write_text(text, encoding="utf-8", newline="\n")
    print(f"[OK] README.md updated ({changes} change(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())