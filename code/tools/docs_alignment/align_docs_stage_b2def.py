"""v3.4.3 doc alignment — Stage B-2d/e/f: update §2.1 / §2.2 / §2.3.

Replaces the contiguous block from `### 2.1 整体结构` to just before
`## 3. 设计理论` with the new 7-layer versions.
"""
from __future__ import annotations
import sys
from pathlib import Path

DOC = (Path(__file__).resolve().parent.parent.parent
       / "code" / "docs" / "samples" / "LAYER_DESIGN_zh.md")

START_MARKER = "### 2.1 整体结构"
END_MARKER = "## 3. 设计理论"

NEW_BLOCK = """### 2.1 整体结构

```mermaid
flowchart TB
    Panel["Android 面板<br/>(主控 / UI / IoT)"]
    App["Application 层<br/>(序列执行 / 状态报告)"]
    MwMic["MwMicrowave 层<br/>(微波控制)"]
    MwOven["MwOven 层<br/>(烤箱 / 热风)"]
    MwGrill["MwGrill 层<br/>(烧烤)"]
    MwSteam["MwSteam 层<br/>(蒸汽)"]
    DrvIn["DriverInput 层<br/>(传感器 / RX / 门)"]
    DrvOut["DriverOutput 层<br/>(加热器 / 风扇 / TX)"]

    Panel -->|"序列命令 (RX)"| DrvIn
    DrvOut -->|"状态报告 (TX)"| Panel
    App --> MwMic
    App --> MwOven
    App --> MwGrill
    App --> MwSteam
    MwMic --> DrvIn
    MwMic --> DrvOut
    MwOven --> DrvIn
    MwOven --> DrvOut
    MwGrill --> DrvIn
    MwGrill --> DrvOut
    MwSteam --> DrvIn
    MwSteam --> DrvOut
```

### 2.2 层一览

| # | 层 | 职责 | 状态数 | 优先级 |
|---|---|---:|---:|---:|
| 1 | **Application** | 烹饪序列执行、状态报告 | 5 | 5 |
| 2 | **MwSteam** | 蒸汽发生控制 | 5 | 3 |
| 3 | **MwGrill** | 烧烤加热控制 | 3 | 3 |
| 4 | **MwOven** | 烤箱 / 热风控制 | 3 | 3 |
| 5 | **MwMicrowave** | 微波控制 | 4 | 3 |
| 6 | **DriverInput** | 输入系（传感器 / RX / 门） | 5 | 1 |
| 7 | **DriverOutput** | 输出系（加热器 / 风扇 / TX） | 6 | 1 |

**优先级数值越小越先执行**（DriverInput / DriverOutput 最优先）。

### 2.3 命名空间

| 层名 | 命名空间 | 生成文件前缀 |
|---|---|---|
| Application | `Application.*` | `statable_*_Application.c` |
| MwSteam | `MwSteam.*` | `statable_*_MwSteam.c` |
| MwGrill | `MwGrill.*` | `statable_*_MwGrill.c` |
| MwOven | `MwOven.*` | `statable_*_MwOven.c` |
| MwMicrowave | `MwMicrowave.*` | `statable_*_MwMicrowave.c` |
| DriverInput | `DriverInput.*` | `statable_*_DriverInput.c` |
| DriverOutput | `DriverOutput.*` | `statable_*_DriverOutput.c` |

---

"""


def main() -> int:
    if not DOC.exists():
        print(f"[ERR] {DOC} not found")
        return 1

    text = DOC.read_text(encoding="utf-8")

    if "DriverInput 层<br/>(传感器" in text or "| 6 | **DriverInput** |" in text:
        print("[SKIP] §2.1-2.3 already updated")
        return 0

    s = text.find(START_MARKER)
    e = text.find(END_MARKER)
    if s == -1 or e == -1 or e <= s:
        print(f"[ERR] markers not found or out of order")
        print(f"     start={s}, end={e}")
        return 1

    old_block = text[s:e]
    new_text = text[:s] + NEW_BLOCK + text[e:]
    DOC.write_text(new_text, encoding="utf-8", newline="\n")
    print(f"[OK] LAYER_DESIGN_zh.md: §2.1-2.3 updated")
    print(f"     old block: {len(old_block)} chars")
    print(f"     new block: {len(NEW_BLOCK)} chars")
    return 0


if __name__ == "__main__":
    sys.exit(main())