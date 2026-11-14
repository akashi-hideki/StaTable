from pathlib import Path
ROOT = Path(".")

for rel in ["codegen/enum_generator.py", "codegen/validate/logger.py"]:
    p = ROOT / rel
    t = p.read_text(encoding="utf-8")
    import re
    m = re.search(r"from typing import ([^\n]+)", t)
    if m:
        imported = m.group(1)
        if "Optional" not in imported:
            t = t.replace(
                f"from typing import {imported}",
                f"from typing import {imported}, Optional",
                1,
            )
            p.write_text(t, encoding="utf-8")
            print(f"[OK] added Optional to {rel}")
        else:
            print(f"[SKIP] {rel}: Optional already imported")
    else:
        # no typing import
        print(f"[WARN] {rel}: no typing import")
