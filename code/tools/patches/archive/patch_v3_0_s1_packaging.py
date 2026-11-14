# code/tools/patches/patch_v3_0_s1_packaging.py
"""
Phase S-1 patch for v3.0: Packaging foundation.

Targets:
  - code/pyproject.toml          (new file)
  - code/statable/__init__.py    (add __version__)
  - code/codegen/__init__.py     (add __version__)

Edits:
  E1. Create code/pyproject.toml with [project] name="statable",
      entry point statable-cli, extras (gui / dev).
  E2. Insert __version__ = "3.0.0" before __all__ in statable/__init__.py.
  E3. Insert __version__ = "3.0.0" before __all__ in codegen/__init__.py.

Safety:
  - Idempotent (skips if marker already present)
  - Backup once (.bak_s1)
  - Refuses if anchor missing or duplicated

Usage:
    cd code
    python tools\\patches\\patch_v3_0_s1_packaging.py
    python tools\\patches\\patch_v3_0_s1_packaging.py --apply
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# code/tools/patches/patch_v3_0_s1_packaging.py
#   .parent           = code/tools/patches
#   .parent.parent    = code/tools
#   .parent.parent.parent = code
CODE = Path(__file__).resolve().parent.parent.parent

PYPROJECT = CODE / "pyproject.toml"
STATABLE_INIT = CODE / "statable" / "__init__.py"
CODEGEN_INIT = CODE / "codegen" / "__init__.py"

VERSION = "3.0.0"
VERSION_LINE = f'__version__ = "{VERSION}"\n'


PYPROJECT_TEMPLATE = '''\
# code/pyproject.toml
# StaTable packaging foundation (v3.0 / Phase S-1)
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "statable"
version = "3.0.0"
description = "MISRA C:2012-aware state machine design and C code generation for embedded systems"
readme = { file = "../README.md", content-type = "text/markdown" }
requires-python = ">=3.10"
license = { text = "Apache-2.0" }
authors = [{ name = "Hideki Akashi" }]
keywords = [
    "state machine",
    "MISRA",
    "embedded",
    "code generation",
    "C",
]
classifiers = [
    "Development Status :: 4 - Beta",
    "License :: OSI Approved :: Apache Software License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Topic :: Software Development :: Code Generators",
    "Topic :: Software Development :: Embedded Systems",
]

[project.optional-dependencies]
gui = ["PySide6>=6.0"]
dev = ["pytest>=7.0", "pycparser"]

[project.scripts]
statable-cli = "statable.cli:main"

[project.urls]
Homepage = "https://github.com/akashi-hideki/StaTable"
Repository = "https://github.com/akashi-hideki/StaTable"
Issues = "https://github.com/akashi-hideki/StaTable/issues"

[tool.setuptools.packages.find]
where = ["."]
include = ["statable*", "codegen*", "statable_gui*"]
'''


def _hdr(mode: str) -> None:
    print("=" * 70)
    print(f"  patch_v3_0_s1_packaging  [{mode}]")
    print("=" * 70)


def _backup_once(path: Path) -> None:
    bak = path.with_suffix(path.suffix + ".bak_s1")
    if not bak.exists():
        bak.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"  Backup: {bak.name}")


def edit_pyproject(apply: bool) -> int:
    if PYPROJECT.exists():
        text = PYPROJECT.read_text(encoding="utf-8")
        if 'name = "statable"' in text and f'version = "{VERSION}"' in text:
            print(f"[SKIP] pyproject.toml already at v{VERSION}")
            return 0
        print("[FAIL] pyproject.toml exists but is not the expected file")
        return 1

    print(f"[APPLY] create {PYPROJECT.relative_to(CODE.parent)}")
    if not apply:
        return 0
    PYPROJECT.write_text(PYPROJECT_TEMPLATE, encoding="utf-8")
    print(f"[DONE] pyproject.toml created ({len(PYPROJECT_TEMPLATE)} chars)")
    return 0


def edit_version(path: Path, apply: bool) -> int:
    rel = path.relative_to(CODE.parent)
    if not path.exists():
        print(f"[FAIL] not found: {rel}")
        return 1

    text = path.read_text(encoding="utf-8")

    if VERSION_LINE in text:
        print(f"[SKIP] {rel} already has __version__ = \"{VERSION}\"")
        return 0

    anchor = "__all__ = ["
    count = text.count(anchor)
    if count == 0:
        print(f"[FAIL] anchor '{anchor}' not found in {rel}")
        return 1
    if count > 1:
        print(f"[FAIL] anchor '{anchor}' found {count} times in {rel}")
        return 1

    idx = text.find(anchor)
    insert = VERSION_LINE + "\n"
    patched = text[:idx] + insert + text[idx:]

    print(f"[APPLY] insert __version__ before __all__ in {rel} (offset {idx})")
    if not apply:
        return 0

    _backup_once(path)
    path.write_text(patched, encoding="utf-8")
    print(f"[DONE] {rel} updated ({len(patched)} chars)")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)

    mode = "APPLY" if args.apply else "DRY-RUN"
    _hdr(mode)

    rc = 0
    rc |= edit_pyproject(args.apply)
    print()
    rc |= edit_version(STATABLE_INIT, args.apply)
    print()
    rc |= edit_version(CODEGEN_INIT, args.apply)
    print()

    if not args.apply:
        print("[DRY-RUN] no file written; pass --apply to execute.")
    else:
        print("Verify:")
        print("  python tests\\test_v3_0_s1_packaging.py")
    return rc


if __name__ == "__main__":
    sys.exit(main())