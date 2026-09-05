# statable_gui/transition_editor_direct/code_widget.py
"""
コード表示ウィジェット（読み取り専用、has_else対応、ロール関数個別生成対応）
"""

import logging

from PySide6.QtWidgets import QPlainTextEdit
from .draft import ActionDraft

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
        # システムグローバル定義
        for g in self.draft.system_globals:
            lines.append(f"{g.type} {g.name} = {g.initial_value};")
        if self.draft.system_globals:
            lines.append("")

        # 個別ロール関数のプロトタイプ宣言を収集
        proto_lines = []
        for item in self.draft.flow_items:
            if item.item_type == "function":
                func_name = self.draft.get_role_func_name(item.name, "FLOW")
                proto_lines.append(f"void {func_name}(SystemContext_t *ctx, const TransitionContext_t *transition);")
            elif item.item_type == "transition":
                for pre_action in item.params.get('pre_actions', []):
                    func_name = self.draft.get_role_func_name(pre_action, "PRE")
                    proto_lines.append(f"void {func_name}(SystemContext_t *ctx, const TransitionContext_t *transition);")
        if proto_lines:
            lines.extend(proto_lines)
            lines.append("")

        # メイン処理（状態遷移イベント処理）
        for item in self.draft.flow_items:
            if item.item_type == "function":
                func_name = self.draft.get_role_func_name(item.name, "FLOW")
                lines.append(f"{func_name}(ctx, transition);")
            elif item.item_type == "transition":
                cond = item.params.get('condition', '')
                target = item.params.get('target', '')
                pre = item.params.get('pre_actions', [])
                has_else = item.params.get('has_else', True)
                else_target = item.params.get('else_target', '')

                if cond:
                    lines.append(f"if ({cond}) {{")
                    for p in pre:
                        func_name = self.draft.get_role_func_name(p, "PRE")
                        lines.append(f"    {func_name}(ctx, transition);")
                    lines.append(f"    next_state = {target};")
                    lines.append("}")
                    if has_else:
                        lines.append("else {")
                        if else_target:
                            lines.append(f"    next_state = {else_target};")
                        else:
                            lines.append("    // else処理（未設定）")
                        lines.append("}")
                else:
                    # 条件なしの場合、既存コードでは直前処理を無視していたが、
                    # ロール関数共通化では必要に応じて実行すべきかもしれない。
                    # ここでは既存の挙動を維持（何もしない）
                    lines.append(f"next_state = {target};")
                    if has_else:
                        lines.append(f"// else: {else_target}" if else_target else "// else: 未設定")

        if self.draft.default_target:
            lines.append(f"// default: {self.draft.default_target}")

        # 個別ロール関数の定義
        if self.draft.role_func_map:
            lines.append("")
            lines.append("/* === ロール関数定義（ユーザー編集領域） === */")
            for key, func_name in sorted(self.draft.role_func_map.items()):
                # key は "source|event|phase|base_name"
                source, event, phase, base_name = key.split('|')
                lines.append(f"void {func_name}(SystemContext_t *ctx, const TransitionContext_t *transition) {{")
                user_code = self.draft.user_code.get(func_name, "")
                if user_code:
                    lines.append(f"    // === USER CODE BEGIN: {func_name} ===")
                    for code_line in user_code.strip().splitlines():
                        lines.append(f"    {code_line}")
                    lines.append(f"    // === USER CODE END: {func_name} ===")
                else:
                    lines.append("    // TODO: 実装してください")
                lines.append("}")
                lines.append("")

        return "\n".join(lines)