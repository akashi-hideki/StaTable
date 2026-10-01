# code/tools/i18n_import.py
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
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        ctx, src, tr = parts[0], parts[1], parts[2]
        # unescape \n back to real newlines
        tr = tr.replace("\\n", "\n")
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
