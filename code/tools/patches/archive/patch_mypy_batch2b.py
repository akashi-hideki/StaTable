"""patch_mypy_batch2b.py"""
from __future__ import annotations
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def _must(path, old, new, label, count=1):
    p = ROOT / path
    t = p.read_text(encoding="utf-8")
    n = t.count(old)
    if n != count:
        raise SystemExit(f"[FAIL] {label}: count={n} (expected {count})")
    t = t.replace(old, new)
    p.write_text(t, encoding="utf-8")
    print(f"[OK] {label}")

def _ensure_import(path, names):
    p = ROOT / path
    t = p.read_text(encoding="utf-8")
    m = re.search(r"from typing import ([^\n]+)", t)
    if m:
        imported = m.group(1)
        needs = [n for n in names if n not in imported]
        if needs:
            t = t.replace(
                f"from typing import {imported}",
                f"from typing import {imported}, {', '.join(needs)}",
                1,
            )
            p.write_text(t, encoding="utf-8")
            print(f"[OK] added {needs} to {path}")
        else:
            print(f"[SKIP] {path}: {names} already imported")
    else:
        # No typing import: add one after the first import line
        lines = t.split("\n")
        for i, l in enumerate(lines):
            if l.startswith("import ") or l.startswith("from "):
                lines.insert(i + 1, f"from typing import {', '.join(names)}")
                break
        p.write_text("\n".join(lines), encoding="utf-8")
        print(f"[OK] added typing import to {path}")

# --- 1. action_definitions.py ---
_ensure_import("codegen/validate/data/action_definitions.py",
               ["Any", "Dict"])
_must(
    "codegen/validate/data/action_definitions.py",
    "ACTION_DEFINITIONS = {\n",
    "ACTION_DEFINITIONS: Dict[str, Dict[str, Any]] = {\n",
    "action_definitions type",
)

# --- 2. keywords.py ---
_ensure_import("codegen/validate/data/keywords.py",
               ["Any", "Dict"])
_must(
    "codegen/validate/data/keywords.py",
    "MARKERS = {\n",
    "MARKERS: Dict[str, Any] = {\n",
    "keywords MARKERS type",
)

# --- 3. variable_generator.py ---
_ensure_import("codegen/variable_generator.py",
               ["Any", "Callable", "Dict", "List"])
_must(
    "codegen/variable_generator.py",
    "    INIT_FUNCTION_STEPS = [\n",
    "    INIT_FUNCTION_STEPS: List[Dict[str, Any]] = [\n",
    "INIT_FUNCTION_STEPS type",
)
_must(
    "codegen/variable_generator.py",
    "        self.step_executors = {\n",
    "        self.step_executors: Dict[str, Callable[..., Any]] = {\n",
    "step_executors type",
)

print("[DONE]")
