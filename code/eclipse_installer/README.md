# StaTable Eclipse Installer

**Version:** 0.1.1
**Standalone tool** — not bundled with StaTable itself.

## What it does

Installs StaTable-generated C code into an Eclipse CDT / ARM Cross GCC
project, with optional scaffolding:

| File | Purpose |
|------|---------|
| `startup_stm32f405.s` | Cortex-M4 vector table + Reset_Handler |
| `linker_stm32f405.ld` | FLASH 1MB / RAM 128KB (STM32F405) |
| `syscalls.c` | `printf` -> USART1 (QEMU netduinoplus2 / real HW) |
| `main.c` | demo entry with weak `app_init()` / `app_step()` |
| `Makefile` | cross-platform (Windows / POSIX) |
| `.project` / `.cproject` | Eclipse 4.41 ARM Cross GCC |
| `.settings/*` | encoding + language providers |

## Quick start (GUI)

1. Launch `StaTable-Eclipse-Installer.exe`.
2. **Eclipse project root**: select the folder containing `.project`
   (or an empty folder to create a new project).
3. **StaTable output/ dir**: select the directory where StaTable
   wrote its generated C code.
4. Leave the scaffolding checkboxes checked (recommended).
5. Click **Install**.
6. Open Eclipse, import the project
   (**File -> Import -> Existing Projects into Workspace**),
   then **Ctrl+B** to build.

## Quick start (CLI)

```
StaTable-Eclipse-Installer.exe --cli ^
    --project C:\path\to\eclipse_project ^
    --output C:\path\to\statable\output
```

Optional flags:

| Flag | Effect |
|------|--------|
| `--no-startup` / `--no-linker` / `--no-syscalls` / `--no-main` / `--no-makefile` / `--no-eclipse-project` | skip specific scaffolding |
| `--samples` | also copy `*.xml` to `<project>/samples/` |
| `--overwrite-scaffolding` | overwrite existing root-level scaffolding files |
| `--subdir <path>` | install generated C under a custom subdir |

## Requirements

- Windows 10/11 (64-bit)
- Eclipse IDE for Embedded C/C++ Developers 4.41+ (ARM Cross GCC)
- Arm GNU Toolchain (`arm-none-eabi-gcc`) on PATH
- (optional, for verification) QEMU `netduinoplus2`

## Safety

- Generated C code is overwritten by default.
- Scaffolding files (main.c, Makefile, .project, etc.) are **not**
  overwritten unless `--overwrite-scaffolding` is given.

## Verified

- Eclipse 4.41 (embedcpp) ARM Cross GCC: import + build 0 errors
- `firmware.elf` 5528 bytes; `firmware.bin` 5192 bytes
- QEMU `netduinoplus2`: UART output via USART1

## License

Same as StaTable project (see repository root).
