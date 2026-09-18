# apply_batch10.py - Fill residuals.json with English translations
# and merge into translations.json. Windows PowerShell friendly.

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# --- TRANSLATIONS dict (前回と同じ。省略せずコピーしてください) ---
TRANSLATIONS = {
    # ...（前回の apply_batch10.py の中身をそのまま）...
}


def fill_residuals(dry_run=False):
    rp = PROJECT_ROOT / "residuals.json"
    if not rp.exists():
        print(f"ERROR: {rp} not found")
        return None, 0, []
    data = json.loads(rp.read_text(encoding="utf-8"))
    filled, missing = 0, []
    for e in data["strings"]:
        jp = e.get("japanese", "")
        if jp in TRANSLATIONS:
            e["english"] = TRANSLATIONS[jp]
            filled += 1
        else:
            missing.append((e["id"], jp[:70].replace("\n", "\\n")))
    total = len(data["strings"])
    print(f"[residuals] filled {filled}/{total}, missing {len(missing)}")
    if missing:
        print("--- unmatched (first 50) ---")
        for sid, snip in missing[:50]:
            print(f"  {sid}: {snip}")
    if not dry_run:
        rp.write_text(json.dumps(data, ensure_ascii=False, indent=2),
                      encoding="utf-8")
        print(f"[residuals] wrote {rp}")
    return data, filled, missing


def merge_into_translations(residual_data, dry_run=False):
    tp = PROJECT_ROOT / "translations.json"
    if not tp.exists():
        print(f"ERROR: {tp} not found")
        return 0
    t = json.loads(tp.read_text(encoding="utf-8"))
    existing = {e.get("japanese", "") for e in t["strings"]}
    added = 0
    for e in residual_data["strings"]:
        if e.get("english", "").strip() and e.get("japanese", "") not in existing:
            t["strings"].append(e)
            existing.add(e["japanese"])
            added += 1
    print(f"[merge] added {added} new entries, total {len(t['strings'])}")
    if not dry_run:
        tp.write_text(json.dumps(t, ensure_ascii=False, indent=2),
                      encoding="utf-8")
        print(f"[merge] wrote {tp}")
    return added


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    data, filled, missing = fill_residuals(dry_run=args.dry_run)
    if data is None:
        return 1
    added = merge_into_translations(data, dry_run=args.dry_run)
    print()
    print(f"Summary: filled={filled}, missing={len(missing)}, merged={added}")
    return 0 if not missing else 2


if __name__ == "__main__":
    sys.exit(main())