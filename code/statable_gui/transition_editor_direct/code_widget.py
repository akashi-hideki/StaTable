# statable_gui/transition_editor_direct/code_widget.py
"""
コード表示ウィジェット（デバッグログ強化版・型安全化）
"""

import logging

from PySide6.QtWidgets import QPlainTextEdit
from .draft import ActionDraft, ensure_list

logger = logging.getLogger("transition_editor_direct.code")


class CodeWidget(QPlainTextEdit):
    def __init__(self, draft: ActionDraft, parent=None):
        super().__init__(parent)
        self.draft = draft
        self.setReadOnly(True)
        self.update_code()

    def update_code(self):
        code = self._generate_code()
        self.draft.generated_code = code
        self.setPlainText(code)
        logger.debug(f"Code updated ({len(code)} chars)")

    def _generate_code(self) -> str:
        lines = []
        # システムグローバル
        for g in self.draft.system_globals:
            lines.append(f"{g.type} {g.name} = {g.initial_value};")
        if self.draft.system_globals:
            lines.append("")

        # プロトタイプ収集
        proto_lines = []
        for idx, item in enumerate(self.draft.flow_items):
            if item.item_type == "transition":
                pre_actions = ensure_list(item.params.get('pre_actions', []))
                else_actions = ensure_list(item.params.get('else_actions', []))
                logger.debug(f"CodeGen flow_item[{idx}]: condition='{item.params.get('condition','')}', pre_actions={pre_actions}, else_actions={else_actions}")
                for p in pre_actions:
                    proto_lines.append(f"void RoleFunc_{p}(SystemContext_t *ctx, const TransitionContext_t *transition);")
                for ea in else_actions:
                    proto_lines.append(f"void RoleFunc_{ea}(SystemContext_t *ctx, const TransitionContext_t *transition);")
            elif item.item_type == "function":
                func_name = item.name
                proto_lines.append(f"void RoleFunc_{func_name}(SystemContext_t *ctx, const TransitionContext_t *transition);")
        if proto_lines:
            lines.extend(proto_lines)
            lines.append("")

        # 本体
        for idx, item in enumerate(self.draft.flow_items):
            if item.item_type == "transition":
                cond = item.params.get('condition', '')
                target = item.params.get('target', '')
                pre_actions = ensure_list(item.params.get('pre_actions', []))
                else_actions = ensure_list(item.params.get('else_actions', []))
                has_else = item.params.get('has_else', True)
                else_target = item.params.get('else_target', '')

                if cond:
                    lines.append(f"if ({cond}) {{")
                    for p in pre_actions:
                        lines.append(f"    RoleFunc_{p}(ctx, transition);")
                    lines.append(f"    next_state = {target};")
                    lines.append("}")
                    if has_else:
                        lines.append("else {")
                        for ea in else_actions:
                            lines.append(f"    RoleFunc_{ea}(ctx, transition);")
                        if else_target:
                            lines.append(f"    next_state = {else_target};")
                        else:
                            lines.append("    // else遷移先（未設定）")
                        lines.append("}")
                else:
                    lines.append(f"next_state = {target};")
            elif item.item_type == "function":
                lines.append(f"RoleFunc_{item.name}(ctx, transition);")

        if self.draft.default_target:
            lines.append(f"// default: {self.draft.default_target}")

        # 関数定義（将来対応用に role_func_map を出力しない）
        return "\n".join(lines)