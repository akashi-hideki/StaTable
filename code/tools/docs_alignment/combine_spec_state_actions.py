"""Combine chunk files into SPEC_STATE_ACTIONS_v1_{en,zh}.md.

Path layout:
  this script:  code/tools/docs_alignment/combine_spec_state_actions.py
  TMP:          code/tools/docs_alignment/_tmp/
  OUT_DIR:      code/docs/

Chunks 1-3 are joined with `\n\n`.
Chunk 4 keeps only up to §14 Revision History (drops the
Placement Procedure + Main Changes sections, which are JA-specific).
"""
from __future__ import annotations
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent          # code/tools/docs_alignment/
CODE_DIR = HERE.parent.parent                    # code/
TMP = HERE / "_tmp"
OUT_DIR = CODE_DIR / "docs"

JA_ONLY_MARKER = "## Placement Procedure"


def combine(lang: str) -> int:
    chunks = []
    for i in range(1, 5):
        p = TMP / f"chunk_{i}_{lang}.md"
        if not p.exists():
            print(f"[ERR] missing: {p}")
            return 1
        chunks.append(p.read_text(encoding="utf-8"))

    # Drop JA-only tail from chunk 4
    c4 = chunks[3]
    idx = c4.find(JA_ONLY_MARKER)
    if idx != -1:
        c4 = c4[:idx].rstrip() + "\n"
        chunks[3] = c4
        print(f"  [{lang}] chunk_4 trimmed at '{JA_ONLY_MARKER}'")
    else:
        print(f"  [{lang}] chunk_4 marker not found; keeping full")

    body = "\n\n".join(c.rstrip() + "\n" for c in chunks)
    out = OUT_DIR / f"SPEC_STATE_ACTIONS_v1_{lang}.md"
    out.write_text(body, encoding="utf-8", newline="\n")
    print(f"[OK]   wrote {out.name} ({out.stat().st_size} bytes)")
    return 0


def main() -> int:
    print("=" * 74)
    print("  Combine SPEC_STATE_ACTIONS chunks")
    print("=" * 74)
    print(f"  TMP:     {TMP}")
    print(f"  OUT_DIR: {OUT_DIR}")
    print("=" * 74)
    for lang in ("en", "zh"):
        combine(lang)
    print("=" * 74)
    return 0


if __name__ == "__main__":
    sys.exit(main())