# statable_gui/transition_editor_direct/code_widget.py
"""
コード表示ウィジェット（読み取り専用、ActionDraft対応）
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
        # システムグローバル定義（あれば）
        for g in self.draft.system_globals:
            lines.append(f"{g.type} {g.name} = {g.initial_value};")
        if self.draft.system_globals:
            lines.append("")

        # ロール関数プロトタイプ収集（重複を除去）
        proto_names = set()
        for item in self.draft.flow_items:
            if item.item_type == "transition":
                pre_actions = ensure_list(item.params.get('pre_actions', []))
                else_actions = ensure_list(item.params.get('else_actions', []))
                for p in pre_actions:
                    proto_names.add(p)
                for ea in else_actions:
                    proto_names.add(ea)
            elif item.item_type == "function":
                proto_names.add(item.name)

        if proto_names:
            # ソートして安定した順序で出力
            for name in sorted(proto_names):
                lines.append(f"void RoleFunc_{name}(SystemContext_t *ctx, const TransitionContext_t *transition);")
            lines.append("")

        # 本体
        for item in self.draft.flow_items:
            if item.item_type == "transition":
                cond = item.params.get('condition', '')
                target = item.params.get('target', '')
                if not target:
                    target = self.draft.default_target  # フォールバック
                pre_actions = ensure_list(item.params.get('pre_actions', []))
                else_actions = ensure_list(item.params.get('else_actions', []))
                has_else = item.params.get('has_else', True)
                else_target = item.params.get('else_target', '')
                if not else_target:
                    else_target = self.draft.default_target  # フォールバック

                if cond:
                    lines.append(f"if ({cond}) {{")
                    for p in pre_actions:
                        lines.append(f"    RoleFunc_{p}(ctx, transition);")
                    if target:
                        lines.append(f"    next_state = {target};")
                    else:
                        lines.append("    // 遷移先未設定")
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
                    if target:
                        lines.append(f"next_state = {target};")
                    else:
                        lines.append("// 遷移先未設定")
            elif item.item_type == "function":
                lines.append(f"RoleFunc_{item.name}(ctx, transition);")

        return "\n".join(lines)