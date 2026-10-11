"""diag_idempotency.py"""
from __future__ import annotations
import sys, tempfile, os
from pathlib import Path

sys.path.insert(0, ".")
from eclipse_installer.core import InstallOptions, install

def _mkfile(root, rel, content="x"):
    full = os.path.join(root, rel)
    parent = os.path.dirname(full)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)
    return os.path.abspath(full)

with tempfile.TemporaryDirectory() as out_td, \
     tempfile.TemporaryDirectory() as proj_td:
    _mkfile(out_td, "x.c", "// x")
    opts = InstallOptions(
        project_root=Path(proj_td),
        output_dir=Path(out_td),
    )
    res1 = install(opts)
    print(f"1st: installed={len(res1.installed)} skipped={len(res1.skipped)}")
    for p in res1.installed:
        print(f"  I: {p}")
    for p in res1.skipped:
        print(f"  S: {p}")

    res2 = install(opts)
    print(f"\n2nd: installed={len(res2.installed)} skipped={len(res2.skipped)}")
    for p in res2.installed:
        print(f"  I: {p}")
    for p in res2.skipped:
        print(f"  S: {p}")
