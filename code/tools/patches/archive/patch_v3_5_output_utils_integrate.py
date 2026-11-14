"""patch_v3_5_output_utils_integrate.py

v3.5.0: integrate statable.output_utils into __init__ and codegen.
"""
from __future__ import annotations
from pathlib import Path

HERE = Path(__file__).resolve()
ROOT = HERE.parents[2]

INIT = ROOT / "statable" / "__init__.py"
CG = ROOT / "codegen" / "c_code_generator.py"


def _must_replace(text, old, new, label):
    if old not in text:
        raise SystemExit(f"[FAIL] marker not found: {label}")
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"[FAIL] marker not unique ({n}): {label}")
    return text.replace(old, new, 1)


def patch_init():
    text = INIT.read_text(encoding="utf-8")
    imp_old = (
        "# state_machine.py (depends on model)\n"
        "from .state_machine import StateMachine\n"
        "\n"
        "# global_defs.py (no dependencies)\n"
    )
    imp_new = (
        "# state_machine.py (depends on model)\n"
        "from .state_machine import StateMachine\n"
        "\n"
        "# output_utils.py (v3.5.0, stdlib os only)\n"
        "from .output_utils import find_orphan_files\n"
        "\n"
        "# global_defs.py (no dependencies)\n"
    )
    text = _must_replace(text, imp_old, imp_new, "init import")
    all_old = (
        "    # state_machine\n"
        "    'StateMachine',\n"
        "    # global_defs\n"
    )
    all_new = (
        "    # state_machine\n"
        "    'StateMachine',\n"
        "    # output_utils (v3.5.0)\n"
        "    'find_orphan_files',\n"
        "    # global_defs\n"
    )
    text = _must_replace(text, all_old, all_new, "init __all__")
    INIT.write_text(text, encoding="utf-8")
    print(f"[OK] patched {INIT}")


def patch_codegen():
    text = CG.read_text(encoding="utf-8")
    imp_old = (
        "from statable.state_machine import StateMachine\n"
        "from statable.global_defs import GlobalDefinitions\n"
    )
    imp_new = (
        "from statable.state_machine import StateMachine\n"
        "from statable.global_defs import GlobalDefinitions\n"
        "from statable.output_utils import find_orphan_files\n"
    )
    text = _must_replace(text, imp_old, imp_new, "cg import")
    init_old = (
        "        self.templates = CodeTemplates()\n"
        "        self.strings = self.templates.STRINGS\n"
    )
    init_new = (
        "        self.templates = CodeTemplates()\n"
        "        self.strings = self.templates.STRINGS\n"
        "        # [v3.5.0] Orphan (stale) files left over from a\n"
        "        # previous generation in output_dir.  Populated\n"
        "        # by save_generated_code(); read by GUI/CLI to\n"
        "        # warn the user before a build fails.\n"
        "        self.last_orphans: List[str] = []\n"
    )
    text = _must_replace(text, init_old, init_new, "cg __init__")
    sv_old = (
        "            with open(filepath, 'w', encoding='utf-8') as f:\n"
        "                f.write(content)\n"
        "            saved_files.append(filepath)\n"
        "        return saved_files\n"
    )
    sv_new = (
        "            with open(filepath, 'w', encoding='utf-8') as f:\n"
        "                f.write(content)\n"
        "            saved_files.append(filepath)\n"
        "        # [v3.5.0] Record stale files for the caller.\n"
        "        self.last_orphans = find_orphan_files(\n"
        "            output_dir, saved_files)\n"
        "        if self.last_orphans:\n"
        "            logger.warning(\n"
        "                '%d stale file(s) left in %s',\n"
        "                len(self.last_orphans), output_dir)\n"
        "        return saved_files\n"
    )
    text = _must_replace(text, sv_old, sv_new, "cg save")
    CG.write_text(text, encoding="utf-8")
    print(f"[OK] patched {CG}")


def main():
    patch_init()
    patch_codegen()
    print("[DONE]")


if __name__ == "__main__":
    main()
