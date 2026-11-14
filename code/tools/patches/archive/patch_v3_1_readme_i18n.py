# code/tools/patches/patch_v3_1_readme_i18n.py
r"""
v3.1: update README with Chinese language support.

Edits:
  E1. Insert "What's New in v3.1" section before v2.8.0 section.
  E2. Insert "Language / 语言" section before "Run the Test Suite".
  E3. Insert v3.1 subsection before "### v3.1+ (Exploring)".

Usage:
    cd code
    python tools\patches\patch_v3_1_readme_i18n.py
    python tools\patches\patch_v3_1_readme_i18n.py --apply
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent.parent
README = REPO / "README.md"

# ---------- E1: What's New in v3.1 ----------
E1_ANCHOR = "## What's New in v2.8.0"
E1_INSERT = """## What's New in v3.1

> **Chinese Language Support** — Released 2026-10-01

StaTable now supports **简体中文 (Simplified Chinese)** in the GUI.

- **Language menu** — switch between English and 简体中文
- **Auto restart** — click "Restart now" to apply the new language
- **97.4% translation** (485 / 498 strings)
- **Unified startup** — `python -m statable` and `python gui_main.py`
  both apply the saved language

To switch:

1. Menu bar: **Language / 语言** → **简体中文**
2. Click **Restart now / 立即重启** in the dialog
3. StaTable restarts with the Chinese UI

"""

# ---------- E2: Language section ----------
E2_ANCHOR = "### Run the Test Suite"
E2_INSERT = """### Language / 语言

StaTable supports English and Simplified Chinese (简体中文).

To change the language:

1. Menu bar: **Language / 语言**
2. Select **English** or **简体中文**
3. Click **Restart now** in the dialog

The setting is saved and applied on the next startup.

"""

# ---------- E3: Roadmap v3.1 ----------
E3_ANCHOR = "### v3.1+ (Exploring)"
E3_INSERT = """### v3.1 (In Progress — Chinese Language Support)

- ✅ **Chinese-language GUI** (简体中文, 97.4%)
- ✅ **Language menu** (English ↔ 简体中文)
- ✅ **Auto restart** on language change
- ⏳ Chinese-language documentation

"""


def _apply_once(text, anchor, insert, tag):
    if insert.split("\n")[0] in text:
        print(f"[SKIP] {tag}: already applied")
        return text, True
    n = text.count(anchor)
    if n == 0:
        print(f"[FAIL] {tag}: anchor not found: {anchor!r}")
        return text, False
    if n > 1:
        print(f"[FAIL] {tag}: anchor found {n} times")
        return text, False
    print(f"[APPLY] {tag}")
    return text.replace(anchor, insert + anchor, 1), True


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)

    mode = "APPLY" if args.apply else "DRY-RUN"
    print("=" * 70)
    print(f"  patch_v3_1_readme_i18n  [{mode}]")
    print("=" * 70)

    if not README.exists():
        print(f"[FAIL] not found: {README}")
        return 1

    text = README.read_text(encoding="utf-8")
    patched = text
    ok = True

    for tag, anchor, insert in (
        ("E1 What's New in v3.1", E1_ANCHOR, E1_INSERT),
        ("E2 Language section", E2_ANCHOR, E2_INSERT),
        ("E3 Roadmap v3.1", E3_ANCHOR, E3_INSERT),
    ):
        patched, success = _apply_once(patched, anchor, insert, tag)
        if not success:
            ok = False
        print()

    if not ok:
        print("[ABORT] some edits failed; no file written")
        return 1

    if patched == text:
        print("[SKIP] README.md already up to date")
        return 0

    if not args.apply:
        print("[DRY-RUN] no file written; pass --apply")
        return 0

    bak = README.with_suffix(README.suffix + ".bak_v3_1")
    if not bak.exists():
        bak.write_text(text, encoding="utf-8")
        print(f"  Backup: {bak.name}")

    README.write_text(patched, encoding="utf-8")
    print(f"[DONE] README.md updated ({len(text)} -> {len(patched)} chars)")
    return 0


if __name__ == "__main__":
    sys.exit(main())