# codegen/role_function_generator.py
"""
ロール関数生成モジュール（多層ステートマシン対応版）

生成するもの:
  1. ロール関数の宣言
  2. ロール関数の実装

新シグネチャ:
    int RoleFunc_<Layer>_<Name>(
        const TransitionContext_<Layer>_t *transition,
        SystemContext_t *ctx
    )

設計方針:
  - 文字列リテラルは string.Template によるデータテーブルに集約
  - 層名は set_layer() で設定
  - ユーザーコードマーカーは層名込み（code_merger.py の抽出パターンと一致）
  - 同名ロール関数は name 属性で一意化（挿入順を保持）
"""

import sys
import os
import logging
from string import Template
from typing import Dict, List, Iterable

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

    # ================================================================
    # 【データテーブル①】宣言用テンプレート
    # ================================================================
    DECLARATION_TEMPLATES = {
        # --- コメントブロック（説明あり） ---
        'comment_with_desc': Template(
            '/**\n'
            ' * @brief  ロール関数: $title\n'
            ' * @note   $description\n'
            ' * @param  transition  遷移コンテキスト（セル情報）\n'
            ' * @param  ctx         システムコンテキストポインタ\n'
            ' * @return 0: 成功, 0以外: エラー（条件判定にも使用可）\n'
            ' */\n'
        ),

        # --- コメントブロック（説明なし） ---
        'comment_no_desc': Template(
            '/**\n'
            ' * @brief  ロール関数: $title\n'
            ' * @param  transition  遷移コンテキスト（セル情報）\n'
            ' * @param  ctx         システムコンテキストポインタ\n'
            ' * @return 0: 成功, 0以外: エラー（条件判定にも使用可）\n'
            ' */\n'
        ),

        # --- シグネチャ開始 ---
        'signature_open': Template(
            'int $func_name(\n'
        ),

        # --- 引数ブロック ---
        'signature_args': Template(
            '    const $context_type *transition,\n'
            '    SystemContext_t *ctx\n'
        ),

        # --- 宣言終了 ---
        'declaration_close': ');\n',
    }

    # ================================================================
    # 【データテーブル②】実装用テンプレート
    # ================================================================
    IMPLEMENTATION_TEMPLATES = {
        # --- コメントブロック（説明あり） ---
        'comment_with_desc': Template(
            '/**\n'
            ' * @brief  ロール関数: $title\n'
            ' * @note   $description\n'
            ' */\n'
        ),

        # --- コメントブロック（説明なし） ---
        'comment_no_desc': Template(
            '/**\n'
            ' * @brief  ロール関数: $title\n'
            ' */\n'
        ),

        # --- シグネチャ開始 ---
        'signature_open': Template(
            'int $func_name(\n'
        ),

        # --- 引数ブロック ---
        'signature_args': Template(
            '    const $context_type *transition,\n'
            '    SystemContext_t *ctx\n'
        ),

        # --- 本体開始 ---
        'body_open': (
            ')\n'
            '{\n'
        ),

        # --- 未使用引数の警告抑制 ---
        'unused_args': (
            '    (void)transition;  /* 未使用引数の警告抑制 */\n'
            '    (void)ctx;         /* 未使用引数の警告抑制 */\n'
        ),

        # --- TODO コメント ---
        'todo_comment': Template(
            '    /* $todo */\n'
        ),

        # --- 空行 ---
        'blank': '\n',

        # --- ユーザーコードマーカー開始 ---
        'user_marker_start': Template(
            '    /* [[STABLE_USER_CODE_START:$marker_name]] */\n'
        ),

        # --- ユーザーコード案内コメント ---
        'user_marker_hint': (
            '    /* ユーザー実装コードをここに記述 */\n'
        ),

        # --- ユーザーコードマーカー終了 ---
        'user_marker_end': Template(
            '    /* [[STABLE_USER_CODE_END:$marker_name]] */\n'
        ),

        # --- 戻り値 ---
        'return_default': (
            '    return 0;  /* デフォルト値: 0 = 成功 */\n'
        ),

        # --- 本体終了 ---
        'body_close': '}\n',
    }

    # ================================================================
    # コンストラクタ
    # ================================================================
    def __init__(self):
        self.mapper = CTypeMapper()
        self.naming = CNamingConvention()
        self.templates = CodeTemplates()
        self.strings = self.templates.STRINGS
        self.formats = self.templates.FORMATS
        self.merger = CodeMerger()

        # 層名（set_layer で設定）
        self.layer_name: str = ""

    def set_layer(self, layer_name: str):
        """層名を設定"""
        self.layer_name = layer_name

    def _log_debug(self, message, level='debug'):
        log_func = getattr(logger, level, logger.debug)
        log_func(message)

    # ================================================================
    # 名前生成
    # ================================================================
    def _generate_function_name(self, func) -> str:
        """RoleFunc_<Layer>_<Name>"""
        name = getattr(func, 'name', 'unnamed')
        pascal = self.naming.to_pascal_case(name)
        if self.layer_name:
            return f"RoleFunc_{self.layer_name}_{pascal}"
        return f"RoleFunc_{pascal}"

    def _get_marker_name(self, func) -> str:
        """
        マーカー用の名前: <Layer>_<Name>（層名なしの場合は <Name>）

        注意: code_merger.py の抽出パターン
              r'RoleFunc_(\\w+)\\s*\\(' で "Driver_CheckSensor" が取れる形式に
              一致させること。
        """
        name = getattr(func, 'name', 'unnamed')
        pascal = self.naming.to_pascal_case(name)
        if self.layer_name:
            return f"{self.layer_name}_{pascal}"
        return pascal

    def _context_type(self) -> str:
        """遷移コンテキスト型名"""
        if self.layer_name:
            return f"TransitionContext_{self.layer_name}_t"
        return "TransitionContext_t"

    # ================================================================
    # 重複除去
    # ================================================================
    def _dedupe_by_name(self, funcs: Iterable) -> List:
        """RoleFunction のリストを name 属性で一意化（挿入順を保持）"""
        seen = set()
        result = []
        for func in funcs:
            name = getattr(func, 'name', None)
            if not name:
                self._log_debug(
                    f"_dedupe_by_name: skip (no name): {func!r}", 'warning'
                )
                continue
            if name in seen:
                self._log_debug(f"_dedupe_by_name: duplicate skipped: {name}")
                continue
            seen.add(name)
            result.append(func)
        return result

    # ================================================================
    # コメントタイトル決定
    # ================================================================
    def _resolve_comment_title(self, func) -> str:
        """@brief に出すタイトルを決定"""
        title = getattr(func, 'title', '')
        name = getattr(func, 'name', 'unnamed')
        if title and title != f"ロール関数: {name}":
            return title
        return name

    # ================================================================
    # 宣言生成
    # ================================================================
    def generate_declaration(self, func) -> str:
        """ロール関数の宣言を生成"""
        self._log_debug(f"Generating declaration: {getattr(func, 'name', 'unknown')}")

        T = self.DECLARATION_TEMPLATES
        parts = []

        # --- コメント ---
        title = self._resolve_comment_title(func)
        description = getattr(func, 'description', '')

        if description:
            parts.append(T['comment_with_desc'].substitute(
                title=title, description=description,
            ))
        else:
            parts.append(T['comment_no_desc'].substitute(title=title))

        # --- シグネチャ ---
        parts.append(T['signature_open'].substitute(
            func_name=self._generate_function_name(func),
        ))
        parts.append(T['signature_args'].substitute(
            context_type=self._context_type(),
        ))
        parts.append(T['declaration_close'])

        return ''.join(parts)

    # ================================================================
    # 実装生成
    # ================================================================
    def generate_implementation(self, func) -> str:
        """ロール関数の実装を生成"""
        self._log_debug(f"Generating implementation: {getattr(func, 'name', 'unknown')}")

        T = self.IMPLEMENTATION_TEMPLATES
        parts = []

        # --- コメント ---
        title = self._resolve_comment_title(func)
        description = getattr(func, 'description', '')

        if description:
            parts.append(T['comment_with_desc'].substitute(
                title=title, description=description,
            ))
        else:
            parts.append(T['comment_no_desc'].substitute(title=title))

        # --- シグネチャ ---
        parts.append(T['signature_open'].substitute(
            func_name=self._generate_function_name(func),
        ))
        parts.append(T['signature_args'].substitute(
            context_type=self._context_type(),
        ))
        parts.append(T['body_open'])

        # --- 未使用引数の警告抑制 ---
        parts.append(T['unused_args'])

        # --- TODO コメント ---
        parts.append(T['todo_comment'].substitute(todo=self.strings['todo']))

        # --- 空行 ---
        parts.append(T['blank'])

        # --- ユーザーコードマーカー ---
        marker_name = self._get_marker_name(func)
        parts.append(T['user_marker_start'].substitute(marker_name=marker_name))
        parts.append(T['user_marker_hint'])
        parts.append(T['user_marker_end'].substitute(marker_name=marker_name))

        # --- 空行 ---
        parts.append(T['blank'])

        # --- 戻り値 + 終了 ---
        parts.append(T['return_default'])
        parts.append(T['body_close'])

        return ''.join(parts)

    # ================================================================
    # 呼び出し生成
    # ================================================================
    def generate_call(self, func_name: str) -> str:
        """ロール関数の呼び出しを生成: RoleFunc_<Layer>_<Name>(transition, ctx)"""
        if func_name.startswith("RoleFunc_"):
            full_name = func_name
        elif self.layer_name:
            full_name = f"RoleFunc_{self.layer_name}_{self.naming.to_pascal_case(func_name)}"
        else:
            full_name = f"RoleFunc_{self.naming.to_pascal_case(func_name)}"
        return f"{full_name}(transition, ctx)"

    # ================================================================
    # 一括生成
    # ================================================================
    def generate_all_declarations(self, role_functions: List) -> str:
        """全ロール関数の宣言を生成（name で一意化）"""
        unique_funcs = self._dedupe_by_name(role_functions)
        self._log_debug(
            f"generate_all_declarations: {len(role_functions)} raw → "
            f"{len(unique_funcs)} unique"
        )

        parts = []
        for func in unique_funcs:
            parts.append(self.generate_declaration(func))
            parts.append('\n')
        return ''.join(parts)

    def generate_all_implementations(self, role_functions: List) -> str:
        """全ロール関数の実装を生成（name で一意化）"""
        unique_funcs = self._dedupe_by_name(role_functions)
        self._log_debug(
            f"generate_all_implementations: {len(role_functions)} raw → "
            f"{len(unique_funcs)} unique"
        )

        parts = []
        for func in unique_funcs:
            parts.append(self.generate_implementation(func))
            parts.append('\n')
        return ''.join(parts)

    # ================================================================
    # 後方互換
    # ================================================================
    def _collect_args(self, func) -> List[tuple]:
        """後方互換: 引数情報を返す"""
        return [
            (
                'transition',
                f'const TransitionContext_{self.layer_name}_t *'
                if self.layer_name else 'const TransitionContext_t *',
                '遷移コンテキスト',
            ),
            ('ctx', 'SystemContext_t *', 'システムコンテキストポインタ'),
        ]