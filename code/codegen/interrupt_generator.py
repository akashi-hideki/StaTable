# codegen/interrupt_generator.py
"""
割り込み処理ISR生成モジュール（H3: ISR コンテキスト対応版）

機能:
  1. ctx ポインタの自動挿入（SystemContext_t *ctx = &g_ctx;）
  2. アクションの Namespace.Name → RoleFunc_<NS>_<Name>(NULL, ctx) 変換
  3. 旧形式 identifier(args) → RoleFunc_<Layer>_<Pascal>(NULL, ctx) 変換
  4. ユーザーマーカー [[STABLE_USER_CODE_START:<Marker>]]
  5. used_role_functions / used_variables の自動抽出
  6. 入場・退場ログ

マーカー命名規則:
  handler.name = "TIMER0"  → ISR_TIMER0  / Marker "TIMER0"
  handler.name = "UART_RX" → ISR_UARTRX  / Marker "UARTRX"
"""

import sys
import os
import re
import logging
from typing import Dict, Callable, List, Any, Optional, Tuple

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from statable.global_defs import (
    InterruptHandlerDef, InterruptAction, GlobalDefinitions,
)

try:
    from .naming_convention import CNamingConvention
    from .code_templates import CodeTemplates
except ImportError:
    from naming_convention import CNamingConvention
    from code_templates import CodeTemplates

logger = logging.getLogger(__name__)


# C 予約語（関数呼び出し形式で誤変換しないよう除外）
_C_KEYWORDS = {
    'if', 'else', 'for', 'while', 'do', 'switch', 'case',
    'default', 'break', 'continue', 'return', 'goto',
    'sizeof', 'typedef', 'struct', 'union', 'enum',
    'static', 'const', 'volatile', 'extern', 'inline',
    'void', 'int', 'char', 'short', 'long', 'float', 'double',
    'signed', 'unsigned', 'bool', 'true', 'false', 'NULL',
}


class InterruptGenerator:
    """割り込み処理ISR生成クラス（H3: コンテキスト対応）"""

    # ================================================================
    # クラス定数
    # ================================================================
    AUTO_INSERT_CTX = True
    CTX_VAR_NAME = 'ctx'
    G_CTX_NAME = 'g_ctx'

    def __init__(self):
        self.naming = CNamingConvention()
        self.templates = CodeTemplates()
        self.strings = self.templates.STRINGS
        self.formats = self.templates.FORMATS
        self.layer_name: str = ''

        # ============================================================
        # 生成ステップ
        # ============================================================
        self.isr_steps = [
            {'action': 'comment'},
            {'action': 'signature'},
            {'action': 'open'},
            {'action': 'context'},
            {'action': 'enter_log'},
            {'action': 'actions'},
            {'action': 'user_section'},
            {'action': 'exit_log'},
            {'action': 'close'},
        ]

        self.step_executors: Dict[str, Callable] = {
            'comment':      self._execute_comment_step,
            'signature':    self._execute_signature_step,
            'open':         self._execute_open_step,
            'context':      self._execute_context_step,
            'enter_log':    self._execute_enter_log_step,
            'actions':      self._execute_actions_step,
            'user_section': self._execute_user_section_step,
            'exit_log':     self._execute_exit_log_step,
            'close':        self._execute_close_step,
        }

    def set_layer(self, layer_name: str):
        """層名を設定（旧形式 identifier(args) の RoleFunc 名生成に使用）"""
        self.layer_name = layer_name or ''

    def _log_debug(self, message, level='debug'):
        log_func = getattr(logger, level, logger.debug)
        log_func(message)

    # ================================================================
    # 名前生成
    # ================================================================
    def _get_isr_function_name(self, handler) -> str:
        """ISR_<PascalCase(handler.name)>"""
        name = getattr(handler, 'name', '') or 'unnamed'
        return f"ISR_{self.naming.to_pascal_case(name)}"

    def _get_marker_name(self, handler) -> str:
        """PascalCase(handler.name)"""
        name = getattr(handler, 'name', '') or 'unnamed'
        return self.naming.to_pascal_case(name)

    def _get_handler_display_name(self, handler) -> str:
        """ログ用表示名（元の名前そのまま）"""
        return getattr(handler, 'name', '') or 'unnamed'

    # ================================================================
    # アクション パース
    # ================================================================
    def _parse_action(self, action_text: str) -> Tuple[str, List[str]]:
        """
        アクション文字列を C コードに変換

        Args:
            action_text: 入力アクション文字列

        Returns:
            (c_code, used_role_functions)

        変換規則:
          1. Namespace.Name [(args)] → RoleFunc_Namespace_Name(NULL, ctx)
          2. identifier(args)          → RoleFunc_<Layer>_PascalId(NULL, ctx)
          3. それ以外                  → そのまま
        """
        if not action_text:
            return "", []
        text = action_text.strip()
        if not text:
            return "", []

        used: List[str] = []

        # --- 1. Namespace.Name 形式 ---
        m = re.fullmatch(
            r'([A-Z]\w*)\.([A-Za-z_]\w*)\s*(\(.*\))?',
            text, re.DOTALL,
        )
        if m:
            ns = m.group(1)
            name = m.group(2)
            pascal = self.naming.to_pascal_case(name)
            qualified = f"{ns}.{name}"
            used.append(qualified)
            return f"RoleFunc_{ns}_{pascal}(NULL, ctx)", used

        # --- 2. 関数呼び出し形式 ---
        m = re.fullmatch(
            r'([A-Za-z_]\w*)\s*(\(.*\))',
            text, re.DOTALL,
        )
        if m:
            fname = m.group(1)
            # 既に RoleFunc_ / ISR_ で始まるものはそのまま
            if fname.startswith('RoleFunc_') or fname.startswith('ISR_'):
                return text, used
            # C キーワードはそのまま
            if fname in _C_KEYWORDS:
                return text, used
            # RoleFunc 名に変換（引数は破棄）
            pascal = self.naming.to_pascal_case(fname)
            if self.layer_name:
                call = f"RoleFunc_{self.layer_name}_{pascal}(NULL, ctx)"
                qualified = f"{self.layer_name}.{pascal}"
            else:
                call = f"RoleFunc_{pascal}(NULL, ctx)"
                qualified = pascal
            used.append(qualified)
            return call, used

        # --- 3. そのまま ---
        return text, used

    def _parse_action_with_semicolon(
        self, action: InterruptAction,
    ) -> Tuple[str, List[str]]:
        """condition 付きアクションを 1 行の C コードに変換"""
        body, used = self._parse_action(getattr(action, 'action', ''))
        if not body:
            return "", used
        # 末尾セミコロンを正規化
        body = body.rstrip(';').rstrip()
        condition = (getattr(action, 'condition', '') or '').strip()
        if condition:
            return f"if ({condition}) {{ {body}; }}", used
        return f"{body};", used

    # ================================================================
    # 使用シンボル抽出
    # ================================================================
    def extract_used_symbols(
        self, handler: InterruptHandlerDef,
    ) -> Tuple[List[str], List[str]]:
        """
        handler から使用ロール関数と使用変数を抽出

        Returns:
            (used_role_functions, used_variables)
            used_role_functions: ["Driver.Init", "Application.HandleTick"]
            used_variables:      ["counter", "EVT_START"]
        """
        used_rfs: List[str] = []
        used_vars: List[str] = []
        seen_rf = set()
        seen_var = set()

        for action in getattr(handler, 'actions', []):
            text = getattr(action, 'action', '') or ''
            _, rfs = self._parse_action(text)
            for r in rfs:
                if r and r not in seen_rf:
                    seen_rf.add(r)
                    used_rfs.append(r)

            # ctx->data.X / ctx->flags.X
            for m in re.finditer(
                r'ctx->(?:data|flags)\.([A-Za-z_]\w*)', text,
            ):
                v = m.group(1)
                if v and v not in seen_var:
                    seen_var.add(v)
                    used_vars.append(v)

        return used_rfs, used_vars

    def update_handler_symbols(self, handler: InterruptHandlerDef):
        """handler の used_role_functions / used_variables を再計算して書き戻す"""
        used_rfs, used_vars = self.extract_used_symbols(handler)
        handler.used_role_functions = used_rfs
        handler.used_variables = used_vars

    # ================================================================
    # ステップ実行
    # ================================================================
    def _execute_comment_step(self, step, context):
        handler = context['handler']
        display = self._get_handler_display_name(handler)
        used_rfs = context.get('used_role_functions', [])
        description = getattr(handler, 'description', '') or ''

        lines = [
            "/**",
            f" * @brief  {display} 割り込みハンドラ",
        ]
        if description:
            lines.append(f" * @note   {description}")
        if used_rfs:
            lines.append(" * @note   使用ロール関数:")
            for r in used_rfs:
                lines.append(f" *         - {r}")
        lines.append(" */")
        return lines

    def _execute_signature_step(self, step, context):
        handler = context['handler']
        func_name = self._get_isr_function_name(handler)
        return [f"void {func_name}(void)"]

    def _execute_open_step(self, step, context):
        return ["{"]

    def _execute_context_step(self, step, context):
        if not self.AUTO_INSERT_CTX:
            return []
        return [
            "",
            "    /* ===== コンテキスト参照（自動生成） ===== */",
            f"    SystemContext_t *{self.CTX_VAR_NAME} = &{self.G_CTX_NAME};",
            f"    (void){self.CTX_VAR_NAME};",
        ]

    def _execute_enter_log_step(self, step, context):
        handler = context['handler']
        display = self._get_handler_display_name(handler)
        return [
            "",
            "    /* ===== 入場ログ ===== */",
            f'    LOG_DEBUG("Enter ISR: {display}");',
        ]

    def _execute_actions_step(self, step, context):
        handler = context['handler']
        actions = getattr(handler, 'actions', []) or []
        if not actions:
            return []

        lines = [
            "",
            "    /* ===== アクション（自動生成） ===== */",
        ]
        has_action = False
        for action in actions:
            body, _ = self._parse_action_with_semicolon(action)
            if body:
                lines.append(f"    {body}")
                has_action = True
        if not has_action:
            lines.append("    /* （アクション未定義） */")
        return lines

    def _execute_user_section_step(self, step, context):
        handler = context['handler']
        marker = self._get_marker_name(handler)
        return [
            "",
            "    /* ===== ユーザー追加領域 ===== */",
            f"    /* [[STABLE_USER_CODE_START:{marker}]] */",
            "    /* ユーザー追加コードをここに記述 */",
            f"    /* [[STABLE_USER_CODE_END:{marker}]] */",
        ]

    def _execute_exit_log_step(self, step, context):
        handler = context['handler']
        display = self._get_handler_display_name(handler)
        return [
            "",
            "    /* ===== 退場ログ ===== */",
            f'    LOG_DEBUG("Exit ISR: {display}");',
        ]

    def _execute_close_step(self, step, context):
        return ["}"]

    # ================================================================
    # 公開 API
    # ================================================================
    def generate_isr(
        self, handler: InterruptHandlerDef,
        update_handler: bool = False,
    ) -> str:
        """
        ISR 生成

        Args:
            handler: 割り込みハンドラ定義
            update_handler: True なら used_* を handler に書き戻す
        """
        self._log_debug(f"Generating ISR for: {handler.name}")

        used_rfs, used_vars = self.extract_used_symbols(handler)

        if update_handler:
            handler.used_role_functions = used_rfs
            handler.used_variables = used_vars

        context = {
            'handler': handler,
            'used_role_functions': used_rfs,
            'used_variables': used_vars,
        }
        lines: List[str] = []
        for step in self.isr_steps:
            executor = self.step_executors.get(step['action'])
            if executor is None:
                continue
            result = executor(step, context)
            if result:
                lines.extend(result)
        return '\n'.join(lines)

    def generate_all_isrs(
        self, global_defs: GlobalDefinitions,
        update_handlers: bool = False,
    ) -> str:
        """全 ISR 生成"""
        lines: List[str] = []
        for handler in getattr(global_defs, 'interrupts', []):
            lines.append(self.generate_isr(
                handler, update_handler=update_handlers,
            ))
            lines.append("")
            lines.append("")
        return '\n'.join(lines).rstrip() + '\n'