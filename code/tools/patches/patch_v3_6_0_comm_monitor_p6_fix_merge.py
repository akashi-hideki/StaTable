#!/usr/bin/env python3
"""patch_v3_6_0_comm_monitor_p6_fix_merge.py

Fix: NameError 'state_machine' is not defined in generate_all_layers /
_generate_all_by_layer when comm_monitor is enabled.

Root cause:
  _merge_comm_monitor_files(self, generated_files, state_machine, global_defs)
  has an unused `state_machine` parameter, but generate_all_layers and
  _generate_all_by_layer pass an undefined local `state_machine`.

Fix:
  Drop the unused `state_machine` parameter from the signature and all
  3 call sites.

Idempotent: safe to re-run.
"""
import re
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parent.parent.parent
TARGET = CODE / "codegen" / "c_code_generator.py"


def main() -> int:
    print("=== patch_v3_6_0_comm_monitor_p6_fix_merge ===")
    if not TARGET.is_file():
        print(f"[error] not found: {TARGET}", file=sys.stderr)
        return 1

    text = TARGET.read_text(encoding="utf-8")

    # Idempotency marker
    if "def _merge_comm_monitor_files(self, generated_files, global_defs):" in text:
        print(f"  [skip] already patched: {TARGET.name}")
        return 0

    # 1) Signature: drop `state_machine` parameter (multi-line + single-line tolerant)
    sig_patterns = [
        # multi-line (current style)
        (r"def _merge_comm_monitor_files\(self,\s*generated_files,\s*\n\s*state_machine,\s*global_defs\):",
         "def _merge_comm_monitor_files(self, generated_files, global_defs):"),
        # single-line
        (r"def _merge_comm_monitor_files\(self,\s*generated_files,\s*state_machine,\s*global_defs\):",
         "def _merge_comm_monitor_files(self, generated_files, global_defs):"),
    ]
    sig_done = False
    for pat, rep in sig_patterns:
        new_text, n = re.subn(pat, rep, text, count=1)
        if n:
            text = new_text
            sig_done = True
            break
    if not sig_done:
        print("[error] signature pattern not found", file=sys.stderr)
        return 1
    print("  [patched] signature")

    # 2) Call sites: generated_files, state_machine, global_defs -> generated_files, global_defs
    call_pattern = re.compile(
        r"_merge_comm_monitor_files\(\s*generated_files,\s*state_machine,\s*global_defs\)"
    )
    text, n = call_pattern.subn(
        "_merge_comm_monitor_files(generated_files, global_defs)", text
    )
    if n == 0:
        print("[error] no call site matched", file=sys.stderr)
        return 1
    print(f"  [patched] {n} call site(s)")

    TARGET.write_text(text, encoding="utf-8")
    print("=== done ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())