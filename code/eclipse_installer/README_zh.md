# StaTable Eclipse Installer

**版本：** 0.1.1
**独立工具** —— 不随 StaTable 本体捆绑发布。

## 功能

将 StaTable 生成的 C 代码安装到 Eclipse CDT / ARM Cross GCC 项目，
并可选地生成以下脚手架文件：

| 文件 | 用途 |
|------|------|
| `startup_stm32f405.s` | Cortex-M4 向量表 + Reset_Handler |
| `linker_stm32f405.ld` | FLASH 1MB / RAM 128KB (STM32F405) |
| `syscalls.c` | `printf` -> USART1（QEMU netduinoplus2 / 实机） |
| `main.c` | 含弱符号 `app_init()` / `app_step()` 的演示入口 |
| `Makefile` | 跨平台（Windows / POSIX） |
| `.project` / `.cproject` | Eclipse 4.41 ARM Cross GCC 工程 |
| `.settings/*` | 编码与语言设置 |

## 快速上手（图形界面）

1. 启动 `StaTable-Eclipse-Installer.exe`。
2. **Eclipse project root**：选择包含 `.project` 的文件夹
   （或选择一个空文件夹以创建新工程）。
3. **StaTable output/ dir**：选择 StaTable 生成 C 代码的目录。
4. 保持脚手架复选框为选中状态（推荐）。
5. 点击 **Install**。
6. 打开 Eclipse，导入工程
   （**File -> Import -> Existing Projects into Workspace**），
   然后按 **Ctrl+B** 编译。

## 快速上手（命令行）

```
StaTable-Eclipse-Installer.exe --cli ^
    --project C:\path\to\eclipse_project ^
    --output C:\path\to\statable\output
```

可选参数：

| 参数 | 作用 |
|------|------|
| `--no-startup` / `--no-linker` / `--no-syscalls` / `--no-main` / `--no-makefile` / `--no-eclipse-project` | 跳过特定脚手架文件 |
| `--samples` | 同时将 `*.xml` 复制到 `<project>/samples/` |
| `--overwrite-scaffolding` | 覆盖已存在的根目录脚手架文件 |
| `--subdir <path>` | 将生成的 C 代码安装到自定义子目录 |

## 运行要求

- Windows 10/11（64 位）
- Eclipse IDE for Embedded C/C++ Developers 4.41 及以上（ARM Cross GCC）
- Arm GNU Toolchain（`arm-none-eabi-gcc`）已加入 PATH
- （可选，用于验证）QEMU `netduinoplus2`

## 安全性

- 生成的 C 代码默认会被覆盖。
- 脚手架文件（main.c、Makefile、.project 等）在未指定
  `--overwrite-scaffolding` 时**不会被覆盖**。

## 已验证

- Eclipse 4.41 (embedcpp) ARM Cross GCC：导入 + 编译 0 错误
- `firmware.elf` 5528 字节；`firmware.bin` 5192 字节
- QEMU `netduinoplus2`：通过 USART1 输出 UART 日志

## 许可证

与 StaTable 项目一致（见仓库根目录）。
