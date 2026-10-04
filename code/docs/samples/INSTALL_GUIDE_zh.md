# StaTable 安装指南 — 复合烹饪器具

Version: 1.0
Date: 2026-10-04
适用：Windows 10 / 11（x64）

---

## 目录

1. 两种安装方式
2. 方式 A: 便携版 ZIP（推荐）
3. 方式 B: Python 包（开发用）
4. 首次启动
5. 验证安装
6. 常见问题

---

## 1. 两种安装方式

| 方式 | 适用 | Python 需要 | 安装时间 |
|---|---|---|---|
| **A: 便携版 ZIP** | 一般设计者 | 不需要 | 5 分钟 |
| **B: Python 包** | 开发 / CLI 用户 | 需要 | 10 分钟 |

**推荐**：日常使用选 **A**；需要 CLI 或 SDK 集成选 **B**。

---

## 2. 方式 A: 便携版 ZIP（推荐）

### 2.1 前提

- Windows 10 / 11 (x64)
- 解压工具（7-Zip / Windows 标准功能）
- 约 500 MB 空闲磁盘空间

### 2.2 安装步骤

#### 步骤 1: 下载

从 GitHub Release 下载:
```
StaTable-portable-v3.3.0-win64.zip (约 174 MB)
```

**地址**: `https://github.com/akashi-hideki/StaTable/releases/tag/v3.3.0`

#### 步骤 2: 解压

1. 右键 ZIP → **全部解压缩**
2. 解压位置: **全英文路径** 推荐
   - ✅ 推荐: `C:\StaTable\`
   - ❌ 避免: `C:\用户\文档\StaTable\`

#### 步骤 3: 确认文件结构

```
C:\StaTable\
├── StaTable.exe          ← 双击启动
├── _internal\            ← 依赖文件
├── docs\                 ← 同梱文档
├── Resources\            ← Mermaid 等
└── ...
```

### 2.3 启动

1. 双击 `StaTable.exe`
2. Windows Defender 可能提示警告
   → 点击 **更多信息** → **仍要运行**
3. StaTable GUI 启动

---

## 3. 方式 B: Python 包（开发用）

### 3.1 前提

- Python 3.10 或更高
- pip (Python 附带)

### 3.2 安装

```powershell
# 含 GUI
pip install "statable[gui]"

# 仅 CLI
pip install statable
```

### 3.3 启动

```powershell
# GUI
python -m statable

# CLI
statable-cli --help
```

---

## 4. 首次启动

### 4.1 启动画面

```
+------------------------------------------+
|  StaTable - Untitled[*]                  |
+------------------------------------------+
|  File  Edit  Code generation  Validate   |
+------------------------------------------+
|                                          |
|  [Application] [Driver] [Middleware]     |
|                                          |
|  +-- Matrix (top) -----------------+     |
|  |                                 |     |
|  +---------------------------------+     |
|  +-- Mermaid diagram -------------+      |
|  |                                 |     |
|  +---------------------------------+     |
+------------------------------------------+
```

### 4.2 打开示例项目

1. **File → Open Project...**
2. 选择 `code/docs/samples/cooking_heater_controller.xml`
3. 六层架构示例加载（约 5 秒）

### 4.3 生成 C 代码

1. **Code generation → Code generation... (Ctrl+G)**
2. 输出先: `C:\projects\cooking\output`
3. 点击 **Generate** 按钮 → 生成约 51 个文件

### 4.4 编译验证

命令行:

```powershell
cd C:\path\to\StaTable\code
python tools\verify_c_syntax.py `
    --root C:\projects\cooking\output `
    --compiler both `
    --std c99 --strict
```

**预期输出**:
```
gcc      PASS     (24/24)
arm      PASS     (24/24)
Overall:  ALL PASS
```

---

## 5. 验证安装

### 5.1 便携版 ZIP

| 检查 | 期望 |
|---|---|
| StaTable.exe 存在 | ✅ |
| 双击启动 | GUI 显示 |
| 打开示例 XML | 加载成功 |
| 生成 C 代码 | 51 文件 |

### 5.2 Python 包

```powershell
python -c "import statable; print(statable.__version__)"
# → 3.3.0
```

---

## 6. 常见问题

### Q1: Windows Defender 阻止启动

**原因**: 未签名 exe。

**对策**: **更多信息** → **仍要运行**，或加入排除列表。

### Q2: 中文路径下无法启动

**原因**: Qt / Python 对非 ASCII 路径支持有限。

**对策**: 移动到 `C:\StaTable\` 等全英文路径。

### Q3: 缺少 MSVCRUNTIME140.dll

**原因**: Visual C++ Redistributable 未安装。

**对策**: 下载安装 `vc_redist.x64.exe`（Microsoft 官网）。

### Q4: GUI 不显示（黑屏）

**原因**: 显卡驱动问题。

**对策**:
```powershell
# 环境变量设置
$env:QT_OPENGL = "software"
C:\StaTable\StaTable.exe
```

### Q5: 生成文件过大（500+ MB）

**原因**: 包含 PySide6 / Qt 全库。

**对策**: 这是正常大小。分发时用 ZIP 压缩到约 174 MB。

### Q6: 无法连接 GitHub 下载

**原因**: 网络限制。

**对策**:
- 使用代理 / VPN
- 或从镜像下载（如有）

---

## 变更历史

| 版本 | 日期 | 内容 |
|---|---|---|
| 1.0 | 2026-10-04 | 初版 |

---

*本指南为 Galanz 复合烹饪器具的 StaTable 安装参考。*