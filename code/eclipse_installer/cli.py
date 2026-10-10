# eclipse_installer/cli.py
"""[Eclipse Installer] Command-line interface."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .core import InstallOptions, install


def main(argv=None) -> int:
    p = argparse.ArgumentParser(
        prog="eclipse_installer",
        description="Install StaTable-generated C code into an Eclipse project.",
    )
    p.add_argument("--project", required=True,
                   help="Eclipse project root directory")
    p.add_argument("--output", required=True,
                   help="StaTable output/ source directory")
    p.add_argument("--subdir", default="src/statable_generated",
                   help="Install subdir under project (default: %(default)s)")

    # Scaffolding toggles (default ON; use --no-X to disable)
    for name in ("startup", "linker", "syscalls", "main",
                 "makefile", "eclipse-project"):
        p.add_argument(f"--no-{name}", action="store_true",
                       help=f"Do not write {name} scaffolding")

    p.add_argument("--samples", action="store_true",
                   help="Also copy samples/*.xml")
    p.add_argument("--overwrite-scaffolding", action="store_true",
                   help="Overwrite existing root-level scaffolding files")

    args = p.parse_args(argv)

    opts = InstallOptions(
        project_root=Path(args.project),
        output_dir=Path(args.output),
        generated_subdir=args.subdir,
        with_startup=not args.no_startup,
        with_linker=not args.no_linker,
        with_syscalls=not args.no_syscalls,
        with_main=not args.no_main,
        with_makefile=not args.no_makefile,
        with_eclipse_project=not args.no_eclipse_project,
        with_samples=args.samples,
        overwrite_generated=True,
        overwrite_scaffolding=args.overwrite_scaffolding,
    )
    res = install(opts)

    for f in res.installed:
        print(f"[OK]    {f}")
    for f in res.skipped:
        print(f"[SKIP]  {f}")
    for f, m in res.errors:
        print(f"[ERROR] {f}: {m}", file=sys.stderr)

    print(f"\nInstalled: {len(res.installed)}  "
          f"Skipped: {len(res.skipped)}  "
          f"Errors: {len(res.errors)}")
    return 0 if not res.errors else 1


if __name__ == "__main__":
    sys.exit(main())
