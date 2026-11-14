"""show_type_defs.py"""
import re
from pathlib import Path

FILES = [
    ("codegen/validate/data/action_definitions.py",
     ["ACTION_DEFINITIONS"]),
    ("codegen/validate/response_parser.py",
     ["markers", "self.markers"]),
    ("codegen/validate/response_validator.py",
     ["action_definitions", "self.action_definitions"]),
    ("codegen/validate/prompt_generator.py",
     ["action_definitions", "self.action_definitions"]),
    ("codegen/variable_generator.py",
     ["INIT_FUNCTION_STEPS", "step_executors", "self.step_executors"]),
]

for path, names in FILES:
    print(f"\n===== {path} =====")
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    for i, l in enumerate(lines):
        for name in names:
            # assignment or annotation
            if re.search(rf"\b{re.escape(name)}\b\s*[:=]", l):
                print(f"  {i+1:5d}: {l}")
                break
