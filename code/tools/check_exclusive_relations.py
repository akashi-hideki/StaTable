#!/usr/bin/env python3
"""
Check that exclusive relations force early_return=True on all members.

Reads XML and reports:
  - Members of exclusive relations
  - Whether each member has early_return=True
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from statable.xml_io import project_from_xml


def main():
    xml = sys.argv[1] if len(sys.argv) > 1 else "tests/data/v22_features_test3.xml"
    tabs, gd, _, _, _, _ = project_from_xml(xml)

    issues = []
    for tab_name, sm in tabs:
        for (source, event) in sm.get_cell_keys():
            relations = sm.get_relations_for_cell(source, event)
            transitions = sm.get_transitions_for_cell(source, event)
            by_label = {getattr(t, 'label', ''): t for t in transitions}

            for rel in relations:
                if rel.kind != "exclusive":
                    continue
                for m in rel.members:
                    t = by_label.get(m)
                    if t is None:
                        continue
                    if not getattr(t, 'early_return', False):
                        issues.append(
                            f"[{tab_name}] ({source}, {event or 'Completion'}): "
                            f"exclusive member '{m}' has early_return=False")

    print("=" * 70)
    print(f"  Exclusive relation check: {xml}")
    print("=" * 70)
    if issues:
        print(f"\n[WARN] {len(issues)} issue(s):")
        for i in issues:
            print(f"  {i}")
    else:
        print("\n[OK] All exclusive members have early_return=True")

    return 0 if not issues else 1


if __name__ == "__main__":
    sys.exit(main())