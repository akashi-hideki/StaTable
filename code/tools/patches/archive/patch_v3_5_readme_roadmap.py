"""patch_v3_5_readme_roadmap.py"""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # repo root
README = ROOT / "README.md"

ANCHOR = "## Roadmap\n### v2.8.0"

INSERT = """## Roadmap
### v3.5.0 Released (2026-10-11)

**Status:** Released

GUI output-directory hygiene: prevent stale files from a previous
generation causing undefined-symbol link errors.

**Highlights**

- **Public API** `statable.output_utils.find_orphan_files()`:
  recursive scan; returns files not written by the current run.
- **codegen** `CCodeGenerator.last_orphans`: recorded after every
  `save_generated_code()` call (API-compatible: return value unchanged).
- **GUI warning** `show_orphan_warning()`: dialog with
  `[Clean && Regenerate] [Ignore]`; wired into both the main-window
  toolbar/menu and the CodeGenerationDialog save flow.
- **Robust delete** `fs_cleanup.robust_rmtree()`: `chmod S_IWRITE`
  + 3 retries; resolves WinError 5 on Windows/OneDrive (PINNED /
  REPARSE_POINT attributes).
- **New UI** main-window `clean_generate_code()`: toolbar / menu
  `Clean generate` action, also used as the warning dialog callback.

**Also in this release**

- Phase 1b: mypy baseline 218 -> 58 errors (informational).
- S-4: Python 3.10-3.13 test matrix + coverage artifacts.
- S-5: GitHub Actions upgraded to Node.js 24 versions.
- S-1: frozen-exe smoke tests expanded to 4 levels.

**Verification**

- 47 test suites / **1682 PASS** / 0 FAIL (Python 3.10-3.13).
- gcc + ARM Cortex-M4 syntax + link verification: **PASS**
  (firmware.bin 28540 bytes, identical to v3.4.3).
- GUI end-to-end: WinError 5 resolved; Clean && Regenerate flow
  verified on Windows.

**Remaining (v3.5.1+)**

- Phase 1c: residual 58 mypy errors (`statable/xml_io.py`).
- S-3 Step 2: ubuntu-26.04 preview job (2026-10-19 onwards).


### v2.8.0"""

t = README.read_text(encoding="utf-8")

if "### v3.5.0 Released" in t:
    print("[SKIP] already present")
elif ANCHOR not in t:
    raise SystemExit("[FAIL] anchor not found")
else:
    t = t.replace(ANCHOR, INSERT, 1)
    README.write_text(t, encoding="utf-8")
    print(f"[OK] {README}")
