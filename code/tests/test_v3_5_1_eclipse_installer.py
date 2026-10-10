# tests/test_v3_5_1_eclipse_installer.py
"""
StaTable v3.5.1 Eclipse Installer test suite

Static + runtime checks for `eclipse_installer`:
  - Package structure (core / gui / cli / templates)
  - Template placeholders (@@KEY@@)
  - Template tab characters in Makefile
  - Core install: copies generated code + scaffolding
  - Safety: overwrite flags respected
  - Placeholder substitution (PROJECT_NAME / VERSION)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tempfile
from pathlib import Path

_total = 0
_passed = 0
_failed = 0


def check(label, condition):
    global _total, _passed, _failed
    _total += 1
    if condition:
        _passed += 1
        print(f"  [PASS] {label}")
    else:
        _failed += 1
        print(f"  [FAIL] {label}")


def section(title):
    print()
    print(f"[{title}]")


ROOT = Path(__file__).resolve().parent.parent
EI = ROOT / "eclipse_installer"
TPL = EI / "templates"

# ======================================================================
# [1] Static: package structure
# ======================================================================
section("1 package structure")

check("eclipse_installer/__init__.py exists",
      (EI / "__init__.py").is_file())
check("eclipse_installer/core.py exists",
      (EI / "core.py").is_file())
check("eclipse_installer/gui.py exists",
      (EI / "gui.py").is_file())
check("eclipse_installer/cli.py exists",
      (EI / "cli.py").is_file())
check("eclipse_installer/__main__.py exists",
      (EI / "__main__.py").is_file())

# ======================================================================
# [2] Static: templates
# ======================================================================
section("2 templates")

expected_tpls = [
    "startup_stm32f405.s",
    "linker_stm32f405.ld",
    "syscalls.c",
    "main_demo.c",
    "Makefile.tmpl",
    "project.tmpl",
    "cproject.tmpl",
]
for name in expected_tpls:
    check(f"template: {name}", (TPL / name).is_file())

check("template: settings/org.eclipse.core.resources.prefs",
      (TPL / "settings" / "org.eclipse.core.resources.prefs").is_file())
check("template: settings/language.settings.xml",
      (TPL / "settings" / "language.settings.xml").is_file())

# Tab characters in Makefile (recipe lines need literal tabs)
mk_bytes = (TPL / "Makefile.tmpl").read_bytes()
check("Makefile.tmpl contains tab characters (>= 5)",
      mk_bytes.count(9) >= 5)

# Placeholders
mk_text = (TPL / "main_demo.c").read_text(encoding="utf-8")
check("main_demo.c uses @@PROJECT_NAME@@",
      "@@PROJECT_NAME@@" in mk_text)
check("main_demo.c uses @@VERSION@@",
      "@@VERSION@@" in mk_text)

proj_text = (TPL / "project.tmpl").read_text(encoding="utf-8")
check("project.tmpl uses @@PROJECT_NAME@@",
      "@@PROJECT_NAME@@" in proj_text)

cproj_text = (TPL / "cproject.tmpl").read_text(encoding="utf-8")
check("cproject.tmpl uses @@PROJECT_NAME@@",
      "@@PROJECT_NAME@@" in cproj_text)
check("cproject.tmpl has Arm Cross GCC toolchain",
      "Arm Cross GCC" in cproj_text)
check("cproject.tmpl has arm-none-eabi- prefix",
      "arm-none-eabi-" in cproj_text)

# No BOM in linker.ld (would break ld)
ld_bytes = (TPL / "linker_stm32f405.ld").read_bytes()
check("linker_stm32f405.ld has no BOM",
      not ld_bytes.startswith(b"\xef\xbb\xbf"))

# _sbrk present in syscalls.c
sc_text = (TPL / "syscalls.c").read_text(encoding="utf-8")
check("syscalls.c defines _sbrk", "_sbrk" in sc_text)
check("syscalls.c uses USART1 (QEMU netduinoplus2)",
      "USART1" in sc_text)

# ======================================================================
# [3] Runtime: core.install with tempdir
# ======================================================================
section("3 core.install runtime")

from eclipse_installer.core import InstallOptions, install


def _mkfile(root, rel, content="x"):
    full = os.path.join(root, rel)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)
    return os.path.abspath(full)


with tempfile.TemporaryDirectory() as out_td:
    with tempfile.TemporaryDirectory() as proj_td:
        # Fake output_dir with a generated C file + header
        _mkfile(out_td, "Application/statable_transitions_Application.c",
                "/* generated */")
        _mkfile(out_td, "Application/statable_transitions_Application.h",
                "/* header */")
        _mkfile(out_td, "statable_init.c", "/* init */")

        opts = InstallOptions(
            project_root=Path(proj_td),
            output_dir=Path(out_td),
        )
        res = install(opts)

        check("install: no errors", len(res.errors) == 0)
        check("install: installed > 0", len(res.installed) > 0)

        # Generated C files under src/statable_generated
        gen_dir = Path(proj_td) / "src" / "statable_generated"
        check("generated C copied",
              (gen_dir / "Application"
               / "statable_transitions_Application.c").is_file())
        check("generated H copied",
              (gen_dir / "Application"
               / "statable_transitions_Application.h").is_file())
        check("root-level generated .c copied",
              (gen_dir / "statable_init.c").is_file())

        # Scaffolding files at project root
        check("startup.s installed",
              (Path(proj_td) / "startup_stm32f405.s").is_file())
        check("linker.ld installed",
              (Path(proj_td) / "linker_stm32f405.ld").is_file())
        check("syscalls.c installed",
              (Path(proj_td) / "syscalls.c").is_file())
        check("main.c installed",
              (Path(proj_td) / "main.c").is_file())
        check("Makefile installed",
              (Path(proj_td) / "Makefile").is_file())
        check(".project installed",
              (Path(proj_td) / ".project").is_file())
        check(".cproject installed",
              (Path(proj_td) / ".cproject").is_file())
        check(".settings installed",
              (Path(proj_td) / ".settings"
               / "org.eclipse.core.resources.prefs").is_file())

        # Placeholder substitution
        main_c = (Path(proj_td) / "main.c").read_text(encoding="utf-8")
        check("main.c: PROJECT_NAME replaced",
              "@@PROJECT_NAME@@" not in main_c
              and Path(proj_td).name in main_c)
        check("main.c: VERSION replaced",
              "@@VERSION@@" not in main_c)

        proj_xml = (Path(proj_td) / ".project").read_text(encoding="utf-8")
        check(".project: PROJECT_NAME replaced",
              Path(proj_td).name in proj_xml
              and "@@PROJECT_NAME@@" not in proj_xml)

        # Safety: overwrite_scaffolding=False by default
        # Write a sentinel to main.c, then re-install
        (Path(proj_td) / "main.c").write_text(
            "/* user modified */", encoding="utf-8")
        res2 = install(opts)
        check("2nd install: scaffolding preserved (not overwritten)",
              (Path(proj_td) / "main.c").read_text(encoding="utf-8")
              == "/* user modified */")

        # Safety: overwrite_generated=True by default -> generated C refreshed
        gen_c = (gen_dir / "Application"
                 / "statable_transitions_Application.c")
        gen_c.write_text("/* user modified gen */", encoding="utf-8")
        res3 = install(opts)
        check("3rd install: generated C overwritten",
              gen_c.read_text(encoding="utf-8") == "/* generated */")

# Missing dirs -> errors
with tempfile.TemporaryDirectory() as td:
    res = install(InstallOptions(
        project_root=Path(td) / "no_such",
        output_dir=Path(td),
    ))
    check("missing project_root: error reported",
          len(res.errors) >= 1)

with tempfile.TemporaryDirectory() as td:
    res = install(InstallOptions(
        project_root=Path(td),
        output_dir=Path(td) / "no_such_out",
    ))
    check("missing output_dir: error reported",
          len(res.errors) >= 1)

# ======================================================================
# Summary
# ======================================================================
print()
print("=" * 70)
print(f"  TOTAL: {_total}  PASSED: {_passed}  FAILED: {_failed}")
print("=" * 70)

os._exit(0 if _failed == 0 else 1)
