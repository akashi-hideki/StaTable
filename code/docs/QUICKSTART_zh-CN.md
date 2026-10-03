# StaTable 快速开始（5 分钟）

> 面向嵌入式系统的 MISRA C:2012 状态机设计与 C 代码生成工具

---

## 🚀 方式 1: 便携版（推荐，无需 Python）

### 步骤 1: 下载

从以下任一渠道下载 `StaTable-portable-v3.1.1-win64.zip`（约 174 MB）:

- **Gitee（中国国内高速）**: https://gitee.com/akashi-hideki/StaTable/releases
- **GitHub**: https://github.com/akashi-hideki/StaTable/releases

### 步骤 2: 解压

右键 → 解压到任意文件夹（如 `C:\StaTable`）

### 步骤 3: 启动

双击 `StaTable.exe`（首次启动可能较慢，10-20 秒）

### 步骤 4: 打开示例

菜单栏: **文件** → **打开** → `_internal/samples/vending_machine.xml`

**完成！** 您现在看到的是自动售货机的 3 层状态机示例。

---

## 🐍 方式 2: pip 安装（开发者）

```bash
pip install statable[gui]
python -m statable
```

---

## 🔧 常用操作

### 切换中文界面

1. 菜单栏: **Language / 语言** → **简体中文**
2. 点击 **立即重启**
3. 界面变为中文

### 生成 C 代码

1. **代码生成** → **生成 C 代码**
2. 选择输出文件夹
3. 点击生成

生成的文件符合 **MISRA C:2012** 规范，包含:

- 状态机转移表
- 角色函数框架
- 事件队列
- 中断处理
- 状态动作（Entry / Exit / Do）

### 查看状态图

每个状态机标签页自动显示 **Mermaid 状态图**。

---

## 📋 系统要求

| 方式 | 要求 |
|------|------|
| 便携版 | Windows 10/11 (x64) |
| pip | Python 3.10+, PySide6 |

---

## 📚 详细文档

- 完整教程: `_internal/docs/TUTORIAL_zh.md`
- README: `_internal/docs/README_zh-CN.md`

---

## 🆘 帮助

- **GitHub Issues**: https://github.com/akashi-hideki/StaTable/issues
- **Gitee Issues**: https://gitee.com/akashi-hideki/StaTable/issues
- **Email**: akashi.hideki@gmail.com

---

**License: Apache-2.0** | 商用可 | OEM 授权可

**Built with ❤️ for embedded engineers**
