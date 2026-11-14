# code/tools/patches/patch_v3_1_i18n_review.py
r"""
Add --dump-all command to i18n_auto.py for full review.

Usage:
    cd code
    python tools\patches\patch_v3_1_i18n_review.py --apply
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parent.parent.parent
TARGET = CODE / "tools" / "i18n_auto.py"

ADDON = '''

def dump_all(lang: str) -> int:
    """Dump ALL strings (existing + pending) for review."""
    ts = _ts_path(lang)
    if not ts.exists():
        print(f"[FAIL] not found: {ts}")
        return 1

    tree, root = _read_ts(lang)
    all_items = {}

    for ctx in root.findall("context"):
        ctx_name = ctx.findtext("name", "") or ""
        for msg in ctx.findall("message"):
            src = msg.findtext("source", "") or ""
            if not src.strip():
                continue
            tr_el = msg.find("translation")
            tr = ""
            if tr_el is not None:
                tr = tr_el.text or ""
                if tr_el.get("type") == "unfinished":
                    tr = ""
            all_items[src] = tr

    out = {
        "_meta": {
            "language": lang,
            "purpose": "full review: existing + pending",
            "total": len(all_items),
        },
        "translations": all_items,
    }

    WORK.mkdir(parents=True, exist_ok=True)
    jp = WORK / f"{lang}_review.json"
    jp.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[DONE] dumped {len(all_items)} strings -> {jp}")
    return 0

'''

MARKER = "if __name__ == \"__main__\":"


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)

    mode = "APPLY" if args.apply else "DRY-RUN"
    print("=" * 70)
    print(f"  patch_v3_1_i18n_review  [{mode}]")
    print("=" * 70)

    if not TARGET.exists():
        print(f"[FAIL] not found: {TARGET}")
        return 1

    text = TARGET.read_text(encoding="utf-8")
    if "def dump_all" in text:
        print("[SKIP] already patched")
        return 0

    if MARKER not in text:
        print(f"[FAIL] marker not found")
        return 1

    # Insert dump_all before the __main__ block
    new_text = text.replace(MARKER, ADDON + "\n" + MARKER, 1)

    # Add CLI option
    new_text = new_text.replace(
        '    ap.add_argument("--status", action="store_true")',
        '    ap.add_argument("--status", action="store_true")\n'
        '    ap.add_argument("--dump-all", action="store_true")'
    )
    new_text = new_text.replace(
        '    if args.dump:\n        return dump(args.lang)',
        '    if args.dump_all:\n        return dump_all(args.lang)\n'
        '    if args.dump:\n        return dump(args.lang)'
    )

    print("[APPLY] add --dump-all to i18n_auto.py")
    if not args.apply:
        return 0

    bak = TARGET.with_suffix(TARGET.suffix + ".bak_review")
    if not bak.exists():
        bak.write_text(text, encoding="utf-8")

    TARGET.write_text(new_text, encoding="utf-8")
    print(f"[DONE] {TARGET.name} updated")
    return 0


if __name__ == "__main__":
    sys.exit(main())