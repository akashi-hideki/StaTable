# tests/test_v3_5_gui_output_clean.py
"""
StaTable v3.5.0 S-GUI test suite

B: stale-file (orphan) detection
C: Clean & Regenerate UI + robust_rmtree

Static checks (source-level):
  - statable/output_utils.py defines find_orphan_files
  - statable/__init__.py re-exports find_orphan_files
  - codegen records last_orphans in save_generated_code
  - main_window / dialog call show_orphan_warning
  - clean_generate_code uses robust_rmtree

Runtime checks (offscreen, tempdir):
  - find_orphan_files: clean -> [], orphan -> path,
    nested orphan, missing dir -> [], abs/rel mix
  - robust_rmtree: removes read-only files, returns []
  - robust_rmtree: retries & reports missing permission
"""

import os
import stat
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import tempfile
from pathlib import Path

_total = 0
_passed = 0
_failed = 0


def check(label, condition):
    global _total, _passed, _failed
    _total += 1
    if condition:
        _passed += 1
        print(f"  [PASS] {label}")
    else:
        _failed += 1
        print(f"  [FAIL] {label}")


def section(title):
    print()
    print(f"[{title}]")


ROOT = Path(__file__).resolve().parent.parent

# ======================================================================
# [1] Source-level structure
# ======================================================================
section("1 source structure")
utils = (ROOT / "statable" / "output_utils.py").read_text(encoding="utf-8")
init = (ROOT / "statable" / "__init__.py").read_text(encoding="utf-8")
cg = (ROOT / "codegen" / "c_code_generator.py").read_text(encoding="utf-8")
mw = (ROOT / "statable_gui" / "main_window.py").read_text(encoding="utf-8")
dg = (ROOT / "statable_gui" / "code_generation_dialog.py").read_text(encoding="utf-8")
ow = (ROOT / "statable_gui" / "output_warning.py").read_text(encoding="utf-8")
fc = (ROOT / "statable_gui" / "fs_cleanup.py").read_text(encoding="utf-8")

check("output_utils defines find_orphan_files",
      "def find_orphan_files(" in utils)
check("output_utils in __all__",
      '"find_orphan_files"' in utils and "find_orphan_files" in init)
check("statable re-exports find_orphan_files",
      "from .output_utils import find_orphan_files" in init)
check("codegen imports find_orphan_files",
      "from statable.output_utils import find_orphan_files" in cg)
check("codegen initializes last_orphans",
      "self.last_orphans: List[str] = []" in cg)
check("codegen records last_orphans on save",
      "self.last_orphans = find_orphan_files(" in cg)
check("main_window calls show_orphan_warning",
      "show_orphan_warning(" in mw and "from .output_warning" in mw)
check("main_window has Clean generate action",
      'self.tr("Clean generate"), self)' in mw)
check("main_window clean uses robust_rmtree",
      "robust_rmtree(output_dir)" in mw)
check("main_window clean has skip_confirm param",
      "skip_confirm: bool = False" in mw)
check("dialog calls show_orphan_warning",
      "show_orphan_warning(" in dg)
check("dialog has _clean_and_resave",
      "def _clean_and_resave" in dg)
check("dialog clean uses robust_rmtree",
      "robust_rmtree(output_dir)" in dg)
check("output_warning exposes on_clean callback",
      "on_clean=None" in ow and "Clean && Regenerate" in ow)
check("fs_cleanup chmod + retry",
      "os.chmod(p, stat.S_IWRITE)" in fc and "max_retries" in fc)

# ======================================================================
# [2] find_orphan_files runtime
# ======================================================================
section("2 find_orphan_files runtime")

from statable.output_utils import find_orphan_files


def _mkfile(root, rel, content="x"):
    full = os.path.join(root, rel)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)
    return os.path.abspath(full)


with tempfile.TemporaryDirectory() as td:
    a1 = _mkfile(td, "a.c")
    a2 = _mkfile(td, "sub/b.c")
    check("clean dir -> []", find_orphan_files(td, [a1, a2]) == [])

    _mkfile(td, "stale.c")
    o = find_orphan_files(td, [a1, a2])
    check("single orphan detected", len(o) == 1 and o[0].endswith("stale.c"))

    _mkfile(td, "Driver/old.c")
    o = find_orphan_files(td, [a1, a2])
    check("nested orphan detected",
          any(p.endswith(os.path.join("Driver", "old.c")) for p in o))
    check("orphan list sorted", o == sorted(o))

with tempfile.TemporaryDirectory() as td:
    check("empty dir -> []", find_orphan_files(td, []) == [])

check("missing dir -> []",
      find_orphan_files(os.path.join(tempfile.gettempdir(),
                                     "no_such_xyz_987"), []) == [])

with tempfile.TemporaryDirectory() as td:
    f = _mkfile(td, "keep.c")
    check("abs/rel normalization",
          find_orphan_files(td, [os.path.relpath(f)]) == [])

# ======================================================================
# [3] robust_rmtree runtime
# ======================================================================
section("3 robust_rmtree runtime")

from statable_gui.fs_cleanup import robust_rmtree

with tempfile.TemporaryDirectory() as td:
    _mkfile(td, "sub/ro.c", "readonly")
    ro = os.path.join(td, "sub", "ro.c")
    os.chmod(ro, stat.S_IREAD)
    errs = robust_rmtree(td)
    check("removes read-only file", errs == [] and not os.path.exists(td))

with tempfile.TemporaryDirectory() as td:
    _mkfile(td, "a.c")
    _mkfile(td, "sub/b.c")
    errs = robust_rmtree(td)
    check("removes normal tree", errs == [])

errs = robust_rmtree(os.path.join(tempfile.gettempdir(),
                                  "no_such_dir_zzz"))
check("missing dir -> no crash", isinstance(errs, list))

# ======================================================================
# Summary
# ======================================================================
print()
print("=" * 70)
print(f"  TOTAL: {_total}  PASSED: {_passed}  FAILED: {_failed}")
print("=" * 70)

os._exit(0 if _failed == 0 else 1)
