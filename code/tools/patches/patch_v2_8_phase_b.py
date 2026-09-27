# code/tools/patch_v2_8_phase_b.py
"""
Phase B patch for v2.8.0.

Targets:
    codegen/validate/change_actions.py
    codegen/validate/response_parser.py

Edits:

  change_actions.py:
    E1. import typing: add List.
    E2. Replace ChangeRequest with an extended version:
          + id: str = ""
          + evidence: List[str] = field(default_factory=list)
          + priority: str = "medium"
          + confidence: float = 1.0
        to_dict / from_dict updated to round-trip the new fields.
        Existing code (positional/keyword use of the 4 original
        fields) remains source-compatible because the new fields
        are appended with defaults.

  response_parser.py:
    E3. Replace ACTION_MAPPING with an auto-generated dict of all
        17 ChangeActionType values (10 legacy + 7 cell-level).
    E4. Update _extract_json to try <response> first, then <json>,
        then MARKERS-based, then brace-matching fallback.
    E5. Update _parse_change to preserve id / evidence / priority /
        confidence when present in the AI JSON.

Safety:
    - Backup once per target (kept if already present).
    - Literal anchors; refuses to apply on missing / multi-hit.
    - Idempotent.

Usage:
    cd C:\\Users\\user\\OneDrive\\ドキュメント\\GitHub\\StaTable\\code
    python tools\\patch_v2_8_phase_b.py
"""
from __future__ import annotations

import sys
from pathlib import Path

CODE_DIR = Path(__file__).resolve().parent.parent
CHANGE_ACTIONS = CODE_DIR / "codegen" / "validate" / "change_actions.py"
RESPONSE_PARSER = CODE_DIR / "codegen" / "validate" / "response_parser.py"


# ======================================================================
# E1: typing import
# ======================================================================
E1_OLD = "from typing import Dict, Any\n"
E1_NEW = "from typing import Dict, Any, List\n"


# ======================================================================
# E2: ChangeRequest dataclass
# ======================================================================
E2_OLD = '''@dataclass
class ChangeRequest:
    """Change request"""
    action: ChangeActionType
    params: Dict[str, Any] = field(default_factory=dict)
    reason: str = ""
    source: str = "ai"

    def to_dict(self) -> Dict:
        return {
            'action': self.action.value,
            'params': self.params,
            'reason': self.reason,
            'source': self.source,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'ChangeRequest':
        return cls(
            action=ChangeActionType(data['action']),
            params=data.get('params', {}),
            reason=data.get('reason', ''),
            source=data.get('source', 'ai'),
        )

    def __str__(self) -> str:
        return (f"ChangeRequest(action={self.action.value}, "
                f"params={self.params}, reason={self.reason})")
'''

E2_NEW = '''@dataclass
class ChangeRequest:
    """Change request.

    [v2.8.0 Phase B]
      Added extended fields so AI proposals can carry:
        id          - stable identifier (e.g. "C-001")
        evidence    - list of validation codes / identifiers
        priority    - "high" | "medium" | "low"
        confidence  - 0.0 .. 1.0

      Backward compatible: the original 4 fields keep their
      positions and defaults; the new fields are appended with
      defaults, so existing constructor calls are unaffected.
    """
    action: ChangeActionType
    params: Dict[str, Any] = field(default_factory=dict)
    reason: str = ""
    source: str = "ai"
    # [v2.8.0 Phase B] extended fields
    id: str = ""
    evidence: List[str] = field(default_factory=list)
    priority: str = "medium"
    confidence: float = 1.0

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'action': self.action.value,
            'params': self.params,
            'reason': self.reason,
            'source': self.source,
            'evidence': list(self.evidence),
            'priority': self.priority,
            'confidence': self.confidence,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'ChangeRequest':
        try:
            confidence = float(data.get('confidence', 1.0))
        except (TypeError, ValueError):
            confidence = 1.0
        return cls(
            action=ChangeActionType(data['action']),
            params=data.get('params', {}),
            reason=data.get('reason', ''),
            source=data.get('source', 'ai'),
            id=str(data.get('id', '') or ''),
            evidence=list(data.get('evidence', []) or []),
            priority=str(data.get('priority', 'medium') or 'medium'),
            confidence=confidence,
        )

    def __str__(self) -> str:
        return (f"ChangeRequest(action={self.action.value}, "
                f"params={self.params}, reason={self.reason})")
'''


# ======================================================================
# E3: ACTION_MAPPING auto-generation
# ======================================================================
E3_OLD = '''    ACTION_MAPPING = {
        'set_initial': ChangeActionType.SET_INITIAL,
        'add_transition': ChangeActionType.ADD_TRANSITION,
        'add_state': ChangeActionType.ADD_STATE,
        'add_event': ChangeActionType.ADD_EVENT,
        'remove_transition': ChangeActionType.REMOVE_TRANSITION,
        'update_transition': ChangeActionType.UPDATE_TRANSITION,
        'add_role_function': ChangeActionType.ADD_ROLE_FUNCTION,
        'remove_role_function': ChangeActionType.REMOVE_ROLE_FUNCTION,
        'add_variable': ChangeActionType.ADD_VARIABLE,
        'add_flag': ChangeActionType.ADD_FLAG,
    }
'''

E3_NEW = '''    # [v2.8.0 Phase B]
    # Auto-generated from ChangeActionType so every future action
    # is picked up without touching this file. Covers all 17 types
    # (10 legacy + 7 cell-level).
    ACTION_MAPPING = {t.value: t for t in ChangeActionType}
'''


# ======================================================================
# E4: _extract_json
# ======================================================================
E4_OLD = '''    def _extract_json(self, text: str) -> Optional[str]:
        primary = self.markers.get('primary', {})
        json_text = self._extract_with_markers(text, primary.get('start', ''), primary.get('end', ''))
        if json_text:
            return json_text
        
        for alt in self.markers.get('alternatives', []):
            json_text = self._extract_with_markers(text, alt.get('start', ''), alt.get('end', ''))
            if json_text:
                return json_text
        
        start_idx = text.find('{')
        end_idx = text.rfind('}')
        if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
            candidate = text[start_idx:end_idx + 1]
            try:
                json.loads(candidate)
                return candidate
            except json.JSONDecodeError:
                pass
        return None
'''

E4_NEW = '''    def _extract_json(self, text: str) -> Optional[str]:
        """Extract the JSON payload from an AI reply.

        Priority (v2.8.0 Phase B):
          1. <response>...</response>  - v2.8.0 marker
          2. <json>...</json>          - legacy marker
          3. MARKERS-configured markers (keywords.py)
          4. Brace matching { ... }    - last-resort fallback
        """
        # 1. <response>...</response>
        json_text = self._extract_with_markers(
            text, '<response>', '</response>')
        if json_text:
            return json_text

        # 2. <json>...</json> (legacy)
        json_text = self._extract_with_markers(text, '<json>', '</json>')
        if json_text:
            return json_text

        # 3. MARKERS-configured markers (keywords.py)
        primary = self.markers.get('primary', {})
        json_text = self._extract_with_markers(
            text, primary.get('start', ''), primary.get('end', ''))
        if json_text:
            return json_text

        for alt in self.markers.get('alternatives', []):
            json_text = self._extract_with_markers(
                text, alt.get('start', ''), alt.get('end', ''))
            if json_text:
                return json_text

        # 4. Brace-matching fallback
        start_idx = text.find('{')
        end_idx = text.rfind('}')
        if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
            candidate = text[start_idx:end_idx + 1]
            try:
                json.loads(candidate)
                return candidate
            except json.JSONDecodeError:
                pass
        return None
'''


# ======================================================================
# E5: _parse_change
# ======================================================================
E5_OLD = '''    def _parse_change(self, data: Dict) -> Optional[ChangeRequest]:
        action_str = data.get('action', '')
        if action_str not in self.ACTION_MAPPING:
            return None
        return ChangeRequest(
            action=self.ACTION_MAPPING[action_str],
            params=data.get('params', {}),
            reason=data.get('reason', ''),
            source='ai'
        )
'''

E5_NEW = '''    def _parse_change(self, data: Dict) -> Optional[ChangeRequest]:
        action_str = data.get('action', '')
        if action_str not in self.ACTION_MAPPING:
            return None
        # [v2.8.0 Phase B] Preserve extended fields when present.
        try:
            confidence = float(data.get('confidence', 1.0))
        except (TypeError, ValueError):
            confidence = 1.0
        return ChangeRequest(
            action=self.ACTION_MAPPING[action_str],
            params=data.get('params', {}),
            reason=data.get('reason', ''),
            source='ai',
            id=str(data.get('id', '') or ''),
            evidence=list(data.get('evidence', []) or []),
            priority=str(data.get('priority', 'medium') or 'medium'),
            confidence=confidence,
        )
'''


# ======================================================================
# Edit helpers
# ======================================================================
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


def _backup(target: Path) -> None:
    backup = target.with_suffix(target.suffix + ".bak")
    if not backup.exists():
        backup.write_text(target.read_text(encoding="utf-8"),
                          encoding="utf-8")
        print(f"  Backup: {backup}")
    else:
        print(f"  Backup: already exists, keeping {backup}")


def _patch_file(target: Path, edits: list) -> bool:
    print(f"\nTarget: {target}")
    if not target.exists():
        print(f"  [FAIL] not found")
        raise SystemExit(1)

    original = target.read_text(encoding="utf-8")
    _backup(target)

    patched = original
    for anchor, replacement, label in edits:
        patched = _apply_edit(patched, anchor, replacement, label)

    if patched == original:
        print("  [INFO] no changes (already up to date)")
        return False
    target.write_text(patched, encoding="utf-8")
    print(f"  [DONE] {target.name} patched")
    return True


# ======================================================================
# Main
# ======================================================================
def main() -> int:
    print("=" * 70)
    print("  v2.8.0 Phase B patch")
    print("=" * 70)

    _patch_file(CHANGE_ACTIONS, [
        (E1_OLD, E1_NEW, "E1 import List"),
        (E2_OLD, E2_NEW, "E2 ChangeRequest extended fields"),
    ])

    _patch_file(RESPONSE_PARSER, [
        (E3_OLD, E3_NEW, "E3 ACTION_MAPPING auto-generated (17)"),
        (E4_OLD, E4_NEW, "E4 _extract_json: <response> priority"),
        (E5_OLD, E5_NEW, "E5 _parse_change: preserve new fields"),
    ])

    print()
    print("[COMPLETE] Phase B patch done.")
    print()
    print("Next:")
    print("  python tests\\test_v2_8_p2_response_parser.py")
    print("  python tests\\test_v2_8_p1_ai_prompt.py    (regression)")
    print("  python tests\\test_v2_2_p12_6.py           (regression)")
    return 0


if __name__ == "__main__":
    sys.exit(main())