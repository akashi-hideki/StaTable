"""Build distribution package for Galanz cooking appliance.

Assembles docs + sample + portable ZIP into a single folder,
then optionally compresses it.
"""
from __future__ import annotations

import argparse
import shutil
import sys
import zipfile
from pathlib import Path

SCRIPT = Path(__file__).resolve()
CODE_DIR = SCRIPT.parent.parent.parent        # code/
REPO_DIR = CODE_DIR.parent                     # StaTable/
SAMPLES_SRC = CODE_DIR / "docs" / "samples"
PORTABLE_SRC = CODE_DIR / "StaTable-portable-v3.3.0-win64.zip"

DEFAULT_OUT = REPO_DIR / "dist_package" / "StaTable-CookingHeater-Package-v3.3.0"


def copy_docs(out: Path) -> None:
    """Copy docs to their subfolders."""
    (out / "docs").mkdir(parents=True, exist_ok=True)
    (out / "samples").mkdir(parents=True, exist_ok=True)

    # Top-level: README + INSTALL_GUIDE
    for f in ("README_zh.md", "INSTALL_GUIDE_zh.md"):
        src = SAMPLES_SRC / f
        if not src.exists():
            print(f"[FAIL] missing {src}")
            sys.exit(1)
        shutil.copy2(src, out / f)
        print(f"[OK] {f}")

    # docs/: design/role/eclipse
    for f in ("LAYER_DESIGN_zh.md", "ROLE_FUNCTIONS_zh.md",
              "ECLIPSE_INTEGRATION_zh.md"):
        src = SAMPLES_SRC / f
        if not src.exists():
            print(f"[FAIL] missing {src}")
            sys.exit(1)
        shutil.copy2(src, out / "docs" / f)
        print(f"[OK] docs/{f}")

    # samples/: XML
    src = SAMPLES_SRC / "cooking_heater_controller.xml"
    if not src.exists():
        print(f"[FAIL] missing {src}")
        sys.exit(1)
    shutil.copy2(src, out / "samples" / "cooking_heater_controller.xml")
    print(f"[OK] samples/cooking_heater_controller.xml")


def copy_portable(out: Path) -> None:
    """Copy portable ZIP to install/."""
    (out / "install").mkdir(parents=True, exist_ok=True)
    if not PORTABLE_SRC.exists():
        print(f"[WARN] portable ZIP not found: {PORTABLE_SRC}")
        print("       (skip — package will lack the executable)")
        return
    shutil.copy2(PORTABLE_SRC, out / "install" / PORTABLE_SRC.name)
    size_mb = PORTABLE_SRC.stat().st_size / 1024 / 1024
    print(f"[OK] install/{PORTABLE_SRC.name} ({size_mb:.1f} MB)")


def make_zip(out: Path) -> Path:
    """Compress the package folder into a ZIP."""
    zip_path = out.parent / f"{out.name}.zip"
    if zip_path.exists():
        zip_path.unlink()
    print(f"\n[i] creating {zip_path} ...")
    with zipfile.ZipFile(zip_path, "w",
                         zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for p in sorted(out.rglob("*")):
            if p.is_file():
                z.write(p, p.relative_to(out.parent))
    size_mb = zip_path.stat().st_size / 1024 / 1024
    print(f"[OK] {zip_path.name} ({size_mb:.1f} MB)")
    return zip_path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--no-zip", action="store_true")
    ap.add_argument("--keep", action="store_true",
                    help="do not delete existing out folder")
    args = ap.parse_args()

    out = Path(args.out)
    if out.exists():
        if args.keep:
            print(f"[i] keeping existing {out}")
        else:
            shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)

    print(f"[i] building package at: {out}\n")
    copy_docs(out)
    print()
    copy_portable(out)

    if not args.no_zip:
        make_zip(out)

    print("\n[PASS] package complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())