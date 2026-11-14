# code/tools/cleanup_v2_8_final.py
"""
Final pre-commit cleanup for v2.8.0.

Three phases:
  A. All *.bak* files:
       - tracked   -> `git rm`
       - untracked -> unlink
  B. v2.8 one-shot patch scripts -> tools/patches/
  C. .gitignore patterns (idempotent)

Dry-run by default. Pass --apply to execute.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
CODE = REPO / "code"


GITIGNORE_MARKER = "# Backups (project-wide, v2.8)"
GITIGNORE_ADDITIONS = f"""
{GITIGNORE_MARKER}
# -------------------------------------------------------------------
*.bak
*.bak2
*.bak3
*.bak_*
*.bak-*
*.repair.bak
*.legacy*.bak
*.legacy_*.bak
*.v2*bak
*.v27*bak
*.v28*bak

# -------------------------------------------------------------------
# Runtime artifacts (not part of the source tree)
# -------------------------------------------------------------------
code/logs/
code/output/
code/output_vending/
code/misra_report/
code/misra_report_vending/
code/verify_report/
"""

PATCH_SCRIPTS_TO_MOVE = [
    "patch_v2_8_ci.py",
    "patch_v2_8_readme_numbers.py",
    "patch_v2_8_readme.py",
    "patch_v2_8_fix5.py",
    "patch_v2_8_fix6.py",
    "cleanup_before_v2_8_commit.py",
    "cleanup_v2_8_final.py",
]


# ----------------------------------------------------------------------
# A. Backups
# ----------------------------------------------------------------------
def find_backups() -> list[Path]:
    found: set[Path] = set()
    for pattern in ("*.bak", "*.bak2", "*.bak3",
                    "*.bak_*", "*.bak-*",
                    "*.repair.bak"):
        for p in REPO.rglob(pattern):
            if p.is_file():
                found.add(p)
    return sorted(found)


def is_tracked(path: Path) -> bool:
    rel = path.relative_to(REPO).as_posix()
    r = subprocess.run(
        ["git", "ls-files", "--error-unmatch", rel],
        cwd=str(REPO), capture_output=True, text=True,
    )
    return r.returncode == 0


def remove_backups(dry_run: bool) -> tuple[int, int]:
    backups = find_backups()
    tracked = untracked = 0
    for p in backups:
        rel = p.relative_to(REPO).as_posix()
        t = is_tracked(p)
        tag = "TRACKED" if t else "untracked"
        if t:
            tracked += 1
        else:
            untracked += 1
        print(f"  DEL  [{tag}] {rel}")
        if dry_run:
            continue
        if t:
            subprocess.run(["git", "rm", "-f", rel],
                           cwd=str(REPO), capture_output=True)
        else:
            p.unlink()
    return tracked, untracked


# ----------------------------------------------------------------------
# B. Patch scripts
# ----------------------------------------------------------------------
def move_patches(dry_run: bool) -> None:
    patches_dir = CODE / "tools" / "patches"
    if not dry_run:
        patches_dir.mkdir(parents=True, exist_ok=True)
    for name in PATCH_SCRIPTS_TO_MOVE:
        src = CODE / "tools" / name
        dst = patches_dir / name
        if not src.exists():
            print(f"  --   tools/{name}  (not present)")
            continue
        if dst.exists():
            print(f"  DEL  tools/{name}  (already in patches/)")
            if not dry_run:
                src.unlink()
            continue
        print(f"  MV   tools/{name} -> tools/patches/{name}")
        if not dry_run:
            src.rename(dst)


# ----------------------------------------------------------------------
# C. .gitignore
# ----------------------------------------------------------------------
def ensure_gitignore(dry_run: bool) -> None:
    gi = REPO / ".gitignore"
    existing = gi.read_text(encoding="utf-8") if gi.exists() else ""
    if GITIGNORE_MARKER in existing:
        print("  [SKIP] .gitignore already has v2.8 backup patterns")
        return
    print(f"  [APPLY] append patterns to .gitignore "
          f"({'new file' if not gi.exists() else 'existing'})")
    if dry_run:
        return
    with gi.open("a", encoding="utf-8") as f:
        if existing and not existing.endswith("\n"):
            f.write("\n")
        f.write(GITIGNORE_ADDITIONS)


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)

    mode = "APPLY" if args.apply else "DRY-RUN"
    print("=" * 70)
    print(f"  cleanup_v2_8_final  [{mode}]")
    print("=" * 70)

    print()
    print("[A] Backup files (*.bak*)")
    tracked, untracked = remove_backups(dry_run=not args.apply)
    print(f"  total {tracked + untracked} "
          f"({tracked} tracked / {untracked} untracked)")

    print()
    print(f"[B] v2.8 patch scripts -> "
          f"{(CODE / 'tools' / 'patches').relative_to(REPO)}/")
    move_patches(dry_run=not args.apply)

    print()
    print("[C] .gitignore patterns")
    ensure_gitignore(dry_run=not args.apply)

    print()
    if args.apply:
        print("[DONE] cleanup applied.")
    else:
        print("[DRY-RUN] no changes; pass --apply to execute.")
    return 0


if __name__ == "__main__":
    sys.exit(main())