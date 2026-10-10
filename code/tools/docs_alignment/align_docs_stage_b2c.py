"""v3.4.3 doc alignment — Stage B-2c: update TOC + version.

Updates:
  - TOC section for chapter 4 (6 entries -> 7 entries)
  - File header Version: 1.0 -> 1.1
"""
from __future__ import annotations
import sys
from pathlib import Path

DOC = (Path(__file__).resolve().parent.parent.parent
       / "code" / "docs" / "samples" / "LAYER_DESIGN_zh.md")


# --- TOC block replacement ----------------------------------------------
OLD_TOC = """4. 实现详解
   - 4.1 Driver 层
   - 4.2 MwMicrowave 层
   - 4.3 MwOven 层
   - 4.4 MwGrill 层
   - 4.5 MwSteam 层
   - 4.6 Application 层"""

NEW_TOC = """4. 实现详解
   - 4.1 DriverInput 层（输入系）
   - 4.2 DriverOutput 层（输出系）
   - 4.3 MwMicrowave 层
   - 4.4 MwOven 层
   - 4.5 MwGrill 层
   - 4.6 MwSteam 层
   - 4.7 Application 层"""


def main() -> int:
    if not DOC.exists():
        print(f"[ERR] {DOC} not found")
        return 1

    text = DOC.read_text(encoding="utf-8")
    orig = text

    # Idempotency
    if "4.7 Application 层" in text and "- 4.1 DriverInput 层" in text:
        print("[SKIP] TOC already updated")
    else:
        # Try exact block first
        if OLD_TOC in text:
            text = text.replace(OLD_TOC, NEW_TOC, 1)
            print("[OK]   TOC block replaced (exact match)")
        else:
            # Fallback: replace individual lines
            text = text.replace("- 4.1 Driver 层", "- 4.1 DriverInput 层（输入系）")
            text = text.replace("- 4.2 MwMicrowave 层",
                                "- 4.2 DriverOutput 层（输出系）\n   - 4.3 MwMicrowave 层")
            text = text.replace("- 4.3 MwOven 层", "- 4.4 MwOven 层")
            text = text.replace("- 4.4 MwGrill 层", "- 4.5 MwGrill 层")
            text = text.replace("- 4.5 MwSteam 层", "- 4.6 MwSteam 层")
            text = text.replace("- 4.6 Application 层", "- 4.7 Application 层")
            print("[OK]   TOC updated (line-by-line)")

    # Version bump
    if "Version: 1.0" in text:
        text = text.replace("Version: 1.0", "Version: 1.1", 1)
        print("[OK]   Version: 1.0 -> 1.1")

    if text == orig:
        print("[SKIP] nothing changed")
        return 0

    DOC.write_text(text, encoding="utf-8", newline="\n")
    print(f"[OK] LAYER_DESIGN_zh.md: TOC + version updated")
    return 0


if __name__ == "__main__":
    sys.exit(main())