#!/usr/bin/env python3
"""Patch s1214 / s1216 in translations.json after apply_batch.py."""
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PATH = PROJECT_ROOT / "translations.json"

FIXES = {
    # s1214: keep action_name and multi-line params in the JSON example
    "s1214": (
        "{\\n"
        "  \\\"changes\\\": [\\n"
        "    {\\n"
        "      \\\"action\\\": \\\"set_initial\\\",\\n"
        "      \\\"params\\\": {\\\"state\\\": \\\"INIT\\\"},\\n"
        "      \\\"reason\\\": \\\"Initial state not set\\\"\\n"
        "    },\\n"
        "    {\\n"
        "      \\\"action\\\": \\\"add_transition\\\",\\n"
        "      \\\"params\\\": {\\n"
        "        \\\"source\\\": \\\"ERROR\\\",\\n"
        "        \\\"event\\\": \\\"RESET\\\",\\n"
        "        \\\"target\\\": \\\"IDLE\\\",\\n"
        "        \\\"action_name\\\": \\\"ResetError\\\"\\n"
        "      },\\n"
        "      \\\"reason\\\": \\\"No error recovery transition from error state\\\"\\n"
        "    }\\n"
        "  ]\\n"
        "}"
    ),
    # s1216: restore {action_definitions} and {validation_points}
    "s1216": (
        "You are an expert in embedded software state transition design.\\n\\n"
        "[Task]\\n"
        "Validate state transition design data and output necessary changes in JSON.\\n\\n"
        "[Output format]\\n"
        "Output pure JSON only.\\n"
        "No greetings, explanations, supplements, markers, or code block symbols.\\n\\n"
        "[Output example]\\n"
        "{example}\\n\\n"
        "[Actual data]\\n"
        "{data}\\n\\n"
        "[Instructions]\\n"
        "Propose changes to the actual data using the same JSON format as the example.\\n"
        "Do not output anything other than JSON.\\n\\n"
        "{action_definitions}\\n\\n"
        "{validation_points}\\n"
    ),
}


def main() -> int:
    data = json.loads(PATH.read_text(encoding="utf-8"))
    hits = 0
    for entry in data.get("strings", []):
        sid = entry.get("id")
        if sid in FIXES:
            old = entry.get("english", "")
            new = FIXES[sid]
            if old != new:
                entry["english"] = new
                hits += 1
                print(f"[FIX] {sid}: patched ({len(old)} -> {len(new)} chars)")
            else:
                print(f"[OK]  {sid}: already correct")
    if hits == 0:
        print("Nothing to fix.")
    PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Wrote {PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())