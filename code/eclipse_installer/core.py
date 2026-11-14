# eclipse_installer/core.py
"""[Eclipse Installer] Core logic (Qt-independent).

Copies StaTable-generated C code into an Eclipse project tree, with
optional scaffolding files (startup.s, linker.ld, main.c, syscalls.c,
Makefile, .project, .cproject).
"""
from __future__ import annotations

import os
import sys
import shutil
from dataclasses import dataclass, field
from pathlib import Path

# PyInstaller: templates are bundled under sys._MEIPASS
if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    TEMPLATES_DIR = Path(sys._MEIPASS) / "eclipse_installer" / "templates"
else:
    TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"

# [v3.6.0] codegen import root (lazy: only used in XML mode)
_CODE_DIR = Path(__file__).resolve().parent.parent
if str(_CODE_DIR) not in sys.path:
    sys.path.insert(0, str(_CODE_DIR))

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

    # [v3.6.0] XML generation mode (Tri-state comm_monitor)
    xml_path: Path | None = None
    # True = force ON, False = force OFF, None = follow XML (default)
    with_comm_monitor: bool | None = None

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
# ----------------------------------------------------------------------
# [v3.6.0] XML -> C generation helper (embedded)
# ----------------------------------------------------------------------
def _normalize_tabs(tabs) -> list:
    """Return a flat list of StateMachine objects."""
    if isinstance(tabs, dict):
        return list(tabs.values())
    result = []
    for item in tabs:
        if isinstance(item, tuple) and len(item) >= 2:
            result.append(item[1])
        else:
            result.append(item)
    return result


def _resolve_comm_monitor(xml_settings: dict, override) -> bool:
    """Tri-state: None -> follow XML; True/False -> override."""
    if override is not None:
        return bool(override)
    return bool(xml_settings.get('comm_monitor_enabled', False))


def generate_from_xml(xml_path, out_dir, with_comm_monitor=None) -> bool:
    """Generate C code from a StaTable XML file into out_dir.

    with_comm_monitor:
        None  -> follow XML's <CodeGeneration comm_monitor_enabled="..."/>
        True  -> force ON
        False -> force OFF

    Returns the resolved comm_monitor enabled flag.
    Raises RuntimeError on failure.
    """
    from statable.xml_io import project_from_xml
    from codegen.c_code_generator import CCodeGenerator
    from codegen.config import CodeGenerationConfig
    from codegen.comm_monitor.config import CommMonitorConfig

    xml_path = Path(xml_path)
    if not xml_path.is_file():
        raise RuntimeError(f"XML not found: {xml_path}")

    tabs, gd, role_lib, *_rest, settings = project_from_xml(str(xml_path))
    layers = _normalize_tabs(tabs)
    settings_dict = settings if isinstance(settings, dict) else {}

    enabled = _resolve_comm_monitor(settings_dict, with_comm_monitor)

    cfg = CodeGenerationConfig()
    cfg.comm_monitor = CommMonitorConfig(enabled=enabled)
    for k, v in settings_dict.items():
        if hasattr(cfg, k) and k not in ('comm_monitor', 'comm_monitor_enabled'):
            try:
                setattr(cfg, k, v)
            except Exception:
                pass

    gen = CCodeGenerator(config=cfg)
    generated = gen.generate_all_layers(layers, gd, role_lib)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    gen.save_generated_code(generated, str(out_dir))
    return enabled


def install(opts: InstallOptions) -> InstallResult:
    """Install generated code + scaffolding into opts.project_root."""
    res = InstallResult()
    root = Path(opts.project_root).resolve()
    out = Path(opts.output_dir).resolve()

    if not root.is_dir():
        res.errors.append((root, "project root does not exist"))
        return res

    # [v3.6.0] XML -> C generation (before copy)
    if opts.xml_path is not None:
        try:
            out.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            res.errors.append((out, f"cannot create output dir: {e}"))
            return res
        try:
            enabled = generate_from_xml(
                opts.xml_path, out,
                with_comm_monitor=opts.with_comm_monitor)
        except Exception as e:
            res.errors.append((opts.xml_path, f"generation failed: {e}"))
            return res
        source = ("XML" if opts.with_comm_monitor is None
                  else f"XML+override({opts.with_comm_monitor})")
        res.warnings.append(
            f"Generated C code from {opts.xml_path} "
            f"[{source}] comm_monitor={'ON' if enabled else 'OFF'}")
    elif opts.with_comm_monitor is not None:
        res.warnings.append(
            "with_comm_monitor override ignored: no xml_path set "
            "(provide --xml to generate comm_monitor code)")

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
    if opts.with_samples:
        for xml in out.glob("*.xml"):
            _copy_file(xml, root / "samples" / xml.name,
                       opts.overwrite_scaffolding, res)

    return res
