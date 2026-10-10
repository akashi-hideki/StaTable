from pathlib import Path
import re

DOCS = Path(r"C:\Users\user\OneDrive\ドキュメント\GitHub\StaTable\code\docs")

for name in ("SPEC_STATE_ACTIONS_v1_en.md", "SPEC_STATE_ACTIONS_v1_zh.md"):
    p = DOCS / name
    if not p.exists():
        continue
    text = p.read_text(encoding="utf-8")
    new = re.sub(r"^```[ \t]*\n(?:[ \t]*\n)+```[ \t]*\n", "", text, flags=re.MULTILINE)
    if new != text:
        p.write_text(new, encoding="utf-8", newline="\n")
        print("fixed:", name)
    else:
        print("no change:", name)