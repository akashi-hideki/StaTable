# code/tools/i18n_export.py
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
    return s.replace("\t", " ").replace("\r", "").replace("\n", "\\n")


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
        "\n".join("\t".join(r) for r in rows),
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
