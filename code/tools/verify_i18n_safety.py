"""Verify i18n safety: path strings not wrapped, config safe."""
import re
from pathlib import Path

GUI = Path("statable_gui")

# Path-like string detection
PATH_PATTERNS = [
    re.compile(r'^[A-Za-z]:[/\\\\]'),          # C:\ or D:/
    re.compile(r'^(/|\\\\)'),                  # / or \\
    re.compile(r'\.(py|pyc|h|c|xml|json|txt|exe|bat|sh|md|log|bak)$', re.I),
]

def is_path_like(s):
    for p in PATH_PATTERNS:
        if p.search(s):
            return True
    return False

print("=" * 70)
print("  i18n safety check: tr() wrapping of path-like strings")
print("=" * 70)

# 1) Find self.tr("...") with path-like content
tr_pattern = re.compile(r'self\.tr\(\s*["\']([^"\']+)["\']')
suspicious = []
total_tr = 0

for f in GUI.rglob("*.py"):
    try:
        lines = f.read_text(encoding="utf-8").splitlines()
    except Exception:
        continue
    for i, line in enumerate(lines, 1):
        for m in tr_pattern.finditer(line):
            total_tr += 1
            content = m.group(1)
            if is_path_like(content):
                rel = f.relative_to(GUI.parent)
                suspicious.append(f"{rel}:{i}: {content!r}")

print()
print(f"Total self.tr() calls scanned: {total_tr}")
print(f"Suspicious (path-like) strings: {len(suspicious)}")
for s in suspicious[:20]:
    print(f"  [WARN] {s}")

# 2) Check QSettings keys used
print()
print("=" * 70)
print("  QSettings keys in code")
print("=" * 70)

settings_pattern = re.compile(r'settings\.(?:setValue|value)\(\s*["\']([^"\']+)["\']')
keys = set()
for f in GUI.rglob("*.py"):
    try:
        text = f.read_text(encoding="utf-8")
    except Exception:
        continue
    for m in settings_pattern.finditer(text):
        keys.add(m.group(1))

for k in sorted(keys):
    print(f"  {k}")

print()
print("=" * 70)
print("  Summary")
print("=" * 70)
if suspicious:
    print(f"  [ACTION] {len(suspicious)} path-like strings need review")
else:
    print("  [OK] No path-like strings wrapped with self.tr()")