# code/statable/cli.py
"""statable-cli - Command-line interface for StaTable SDK.

Subcommands:
    generate    Generate C code from a design XML file
    validate    Validate a design XML file
    version     Print version

Output:
    stdout: JSON result (default) or plain text
    stderr: log / error messages

Exit codes:
    0   success
    1   validation error (validate --exit-on-error)
    2   internal error (missing file, parse failure, etc.)

Usage:
    statable-cli generate --xml design.xml --out generated/ --format json
    statable-cli validate --xml design.xml --format json --exit-on-error
    statable-cli version
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

CLI_VERSION = "3.1.1"


def _err(msg: str) -> None:
    print(msg, file=sys.stderr)


def _load_project(xml_path: str):
    """Load XML design file.

    Returns (tabs, gd, rf_lib, cond_lib, lit_lib, settings).
    """
    from statable.xml_io import project_from_xml
    return project_from_xml(xml_path)


def _build_config(settings):
    """Build CodeGenerationConfig from project settings dict."""
    from codegen.config import CodeGenerationConfig
    cfg = CodeGenerationConfig()
    if not settings:
        return cfg
    for key, value in settings.items():
        if key == "project_name":
            continue
        if hasattr(cfg, key):
            try:
                setattr(cfg, key, value)
            except Exception:
                pass
    return cfg


def cmd_generate(args) -> int:
    xml_path = args.xml
    out_dir = args.out

    try:
        tabs, gd, rf_lib, _cond, _lit, settings = _load_project(xml_path)
    except FileNotFoundError:
        _err(f"error: XML file not found: {xml_path}")
        return 2
    except Exception as e:
        _err(f"error: failed to load project: {e!r}")
        return 2

    if not tabs:
        _err("error: no tabs/state machines found in project")
        return 2

    try:
        cfg = _build_config(settings)
    except Exception as e:
        _err(f"error: config setup failed: {e!r}")
        return 2

    try:
        from codegen.c_code_generator import CCodeGenerator
        gen = CCodeGenerator(config=cfg)
        generated = gen.generate_all_layers(
            tabs, gd, role_function_library=rf_lib,
        )
    except Exception as e:
        _err(f"error: generation failed: {e!r}")
        return 2

    try:
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        saved = gen.save_generated_code(generated, str(out_dir))
    except Exception as e:
        _err(f"error: save failed: {e!r}")
        return 2

    out_res = Path(out_dir).resolve()
    rel_files = []
    for p in saved:
        try:
            rel_files.append(
                Path(p).resolve().relative_to(out_res).as_posix()
            )
        except ValueError:
            rel_files.append(Path(p).name)
    rel_files.sort()

    if args.format == "json":
        result = {
            "status": "ok",
            "command": "generate",
            "input": str(xml_path),
            "output_dir": str(out_dir),
            "files_generated": rel_files,
            "warnings": [],
        }
        print(json.dumps(result, indent=2))
    else:
        print(f"OK: {len(saved)} files generated in {out_dir}")
        for f in rel_files:
            print(f"  {f}")
    return 0


def cmd_validate(args) -> int:
    xml_path = args.xml

    try:
        tabs, gd, _rf, _cond, _lit, _settings = _load_project(xml_path)
    except FileNotFoundError:
        _err(f"error: XML file not found: {xml_path}")
        return 2
    except Exception as e:
        _err(f"error: failed to load project: {e!r}")
        return 2

    if not tabs:
        _err("error: no tabs/state machines found in project")
        return 2

    try:
        from codegen.validate.validator import CodeGenerationValidator
        validator = CodeGenerationValidator()
    except Exception as e:
        _err(f"error: validator init failed: {e!r}")
        return 2

    all_issues = []
    total_errors = 0
    total_warnings = 0

    for name, sm in tabs:
        try:
            res = validator.validate(sm, gd)
        except Exception as e:
            _err(f"error: validation failed for tab {name!r}: {e!r}")
            return 2
        for issue in res.issues:
            d = issue.to_dict()
            d["tab"] = name
            all_issues.append(d)
        total_errors += res.error_count
        total_warnings += res.warning_count

    status = "ok" if total_errors == 0 else "error"

    if args.format == "json":
        out = {
            "status": status,
            "command": "validate",
            "input": str(xml_path),
            "errors": total_errors,
            "warnings": total_warnings,
            "issues": all_issues,
        }
        print(json.dumps(out, indent=2))
    else:
        print(
            f"{status.upper()}: errors={total_errors} "
            f"warnings={total_warnings}"
        )
        for d in all_issues:
            sev = d.get("severity", "?")
            code = d.get("code", "?")
            msg = d.get("message", "")
            print(f"  [{sev}] {code}: {msg}")

    if args.exit_on_error and total_errors > 0:
        return 1
    return 0


def cmd_version(args) -> int:
    try:
        from statable import __version__ as pkg_version
    except Exception:
        pkg_version = CLI_VERSION
    print(f"statable-cli {pkg_version}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="statable-cli",
        description="StaTable command-line interface",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"statable-cli {CLI_VERSION}",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_gen = sub.add_parser("generate", help="Generate C code from XML")
    p_gen.add_argument("--xml", required=True,
                       help="Input design XML file")
    p_gen.add_argument("--out", required=True,
                       help="Output directory")
    p_gen.add_argument("--format", choices=["json", "text"],
                       default="json")
    p_gen.set_defaults(func=cmd_generate)

    p_val = sub.add_parser("validate", help="Validate XML design file")
    p_val.add_argument("--xml", required=True,
                       help="Input design XML file")
    p_val.add_argument("--format", choices=["json", "text"],
                       default="json")
    p_val.add_argument("--exit-on-error", action="store_true",
                       help="Return exit code 1 on validation error")
    p_val.set_defaults(func=cmd_validate)

    p_ver = sub.add_parser("version", help="Print version")
    p_ver.set_defaults(func=cmd_version)

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
