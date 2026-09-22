#!/usr/bin/env python3
# code/tools/gen_output_from_xml.py
"""Generate C code from an XML project file into an output directory.

Usage:
    python tools/gen_output_from_xml.py --xml path/to/project.xml
    python tools/gen_output_from_xml.py --xml path/to/project.xml --out output

This is a thin wrapper around statable.xml_io + CCodeGenerator, used to
produce a deterministic `output/` tree for tools/verify_c_syntax.py.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_CODE_DIR = Path(__file__).resolve().parent.parent
if str(_CODE_DIR) not in sys.path:
    sys.path.insert(0, str(_CODE_DIR))

from statable.xml_io import project_from_xml
from codegen.c_code_generator import CCodeGenerator
from codegen.config import ConfigManager


# ----------------------------------------------------------------------
# tabs normalization
# ----------------------------------------------------------------------
def normalize_tabs(tabs) -> list:
    """Return a flat list of StateMachine objects regardless of the
    shape returned by project_from_xml.

    Possible shapes:
      - list[StateMachine]
      - list[(name, StateMachine)]
      - dict[name, StateMachine]
    """
    if isinstance(tabs, dict):
        return list(tabs.values())
    result = []
    for item in tabs:
        if isinstance(item, tuple) and len(item) >= 2:
            result.append(item[1])
        else:
            result.append(item)
    return result


def tab_names(layers: list) -> list:
    names = []
    for sm in layers:
        name = getattr(sm, 'layer_name', '') or getattr(sm, 'name', '') \
            or type(sm).__name__
        names.append(name)
    return names


# ----------------------------------------------------------------------
# Config setup
# ----------------------------------------------------------------------
def build_config(project_settings):
    """Build a CodeGenerationConfig, applying project_settings if possible."""
    cm = ConfigManager()

    applied = False
    if project_settings is not None:
        # Try a few known method names (defensive across versions)
        for method_name in ("apply_project_settings",
                            "load_from_project_settings",
                            "apply_settings",
                            "update_from"):
            method = getattr(cm, method_name, None)
            if callable(method):
                try:
                    method(project_settings)
                    print(f"  applied project_settings via {method_name}()")
                    applied = True
                    break
                except Exception as e:
                    print(f"  warning: {method_name}() failed: {e}")

        # Fallback: if project_settings is a plain dict, set attrs directly
        if not applied and isinstance(project_settings, dict):
            cfg = cm.get_config()
            for k, v in project_settings.items():
                if hasattr(cfg, k):
                    try:
                        setattr(cfg, k, v)
                    except Exception:
                        pass
            applied = True
            print("  applied project_settings via direct attribute set")

        if not applied:
            print("  (project_settings could not be applied; "
                  "using defaults)")

    return cm.get_config()


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--xml", required=True, help="input project XML file")
    ap.add_argument("--out", default="output",
                    help="output directory (default: output)")
    args = ap.parse_args()

    xml_path = Path(args.xml)
    if not xml_path.is_file():
        print(f"ERROR: {xml_path} not found", file=sys.stderr)
        return 1

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading: {xml_path}")
    tabs, gd, role_lib, cond_lib, lit_lib, project_settings = \
        project_from_xml(str(xml_path))

    layers = normalize_tabs(tabs)
    names = tab_names(layers)

    print(f"  tabs:  {names}")
    print(f"  gd:    variables={len(getattr(gd, 'variables', []))}, "
          f"flags={len(getattr(gd, 'flags', []))}, "
          f"interrupts={len(getattr(gd, 'interrupts', []))}")
    print(f"  roles: {len(role_lib.list_all()) if role_lib else 0}")
    print(f"  layers: {len(layers)}")

    config = build_config(project_settings)
    print(f"  config: folder_structure="
          f"{getattr(config, 'folder_structure', '?')}, "
          f"project_name={getattr(config, 'project_name', '?')}")
    print()

    print("Generating C code ...")
    generator = CCodeGenerator(config=config)
    files = generator.generate_all_layers(layers, gd, role_lib)
    print(f"  generated {len(files)} files")

    saved = generator.save_generated_code(files, str(out_dir))
    print(f"  saved {len(saved)} files to {out_dir.resolve()}")

    c_files = sorted(out_dir.rglob("*.c"))
    h_files = sorted(out_dir.rglob("*.h"))
    print()
    print(f"Result: {len(c_files)} .c / {len(h_files)} .h under {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())