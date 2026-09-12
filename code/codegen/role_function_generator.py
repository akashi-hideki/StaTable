# codegen/role_function_generator.py
"""
ロール関数生成モジュール（多層ステートマシン対応版）
新シグネチャ: int RoleFunc_<Layer>_<Name>(
    const TransitionContext_<Layer>_t *transition,
    SystemContext_t *ctx
)
"""

import sys
import os
import logging
from typing import Dict, Callable, List, Any, Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from statable.model import RoleFunction

try:
    from .type_mapper import CTypeMapper
    from .naming_convention import CNamingConvention
    from .code_templates import CodeTemplates
    from .code_merger import CodeMerger
except ImportError:
    from type_mapper import CTypeMapper
    from naming_convention import CNamingConvention
    from code_templates import CodeTemplates
    from code_merger import CodeMerger

logger = logging.getLogger(__name__)


class RoleFunctionGenerator:
    """ロール関数生成クラス（多層ステートマシン対応）"""
    
    def __init__(self):
        self.mapper = CTypeMapper()
        self.naming = CNamingConvention()
        self.templates = CodeTemplates()
        self.strings = self.templates.STRINGS
        self.formats = self.templates.FORMATS
        self.merger = CodeMerger()
        
        # ★ 層名（コンストラクタ引数 or set_layer で設定）
        self.layer_name: str = ""
    
    def set_layer(self, layer_name: str):
        """層名を設定"""
        self.layer_name = layer_name
    
    def _log_debug(self, message, level='debug'):
        log_func = getattr(logger, level, logger.debug)
        log_func(message)
    
    # ===== ★ 関数名生成（層名付き） =====
    def _generate_function_name(self, func) -> str:
        """
        ロール関数名: RoleFunc_<Layer>_<Name>
        例: RoleFunc_Driver_CheckSensor
        """
        name = getattr(func, 'name', 'unnamed')
        pascal_name = self.naming.to_pascal_case(name)
        
        if self.layer_name:
            return f"RoleFunc_{self.layer_name}_{pascal_name}"
        return f"RoleFunc_{pascal_name}"
    
    def _get_short_func_name(self, func) -> str:
        """層名を含まない短縮名（マーカー用）"""
        name = getattr(func, 'name', 'unnamed')
        return self.naming.to_pascal_case(name)
    
    # ===== ★ 引数（固定: transition, ctx） =====
    def _generate_args_str(self, indent: str = None) -> str:
        """
        固定引数を生成:
            const TransitionContext_<Layer>_t *transition,
            SystemContext_t *ctx
        """
        if indent is None:
            indent = self.strings['indent_1']
        
        if self.layer_name:
            context_type = f"TransitionContext_{self.layer_name}_t"
        else:
            context_type = "TransitionContext_t"
        
        return (
            f"{indent}const {context_type} *transition,\n"
            f"{indent}SystemContext_t *ctx"
        )
    
    # ===== ★ 宣言生成 =====
    def generate_declaration(self, func) -> str:
        """ロール関数の宣言を生成"""
        self._log_debug(f"Generating declaration: {getattr(func, 'name', 'unknown')}")
        
        func_name = self._generate_function_name(func)
        lines = []
        
        # コメント
        lines.append("/**")
        title = getattr(func, 'title', '')
        name = getattr(func, 'name', 'unnamed')
        if title and title != f"ロール関数: {name}":
            lines.append(f" * @brief  ロール関数: {title}")
        else:
            lines.append(f" * @brief  ロール関数: {name}")
        if getattr(func, 'description', ''):
            lines.append(f" * @note   {func.description}")
        lines.append(f" * @param  transition  遷移コンテキスト（セル情報）")
        lines.append(f" * @param  ctx         システムコンテキストポインタ")
        lines.append(f" * @return 0: 成功, 0以外: エラー（条件判定にも使用可）")
        lines.append(" */")
        
        # シグネチャ
        lines.append(f"int {func_name}(")
        lines.append(self._generate_args_str())
        lines.append(");")
        
        return '\n'.join(lines)
    
    # ===== ★ 実装生成 =====
    def generate_implementation(self, func) -> str:
        """ロール関数の実装を生成"""
        self._log_debug(f"Generating implementation: {getattr(func, 'name', 'unknown')}")
        
        func_name = self._generate_function_name(func)
        short_name = self._get_short_func_name(func)
        lines = []
        
        # コメント
        lines.append("/**")
        title = getattr(func, 'title', '')
        name = getattr(func, 'name', 'unnamed')
        if title and title != f"ロール関数: {name}":
            lines.append(f" * @brief  ロール関数: {title}")
        else:
            lines.append(f" * @brief  ロール関数: {name}")
        
        if getattr(func, 'description', ''):
            lines.append(f" * @note   {func.description}")
        lines.append(" */")
        
        # シグネチャ + ボディ開始
        lines.append(f"int {func_name}(")
        lines.append(self._generate_args_str())
        lines.append(")")
        lines.append("{")
        lines.append("    (void)transition;  /* 未使用引数の警告抑制 */")
        lines.append("    (void)ctx;         /* 未使用引数の警告抑制 */")
        lines.append(f"    /* {self.strings['todo']} */")
        lines.append("")
        
        # ユーザーコードマーカー
        start = self.merger.markers['func_user_start'].format(func_name=short_name)
        end = self.merger.markers['func_user_end'].format(func_name=short_name)
        lines.append(f"    {start}")
        lines.append(f"    /* ユーザー実装コードをここに記述 */")
        lines.append(f"    {end}")
        lines.append("")
        
        # 戻り値
        lines.append("    return 0;  /* デフォルト値: 0 = 成功 */")
        lines.append("}")
        
        return '\n'.join(lines)
    
    # ===== ★ 呼び出し生成（セル単位関数から使用） =====
    def generate_call(self, func_name: str) -> str:
        """
        ロール関数の呼び出しを生成:
            RoleFunc_<Layer>_<Name>(transition, ctx)
        """
        # func_name が既に完全名か短縮名か判定
        if func_name.startswith("RoleFunc_"):
            full_name = func_name
        elif self.layer_name:
            full_name = f"RoleFunc_{self.layer_name}_{self.naming.to_pascal_case(func_name)}"
        else:
            full_name = f"RoleFunc_{self.naming.to_pascal_case(func_name)}"
        
        return f"{full_name}(transition, ctx)"
    
    # ===== ★ 一括生成 =====
    def generate_all_declarations(self, role_functions: List) -> str:
        """全ロール関数の宣言を生成"""
        lines = []
        for func in role_functions:
            lines.append(self.generate_declaration(func))
            lines.append("")
        return '\n'.join(lines)
    
    def generate_all_implementations(self, role_functions: List) -> str:
        """全ロール関数の実装を生成"""
        lines = []
        for func in role_functions:
            lines.append(self.generate_implementation(func))
            lines.append("")
        return '\n'.join(lines)
    
    # ===== 後方互換: 明示的な型引数を持つ場合 =====
    def _collect_args(self, func) -> List[tuple]:
        """
        カスタム引数がある場合はそれを返す（後方互換）
        ※ 新シグネチャでは使われない
        """
        args = [
            ('transition', f'const TransitionContext_{self.layer_name}_t *' if self.layer_name else 'const TransitionContext_t *', '遷移コンテキスト'),
            ('ctx', 'SystemContext_t *', 'システムコンテキストポインタ'),
        ]
        return args