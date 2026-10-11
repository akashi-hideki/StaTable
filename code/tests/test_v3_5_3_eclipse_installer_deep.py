# tests/test_v3_5_3_eclipse_installer_deep.py
"""
StaTable v3.5.3 Eclipse Installer deep test suite (L1+L2)

L1: Template integrity
  - No BOM, LF-only
  - Placeholder syntax @@KEY@@
  - Valid XML for .project / .cproject
  - Makefile tab chars
  - Required templates present
  - linker.ld / startup.s / syscalls.c / main_demo.c content

L2: core.install edge cases
  - Custom generated_subdir
  - with_* flags all off
  - Idempotency
  - overwrite_generated=False
  - Empty output_dir
  - Deep nested structure
  - Unicode filename
  - Same filename in different subdirs
  - with_samples=True
  - Missing project_root error
"""
import os
import re
import stat
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
# L1: Template integrity
# ======================================================================
section("L1 template integrity")

# 1-1: No BOM
for f in TPL.rglob("*"):
    if f.is_file():
        data = f.read_bytes()
        check(f"no BOM: {f.relative_to(TPL)}",
              not data.startswith(b"\xef\xbb\xbf"))

# 1-2: LF-only
for f in TPL.rglob("*"):
    if f.is_file():
        data = f.read_bytes()
        check(f"LF-only: {f.relative_to(TPL)}", b"\r\n" not in data)

# 1-3: Placeholder syntax @@KEY@@ (meta + actual)
_placeholder_re = re.compile(r"(?<!@)@([A-Z_]+)@(?!@)")
check("placeholder regex detects single-@ (meta)",
      bool(_placeholder_re.search("X @FOO@ Y")))
check("placeholder regex allows @@ (meta)",
      not _placeholder_re.search("X @@FOO@@ Y"))

for f in TPL.rglob("*"):
    if not f.is_file():
        continue
    try:
        t = f.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        continue
    bad = _placeholder_re.findall(t)
    check(f"placeholder syntax: {f.relative_to(TPL)}", not bad)

# 1-4: Valid XML
for name in ("project.tmpl", "cproject.tmpl"):
    p = TPL / name
    try:
        ET.fromstring(p.read_text(encoding="utf-8"))
        check(f"valid XML: {name}", True)
    except ET.ParseError as e:
        check(f"valid XML: {name} ({e})", False)

# 1-5: Makefile tab bytes
mk_bytes = (TPL / "Makefile.tmpl").read_bytes()
check("Makefile.tmpl has >= 5 tab bytes", mk_bytes.count(9) >= 5)
mk_text = (TPL / "Makefile.tmpl").read_text(encoding="utf-8")
tab_lines = sum(1 for l in mk_text.split("\n") if l.startswith("\t"))
check("Makefile.tmpl has >= 5 tab-prefixed lines", tab_lines >= 5)

# 1-6: Required templates present
required = [
    "startup_stm32f405.s", "linker_stm32f405.ld", "syscalls.c",
    "main_demo.c", "Makefile.tmpl", "project.tmpl", "cproject.tmpl",
    "settings/org.eclipse.core.resources.prefs",
    "settings/language.settings.xml",
]
for rel in required:
    check(f"template present: {rel}", (TPL / rel).is_file())

# 1-7: linker.ld content
ld_text = (TPL / "linker_stm32f405.ld").read_text(encoding="utf-8")
check("linker.ld ENTRY(Reset_Handler)",
      "ENTRY(Reset_Handler)" in ld_text)
check("linker.ld FLASH 0x08000000",
      "ORIGIN = 0x08000000" in ld_text)
check("linker.ld RAM 0x20000000",
      "ORIGIN = 0x20000000" in ld_text)

# 1-8: startup.s content
st_text = (TPL / "startup_stm32f405.s").read_text(encoding="utf-8")
check("startup.s Reset_Handler", "Reset_Handler:" in st_text)
check("startup.s g_pfnVectors", "g_pfnVectors:" in st_text)

# 1-9: syscalls.c newlib stubs
sc_text = (TPL / "syscalls.c").read_text(encoding="utf-8")
for stub in ("_write", "_read", "_sbrk", "_close", "_fstat", "_exit"):
    check(f"syscalls.c has {stub}", stub in sc_text)

# 1-10: main_demo.c weak hooks
md_text = (TPL / "main_demo.c").read_text(encoding="utf-8")
check("main_demo.c app_init weak",
      "__attribute__((weak)) void app_init" in md_text)
check("main_demo.c app_step weak",
      "__attribute__((weak)) void app_step" in md_text)

# ======================================================================
# L2: core.install edge cases
# ======================================================================
section("L2 core.install edge cases")

from eclipse_installer.core import InstallOptions, install


def _mkfile(root, rel, content="x"):
    full = os.path.join(root, rel)
    parent = os.path.dirname(full)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)
    return os.path.abspath(full)


# 2-1: Custom generated_subdir
with tempfile.TemporaryDirectory() as out_td, \
     tempfile.TemporaryDirectory() as proj_td:
    _mkfile(out_td, "a.c", "// a")
    opts = InstallOptions(
        project_root=Path(proj_td),
        output_dir=Path(out_td),
        generated_subdir="my/custom/dir",
    )
    res = install(opts)
    check("2-1 custom subdir: no errors", not res.errors)
    check("2-1 custom subdir: file placed",
          (Path(proj_td) / "my" / "custom" / "dir" / "a.c").is_file())


# 2-2: All with_* off -> only generated C
with tempfile.TemporaryDirectory() as out_td, \
     tempfile.TemporaryDirectory() as proj_td:
    _mkfile(out_td, "x.c", "// x")
    opts = InstallOptions(
        project_root=Path(proj_td),
        output_dir=Path(out_td),
        with_startup=False, with_linker=False, with_syscalls=False,
        with_main=False, with_makefile=False, with_eclipse_project=False,
    )
    res = install(opts)
    check("2-2 all off: no errors", not res.errors)
    check("2-2 all off: no main.c",
          not (Path(proj_td) / "main.c").exists())
    check("2-2 all off: no .project",
          not (Path(proj_td) / ".project").exists())
    check("2-2 all off: generated C copied",
          (Path(proj_td) / "src" / "statable_generated" / "x.c").is_file())


# 2-3: Idempotency
with tempfile.TemporaryDirectory() as out_td, \
     tempfile.TemporaryDirectory() as proj_td:
    _mkfile(out_td, "x.c", "// x")
    opts = InstallOptions(
        project_root=Path(proj_td),
        output_dir=Path(out_td),
    )
    res1 = install(opts)
    res2 = install(opts)
    check("2-3 idempotent: 1st no errors", not res1.errors)
    check("2-3 idempotent: 2nd no errors", not res2.errors)
    # 1st install: everything fresh (installed = all)
    # 2nd install: generated C overwritten (installed), scaffolding
    #   skipped (overwrite_scaffolding=False default)
    check("2-3 idempotent: 2nd has fewer installed",
          len(res2.installed) < len(res1.installed))
    check("2-3 idempotent: 2nd skipped scaffolding (>= 1)",
          len(res2.skipped) >= 1)
    check("2-3 idempotent: 2nd installed + skipped == 1st installed",
          len(res2.installed) + len(res2.skipped) == len(res1.installed))


# 2-4: overwrite_generated=False preserves generated C
with tempfile.TemporaryDirectory() as out_td, \
     tempfile.TemporaryDirectory() as proj_td:
    _mkfile(out_td, "x.c", "// original")
    opts = InstallOptions(
        project_root=Path(proj_td),
        output_dir=Path(out_td),
        overwrite_generated=False,
    )
    install(opts)
    target = Path(proj_td) / "src" / "statable_generated" / "x.c"
    target.write_text("// user modified", encoding="utf-8")
    res2 = install(opts)
    check("2-4 overwrite=False: user file preserved",
          target.read_text(encoding="utf-8") == "// user modified")
    check("2-4 overwrite=False: skipped reported",
          len(res2.skipped) >= 1)


# 2-5: Empty output_dir
with tempfile.TemporaryDirectory() as out_td, \
     tempfile.TemporaryDirectory() as proj_td:
    opts = InstallOptions(
        project_root=Path(proj_td),
        output_dir=Path(out_td),
    )
    res = install(opts)
    check("2-5 empty output: no errors", not res.errors)
    src_dir = Path(proj_td) / "src"
    gen_c = list(src_dir.rglob("*.c")) if src_dir.exists() else []
    check("2-5 empty output: 0 generated C", not gen_c)

# 2-6: Deeply nested structure preserved
with tempfile.TemporaryDirectory() as out_td, \
     tempfile.TemporaryDirectory() as proj_td:
    _mkfile(out_td, "a/b/c/d/e/deep.c", "// deep")
    opts = InstallOptions(
        project_root=Path(proj_td),
        output_dir=Path(out_td),
    )
    install(opts)
    check("2-6 deep nested preserved",
          (Path(proj_td) / "src" / "statable_generated"
           / "a" / "b" / "c" / "d" / "e" / "deep.c").is_file())


# 2-7: Unicode filename
with tempfile.TemporaryDirectory() as out_td, \
     tempfile.TemporaryDirectory() as proj_td:
    _mkfile(out_td, "\u65e5\u672c\u8a9e.c", "// unicode")
    opts = InstallOptions(
        project_root=Path(proj_td),
        output_dir=Path(out_td),
    )
    res = install(opts)
    check("2-7 unicode: no errors", not res.errors)
    check("2-7 unicode: filename preserved",
          (Path(proj_td) / "src" / "statable_generated"
           / "\u65e5\u672c\u8a9e.c").is_file())


# 2-8: Same filename in different subdirs
with tempfile.TemporaryDirectory() as out_td, \
     tempfile.TemporaryDirectory() as proj_td:
    _mkfile(out_td, "a/x.c", "// a")
    _mkfile(out_td, "b/x.c", "// b")
    opts = InstallOptions(
        project_root=Path(proj_td),
        output_dir=Path(out_td),
    )
    res = install(opts)
    check("2-8 dup name: no errors", not res.errors)
    a = (Path(proj_td) / "src" / "statable_generated" / "a" / "x.c")
    b = (Path(proj_td) / "src" / "statable_generated" / "b" / "x.c")
    check("2-8 dup name: a/x.c exists", a.is_file())
    check("2-8 dup name: b/x.c exists", b.is_file())
    check("2-8 dup name: content distinct",
          a.read_text(encoding="utf-8") == "// a"
          and b.read_text(encoding="utf-8") == "// b")


# 2-9: with_samples=True copies XML
with tempfile.TemporaryDirectory() as out_td, \
     tempfile.TemporaryDirectory() as proj_td:
    _mkfile(out_td, "x.c", "// x")
    _mkfile(out_td, "sample.xml", "<xml/>")
    opts = InstallOptions(
        project_root=Path(proj_td),
        output_dir=Path(out_td),
        with_samples=True,
    )
    res = install(opts)
    check("2-9 samples: no errors", not res.errors)
    check("2-9 samples: xml copied",
          (Path(proj_td) / "samples" / "sample.xml").is_file())


# 2-10: Missing project_root -> error
with tempfile.TemporaryDirectory() as td:
    res = install(InstallOptions(
        project_root=Path(td) / "no_such",
        output_dir=Path(td),
    ))
    check("2-10 missing project_root: error", len(res.errors) >= 1)


# ======================================================================
# Summary
# ======================================================================
print()
print("=" * 70)
print(f"  TOTAL: {_total}  PASSED: {_passed}  FAILED: {_failed}")
print("=" * 70)

sys.exit(0 if _failed == 0 else 1)
