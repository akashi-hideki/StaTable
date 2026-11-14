"""patch_mypy_batch1.py"""
from __future__ import annotations
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
    print(f"[OK] {label} ({path})")

# --- 1. literal_library.py:50 ---
_must(
    "statable/shared/literal_library.py",
    "    def get(self, name: str) -> LiteralDefinition:\n"
    "        return self.literals.get(name)\n",
    "    def get(self, name: str) -> LiteralDefinition:\n"
    "        result = self.literals.get(name)\n"
    "        assert result is not None, f\"literal not found: {name}\"\n"
    "        return result\n",
    "literal_library get",
)

# --- 2. condition_library.py:47 ---
_must(
    "statable/shared/condition_library.py",
    "    def get(self, name: str) -> ConditionTemplate:\n"
    "        return self.condition_templates.get(name)\n",
    "    def get(self, name: str) -> ConditionTemplate:\n"
    "        result = self.condition_templates.get(name)\n"
    "        assert result is not None, f\"template not found: {name}\"\n"
    "        return result\n",
    "condition_library get",
)

# --- 3. enum_generator.py:315 ---
_must(
    "codegen/enum_generator.py",
    "                           flags: List[EventFlag] = None) -> str:\n",
    "                           flags: Optional[List[EventFlag]] = None) -> str:\n",
    "enum_generator flags Optional",
)

# --- 4. logger.py:9 ---
_must(
    "codegen/validate/logger.py",
    "def setup_logger(name: str = \"validate\", log_dir: str = None) -> logging.Logger:\n",
    "def setup_logger(name: str = \"validate\",\n"
    "                 log_dir: Optional[str] = None) -> logging.Logger:\n",
    "logger log_dir Optional",
)

# --- 5. c_code_generator.py:955 ---
_must(
    "codegen/c_code_generator.py",
    "                self._get_events_list(sm),\n"
    "                None,\n"
    "            )\n",
    "                self._get_events_list(sm),\n"
    "                [],\n"
    "            )\n",
    "c_code_generator None -> []",
)

print("[DONE]")
