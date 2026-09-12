# codegen/role_function_generator.py
"""
ロール関数生成モジュール（多層ステートマシン対応版・完全版）

生成するもの（state_machine 指定時）:
  1. TRANSITION_ID_NONE 定数
  2. 呼び出し元テーブル用 共通構造体 RoleFuncCallSiteEntry_<Layer>_t
  3. Transition_GetId プロトタイプ宣言（static）
  4. ロール関数ごとの呼び出し元テーブル call_sites_<Short>[]
  5. 各ロール関数の実装
     - transition のメンバー展開 (from_state, event)
     - transition_id ローカル変数（Transition_GetId 呼び出し）
     - ctx->data の各メンバーへのローカルポインタ展開
     - 戻り値用ローカル変数 (int ret = 0;)
     - ユーザーコードマーカー
  6. Transition_GetId 本体定義（ファイル末尾、static）
  7. ファイル末尾のユーザー追加領域

state_machine 未指定時:
  - 5. のみ（transition_id なし）+ 7.
"""

import sys
import os
import re
import logging
from string import Template
from typing import Dict, List, Iterable, Optional

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


# ======================================================================
# ヘルパー
# ======================================================================
def ensure_list(value) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        s = value.strip()
        return [s] if s else []
    if isinstance(value, list):
        return [str(x) for x in value if str(x).strip()]
    return [str(value)]


_C_KEYWORDS = {
    'auto', 'break', 'case', 'char', 'const', 'continue',
    'default', 'do', 'double', 'else', 'enum', 'extern',
    'float', 'for', 'goto', 'if', 'inline', 'int', 'long',
    'register', 'restrict', 'return', 'short', 'signed',
    'sizeof', 'static', 'struct', 'switch', 'typedef',
    'union', 'unsigned', 'void', 'volatile', 'while',
    'true', 'false', 'NULL',
}


class RoleFuncCallSite:
    """1つのロール関数呼び出しサイト（from_state × event）"""
    __slots__ = ('func_name', 'kind', 'from_state', 'event', 'target')

    def __init__(self, func_name, kind, from_state, event, target):
        self.func_name = func_name
        self.kind = kind
        self.from_state = from_state
        self.event = event
        self.target = target

    def key(self):
        return (self.from_state, self.event)

    def __repr__(self):
        return (f"CallSite({self.func_name!r}, {self.kind!r}, "
                f"{self.from_state}->{self.target})")


class RoleFunctionGenerator:
    """ロール関数生成クラス（多層ステートマシン対応）"""

    # ================================================================
    # 【テーブル①】宣言用テンプレート
    # ================================================================
    DECLARATION_TEMPLATES = {
        'comment_with_desc': Template(
            '/**\n'
            ' * @brief  ロール関数: $title\n'
            ' * @note   $description\n'
            ' * @param  transition  遷移コンテキスト（セル情報）\n'
            ' * @param  ctx         システムコンテキストポインタ\n'
            ' * @return 0: 成功, 0以外: エラー（条件判定にも使用可）\n'
            ' */\n'
        ),
        'comment_no_desc': Template(
            '/**\n'
            ' * @brief  ロール関数: $title\n'
            ' * @param  transition  遷移コンテキスト（セル情報）\n'
            ' * @param  ctx         システムコンテキストポインタ\n'
            ' * @return 0: 成功, 0以外: エラー（条件判定にも使用可）\n'
            ' */\n'
        ),
        'signature_open': Template('int $func_name(\n'),
        'signature_args': Template(
            '    const $context_type *transition,\n'
            '    SystemContext_t *ctx\n'
        ),
        'declaration_close': ');\n',
    }

    # ================================================================
    # 【テーブル②】実装用テンプレート
    # ================================================================
    IMPLEMENTATION_TEMPLATES = {
        'comment_with_desc': Template(
            '/**\n'
            ' * @brief  ロール関数: $title\n'
            ' * @note   $description\n'
            '$call_sites'
            ' */\n'
        ),
        'comment_no_desc': Template(
            '/**\n'
            ' * @brief  ロール関数: $title\n'
            '$call_sites'
            ' */\n'
        ),
        'signature_open': Template('int $func_name(\n'),
        'signature_args': Template(
            '    const $context_type *transition,\n'
            '    SystemContext_t *ctx\n'
        ),
        'body_open': ')\n{\n',
        'unused_ctx': '    (void)ctx;         /* 未使用引数の警告抑制 */\n',
        'blank': '\n',
        'local_transition_header': '    /* ===== transition のメンバー展開 ===== */\n',
        'local_transition_member': Template(
            '    const $c_type $member_name = transition->$member_name;\n'
        ),
        'local_transition_id_header': (
            '    /* ===== transition ID（call_sites 内のインデックス） ===== */\n'
        ),
        'local_transition_id_decl': Template(
            '    const uint16_t transition_id = Transition_GetId(\n'
            '        transition, $table_arg, $count_arg);\n'
        ),
        'local_data_header': '    /* ===== ctx->data へのローカルポインタ ===== */\n',
        'local_data_pointer': Template(
            '    $c_type *const $var_name = &ctx->data.$var_name;'
            '  /* $comment */\n'
        ),
        'local_data_array': Template(
            '    $c_type *const $var_name = ctx->data.$var_name;'
            '  /* $comment */\n'
        ),
        'local_ret_header': '    /* ===== 戻り値 ===== */\n',
        'local_ret_decl': '    int ret = 0;   /* ユーザーコード内で書き換え可 */\n',
        'todo_comment': Template('    /* $todo */\n'),
        'user_marker_start': Template(
            '    /* [[STABLE_USER_CODE_START:$marker_name]] */\n'
        ),
        'user_marker_hint': '    /* ユーザー実装コードをここに記述 */\n',
        'user_marker_end': Template(
            '    /* [[STABLE_USER_CODE_END:$marker_name]] */\n'
        ),
        'return_default': '    return ret;\n',
        'body_close': '}\n',
    }

    # ================================================================
    # 【テーブル③】TRANSITION_ID_NONE 定数
    # ================================================================
    NONE_DEFINE_TEMPLATES = {
        'section_comment': (
            '\n'
            '/* ============================================================== */\n'
            '/*  Transition ID 定数                                            */\n'
            '/* ============================================================== */\n'
        ),
        'define': '#define TRANSITION_ID_NONE   ((uint16_t)0xFFFF)\n',
    }

    # ================================================================
    # 【テーブル④】呼び出し元テーブル用 共通構造体
    # ================================================================
    ENTRY_STRUCT_TEMPLATES = {
        'section_comment': (
            '\n'
            '/* ============================================================== */\n'
            '/*  ロール関数 呼び出し元テーブル（共通構造体）                    */\n'
            '/*  {from_state, event} の組でセルを識別                          */\n'
            '/* ============================================================== */\n'
        ),
        'struct_typedef': Template(
            'typedef struct {\n'
            '    $state_type from_state;   /* 遷移元状態 */\n'
            '    $event_type event;        /* 発生イベント */\n'
            '} $entry_type;\n'
        ),
    }

    # ================================================================
    # 【テーブル⑤】Transition_GetId
    # ================================================================
    TRANSITION_ID_FUNC_TEMPLATES = {
        'prototype_comment': (
            '\n'
            '/* Transition_GetId 前方宣言（本体はファイル末尾） */\n'
        ),
        'prototype': Template(
            'static uint16_t Transition_GetId(\n'
            '    const $context_type *transition,\n'
            '    const $entry_type *table,\n'
            '    uint16_t table_size);\n'
        ),
        'definition_comment': Template(
            '\n\n'
            '/* ============================================================== */\n'
            '/*  Transition ID 変換（ファイル末尾）                            */\n'
            '/*  ロール関数ごとの call_sites テーブルを線形探索し、             */\n'
            '/*  一致したエントリのインデックスを返す。                        */\n'
            '/*  一致なし / table==NULL の場合は TRANSITION_ID_NONE を返す。   */\n'
            '/* ============================================================== */\n'
            '/**\n'
            ' * @brief  transition 情報を一意な ID に変換する\n'
            ' * @param  transition  遷移コンテキスト\n'
            ' * @param  table       呼び出し元テーブル（NULL 可）\n'
            ' * @param  table_size  テーブルの要素数\n'
            ' * @return テーブル内のインデックス（一致なしは TRANSITION_ID_NONE）\n'
            ' */\n'
        ),
        'definition': Template(
            'static uint16_t Transition_GetId(\n'
            '    const $context_type *transition,\n'
            '    const $entry_type *table,\n'
            '    uint16_t table_size)\n'
            '{\n'
            '    uint16_t i;\n'
            '\n'
            '    if (table == NULL) {\n'
            '        return TRANSITION_ID_NONE;\n'
            '    }\n'
            '\n'
            '    for (i = 0; i < table_size; i++) {\n'
            '        if (table[i].from_state == transition->from_state &&\n'
            '            table[i].event      == transition->event) {\n'
            '            return i;\n'
            '        }\n'
            '    }\n'
            '    return TRANSITION_ID_NONE;\n'
            '}\n'
        ),
    }

    # ================================================================
    # 【テーブル⑥】各関数の call_sites テーブル
    # ================================================================
    CALL_SITE_TABLE_TEMPLATES = {
        'table_header': Template(
            '\n/* --- $func_name の呼び出し元テーブル --- */\n'
        ),
        'table_open': Template(
            'static const $struct_type $table_name[] = {\n'
        ),
        'entry': Template(
            '    { $from_state, $event },\n'
        ),
        'table_close': '};\n',
        'count_macro': Template(
            '#define $count_macro \\\n'
            '    (sizeof($table_name) / sizeof($table_name[0]))\n'
        ),
    }

    # ================================================================
    # 【テーブル⑦】呼び出し元コメント
    # ================================================================
    CALL_SITES_COMMENT_TEMPLATES = {
        'header': ' *\n * @note   呼び出し元:\n',
        'line': Template(
            ' *         - [$kind]$kind_pad  $from_state$from_pad'
            ' -[$event]-> $target\n'
        ),
        'none': ' *\n * @note   呼び出し元: （なし）\n',
    }

    # ================================================================
    # 【テーブル⑧】ファイル末尾のユーザー追加領域
    # ================================================================
    TAIL_USER_SECTION_TEMPLATES = {
        'section_comment': (
            '\n\n'
            '/* ============================================================== */\n'
            '/*  ユーザー追加領域                                              */\n'
            '/*  ここに追加したコードは再生成時も保持されます                  */\n'
            '/* ============================================================== */\n'
        ),
        'marker_start': '/* [[STABLE_USER_CODE_TAIL_START]] */\n',
        'default_hint': '/* ユーザー追加コードをここに記述（ヘルパー関数など） */\n',
        'marker_end': '/* [[STABLE_USER_CODE_TAIL_END]] */\n',
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
        self.layer_name: str = ""

    def set_layer(self, layer_name: str):
        self.layer_name = layer_name

    def _log_debug(self, message, level='debug'):
        log_func = getattr(logger, level, logger.debug)
        log_func(message)

    # ================================================================
    # 名前生成
    # ================================================================
    def _generate_function_name(self, func) -> str:
        name = getattr(func, 'name', 'unnamed')
        pascal = self.naming.to_pascal_case(name)
        if self.layer_name:
            return f"RoleFunc_{self.layer_name}_{pascal}"
        return f"RoleFunc_{pascal}"

    def _get_marker_name(self, func) -> str:
        name = getattr(func, 'name', 'unnamed')
        pascal = self.naming.to_pascal_case(name)
        if self.layer_name:
            return f"{self.layer_name}_{pascal}"
        return pascal

    def _get_short_name(self, func) -> str:
        return self.naming.to_pascal_case(getattr(func, 'name', 'unnamed'))

    def _context_type(self) -> str:
        if self.layer_name:
            return f"TransitionContext_{self.layer_name}_t"
        return "TransitionContext_t"

    def _state_type(self) -> str:
        return f"STATE_{self.layer_name}_t" if self.layer_name else "STATE_t"

    def _event_type(self) -> str:
        return f"EVENT_{self.layer_name}_t" if self.layer_name else "EVENT_t"

    def _state_enum(self, state_name: str) -> str:
        s = self.naming.to_pascal_case(state_name) if state_name else "Unknown"
        return f"STATE_{self.layer_name}_{s}" if self.layer_name else f"STATE_{s}"

    def _event_enum(self, event_name: str) -> str:
        e = self.naming.to_upper_snake(event_name) if event_name else "NONE"
        return f"EVENT_{self.layer_name}_{e}" if self.layer_name else f"EVENT_{e}"

    def _entry_struct_type(self) -> str:
        return f"RoleFuncCallSiteEntry_{self.layer_name}_t" if self.layer_name \
            else "RoleFuncCallSiteEntry_t"

    # ================================================================
    # 重複除去
    # ================================================================
    def _dedupe_by_name(self, funcs: Iterable) -> List:
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

    def _resolve_comment_title(self, func) -> str:
        title = getattr(func, 'title', '')
        name = getattr(func, 'name', 'unnamed')
        if title and title != f"ロール関数: {name}":
            return title
        return name

    # ================================================================
    # 呼び出しサイト収集
    # ================================================================
    def _normalize_func_ref(self, ref: str) -> str:
        if not ref:
            return ""
        name = ref
        if name.startswith("RoleFunc_"):
            name = name[len("RoleFunc_"):]
        if self.layer_name and name.startswith(f"{self.layer_name}_"):
            name = name[len(self.layer_name) + 1:]
        return name

    def _extract_func_names_from_condition(self, condition: str) -> List[str]:
        if not condition:
            return []
        names = set()
        for m in re.finditer(r'\bRoleFunc_\w+', condition):
            names.add(m.group(0))
        for m in re.finditer(r'\b([A-Za-z_][A-Za-z0-9_]*)\s*\(', condition):
            n = m.group(1)
            if n not in _C_KEYWORDS:
                names.add(n)
        stripped = condition.strip()
        if re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', stripped):
            if stripped not in _C_KEYWORDS:
                names.add(stripped)
        return [self._normalize_func_ref(n) for n in names if n]

    def _collect_call_sites(self, state_machine) -> Dict[str, List[RoleFuncCallSite]]:
        if state_machine is None:
            return {}
        call_map: Dict[str, List[RoleFuncCallSite]] = {}
        seen = set()

        for state in state_machine.states.values():
            for event in state_machine.events.values():
                transitions = state_machine.get_transitions_for_cell(
                    state.name, event.name
                )
                for trans in transitions:
                    target = getattr(trans, 'target', '') or ''
                    cond = getattr(trans, 'condition', '') or ''
                    for fname in self._extract_func_names_from_condition(cond):
                        key = (fname, 'condition', state.name, event.name)
                        if key in seen:
                            continue
                        seen.add(key)
                        call_map.setdefault(fname, []).append(RoleFuncCallSite(
                            fname, 'condition', state.name, event.name, target,
                        ))
                    for action in ensure_list(getattr(trans, 'pre_actions', [])):
                        norm = self._normalize_func_ref(action)
                        if not norm:
                            continue
                        key = (norm, 'pre_action', state.name, event.name)
                        if key in seen:
                            continue
                        seen.add(key)
                        call_map.setdefault(norm, []).append(RoleFuncCallSite(
                            norm, 'pre_action', state.name, event.name, target,
                        ))
                    else_target = getattr(trans, 'else_target', '') or ''
                    for action in ensure_list(getattr(trans, 'else_actions', [])):
                        norm = self._normalize_func_ref(action)
                        if not norm:
                            continue
                        key = (norm, 'else_action', state.name, event.name)
                        if key in seen:
                            continue
                        seen.add(key)
                        call_map.setdefault(norm, []).append(RoleFuncCallSite(
                            norm, 'else_action', state.name, event.name,
                            else_target or target,
                        ))

        self._log_debug(
            f"_collect_call_sites: {len(call_map)} funcs, "
            f"{sum(len(v) for v in call_map.values())} call sites"
        )
        return call_map

    def _format_call_sites_comment(self, call_sites) -> str:
        T = self.CALL_SITES_COMMENT_TEMPLATES
        if not call_sites:
            return T['none']
        kind_width = max(len(cs.kind) for cs in call_sites)
        from_width = max(len(self._state_enum(cs.from_state)) for cs in call_sites)
        event_width = max(len(self._event_enum(cs.event)) for cs in call_sites)
        parts = [T['header']]
        for cs in call_sites:
            from_str = self._state_enum(cs.from_state)
            event_str = self._event_enum(cs.event)
            target_str = self._state_enum(cs.target) if cs.target else '(未設定)'
            parts.append(T['line'].substitute(
                kind=cs.kind,
                kind_pad=' ' * (kind_width - len(cs.kind)),
                from_state=from_str,
                from_pad=' ' * (from_width - len(from_str)),
                event=event_str,
                target=target_str,
            ))
        return ''.join(parts)

    # ================================================================
    # TRANSITION_ID_NONE 定数
    # ================================================================
    def generate_none_define(self) -> str:
        T = self.NONE_DEFINE_TEMPLATES
        return T['section_comment'] + T['define']

    # ================================================================
    # 共通構造体
    # ================================================================
    def generate_entry_struct(self) -> str:
        T = self.ENTRY_STRUCT_TEMPLATES
        return (
            T['section_comment'] +
            T['struct_typedef'].substitute(
                state_type=self._state_type(),
                event_type=self._event_type(),
                entry_type=self._entry_struct_type(),
            )
        )

    # ================================================================
    # Transition_GetId プロトタイプ
    # ================================================================
    def generate_transition_id_prototype(self) -> str:
        T = self.TRANSITION_ID_FUNC_TEMPLATES
        return (
            T['prototype_comment'] +
            T['prototype'].substitute(
                context_type=self._context_type(),
                entry_type=self._entry_struct_type(),
            )
        )

    # ================================================================
    # Transition_GetId 本体
    # ================================================================
    def generate_transition_id_function(self) -> str:
        T = self.TRANSITION_ID_FUNC_TEMPLATES
        return (
            T['definition_comment'] +
            T['definition'].substitute(
                context_type=self._context_type(),
                entry_type=self._entry_struct_type(),
            )
        )

    # ================================================================
    # 各関数の call_sites テーブル
    # ================================================================
    def generate_call_sites_table(self, func, call_sites) -> str:
        if not call_sites:
            return ""

        short = self._get_short_name(func)
        table_name = f"call_sites_{short}"
        count_macro = f"CALL_SITES_{short}_COUNT"

        T = self.CALL_SITE_TABLE_TEMPLATES
        parts = [
            T['table_header'].substitute(func_name=short),
            T['table_open'].substitute(
                struct_type=self._entry_struct_type(),
                table_name=table_name,
            ),
        ]

        seen = set()
        for cs in call_sites:
            k = cs.key()
            if k in seen:
                continue
            seen.add(k)
            parts.append(T['entry'].substitute(
                from_state=self._state_enum(cs.from_state),
                event=self._event_enum(cs.event),
            ))

        parts.append(T['table_close'])
        parts.append(T['count_macro'].substitute(
            count_macro=count_macro,
            table_name=table_name,
        ))
        return ''.join(parts)

    # ================================================================
    # ファイル末尾ユーザー領域
    # ================================================================
    def generate_tail_user_section(self) -> str:
        T = self.TAIL_USER_SECTION_TEMPLATES
        return ''.join([
            T['section_comment'],
            T['marker_start'],
            T['default_hint'],
            T['marker_end'],
        ])

    # ================================================================
    # ローカル変数展開
    # ================================================================
    def _format_var_comment(self, var) -> str:
        description = getattr(var, 'description', '') or ''
        unit = getattr(var, 'unit', '') or ''
        if description and unit:
            return f"{description} [{unit}]"
        return description or unit or ""

    def _generate_local_transition_members(self) -> str:
        T = self.IMPLEMENTATION_TEMPLATES
        return ''.join([
            T['local_transition_header'],
            T['local_transition_member'].substitute(
                c_type=self._state_type(), member_name='from_state',
            ),
            T['local_transition_member'].substitute(
                c_type=self._event_type(), member_name='event',
            ),
            T['blank'],
        ])

    def _generate_local_transition_id(self, func, has_call_sites: bool) -> str:
        T = self.IMPLEMENTATION_TEMPLATES
        if has_call_sites:
            short = self._get_short_name(func)
            table_arg = f"call_sites_{short}"
            count_arg = f"(uint16_t)CALL_SITES_{short}_COUNT"
        else:
            table_arg = "NULL"
            count_arg = "0"

        return ''.join([
            T['local_transition_id_header'],
            T['local_transition_id_decl'].substitute(
                table_arg=table_arg,
                count_arg=count_arg,
            ),
            T['blank'],
        ])

    def _generate_local_data_pointers(self, global_defs) -> str:
        if global_defs is None:
            return ""
        variables = getattr(global_defs, 'variables', []) or []
        if not variables:
            return ""
        T = self.IMPLEMENTATION_TEMPLATES
        parts = [T['local_data_header']]
        for var in variables:
            var_name = self.naming.sanitize_identifier(
                getattr(var, 'name', 'unnamed')
            )
            c_type = self.mapper.map_type(getattr(var, 'type', 'void'))
            comment = self._format_var_comment(var)
            array_size = getattr(var, 'array_size', 0)
            if array_size > 0:
                parts.append(T['local_data_array'].substitute(
                    c_type=c_type, var_name=var_name, comment=comment,
                ))
            else:
                parts.append(T['local_data_pointer'].substitute(
                    c_type=c_type, var_name=var_name, comment=comment,
                ))
        parts.append(T['blank'])
        return ''.join(parts)

    def _has_local_data_pointers(self, global_defs) -> bool:
        if global_defs is None:
            return False
        return bool(getattr(global_defs, 'variables', []) or [])

    def _generate_local_retvar(self) -> str:
        T = self.IMPLEMENTATION_TEMPLATES
        return ''.join([
            T['local_ret_header'],
            T['local_ret_decl'],
            T['blank'],
        ])

    # ================================================================
    # 宣言生成
    # ================================================================
    def generate_declaration(self, func) -> str:
        T = self.DECLARATION_TEMPLATES
        parts = []
        title = self._resolve_comment_title(func)
        description = getattr(func, 'description', '')
        if description:
            parts.append(T['comment_with_desc'].substitute(
                title=title, description=description,
            ))
        else:
            parts.append(T['comment_no_desc'].substitute(title=title))
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
    def generate_implementation(self, func, global_defs=None,
                                call_sites=None,
                                include_transition_id: bool = True) -> str:
        T = self.IMPLEMENTATION_TEMPLATES
        parts = []

        title = self._resolve_comment_title(func)
        description = getattr(func, 'description', '')
        call_sites_comment = self._format_call_sites_comment(call_sites or [])

        if description:
            parts.append(T['comment_with_desc'].substitute(
                title=title, description=description,
                call_sites=call_sites_comment,
            ))
        else:
            parts.append(T['comment_no_desc'].substitute(
                title=title, call_sites=call_sites_comment,
            ))

        parts.append(T['signature_open'].substitute(
            func_name=self._generate_function_name(func),
        ))
        parts.append(T['signature_args'].substitute(
            context_type=self._context_type(),
        ))
        parts.append(T['body_open'])

        parts.append(self._generate_local_transition_members())

        if include_transition_id:
            has_cs = bool(call_sites)
            parts.append(self._generate_local_transition_id(func, has_cs))

        if self._has_local_data_pointers(global_defs):
            parts.append(self._generate_local_data_pointers(global_defs))
        else:
            parts.append(T['unused_ctx'])

        parts.append(self._generate_local_retvar())

        parts.append(T['todo_comment'].substitute(todo=self.strings['todo']))
        parts.append(T['blank'])

        marker_name = self._get_marker_name(func)
        parts.append(T['user_marker_start'].substitute(marker_name=marker_name))
        parts.append(T['user_marker_hint'])
        parts.append(T['user_marker_end'].substitute(marker_name=marker_name))
        parts.append(T['blank'])

        parts.append(T['return_default'])
        parts.append(T['body_close'])
        return ''.join(parts)

    # ================================================================
    # 呼び出し生成
    # ================================================================
    def generate_call(self, func_name: str) -> str:
        if func_name.startswith("RoleFunc_"):
            full_name = func_name
        elif self.layer_name:
            full_name = (f"RoleFunc_{self.layer_name}_"
                         f"{self.naming.to_pascal_case(func_name)}")
        else:
            full_name = f"RoleFunc_{self.naming.to_pascal_case(func_name)}"
        return f"{full_name}(transition, ctx)"

    # ================================================================
    # 一括生成
    # ================================================================
    def generate_all_declarations(self, role_functions: List) -> str:
        unique_funcs = self._dedupe_by_name(role_functions)
        parts = []
        for func in unique_funcs:
            parts.append(self.generate_declaration(func))
            parts.append('\n')
        return ''.join(parts)

    def generate_all_implementations(self, role_functions: List,
                                     state_machine=None,
                                     global_defs=None) -> str:
        """
        全ロール関数の実装を生成

        生成順（state_machine 指定時）:
          1. TRANSITION_ID_NONE 定数
          2. 呼び出し元テーブル用 共通構造体
          3. Transition_GetId プロトタイプ宣言
          4. 各関数の call_sites テーブル（name 順）
          5. 各ロール関数の実装（name 順）
          6. Transition_GetId 本体定義（ファイル末尾、static）
          7. ファイル末尾のユーザー追加領域
        """
        unique_funcs = self._dedupe_by_name(role_functions)
        include_transition_id = state_machine is not None
        call_map = self._collect_call_sites(state_machine) \
            if include_transition_id else {}

        parts = []

        if include_transition_id:
            parts.append(self.generate_none_define())
            parts.append('\n')
            parts.append(self.generate_entry_struct())
            parts.append('\n')
            parts.append(self.generate_transition_id_prototype())
            parts.append('\n')

            for func in unique_funcs:
                func_name = getattr(func, 'name', '')
                call_sites = call_map.get(func_name, [])
                table_code = self.generate_call_sites_table(func, call_sites)
                if table_code:
                    parts.append(table_code)
                    parts.append('\n')

            parts.append('\n')

        for func in unique_funcs:
            func_name = getattr(func, 'name', '')
            call_sites = call_map.get(func_name, [])
            parts.append(self.generate_implementation(
                func, global_defs, call_sites, include_transition_id,
            ))
            parts.append('\n')

        if include_transition_id:
            parts.append(self.generate_transition_id_function())

        parts.append(self.generate_tail_user_section())

        return ''.join(parts)

    # ================================================================
    # 後方互換
    # ================================================================
    def _collect_args(self, func) -> List[tuple]:
        return [
            (
                'transition',
                f'const TransitionContext_{self.layer_name}_t *'
                if self.layer_name else 'const TransitionContext_t *',
                '遷移コンテキスト',
            ),
            ('ctx', 'SystemContext_t *', 'システムコンテキストポインタ'),
        ]