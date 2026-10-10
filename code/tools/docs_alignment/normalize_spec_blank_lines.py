"""Normalize blank lines in SPEC_STATE_ACTIONS_v1_{en,zh}.md."""
from __future__ import annotations
import re
import sys
from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent.parent / "docs"


def normalize(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    # 3+ consecutive newlines -> exactly 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Collapse trailing blank lines to single \n
    text = text.rstrip() + "\n"
    path.write_text(text, encoding="utf-8", newline="\n")
    print(f"[OK] {path.name}: {path.stat().st_size} bytes")


def main() -> int:
    for name in ("SPEC_STATE_ACTIONS_v1_en.md", "SPEC_STATE_ACTIONS_v1_zh.md"):
        normalize(DOCS / name)
    return 0


if __name__ == "__main__":
    sys.exit(main())