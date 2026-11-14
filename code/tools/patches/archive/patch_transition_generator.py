"""patch_transition_generator.py"""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TG = ROOT / "codegen" / "transition_generator.py"
t = TG.read_text(encoding="utf-8")

def _must(old, new, label, count=1):
    global t
    n = t.count(old)
    if n != count:
        raise SystemExit(f"[FAIL] {label}: count={n} (expected {count})")
    t = t.replace(old, new)
    print(f"[OK] {label}")

# 1) Callable を import に追加
_must(
    "from typing import Any, Dict, List, Optional\n",
    "from typing import Any, Callable, Dict, List, Optional\n",
    "import Callable",
)

# 2) callable -> Callable (2箇所)
_must(
    "        self.table_generators: Dict[str, callable] = {\n",
    "        self.table_generators: Dict[str, Callable[..., str]] = {\n",
    "table_generators type",
)
_must(
    "        self.process_generators: Dict[str, callable] = {\n",
    "        self.process_generators: Dict[str, Callable[..., str]] = {\n",
    "process_generators type",
)

# 3) table_type: str = None -> Optional[str]
_must(
    "    def generate_transition_table(self, state_machine: StateMachine,\n"
    "                                  table_type: str = None) -> str:\n",
    "    def generate_transition_table(self, state_machine: StateMachine,\n"
    "                                  table_type: Optional[str] = None) -> str:\n",
    "table_type Optional",
)

# 4) generation_style: str = None -> Optional[str]
_must(
    "    def generate_process_function(self, state_machine: StateMachine,\n"
    "                                  generation_style: str = None) -> str:\n",
    "    def generate_process_function(self, state_machine: StateMachine,\n"
    "                                  generation_style: Optional[str] = None) -> str:\n",
    "generation_style Optional",
)

TG.write_text(t, encoding="utf-8")
print(f"[OK] wrote {TG}")
