"""Add launch instructions to README_zh.md (package version)."""
from __future__ import annotations
import sys
from pathlib import Path

README = Path(__file__).resolve().parent.parent.parent.parent \
    / "code" / "docs" / "samples" / "README_zh.md"

INSERTION_MARKER = "## 快速开始"

LAUNCH_BLOCK = """## 本包的使用方法（重要）

**本包为绿色便携版，无需安装即可使用。**

### 启动步骤

1. **解压** `StaTable-CookingHeater-Package-v3.4.3.zip`（一次即可）
2. **进入**解压后的文件夹 `StaTable-CookingHeater-Package-v3.4.3/`
3. **双击** `StaTable\\\\StaTable.exe` 启动

### 重要注意

- `StaTable.exe` 必须与其同目录下的 `_internal\\\\` 文件夹一起使用
- **请勿单独复制** `StaTable.exe`（会无法启动）
- 首次启动约需 2-3 秒

### 首次使用

1. **File > Open Project...**
2. 选择 `samples\\\\cooking_heater_controller.xml`
3. 七层架构示例加载（约 5 秒）
4. **Code generation > Generate Code... (Ctrl+G)** 生成 C 代码

"""


def main() -> int:
    if not README.exists():
        print(f"[ERR] {README} not found")
        return 1
    text = README.read_text(encoding="utf-8")

    if "本包为绿色便携版" in text:
        print("[SKIP] README_zh.md already has package launch instructions")
        return 0

    if INSERTION_MARKER not in text:
        print(f"[ERR] marker '{INSERTION_MARKER}' not found in README_zh.md")
        return 1

    text = text.replace(INSERTION_MARKER, LAUNCH_BLOCK + INSERTION_MARKER, 1)
    README.write_text(text, encoding="utf-8", newline="\n")
    print(f"[OK] README_zh.md updated ({README.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())