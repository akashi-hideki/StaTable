"""fix_logger_optional_import.py"""
from pathlib import Path

p = Path("codegen/validate/logger.py")
t = p.read_text(encoding="utf-8")

old = "import os\nfrom datetime import datetime\n"
new = "import os\nfrom datetime import datetime\nfrom typing import Optional\n"

if "from typing import Optional" in t:
    print("[SKIP] already imported")
elif old in t:
    t = t.replace(old, new, 1)
    p.write_text(t, encoding="utf-8")
    print("[OK] added Optional import")
else:
    raise SystemExit("[FAIL] anchor not found")
