# code/tools/patches/patch_v3_1_i18n_manual_tools.py
r"""
v3.1: create export/import tools for Google Sheets translation.

Files created:
  - code/tools/i18n_export.py   (.ts -> TSV)
  - code/tools/i18n_import.py   (translated TSV -> .ts)
  - code/i18n_work/             (workspace)

Also updates .gitignore.

Usage:
    cd code
    python tools\patches\patch_v3_1_i18n_manual_tools.py
    python tools\patches\patch_v3_1_i18n_manual_tools.py --apply
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parent.parent.parent
REPO = CODE.parent

EXPORT_PY = '''# code/tools/i18n_export.py
"""Export a Qt .ts file to TSV for translation via Google Sheets.

Output columns: context, source, translation (tab-separated)

Usage:
    cd code
    python tools/i18n_export.py <input.ts> <output.tsv>
"""
from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def _clean(s: str) -> str:
    return s.replace("\\t", " ").replace("\\r", "").replace("\\n", "\\\\n")


def export_ts(ts_path: Path, out_path: Path) -> int:
    tree = ET.parse(ts_path)
    root = tree.getroot()
    rows = [("context", "source", "translation")]
    for ctx in root.findall("context"):
        ctx_name = ctx.findtext("name", "") or ""
        for msg in ctx.findall("message"):
            source = msg.findtext("source", "") or ""
            tr_el = msg.find("translation")
            translation = ""
            if tr_el is not None:
                translation = tr_el.text or ""
                if tr_el.get("type") == "unfinished":
                    translation = ""
            rows.append((_clean(ctx_name), _clean(source), _clean(translation)))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        "\\n".join("\\t".join(r) for r in rows),
        encoding="utf-8",
    )
    return len(rows) - 1


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if len(argv) != 2:
        print("Usage: python tools/i18n_export.py <input.ts> <output.tsv>")
        return 1
    n = export_ts(Path(argv[0]).resolve(), Path(argv[1]).resolve())
    print(f"[DONE] exported {n} strings -> {argv[1]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''

IMPORT_PY = '''# code/tools/i18n_import.py
"""Import translated TSV back into a Qt .ts file.

Usage:
    cd code
    python tools/i18n_import.py <input.ts> <translated.tsv>
"""
from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def import_ts(ts_path: Path, tsv_path: Path) -> int:
    translations: dict = {}
    for line in tsv_path.read_text(encoding="utf-8").splitlines()[1:]:
        parts = line.split("\\t")
        if len(parts) < 3:
            continue
        ctx, src, tr = parts[0], parts[1], parts[2]
        # unescape \\n back to real newlines
        tr = tr.replace("\\\\n", "\\n")
        if tr:
            translations[(ctx, src)] = tr

    tree = ET.parse(ts_path)
    root = tree.getroot()
    applied = 0
    for ctx in root.findall("context"):
        ctx_name = ctx.findtext("name", "") or ""
        for msg in ctx.findall("message"):
            source = msg.findtext("source", "") or ""
            key = (ctx_name, source)
            if key not in translations:
                continue
            tr_el = msg.find("translation")
            if tr_el is None:
                tr_el = ET.SubElement(msg, "translation")
            tr_el.text = translations[key]
            if "type" in tr_el.attrib:
                del tr_el.attrib["type"]
            applied += 1

    tree.write(ts_path, encoding="utf-8", xml_declaration=True)
    return applied


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if len(argv) != 2:
        print("Usage: python tools/i18n_import.py <input.ts> <translated.tsv>")
        return 1
    ts = Path(argv[0]).resolve()
    tsv = Path(argv[1]).resolve()
    if not ts.exists():
        print(f"[FAIL] not found: {ts}")
        return 1
    if not tsv.exists():
        print(f"[FAIL] not found: {tsv}")
        return 1
    n = import_ts(ts, tsv)
    print(f"[DONE] applied {n} translations -> {ts}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''

GITIGNORE_ENTRY = "\\n# v3.1: i18n translation workspace (transient)\\ncode/i18n_work/\\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)

    mode = "APPLY" if args.apply else "DRY-RUN"
    print("=" * 70)
    print(f"  patch_v3_1_i18n_manual_tools  [{mode}]")
    print("=" * 70)

    files = [
        (CODE / "tools" / "i18n_export.py", EXPORT_PY),
        (CODE / "tools" / "i18n_import.py", IMPORT_PY),
    ]
    for p, c in files:
        rel = p.relative_to(REPO)
        if p.exists():
            print(f"[SKIP] {rel} exists")
        else:
            print(f"[APPLY] create {rel} ({len(c)} chars)")
            if args.apply:
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(c, encoding="utf-8")

    work = CODE / "i18n_work"
    if work.exists():
        print(f"[SKIP] {work.relative_to(REPO)} exists")
    else:
        print(f"[APPLY] create dir {work.relative_to(REPO)}")
        if args.apply:
            work.mkdir(parents=True, exist_ok=True)

    gi = REPO / ".gitignore"
    if gi.exists():
        txt = gi.read_text(encoding="utf-8")
        if "code/i18n_work/" in txt:
            print("[SKIP] .gitignore already has code/i18n_work/")
        else:
            print("[APPLY] append code/i18n_work/ to .gitignore")
            if args.apply:
                if not txt.endswith("\\n"):
                    txt += "\\n"
                txt += GITIGNORE_ENTRY
                gi.write_text(txt, encoding="utf-8")

    if not args.apply:
        print()
        print("[DRY-RUN] no file written; pass --apply")
    return 0


if __name__ == "__main__":
    sys.exit(main())