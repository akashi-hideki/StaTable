"""v3.4.3 doc alignment — Stage B-3d (v2): update TOC only.

Fixed: restrict replacement to the TOC section (between `## 目录` and
the next `---`), so body headings are not touched.
"""
from __future__ import annotations
import sys
from pathlib import Path

DOC = (Path(__file__).resolve().parent.parent.parent
       / "code" / "docs" / "samples" / "ROLE_FUNCTIONS_zh.md")

TOC_START = "## 目录"
TOC_END = "\n---"

# Old -> new mapping for TOC lines only
TOC_MAP = {
    "3. Driver 层（13 个）":       "3. DriverInput 层（6 个）\n4. DriverOutput 层（13 个）",
    "4. MwMicrowave 层（6 个）":   "5. MwMicrowave 层（6 个）",
    "5. MwOven 层（10 个）":        "6. MwOven 层（10 个）",
    "6. MwGrill 层（6 个）":         "7. MwGrill 层（6 个）",
    "7. MwSteam 层（9 个）":         "8. MwSteam 层（9 个）",
    "8. Application 层（10 个）":   "9. Application 层（10 个）",
    "9. 通用实现模式":                "10. 通用实现模式",
    "10. 变更历史":                   "11. 变更历史",
}


def main() -> int:
    if not DOC.exists():
        print(f"[ERR] {DOC} not found")
        return 1

    text = DOC.read_text(encoding="utf-8")

    # Locate TOC
    toc_start = text.find(TOC_START)
    if toc_start == -1:
        print(f"[ERR] '{TOC_START}' not found")
        return 1
    toc_end = text.find(TOC_END, toc_start + len(TOC_START))
    if toc_end == -1:
        print(f"[ERR] TOC end not found")
        return 1

    toc = text[toc_start:toc_end]

    # Idempotency: check for new entries IN TOC only
    if "3. DriverInput 层（6 个）" in toc:
        print("[SKIP] TOC already updated")
        return 0

    # Apply replacements within TOC
    new_toc = toc
    for old, new in TOC_MAP.items():
        # Match whole line
        import re
        pattern = re.compile(
            rf"^{re.escape(old)}\s*$",
            re.MULTILINE,
        )
        new_toc, n = pattern.subn(new, new_toc)
        if n:
            print(f"  [OK] {old!r} -> {new!r}")

    if new_toc == toc:
        print("[WARN] no TOC changes applied")
        return 1

    new_text = text[:toc_start] + new_toc + text[toc_end:]
    DOC.write_text(new_text, encoding="utf-8", newline="\n")
    print(f"[OK] ROLE_FUNCTIONS_zh.md: TOC updated")
    return 0


if __name__ == "__main__":
    sys.exit(main())