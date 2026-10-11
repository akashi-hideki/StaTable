"""patch_readme_roadmap_352.py"""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
README = ROOT / "README.md"

ANCHOR = "## Roadmap\n### v3.5.1 Released"

INSERT = """## Roadmap
### v3.5.2 Released (2026-10-11)

**Status:** Released

**Highlights**

- **Phase 1c complete**: mypy baseline **58 -> 0 errors**
  (118 source files)
- Annotation-only changes + 2 runtime guards; no behavior change.
- Key fixes:
  - `xml_io.py` (16): ImportError fallback typing, Element
    kwargs invariance, `int(str | None)` guard, append None-guards
  - `validation_dialog.py` (9): PySide6 Qt enum stub suppression
    via `[[tool.mypy.overrides]]`
  - `transition_generator.py` (7): `Callable[..., str]`,
    `Optional[str] = None`
  - `naming_convention.py` (6): typed CONVERSION_PATTERNS
  - `model.py` (4): `Union[List[ActionStep], List[str]]` for
    State entry/exit/do_actions (backward compat with str)
  - misc: enum_generator, variable_generator, c_code_generator,
    logger, response_parser/validator, prompt_generator

**Tests:** 48 suites / 1793 PASS / 0 FAIL.

**Remaining (v3.5.3+)**

- S-3 Step 2: ubuntu-26.04 preview job (2026-10-19 onwards)


### v3.5.1 Released"""

t = README.read_text(encoding="utf-8")
if "### v3.5.2 Released" in t:
    print("[SKIP] already present")
elif ANCHOR not in t:
    raise SystemExit("[FAIL] anchor not found")
else:
    t = t.replace(ANCHOR, INSERT, 1)
    README.write_text(t, encoding="utf-8")
    print(f"[OK] {README}")
