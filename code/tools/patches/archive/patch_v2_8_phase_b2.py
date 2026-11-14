# code/tools/patch_v2_8_phase_b2.py
"""
Re-apply the Phase B ChangeRequest edit (E2) after the first attempt
was skipped due to a whitespace mismatch in the __str__ continuation
line.

Strategy:
    Split E2 into 3 small, robust edits:

      A. Insert 4 new fields right after `source: str = "ai"`.

      B. Extend `to_dict` return dict with the new keys.

      C. Extend `from_dict` with the new keys and a safe float
         coercion for `confidence`.

    Each edit uses a short, distinctive, uniquely-occurring anchor.

Safety:
    - Backup once (kept if already present).
    - Literal anchors; refuses to apply on missing / multi-hit.
    - Idempotent.

Usage:
    cd C:\\Users\\user\\OneDrive\\ドキュメント\\GitHub\\StaTable\\code
    python tools\\patch_v2_8_phase_b2.py
"""
from __future__ import annotations

import sys
from pathlib import Path

CODE_DIR = Path(__file__).resolve().parent.parent
TARGET = CODE_DIR / "codegen" / "validate" / "change_actions.py"


# ======================================================================
# Edit A: new field declarations
# ======================================================================
A_OLD = '    source: str = "ai"\n\n    def to_dict'

A_NEW = (
    '    source: str = "ai"\n'
    '    # [v2.8.0 Phase B] extended fields\n'
    '    id: str = ""\n'
    '    evidence: List[str] = field(default_factory=list)\n'
    '    priority: str = "medium"\n'
    '    confidence: float = 1.0\n'
    '\n'
    '    def to_dict'
)


# ======================================================================
# Edit B: to_dict body
# ======================================================================
B_OLD = (
    "        return {\n"
    "            'action': self.action.value,\n"
    "            'params': self.params,\n"
    "            'reason': self.reason,\n"
    "            'source': self.source,\n"
    "        }"
)

B_NEW = (
    "        return {\n"
    "            'id': self.id,\n"
    "            'action': self.action.value,\n"
    "            'params': self.params,\n"
    "            'reason': self.reason,\n"
    "            'source': self.source,\n"
    "            'evidence': list(self.evidence),\n"
    "            'priority': self.priority,\n"
    "            'confidence': self.confidence,\n"
    "        }"
)


# ======================================================================
# Edit C: from_dict body
# ======================================================================
C_OLD = (
    "        return cls(\n"
    "            action=ChangeActionType(data['action']),\n"
    "            params=data.get('params', {}),\n"
    "            reason=data.get('reason', ''),\n"
    "            source=data.get('source', 'ai'),\n"
    "        )"
)

C_NEW = (
    "        try:\n"
    "            confidence = float(data.get('confidence', 1.0))\n"
    "        except (TypeError, ValueError):\n"
    "            confidence = 1.0\n"
    "        return cls(\n"
    "            action=ChangeActionType(data['action']),\n"
    "            params=data.get('params', {}),\n"
    "            reason=data.get('reason', ''),\n"
    "            source=data.get('source', 'ai'),\n"
    "            id=str(data.get('id', '') or ''),\n"
    "            evidence=list(data.get('evidence', []) or []),\n"
    "            priority=str(data.get('priority', 'medium') or 'medium'),\n"
    "            confidence=confidence,\n"
    "        )"
)


def _apply_edit(text: str, anchor: str, replacement: str, label: str) -> str:
    count = text.count(anchor)
    if count == 0:
        print(f"  [SKIP] {label}: anchor not found (already applied?)")
        return text
    if count > 1:
        print(f"  [FAIL] {label}: anchor found {count} times (expected 1)")
        raise SystemExit(1)
    print(f"  [APPLY] {label}")
    return text.replace(anchor, replacement, 1)


def main() -> int:
    print("=" * 70)
    print("  v2.8.0 Phase B / re-apply E2")
    print("=" * 70)

    if not TARGET.exists():
        print(f"[FAIL] target not found: {TARGET}")
        return 1

    print(f"\nTarget: {TARGET}")
    original = TARGET.read_text(encoding="utf-8")

    backup = TARGET.with_suffix(TARGET.suffix + ".bak2")
    if not backup.exists():
        backup.write_text(original, encoding="utf-8")
        print(f"  Backup: {backup}")
    else:
        print(f"  Backup: already exists, keeping {backup}")

    patched = original
    patched = _apply_edit(patched, A_OLD, A_NEW, "A. field declarations")
    patched = _apply_edit(patched, B_OLD, B_NEW, "B. to_dict body")
    patched = _apply_edit(patched, C_OLD, C_NEW, "C. from_dict body")

    if patched == original:
        print()
        print("[INFO] No changes (already applied).")
        return 0

    TARGET.write_text(patched, encoding="utf-8")
    print()
    print("[DONE] change_actions.py re-patched.")
    print()
    print("Verify:")
    print("  python tools\\diag_change_request.py")
    print("  python tests\\test_v2_8_p2_response_parser.py")
    print("  python tests\\test_v2_8_p1_ai_prompt.py")
    print("  python tests\\test_v2_2_p12_6.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())