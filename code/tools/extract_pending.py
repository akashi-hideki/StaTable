"""Extract pending translations directly via regex, apply to .ts."""
import re
import xml.etree.ElementTree as ET
from pathlib import Path

# Read broken JSON (as text)
p = Path("i18n_work/zh_CN_v3_reviewed.json")
text = p.read_text(encoding="utf-8")

# Find "pending" section
idx = text.find('"pending"')
if idx < 0:
    print("[FAIL] 'pending' not found")
    raise SystemExit(1)

pending_text = text[idx:]
print(f"pending section length: {len(pending_text)}")

# Extract "key": "value" pairs via regex
# Handles escaped \" inside values
pattern = re.compile(r'"((?:[^"\\]|\\.)*)":\s*"((?:[^"\\]|\\.)*)"')
pairs = pattern.findall(pending_text)

print(f"extracted pairs: {len(pairs)}")

# Build translations dict (skip 'pending' key itself)
translations = {}
for k, v in pairs:
    if k == "pending":
        continue
    if not k.strip():
        continue
    # Unescape JSON string escapes
    try:
        v_clean = v.encode("utf-8").decode("unicode_escape").encode("latin-1").decode("utf-8")
    except Exception:
        v_clean = v.replace("\\n", "\n").replace('\\"', '"').replace("\\\\", "\\")
    translations[k] = v_clean

print(f"translations parsed: {len(translations)}")
print()
print("Sample:")
for k in list(translations.keys())[:5]:
    print(f"  {k!r} -> {translations[k]!r}")

# Apply to .ts
ts = Path("statable_gui/i18n/statable_zh_CN.ts")
tree = ET.parse(ts)
root = tree.getroot()

applied = 0
for ctx in root.findall("context"):
    for msg in ctx.findall("message"):
        src = msg.findtext("source", "") or ""
        if src not in translations:
            continue
        tr = translations[src]
        if not tr or tr == src:
            continue
        tr_el = msg.find("translation")
        if tr_el is None:
            tr_el = ET.SubElement(msg, "translation")
        tr_el.text = tr
        if "type" in tr_el.attrib:
            del tr_el.attrib["type"]
        applied += 1

tree.write(ts, encoding="utf-8", xml_declaration=True)
print()
print(f"[DONE] applied {applied}")