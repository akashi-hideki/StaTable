#!/usr/bin/env python3
"""patch_v3_6_0_comm_monitor_p5_gui_cli.py

Wire comm_monitor into GUI / CLI / gen_output_from_xml / CI.

Changes:
  - statable_gui/code_generation_settings_dialog.py: add checkbox + load/save
  - statable/cli.py: add --with-comm-monitor flag
  - tools/gen_output_from_xml.py: add --with-comm-monitor flag
  - codegen/config.py: persist comm_monitor in to_dict/from_dict
  - .github/workflows/check.yml: add comm_monitor generate+verify steps
"""
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parent.parent.parent
REPO = CODE.parent


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _write(p: Path, text: str) -> None:
    p.write_text(text, encoding="utf-8")


def patch_settings_dialog() -> None:
    p = CODE / "statable_gui" / "code_generation_settings_dialog.py"
    if not p.is_file():
        print(f"  [skip] not found: {p}")
        return
    text = _read(p)
    if "enable_comm_monitor_check" in text:
        print(f"  [skip] already patched: {p.name}")
        return

    # 1) UI insertion
    old_ui = (
        "        layout.addWidget(comment_group)\n"
        "        layout.addStretch()"
    )
    new_ui = (
        "        layout.addWidget(comment_group)\n"
        "\n"
        "        # Communication monitor settings\n"
        "        comm_monitor_group = QGroupBox(self.tr(\"Communication monitor\"))\n"
        "        comm_monitor_layout = QVBoxLayout(comm_monitor_group)\n"
        "        self.enable_comm_monitor_check = QCheckBox(\n"
        "            self.tr(\"Generate comm_monitor code (ASCII GET protocol)\"))\n"
        "        self.enable_comm_monitor_check.setToolTip(\n"
        "            self.tr(\"Generates statable_comm_*.c/h files.\\n\"\n"
        "                    \"UART ISR + TX hook must be wired in user code.\"))\n"
        "        comm_monitor_layout.addWidget(self.enable_comm_monitor_check)\n"
        "        layout.addWidget(comm_monitor_group)\n"
        "\n"
        "        layout.addStretch()"
    )
    if old_ui not in text:
        print(f"  [error] UI anchor not found in {p.name}")
        return
    text = text.replace(old_ui, new_ui, 1)

    # 2) Load
    old_load = "        self.enable_markers_check.setChecked(self.config.enable_user_markers)"
    new_load = (
        old_load + "\n"
        "\n"
        "        # Communication monitor\n"
        "        if getattr(self.config, 'comm_monitor', None) is not None:\n"
        "            self.enable_comm_monitor_check.setChecked(\n"
        "                self.config.comm_monitor.enabled)\n"
        "        else:\n"
        "            self.enable_comm_monitor_check.setChecked(False)"
    )
    if old_load not in text:
        print(f"  [error] _load_config anchor not found")
        return
    text = text.replace(old_load, new_load, 1)

    # 3) Save
    old_save = "        self.config.enable_user_markers = self.enable_markers_check.isChecked()"
    new_save = (
        old_save + "\n"
        "\n"
        "        # Communication monitor\n"
        "        from codegen.comm_monitor.config import CommMonitorConfig\n"
        "        if getattr(self.config, 'comm_monitor', None) is None:\n"
        "            self.config.comm_monitor = CommMonitorConfig()\n"
        "        self.config.comm_monitor.enabled = self.enable_comm_monitor_check.isChecked()"
    )
    if old_save not in text:
        print(f"  [error] _save_config anchor not found")
        return
    text = text.replace(old_save, new_save, 1)

    _write(p, text)
    print(f"  [patched] {p.name}")


def patch_config_py() -> None:
    p = CODE / "codegen" / "config.py"
    if not p.is_file():
        print(f"  [skip] not found: {p}")
        return
    text = _read(p)
    if "'comm_monitor':" in text:
        print(f"  [skip] already patched: {p.name}")
        return

    # 1) to_dict
    old_td = (
        "    def to_dict(self) -> Dict:\n"
        "        \"\"\"Convert to dictionary\"\"\"\n"
        "        return {"
    )
    new_td = (
        "    def to_dict(self) -> Dict:\n"
        "        \"\"\"Convert to dictionary\"\"\"\n"
        "        from dataclasses import asdict\n"
        "        return {\n"
        "            'comm_monitor': asdict(self.comm_monitor),"
    )
    if old_td not in text:
        print(f"  [error] to_dict anchor not found")
        return
    text = text.replace(old_td, new_td, 1)

    # 2) from_dict
    old_fd = (
        "        filtered = {k: v for k, v in data.items() if k in valid_keys}\n"
        "        return cls(**filtered)"
    )
    new_fd = (
        "        filtered = {k: v for k, v in data.items() if k in valid_keys}\n"
        "        if 'comm_monitor' in filtered and isinstance(filtered['comm_monitor'], dict):\n"
        "            from .comm_monitor.config import CommMonitorConfig\n"
        "            filtered['comm_monitor'] = CommMonitorConfig(**filtered['comm_monitor'])\n"
        "        return cls(**filtered)"
    )
    if old_fd not in text:
        print(f"  [error] from_dict anchor not found")
        return
    text = text.replace(old_fd, new_fd, 1)

    _write(p, text)
    print(f"  [patched] {p.name}")


def patch_cli_py() -> None:
    p = CODE / "statable" / "cli.py"
    if not p.is_file():
        print(f"  [skip] not found: {p}")
        return
    text = _read(p)
    if "--with-comm-monitor" in text:
        print(f"  [skip] already patched: {p.name}")
        return

    # 1) Args
    old_arg = (
        "    p_gen.add_argument(\"--format\", choices=[\"json\", \"text\"],\n"
        "                       default=\"json\")\n"
        "    p_gen.set_defaults(func=cmd_generate)"
    )
    new_arg = (
        "    p_gen.add_argument(\"--format\", choices=[\"json\", \"text\"],\n"
        "                       default=\"json\")\n"
        "    p_gen.add_argument(\n"
        "        \"--with-comm-monitor\", action=\"store_true\",\n"
        "        help=\"Enable comm_monitor code generation (statable_comm_*.c/h)\")\n"
        "    p_gen.set_defaults(func=cmd_generate)"
    )
    if old_arg not in text:
        print(f"  [error] cli args anchor not found")
        return
    text = text.replace(old_arg, new_arg, 1)

    # 2) Apply in cmd_generate
    old_cfg = (
        "    try:\n"
        "        cfg = _build_config(settings)\n"
        "    except Exception as e:\n"
        "        _err(f\"error: config setup failed: {e!r}\")\n"
        "        return 2\n"
    )
    new_cfg = old_cfg + (
        "\n"
        "    if getattr(args, \"with_comm_monitor\", False):\n"
        "        from codegen.comm_monitor.config import CommMonitorConfig\n"
        "        cfg.comm_monitor = CommMonitorConfig(enabled=True)\n"
    )
    if old_cfg not in text:
        print(f"  [error] cli cmd_generate anchor not found")
        return
    text = text.replace(old_cfg, new_cfg, 1)

    _write(p, text)
    print(f"  [patched] {p.name}")


def patch_gen_output() -> None:
    p = CODE / "tools" / "gen_output_from_xml.py"
    if not p.is_file():
        print(f"  [skip] not found: {p}")
        return
    text = _read(p)
    if "--with-comm-monitor" in text:
        print(f"  [skip] already patched: {p.name}")
        return

    # 1) Args
    old_arg = (
        "    ap.add_argument(\"--out\", default=\"output\",\n"
        "                    help=\"output directory (default: output)\")\n"
        "    args = ap.parse_args()"
    )
    new_arg = (
        "    ap.add_argument(\"--out\", default=\"output\",\n"
        "                    help=\"output directory (default: output)\")\n"
        "    ap.add_argument(\"--with-comm-monitor\", action=\"store_true\",\n"
        "                    help=\"Enable comm_monitor generation\")\n"
        "    args = ap.parse_args()"
    )
    if old_arg not in text:
        print(f"  [error] gen args anchor not found")
        return
    text = text.replace(old_arg, new_arg, 1)

    # 2) Apply to config
    old_cfg = (
        "    config = build_config(project_settings)\n"
        "    print(f\"  config: folder_structure=\""
    )
    new_cfg = (
        "    config = build_config(project_settings)\n"
        "    if args.with_comm_monitor:\n"
        "        from codegen.comm_monitor.config import CommMonitorConfig\n"
        "        config.comm_monitor = CommMonitorConfig(enabled=True)\n"
        "        print(\"  comm_monitor: ENABLED\")\n"
        "    print(f\"  config: folder_structure=\""
    )
    if old_cfg not in text:
        print(f"  [error] gen config anchor not found")
        return
    text = text.replace(old_cfg, new_cfg, 1)

    _write(p, text)
    print(f"  [patched] {p.name}")


def patch_check_yml() -> None:
    p = REPO / ".github" / "workflows" / "check.yml"
    if not p.is_file():
        print(f"  [skip] not found: {p}")
        return
    text = _read(p)
    if "output_cm" in text:
        print(f"  [skip] already patched: {p.name}")
        return

    old_block = (
        "      - name: Generate C code from test XML\n"
        "        run: |\n"
        "          python tools/gen_output_from_xml.py \\\n"
        "            --xml tests/data/v22_features_test3.xml \\\n"
        "            --out output\n"
        "\n"
        "      - name: Verify C syntax (gcc + arm, strict)\n"
        "        run: |\n"
        "          python tools/verify_c_syntax.py \\\n"
        "            --root output --compiler both --strict"
    )
    new_block = (
        "      - name: Generate C code from test XML\n"
        "        run: |\n"
        "          python tools/gen_output_from_xml.py \\\n"
        "            --xml tests/data/v22_features_test3.xml \\\n"
        "            --out output\n"
        "\n"
        "      - name: Generate C code (comm_monitor enabled)\n"
        "        run: |\n"
        "          python tools/gen_output_from_xml.py \\\n"
        "            --xml tests/data/v22_features_test3.xml \\\n"
        "            --out output_cm \\\n"
        "            --with-comm-monitor\n"
        "\n"
        "      - name: Verify C syntax (gcc + arm, strict)\n"
        "        run: |\n"
        "          python tools/verify_c_syntax.py \\\n"
        "            --root output --compiler both --strict\n"
        "\n"
        "      - name: Verify C syntax (comm_monitor, gcc + arm, strict)\n"
        "        run: |\n"
        "          python tools/verify_c_syntax.py \\\n"
        "            --root output_cm --compiler both --strict"
    )
    if old_block not in text:
        print(f"  [error] check.yml block anchor not found")
        return
    text = text.replace(old_block, new_block, 1)

    _write(p, text)
    print(f"  [patched] {p.name}")


def main() -> int:
    print("=== patch_v3_6_0_comm_monitor_p5_gui_cli ===")
    print(f"repo: {REPO}")
    try:
        patch_settings_dialog()
        patch_config_py()
        patch_cli_py()
        patch_gen_output()
        patch_check_yml()
    except Exception as e:
        print(f"[error] {e!r}", file=sys.stderr)
        return 1
    print("=== done ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())