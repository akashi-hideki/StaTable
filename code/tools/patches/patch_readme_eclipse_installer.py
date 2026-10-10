"""patch_readme_eclipse_installer.py"""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
README = ROOT / "README.md"

t = README.read_text(encoding="utf-8")

ANCHOR = "### v2.8.0"

INSERT = """### Eclipse Installer (v0.1.0 / standalone)

**Separate app**, not bundled with StaTable itself.

**StaTable-Eclipse-Installer.exe** copies StaTable-generated C
code into an Eclipse CDT / ARM Cross GCC project, with optional
scaffolding (startup.s, linker.ld, syscalls.c, main.c, Makefile,
.project, .cproject, .settings).

**Download:** see the eclipse-installer-v0.1.0 release:
https://github.com/akashi-hideki/StaTable/releases/tag/eclipse-installer-v0.1.0
(StaTable-Eclipse-Installer-v0.1.0-win64.zip, 45.8 MB).

**Usage (GUI):**

1. Launch StaTable-Eclipse-Installer.exe
2. Select Eclipse project root (folder containing .project)
3. Select StaTable output/ dir (from the code generator)
4. Click Install

**Usage (CLI):**

StaTable-Eclipse-Installer.exe --cli --project P --output O

**Verified:** Eclipse 4.41 (embedcpp) ARM Cross GCC import +
build (0 errors), make build (firmware.elf 5528 bytes),
QEMU netduinoplus2 UART output.


### v2.8.0"""

if "### Eclipse Installer" in t:
    print("[SKIP] already present")
elif ANCHOR not in t:
    raise SystemExit("[FAIL] anchor not found")
else:
    t = t.replace(ANCHOR, INSERT, 1)
    README.write_text(t, encoding="utf-8")
    print(f"[OK] {README}")
