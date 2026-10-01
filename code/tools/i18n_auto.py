# code/tools/i18n_auto.py
"""JSON-based i18n automation.

Workflow:
    1) python tools/i18n_auto.py --lang zh_CN --dump
       -> code/i18n_work/zh_CN.json

    2) Translate pending values in the JSON (e.g. via ChatGPT)

    3) python tools/i18n_auto.py --lang zh_CN --apply
       -> update .ts, compile .qm, show status

    4) python tools/i18n_auto.py --lang zh_CN --status
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

CODE = Path(__file__).resolve().parent.parent
I18N = CODE / "statable_gui" / "i18n"
WORK = CODE / "i18n_work"


def _ts_path(lang: str) -> Path:
    return I18N / f"statable_{lang}.ts"


def _json_path(lang: str) -> Path:
    return WORK / f"{lang}.json"


def _read_ts(lang: str):
    tree = ET.parse(_ts_path(lang))
    return tree, tree.getroot()


def dump(lang: str) -> int:
    ts = _ts_path(lang)
    if not ts.exists():
        print(f"[FAIL] not found: {ts}")
        return 1

    tree, root = _read_ts(lang)
    existing = {}
    pending = {}

    for ctx in root.findall("context"):
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
            if tr:
                existing[src] = tr
            else:
                if src.startswith("_") or src in ("OK", "Cancel"):
                    pending[src] = src
                else:
                    pending[src] = ""

    out = {
        "_meta": {
            "language": lang,
            "total": len(existing) + len(pending),
            "translated": len(existing),
            "pending": len(pending),
        },
        "existing": existing,
        "pending": pending,
    }

    WORK.mkdir(parents=True, exist_ok=True)
    jp = _json_path(lang)
    jp.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[DONE] dumped {len(pending)} pending -> {jp}")
    print(f"       (existing: {len(existing)})")
    return 0


def _find_lrelease():
    try:
        import PySide6
    except ImportError:
        return None
    base = Path(PySide6.__file__).parent
    for name in ("lrelease.exe", "lrelease"):
        p = base / name
        if p.exists():
            return str(p)
    return None


def compile_qm(lang: str) -> int:
    lrelease = _find_lrelease()
    if not lrelease:
        print("[FAIL] lrelease not found")
        return 1
    ts = _ts_path(lang)
    qm = ts.with_suffix(".qm")
    print(f"[lrelease] {ts.name} -> {qm.name}")
    r = subprocess.run([lrelease, str(ts), "-qm", str(qm)])
    return r.returncode


def apply(lang: str) -> int:
    jp = _json_path(lang)
    if not jp.exists():
        print(f"[FAIL] not found: {jp}  (run --dump first)")
        return 1

    data = json.loads(jp.read_text(encoding="utf-8"))
    existing = data.get("existing", {})
    pending = data.get("pending", {})

    translations = {}
    translations.update(existing)
    for k, v in pending.items():
        translations[k] = v

    ts = _ts_path(lang)
    if not ts.exists():
        print(f"[FAIL] not found: {ts}")
        return 1

    tree, root = _read_ts(lang)
    applied = 0
    for ctx in root.findall("context"):
        for msg in ctx.findall("message"):
            src = msg.findtext("source", "") or ""
            if src not in translations:
                continue
            tr_val = translations[src]
            if not tr_val or tr_val == src:
                continue
            tr_el = msg.find("translation")
            if tr_el is None:
                tr_el = ET.SubElement(msg, "translation")
            tr_el.text = tr_val
            if "type" in tr_el.attrib:
                del tr_el.attrib["type"]
            applied += 1

    tree.write(ts, encoding="utf-8", xml_declaration=True)
    print(f"[DONE] applied {applied} translations -> {ts.name}")

    rc = compile_qm(lang)
    if rc != 0:
        return rc

    status(lang)
    return 0


def status(lang: str) -> int:
    ts = _ts_path(lang)
    if not ts.exists():
        print(f"[FAIL] not found: {ts}")
        return 1

    tree, root = _read_ts(lang)
    total = done = pending = vanished = 0
    for ctx in root.findall("context"):
        for msg in ctx.findall("message"):
            total += 1
            tr_el = msg.find("translation")
            if tr_el is None:
                pending += 1
                continue
            ttype = tr_el.get("type", "")
            txt = (tr_el.text or "").strip()
            if ttype == "vanished":
                vanished += 1
            elif ttype == "unfinished" or not txt:
                pending += 1
            else:
                done += 1

    pct = (done / total * 100) if total else 0
    print()
    print(f"  {ts.name}: {done}/{total} ({pct:.1f}%)")
    print(f"    pending={pending}  vanished={vanished}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", required=True)
    ap.add_argument("--dump", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--dump-all", action="store_true")
    args = ap.parse_args(argv)

    if args.dump_all:
        return dump_all(args.lang)
    if args.dump:
        return dump(args.lang)
    if args.apply:
        return apply(args.lang)
    if args.status:
        return status(args.lang)

    print("Usage: --dump | --apply | --status  (with --lang)")
    return 1




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


if __name__ == "__main__":
    sys.exit(main())
