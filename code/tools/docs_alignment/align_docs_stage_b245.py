"""v3.4.3 doc alignment — Stage B-2k/B-4/B-5 batch.

  B-2k: LAYER_DESIGN_zh.md -> add v1.1 entry to 变更历史
  B-4:  README_zh.md -> 23 -> 31 states, 54 -> 60 roles, Driver -> DriverInput/Output
  B-5:  INSTALL_GUIDE_zh.md -> [Driver] -> [DriverInput] [DriverOutput]
"""
from __future__ import annotations
import sys
from pathlib import Path

DOCS = (Path(__file__).resolve().parent.parent.parent
        / "code" / "docs" / "samples")

LAYER = DOCS / "LAYER_DESIGN_zh.md"
README = DOCS / "README_zh.md"
INSTALL = DOCS / "INSTALL_GUIDE_zh.md"


# ============================================================
# B-2k: LAYER_DESIGN changelog
# ============================================================
def patch_b2k() -> bool:
    if not LAYER.exists():
        print(f"[MISS] {LAYER.name}")
        return False
    text = LAYER.read_text(encoding="utf-8")
    if "| 1.1 |" in text and "v3.4.3" in text:
        print(f"[SKIP] {LAYER.name}: v1.1 already present")
        return True

    # Find the changelog table header
    # (usually near end, contains "| 版本 | 日期 | 内容 |")
    marker = "| 1.0 | 2026-10-04 | 初版（六层架构设计指南） |"
    if marker not in text:
        # try alternative
        import re
        m = re.search(r"^\| 1\.0 \| 2026-10-04 \|.*$", text, re.MULTILINE)
        if not m:
            print(f"[ERR]  {LAYER.name}: changelog marker not found")
            return False
        old_line = m.group(0)
    else:
        old_line = marker

    new_line = (
        "| 1.0 | 2026-10-04 | 初版（六层架构设计指南） |\n"
        "| 1.1 | 2026-10-10 | v3.4.3 整備：7 層架構（DriverInput / DriverOutput 分割）、"
        "MwMicrowave +1 状態、MwSteam +2 状態、Role 60 個 |"
    )
    text = text.replace(old_line, new_line, 1)
    LAYER.write_text(text, encoding="utf-8", newline="\n")
    print(f"[OK]   {LAYER.name}: v1.1 entry added")
    return True


# ============================================================
# B-4: README_zh.md updates
# ============================================================
def patch_b4() -> bool:
    if not README.exists():
        print(f"[MISS] {README.name}")
        return False
    text = README.read_text(encoding="utf-8")
    orig = text

    # Layer count / state count
    text = text.replace("| **合计** | | **23** |", "| **合计** | | **31** |")
    text = text.replace("六层架构: **23 状态**", "七层架构: **31 状态**")

    # Role count
    text = text.replace("54 个 Role 函数", "60 个 Role 函数")
    text = text.replace("54 个 **Role 函数**", "60 个 **Role 函数**")

    # Layer table rows
    text = text.replace(
        "| Driver | HW / 通信 / 传感器 | 6 |",
        "| DriverInput | 输入系（传感器 / RX / 门） | 5 |\n"
        "| DriverOutput | 输出系（加热器 / 风扇 / TX） | 6 |"
    )
    text = text.replace(
        "|  Driver 层（HW / 通信 / 传感器）              |",
        "|  DriverInput 层（传感器 / RX / 门）           |\n"
        "|  DriverOutput 层（加热器 / 风扇 / TX）        |"
    )
    # State counts in layer table
    text = text.replace("| MwSteam | 蒸汽发生控制 | 3 |",
                        "| MwSteam | 蒸汽发生控制 | 5 |")
    text = text.replace("| MwMicrowave | 微波控制 | 3 |",
                        "| MwMicrowave | 微波控制 | 4 |")

    if text == orig:
        print(f"[SKIP] {README.name}: nothing to change")
        return True

    README.write_text(text, encoding="utf-8", newline="\n")
    print(f"[OK]   {README.name}: numeric updates applied")
    return True


# ============================================================
# B-5: INSTALL_GUIDE_zh.md tab labels
# ============================================================
def patch_b5() -> bool:
    if not INSTALL.exists():
        print(f"[MISS] {INSTALL.name}")
        return False
    text = INSTALL.read_text(encoding="utf-8")
    if "[DriverInput]" in text:
        print(f"[SKIP] {INSTALL.name}: already updated")
        return True

    text = text.replace(
        "|  [Application] [Driver] [Middleware]     |",
        "|  [Application] [DriverInput] [DriverOutput] |"
    )
    text = text.replace(
        "[Application] [Driver] [Middleware]",
        "[Application] [DriverInput] [DriverOutput]"
    )
    INSTALL.write_text(text, encoding="utf-8", newline="\n")
    print(f"[OK]   {INSTALL.name}: tab labels updated")
    return True


def main() -> int:
    print("=" * 74)
    print("  Stage B-2k / B-4 / B-5 batch")
    print("=" * 74)
    ok1 = patch_b2k()
    ok2 = patch_b4()
    ok3 = patch_b5()
    print()
    print(f"  B-2k (LAYER changelog) : {'OK' if ok1 else 'FAIL'}")
    print(f"  B-4  (README)          : {'OK' if ok2 else 'FAIL'}")
    print(f"  B-5  (INSTALL_GUIDE)   : {'OK' if ok3 else 'FAIL'}")
    return 0 if (ok1 and ok2 and ok3) else 1


if __name__ == "__main__":
    sys.exit(main())