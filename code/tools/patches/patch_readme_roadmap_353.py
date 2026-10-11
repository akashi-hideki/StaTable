"""patch_readme_roadmap_353.py"""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
README = ROOT / "README.md"

ANCHOR = "## Roadmap\n### v3.5.2 Released"

INSERT = """## Roadmap
### v3.5.3 Released (2026-10-11)

**Status:** Released

**Highlights**

- **Eclipse Installer v0.1.1** (separate standalone release):
  - `core.py`: remove duplicate `.settings/*` write (each file
    was written once but appeared in both `installed` and `skipped`)
  - Templates: normalize encoding (remove UTF-8 BOM, CRLF -> LF)
  - README.md / README_zh.md added
- **Deep test suite** `test_v3_5_3_eclipse_installer_deep.py` (80 PASS):
  L1 template integrity + L2 core.install edge cases
- **E2E script** `tools/e2e_eclipse_installer.py` (local-only):
  L3 compile, L4 link, L5 QEMU UART banner

**Tests:** 49 suites / **1873 PASS** / 0 FAIL.

**Remaining (v3.5.4+)**

- S-3 Step 2: ubuntu-26.04 preview job (2026-10-19 onwards)


### v3.5.2 Released"""

t = README.read_text(encoding="utf-8")
if "### v3.5.3 Released" in t:
    print("[SKIP] already present")
elif ANCHOR not in t:
    raise SystemExit("[FAIL] anchor not found")
else:
    t = t.replace(ANCHOR, INSERT, 1)
    README.write_text(t, encoding="utf-8")
    print(f"[OK] {README}")
