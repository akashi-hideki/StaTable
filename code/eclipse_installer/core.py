# eclipse_installer/core.py
"""[Eclipse Installer] Core logic (Qt-independent).

Copies StaTable-generated C code into an Eclipse project tree, with
optional scaffolding files (startup.s, linker.ld, main.c, syscalls.c,
Makefile, .project, .cproject).
"""
from __future__ import annotations

import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"

# ----------------------------------------------------------------------
# Options
# ----------------------------------------------------------------------
@dataclass
class InstallOptions:
    """User-selected install options."""
    project_root: Path          # Eclipse project root
    output_dir: Path            # StaTable output/ source
    generated_subdir: str = "src/statable_generated"

    # Scaffolding
    with_startup: bool = True
    with_linker: bool = True
    with_syscalls: bool = True
    with_main: bool = True
    with_makefile: bool = True
    with_eclipse_project: bool = True
    with_samples: bool = False

    # Safety
    overwrite_generated: bool = True     # C code under generated_subdir
    overwrite_scaffolding: bool = False  # root-level files

# ----------------------------------------------------------------------
# Result
# ----------------------------------------------------------------------
@dataclass
class InstallResult:
    installed: list = field(default_factory=list)   # Path of written files
    skipped: list = field(default_factory=list)     # Path of skipped files
    errors: list = field(default_factory=list)      # (path, message)
    warnings: list = field(default_factory=list)    # strings

# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def _copy_file(src: Path, dst: Path, overwrite: bool,
               result: InstallResult) -> None:
    if not src.exists():
        result.errors.append((dst, f"source not found: {src}"))
        return
    if dst.exists() and not overwrite:
        result.skipped.append(dst)
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    result.installed.append(dst)


def _write_template(name: str, dst: Path, overwrite: bool,
                    result: InstallResult,
                    replacements: dict | None = None) -> None:
    src = TEMPLATES_DIR / name
    if not src.exists():
        result.errors.append((dst, f"template not found: {name}"))
        return
    if dst.exists() and not overwrite:
        result.skipped.append(dst)
        return
    text = src.read_text(encoding="utf-8")
    if replacements:
        for k, v in replacements.items():
            text = text.replace("@@" + k + "@@", v)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text, encoding="utf-8")
    result.installed.append(dst)


# ----------------------------------------------------------------------
# Main entry
# ----------------------------------------------------------------------
def install(opts: InstallOptions) -> InstallResult:
    """Install generated code + scaffolding into opts.project_root."""
    res = InstallResult()
    root = Path(opts.project_root).resolve()
    out = Path(opts.output_dir).resolve()

    if not root.is_dir():
        res.errors.append((root, "project root does not exist"))
        return res
    if not out.is_dir():
        res.errors.append((out, "output dir does not exist"))
        return res

    # --- 1. Copy generated C code (recursive, preserving structure) ---
    dst_gen = root / opts.generated_subdir
    for src in out.rglob("*"):
        if not src.is_file():
            continue
        if src.suffix.lower() not in (".c", ".h"):
            continue
        rel = src.relative_to(out)
        _copy_file(src, dst_gen / rel, opts.overwrite_generated, res)

    # --- 2. Optional scaffolding ---
    repls = {
        "PROJECT_NAME": root.name,
        "VERSION": "3.5.0",
    }
    if opts.with_startup:
        _write_template("startup_stm32f405.s",
                        root / "startup_stm32f405.s",
                        opts.overwrite_scaffolding, res, repls)
    if opts.with_linker:
        _write_template("linker_stm32f405.ld",
                        root / "linker_stm32f405.ld",
                        opts.overwrite_scaffolding, res, repls)
    if opts.with_syscalls:
        _write_template("syscalls.c",
                        root / "syscalls.c",
                        opts.overwrite_scaffolding, res, repls)
    if opts.with_main:
        _write_template("main_demo.c",
                        root / "main.c",
                        opts.overwrite_scaffolding, res, repls)
    if opts.with_makefile:
        _write_template("Makefile.tmpl",
                        root / "Makefile",
                        opts.overwrite_scaffolding, res, repls)
    if opts.with_eclipse_project:
        _write_template("project.tmpl",
                        root / ".project",
                        opts.overwrite_scaffolding, res, repls)
        _write_template("cproject.tmpl",
                        root / ".cproject",
                        opts.overwrite_scaffolding, res, repls)
        _write_template("settings/org.eclipse.core.resources.prefs",
                        root / ".settings" / "org.eclipse.core.resources.prefs",
                        opts.overwrite_scaffolding, res, repls)
        _write_template("settings/language.settings.xml",
                        root / ".settings" / "language.settings.xml",
                        opts.overwrite_scaffolding, res, repls)
        _write_template("settings/org.eclipse.core.resources.prefs",
                        root / ".settings" / "org.eclipse.core.resources.prefs",
                        opts.overwrite_scaffolding, res, repls)
        _write_template("settings/language.settings.xml",
                        root / ".settings" / "language.settings.xml",
                        opts.overwrite_scaffolding, res, repls)
    if opts.with_samples:
        for xml in out.glob("*.xml"):
            _copy_file(xml, root / "samples" / xml.name,
                       opts.overwrite_scaffolding, res)

    return res
