# StaTable Eclipse Installer v0.1.0

**Release date:** 2026-10-11
**Tag:** `eclipse-installer-v0.1.0`

Independent tool that installs StaTable-generated C code into an
Eclipse CDT / ARM Cross GCC project.

## Features

- **Standalone GUI** (`StaTable-Eclipse-Installer.exe`)
- **CLI**: `--cli --project <root> --output <dir>`
- **Scaffolding templates** (optional, on by default):
  startup.s, linker.ld, syscalls.c, main.c, Makefile,
  .project, .cproject, .settings/*
- **Safety**: generated C overwritten; scaffolding preserved
  unless `--overwrite-scaffolding`

## Usage

StaTable-Eclipse-Installer.exe
StaTable-Eclipse-Installer.exe --cli --project <root> --output <dir>

## Verified

- Eclipse 4.41 (embedcpp) ARM Cross GCC: import + build
  (0 errors, 0 warnings)
- make build: firmware.elf 5528 bytes
- QEMU (netduinoplus2): UART output via USART1
- Test suite: test_v3_5_1_eclipse_installer.py (44 PASS)

## Compatibility

- Windows 10/11 (portable)
- Eclipse IDE for Embedded C/C++ Developers 4.41+
- Arm GNU Toolchain (arm-none-eabi-gcc)

## Source

See code/eclipse_installer/ in the repository.
