#!/usr/bin/env python3
"""
Scan Tier 3 files to determine which ones are affected by v2.2.

For each Tier 3 file, search for v2.2 keywords and report relevance.

Usage:
    python tools/scan_tier3.py
    python tools/scan_tier3.py --output json
"""

import argparse
import ast
import json
import re
from pathlib import Path
from typing import Dict, List, Set


# v2.2 keyword -> weight (higher = more critical)
KEYWORDS = {
    # Tier 1/P1 (data model)
    "TransitionStep": 10,
    "ActionStep": 10,
    "TransitionCell": 10,
    "TransitionRelation": 10,
    "early_return": 10,
    "shared_condition": 10,
    "_handled": 8,
    # Tier 2/P2 (codegen)
    "pre_actions": 6,
    "else_actions": 6,
    "has_else": 5,
    "else_target": 5,
    "TransitionContext_t": 5,
    "StateMachine_Process": 5,
    # GUI layer
    "ActionDraft": 8,
    "ActionEditorDialog": 10,
    "FlowItem": 8,
    "FlowCanvas": 8,
    "TransitionListDialog": 8,
    "ConditionBuilderDialog": 6,
    "RoleFunctionLibrary": 4,
    "ConditionLibrary": 4,
    # Preferences
    "Preferences": 3,
    "preference": 2,
    # Entry/exit
    "entry": 4,
    "exit": 4,
}


TIER3_FILES = [
    "statable_gui/main_window.py",
    "statable_gui/widgets.py",
    "statable_gui/action_edit_dialog.py",
    "statable_gui/role_function_dialog.py",
    "statable_gui/common_widgets.py",
    "statable_gui/global_defs_dialog.py",
    "statable_gui/layer_settings_dialog.py",
    "statable_gui/preferences.py",
    "statable_gui/preference_keys.py",
    "statable_gui/validation_dialog.py",
    "statable_gui/interrupt_handler_edit_dialog.py",
    "statable_gui/event_definition_dialog.py",
    "statable_gui/event_delivery_settings_dialog.py",
    "statable_gui/event_queue_dialog.py",
    "statable_gui/code_generation_dialog.py",
    "statable_gui/code_generation_settings_dialog.py",
    "statable_gui/traceball.py",
    "statable_gui/libcntrl/literal_management_dialog.py",
    "statable_gui/sample_data.py",
]


def scan_file(path: Path) -> Dict:
    """Scan one file for v2.2 keywords."""
    try:
        source = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return {"path": str(path), "exists": False, "score": 0, "hits": {}}

    hits: Dict[str, int] = {}
    for kw, weight in KEYWORDS.items():
        # Word boundary search (for identifiers)
        pattern = rf"\b{re.escape(kw)}\b"
        count = len(re.findall(pattern, source))
        if count:
            hits[kw] = count

    score = sum(KEYWORDS[kw] * min(c, 3) for kw, c in hits.items())
    return {
        "path": str(path),
        "exists": True,
        "score": score,
        "hits": hits,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", default=".")
    p.add_argument("--output", default="text", choices=["text", "json"])
    args = p.parse_args()

    root = Path(args.root)
    results = [scan_file(root / f) for f in TIER3_FILES]
    results.sort(key=lambda r: r["score"], reverse=True)

    if args.output == "json":
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return

    print("=== Tier 3 scan results (sorted by score) ===\n")
    print(f"{'Score':>6}  {'File':<55}  Top keywords")
    print("-" * 110)
    for r in results:
        if not r["exists"]:
            print(f"{'MISS':>6}  {r['path']:<55}  (not found)")
            continue
        top = sorted(r["hits"].items(), key=lambda x: -x[1])[:4]
        top_str = ", ".join(f"{k}({v})" for k, v in top)
        print(f"{r['score']:>6}  {r['path']:<55}  {top_str}")

    print("\nLegend:")
    print("  score >= 30 : Tier 3-A (must share for P4)")
    print("  score 10-29 : Tier 3-B (share when needed)")
    print("  score  1-9  : Tier 3-C (reference only)")
    print("  score  0    : Tier 3-D (no change)")


if __name__ == "__main__":
    main()