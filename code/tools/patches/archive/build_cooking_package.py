"""Build distribution package for Galanz cooking appliance (v3.4.3).

Layout:
    StaTable-CookingHeater-Package-v3.4.3/
    ├── README_zh.md
    ├── INSTALL_GUIDE_zh.md
    ├── docs/
    ├── samples/
    └── StaTable/                <- app folder (subfolder)
        ├── StaTable.exe
        └── _internal/

Single-extract: user extracts the ZIP, opens `StaTable/StaTable.exe`.
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
DOCS_SRC = CODE_DIR / "docs"
PORTABLE_SRC = CODE_DIR / "StaTable-portable-v3.4.3-win64.zip"

DEFAULT_OUT = REPO_DIR / "dist_package" / "StaTable-CookingHeater-Package-v3.4.3"

TOP_FILES = ["README_zh.md", "INSTALL_GUIDE_zh.md"]
DOCS_FILES = ["LAYER_DESIGN_zh.md", "ROLE_FUNCTIONS_zh.md",
              "ECLIPSE_INTEGRATION_zh.md"]
DOCS_ROOT_FILES = ["SPEC_STATE_ACTIONS_v1_zh.md",
                   "SPEC_STATE_ACTIONS_v1_en.md"]

APP_SUBDIR = "StaTable"   # <- EXE + _internal go into this folder


def extract_portable(app_dir: Path) -> None:
    """Extract the portable ZIP into `app_dir/` (StaTable/ subfolder)."""
    if not PORTABLE_SRC.exists():
        print(f"[FAIL] portable ZIP not found: {PORTABLE_SRC}")
        sys.exit(1)
    print(f"[i] extracting {PORTABLE_SRC.name} into {APP_SUBDIR}/ ...")
    app_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(PORTABLE_SRC, "r") as z:
        z.extractall(app_dir)
    size_mb = PORTABLE_SRC.stat().st_size / 1024 / 1024
    print(f"[OK] {APP_SUBDIR}/ ({size_mb:.1f} MB compressed)")


def copy_docs(out: Path) -> None:
    """Copy docs into their subfolders."""
    (out / "docs").mkdir(parents=True, exist_ok=True)
    (out / "samples").mkdir(parents=True, exist_ok=True)

    for f in TOP_FILES:
        src = SAMPLES_SRC / f
        if not src.exists():
            print(f"[FAIL] missing {src}")
            sys.exit(1)
        shutil.copy2(src, out / f)
        print(f"[OK] {f}")

    for f in DOCS_FILES:
        src = SAMPLES_SRC / f
        if not src.exists():
            print(f"[FAIL] missing {src}")
            sys.exit(1)
        shutil.copy2(src, out / "docs" / f)
        print(f"[OK] docs/{f}")

    for f in DOCS_ROOT_FILES:
        src = DOCS_SRC / f
        if not src.exists():
            print(f"[WARN] missing {src} (skip)")
            continue
        shutil.copy2(src, out / "docs" / f)
        print(f"[OK] docs/{f}")

    src = SAMPLES_SRC / "cooking_heater_controller.xml"
    if not src.exists():
        print(f"[FAIL] missing {src}")
        sys.exit(1)
    shutil.copy2(src, out / "samples" / "cooking_heater_controller.xml")
    print(f"[OK] samples/cooking_heater_controller.xml")


def make_zip(out: Path) -> Path:
    """Compress the package folder into a ZIP."""
    zip_path = out.parent / f"{out.name}.zip"
    if zip_path.exists():
        zip_path.unlink()
    print(f"\n[i] creating {zip_path.name} ...")
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
    ap.add_argument("--keep", action="store_true")
    args = ap.parse_args()

    out = Path(args.out)
    if out.exists():
        if args.keep:
            print(f"[i] keeping existing {out}")
        else:
            shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)

    print(f"[i] building package at: {out}\n")

    # 1. Extract portable ZIP into `out/StaTable/`
    extract_portable(out / APP_SUBDIR)
    print()

    # 2. Copy docs + sample
    copy_docs(out)

    if not args.no_zip:
        make_zip(out)

    print("\n[PASS] package complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())