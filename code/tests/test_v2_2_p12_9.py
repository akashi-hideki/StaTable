#!/usr/bin/env python3
"""
P12-9 (XML round-trip test) for StaTable v2.2.5.

Verifies that loading an XML and saving it back preserves:
  Level 1: XML structure (canonical form, ignoring attribute order)
  Level 2: StateMachine semantics (states/events/transitions/cells)

Run:
  python tests/test_v2_2_p12_9.py
"""

import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

XML_PATH = PROJECT_ROOT / "tests" / "data" / "v22_features_test3.xml"


# ======================================================================
# Harness
# ======================================================================
class Result:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def ok(self, name):
        self.passed += 1
        print(f"  [PASS] {name}")

    def fail(self, name, msg=""):
        self.failed += 1
        self.errors.append((name, msg))
        print(f"  [FAIL] {name}")
        if msg:
            for line in str(msg).splitlines():
                print(f"         {line}")

    def summary(self):
        total = self.passed + self.failed
        print()
        print("=" * 70)
        print(f"  TOTAL: {total}  PASSED: {self.passed}  FAILED: {self.failed}")
        print("=" * 70)
        if self.errors:
            print("\nFailures:")
            for name, msg in self.errors:
                print(f"  - {name}")
        return self.failed == 0


R = Result()


def check(name, cond, msg=""):
    if cond:
        R.ok(name)
        return True
    R.fail(name, msg)
    return False


# ======================================================================
# Canonical form (recursive, attribute order ignored)
# ======================================================================
def canon(elem):
    """Canonical representation: (tag, sorted_attrs, sorted_children)."""
    attrs = tuple(sorted(elem.attrib.items()))
    children = tuple(sorted(
        (canon(c) for c in elem),
        key=lambda x: repr(x),  # deterministic ordering
    ))
    text = (elem.text or '').strip()
    return (elem.tag, attrs, text, children)


# ======================================================================
# Semantic comparison
# ======================================================================
def sm_summary(sm):
    """Extract comparable summary of a StateMachine."""
    return {
        'states': {
            name: {
                'type': s.type.value,
                'parent': s.parent,
                'entry': list(s.entry),
                'exit': list(s.exit),
                'do': s.do,
                'description': s.description,
            }
            for name, s in sm.states.items()
        },
        'events': {
            name: {
                'id': e.id,
                'kind': e.kind.value,
                'priority': e.priority,
                'delivery_type': e.delivery_type.value,
                'source_layer': e.source_layer.value,
                'data_type': e.data_type,
                'data_name': e.data_name,
                'title': e.title,
            }
            for name, e in sm.events.items()
        },
        'transitions': sorted([
            {
                'source': t.source,
                'event': t.event,
                'condition': t.condition,
                'pre_actions': list(t.pre_actions),
                'target': t.target,
                'has_else': t.has_else,
                'else_target': t.else_target,
                'else_actions': list(t.else_actions),
                'early_return': t.early_return,
                'label': t.label,
                'transition_type': t.transition_type,
                'title': t.title,
            }
            for t in sm.transitions
        ], key=lambda d: (d['source'], d['event'], d['label'], d['condition'])),
        'role_functions': {
            name: {
                'namespace': rf.namespace,
                'return_type': rf.return_type,
                'arg1_type': rf.arg1_type,
                'arg1_name': rf.arg1_name,
                'arg2_type': rf.arg2_type,
                'arg2_name': rf.arg2_name,
                'title': rf.title,
            }
            for name, rf in sm.role_functions.items()
        },
        'initial_state': sm.initial_state,
        'layer_name': sm.layer_name,
        'layer_priority': sm.layer_priority,
        'layer_description': sm.layer_description,
        'cell_actions': {
            key: [
                {'rf': a.role_function, 'trigger': a.trigger, 'title': a.title}
                for a in sm.get_actions_for_cell(*key)
            ]
            for key in sorted(sm.get_cell_keys())
        },
        'cell_relations': {
            key: [rel_summary(r) for r in sm.get_relations_for_cell(*key)]
            for key in sorted(sm.get_cell_keys())
        },
    }


def rel_summary(r):
    return {
        'kind': r.kind,
        'members': list(r.members),
        'shared_condition': r.shared_condition,
        'note': r.note,
        'children': [rel_summary(c) for c in getattr(r, 'children', [])],
    }


# ======================================================================
# Tests
# ======================================================================
def main():
    from statable.xml_io import project_from_xml, project_to_xml

    print("=" * 70)
    print("  StaTable v2.2.5 P12-9 (XML round-trip) test suite")
    print("=" * 70)

    # ---- 1. Load original ----
    print("\n[1] Load original XML")
    tabs1, gd1, rfl1, cl1, ll1, ps1 = project_from_xml(str(XML_PATH))
    check("original loaded", len(tabs1) > 0,
          f"tabs={len(tabs1)}")
    print(f"  tabs: {[n for n, _ in tabs1]}")

    # ---- 2. Save to temp file ----
    print("\n[2] Save to temp file")
    with tempfile.NamedTemporaryFile(
            mode='w', suffix='.xml', delete=False, encoding='utf-8') as f:
        tmp_path = f.name
    try:
        project_to_xml(
            tabs=tabs1, global_defs=gd1, filepath=tmp_path,
            role_function_library=rfl1,
            condition_library=cl1,
            literal_library=ll1,
            project_settings=ps1,
        )
        check("saved", Path(tmp_path).exists())
    except Exception as e:
        check("saved", False, f"{e}")
        return

    # ---- 3. Reload ----
    print("\n[3] Reload saved file")
    try:
        tabs2, gd2, rfl2, cl2, ll2, ps2 = project_from_xml(tmp_path)
        check("reloaded", len(tabs2) == len(tabs1),
              f"tabs1={len(tabs1)}, tabs2={len(tabs2)}")
    except Exception as e:
        check("reloaded", False, f"{e}")
        return

    # ---- 4. Level 1: XML canonical comparison ----
    print("\n[4] Level 1: XML canonical structure")
    tree1 = ET.parse(str(XML_PATH))
    tree2 = ET.parse(tmp_path)
    c1 = canon(tree1.getroot())
    c2 = canon(tree2.getroot())
    check("XML canonical equal", c1 == c2,
          "canonical trees differ" if c1 != c2 else "")

    # ---- 5. Level 2: Semantic comparison ----
    print("\n[5] Level 2: StateMachine semantics")
    for name1, sm1 in tabs1:
        found = None
        for name2, sm2 in tabs2:
            if name1 == name2:
                found = sm2
                break
        if found is None:
            check(f"tab '{name1}' present", False)
            continue

        s1 = sm_summary(sm1)
        s2 = sm_summary(found)

        # Per-key comparison for better error messages
        for key in s1:
            check(f"tab '{name1}': {key}",
                  s1[key] == s2[key],
                  _diff(s1[key], s2[key]) if s1[key] != s2[key] else "")

    # ---- 6. GlobalDefinitions comparison ----
    print("\n[6] GlobalDefinitions")
    check("variables count",
          len(gd1.variables) == len(gd2.variables),
          f"{len(gd1.variables)} vs {len(gd2.variables)}")
    check("flags count",
          len(gd1.flags) == len(gd2.flags),
          f"{len(gd1.flags)} vs {len(gd2.flags)}")
    check("interrupts count",
          len(gd1.interrupts) == len(gd2.interrupts),
          f"{len(gd1.interrupts)} vs {len(gd2.interrupts)}")
    check("event_queues count",
          len(gd1.event_queues) == len(gd2.event_queues),
          f"{len(gd1.event_queues)} vs {len(gd2.event_queues)}")

    # ---- 7. Libraries comparison ----
    print("\n[7] Shared libraries")
    if rfl1 is not None and rfl2 is not None:
        n1 = len(rfl1.list_all())
        n2 = len(rfl2.list_all())
        check("role_function_library count", n1 == n2, f"{n1} vs {n2}")
    if cl1 is not None and cl2 is not None:
        n1 = len(cl1.list_all())
        n2 = len(cl2.list_all())
        check("condition_library count", n1 == n2, f"{n1} vs {n2}")

    # ---- 8. Project settings ----
    print("\n[8] Project settings")
    check("project_name", ps1.get('project_name') == ps2.get('project_name'),
          f"{ps1.get('project_name')} vs {ps2.get('project_name')}")

    ok = R.summary()
    # Cleanup
    try:
        Path(tmp_path).unlink()
    except Exception:
        pass
    sys.exit(0 if ok else 1)


def _diff(a, b):
    """Compact diff for readability."""
    lines = []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in set(a) | set(b):
            if a.get(k) != b.get(k):
                lines.append(f"    {k}:")
                lines.append(f"      1: {a.get(k)!r}")
                lines.append(f"      2: {b.get(k)!r}")
    else:
        lines.append(f"    1: {a!r}")
        lines.append(f"    2: {b!r}")
    return "\n".join(lines)


if __name__ == "__main__":
    main()