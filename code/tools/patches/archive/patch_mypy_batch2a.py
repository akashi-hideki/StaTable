"""patch_mypy_batch2a.py"""
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

# enum_generator.py:158
_must(
    "codegen/enum_generator.py",
    "            comments.append(f\"Title: {state.title}\")\n",
    "            comments.append(f\"Title: {getattr(state, 'title', '')}\")\n",
    "enum state.title",
)

# transition_generator.py:752 (re-apply)
_must(
    "codegen/transition_generator.py",
    "            row = f\"    /* {state_padded}*/ {{ \"\n",
    "            row: str = f\"    /* {state_padded}*/ {{ \"\n",
    "transition row type",
)

print("[DONE]")
