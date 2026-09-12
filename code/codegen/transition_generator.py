# codegen/transition_generator.py
"""
状態遷移関数生成モジュール（多層ステートマシン対応版）

生成物:
  1. セル単位の遷移関数（static、短縮名 t_<State>_<Event>）
     - 前方宣言（プロトタイプ）
     - 実装本体
  2. 遷移テーブル（グローバル const、extern 宣言付き）
  3. 関数ディクショナリ（デバッグ・リフレクション用）
  4. StateMachine_Process_<Layer>() 関数
  5. StateMachine_GetNextEvent_<Layer>() 関数

設計方針:
  - 遷移テーブルは外部から参照可能（グローバル）
  - セル関数は static（内部実装詳細）
  - セル関数は前方宣言してから、テーブル・実装を出力（順序非依存）
  - テーブルは行=状態、列=イベントの横並び仕様書形式
"""

import sys
import os
import logging
from string import Template
from typing import Dict, List

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from statable.model import State, Event, Transition
from statable.state_machine import StateMachine

try:
    from .type_mapper import CTypeMapper
    from .naming_convention import CNamingConvention
    from .code_templates import CodeTemplates
except ImportError:
    from type_mapper import CTypeMapper
    from naming_convention import CNamingConvention
    from code_templates import CodeTemplates

logger = logging.getLogger(__name__)


# ======================================================================
# ヘルパー
# ======================================================================
def ensure_list(value) -> List[str]:
    """文字列/None/リストを List[str] に正規化"""
    if value is None:
        return []
    if isinstance(value, str):
        s = value.strip()
        return [s] if s else []
    if isinstance(value, list):
        return [str(x) for x in value if str(x).strip()]
    return [str(value)]


class TransitionGenerator:
    """状態遷移関数生成クラス（多層ステートマシン対応）"""

    # セル関数の短縮名を使うか（static のため推奨 True）
    SHORT_CELL_NAMES = True

    # 遷移テーブルの最小列幅
    TABLE_MIN_COL_WIDTH = 14

    # デフォルト設定値
    DEFAULT_TABLE_TYPE = 'array'
    DEFAULT_GENERATION_STYLE = 'table_driven'

    # ==================================================================
    # テンプレート群（変更なし）
    # ==================================================================
    CELL_TEMPLATES = {
        # --- ヘッダーコメント ---
        'header': Template(
            '/**\n'
            ' * @brief  セル遷移: $state_enum -[$event_enum]-> $target\n'
            ' */\n'
        ),

        # --- 関数シグネチャ ---
        'signature': Template(
            'static $state_type $func_name(\n'
            '    const $context_type *transition,\n'
            '    SystemContext_t *ctx\n'
            ')\n'
            '{\n'
        ),

        # --- 状態変数初期化 ---
        'body_open': Template(
            '    $state_type next_state = transition->from_state;\n'
        ),

        # --- 条件付き遷移ブロック ---
        'cond_block': Template(
            '\n'
            '    /* 遷移[$idx] */\n'
            '    if ($condition) {\n'
            '$pre_actions'
            '        next_state = $target_enum;\n'
            '        return next_state;\n'
            '    }\n'
        ),

        # --- 条件なし遷移ブロック ---
        'cond_block_empty': Template(
            '\n'
            '    /* 遷移[$idx] (条件なし遷移) */\n'
            '    if (1) {\n'
            '$pre_actions'
            '        next_state = $target_enum;\n'
            '        return next_state;\n'
            '    }\n'
        ),

        # --- pre_action 呼び出し行 ---
        'pre_action_line': Template(
            '        $call;\n'
        ),

        # --- else 節ヘッダー ---
        'else_header': (
            '\n'
            '    /* ==== else 節 ==== */\n'
        ),

        # --- else_action 呼び出し行 ---
        'else_action_line': Template(
            '    $call;\n'
        ),

        # --- else 遷移先 ---
        'else_target': Template(
            '    next_state = $target_enum;\n'
        ),

        # --- else 遷移先未設定 ---
        'else_target_unset': (
            '    /* else遷移先未設定 */\n'
        ),

        # --- 関数本体終了 ---
        'body_close': (
            '\n'
            '    return next_state;\n'
            '}\n'
        ),
    }

    # ==================================================================
    # 【データテーブル①-b】セル関数の前方宣言
    # ==================================================================
    CELL_PROTO_TEMPLATES = {
        # --- セクションコメント ---
        'section_comment': '/* ===== セル単位遷移関数の前方宣言 ===== */\n',

        # --- プロトタイプ本体 ---
        'prototype': Template(
            'static $state_type $func_name(\n'
            '    const $context_type *transition,\n'
            '    SystemContext_t *ctx);\n'
        ),
    }

    # ==================================================================
    # 【データテーブル②】遷移テーブル（グローバル + 横並び）
    # ==================================================================
    TABLE_TEMPLATES = {
        # --- 関数ポインタ型 ---
        'func_ptr_comment': '/* 遷移関数ポインタ型 */\n',
        'func_ptr_typedef': Template(
            'typedef $state_type (*$func_type)(\n'
            '    const $context_type *, SystemContext_t *);\n'
        ),

        # --- テーブル説明コメント ---
        'table_comment': Template(
            '\n'
            '/* ============================================================== */\n'
            '/*  状態遷移テーブル: 行=$row_desc, 列=$col_desc                  */\n'
            '/*  グローバル変数（外部から参照可能）                            */\n'
            '/* ============================================================== */\n'
        ),

        # --- テーブル本体（static なし = グローバル） ---
        'table_open': Template(
            'const $func_type $table_name\n'
            '    [$state_max][$event_max] = {\n'
        ),

        # --- テーブル終了 ---
        'table_close': '};\n',
    }

    # ==================================================================
    # 【データテーブル③】ヘッダ用の extern 宣言
    # ==================================================================
    TABLE_HEADER_TEMPLATES = {
        # --- ヘッダコメント ---
        'header_comment': Template(
            '/**\n'
            ' * @brief  遷移テーブル（$layer層）\n'
            ' * @note   行=$row_desc, 列=$col_desc\n'
            ' */\n'
        ),

        # --- 関数ポインタ型 ---
        'func_ptr_typedef': Template(
            'typedef $state_type (*$func_type)(\n'
            '    const $context_type *, SystemContext_t *);\n'
        ),

        # --- extern 宣言 ---
        'extern_decl': Template(
            'extern const $func_type $table_name\n'
            '    [$state_max][$event_max];\n'
        ),
    }

    # ==================================================================
    # 【データテーブル④】関数ディクショナリ
    # ==================================================================
    DICT_TEMPLATES = {
        # --- エントリ構造体コメント ---
        'struct_comment': (
            '/* 遷移関数ディクショナリ用エントリ */\n'
            '/* デバッグ・ログ出力・動的ディスパッチに使用 */\n'
        ),

        # --- エントリ構造体開始 ---
        'struct_open': (
            'typedef struct {\n'
            '    const char *name;                    /* 遷移名 */\n'
        ),

        # --- メンバ: 遷移元状態 ---
        'struct_field_from': Template(
            '    $state_type from_state;              /* 遷移元状態 */\n'
        ),

        # --- メンバ: 発生イベント ---
        'struct_field_event': Template(
            '    $event_type event;                   /* 発生イベント */\n'
        ),

        # --- メンバ: 代表遷移先 ---
        'struct_field_target': Template(
            '    $state_type default_target;          /* 代表遷移先 */\n'
        ),

        # --- メンバ: 条件式 ---
        'struct_field_condition': (
            '    const char *condition;               /* 条件式（文字列） */\n'
        ),

        # --- メンバ: 遷移関数ポインタ ---
        'struct_field_func': Template(
            '    $func_type func;                     /* 遷移関数ポインタ */\n'
        ),

        # --- エントリ構造体終了 ---
        'struct_close': Template('}} $dict_type;\n'),


        # --- ディクショナリコメント --
        'dict_comment': '\n/* 遷移関数ディクショナリ */\n',
        # --- ディクショナリ開始 ---
        'dict_open': Template(
            'static const $dict_type $dict_name[] = {\n'
        ),

        # --- ディクショナリエントリ ---
        'dict_entry': Template(
            '    { "$trans_name",\n'
            '      $state_enum, $event_enum, $target_enum,\n'
            '      "$condition", $func_name },\n'
        ),

        # --- ディクショナリ終了 ---
        'dict_close': '};\n',

        # --- サイズマクロ ---
        'dict_size': Template(
            '\n'
            '#define $size_macro \\\n'
            '    (sizeof($dict_name) / sizeof($dict_name[0]))\n'
        ),
    }

    # ==================================================================
    # 【データテーブル⑤】StateMachine_Process_<Layer>
    # ==================================================================
    PROCESS_TEMPLATES = {
        # --- コメント ---
        'comment': Template(
            '/**\n'
            ' * @brief  $layer層の状態遷移処理\n'
            ' * @param  current_state  現在の状態\n'
            ' * @param  event          発生したイベント\n'
            ' * @param  ctx            システムコンテキストポインタ\n'
            ' * @return 遷移後の状態\n'
            ' */\n'
        ),

        # --- シグネチャ ---
        'signature': Template(
            '$state_type $func_name(\n'
            '    $state_type current_state,\n'
            '    $event_type event,\n'
            '    SystemContext_t *ctx\n'
            ')\n'
        ),

        # --- 本体 ---
        'body': Template(
            '{\n'
            '    $context_type transition = {\n'
            '        .from_state = current_state,\n'
            '        .event = event,\n'
            '    };\n'
            '    $func_type func = $table_name[current_state][event];\n'
            '    if (func != NULL) {\n'
            '        return func(&transition, ctx);\n'
            '    }\n'
            '    return current_state;\n'
            '}\n'
        ),
    }

    # ==================================================================
    # 【データテーブル⑥】StateMachine_GetNextEvent_<Layer>
    # ==================================================================
    GET_NEXT_TEMPLATES = {
        # --- コメント ---
        'comment': Template(
            '/**\n'
            ' * @brief  $layer層の次のイベントを取得\n'
            ' * @param  ctx  システムコンテキストポインタ\n'
            ' * @return 次のイベント（保留なしの場合は $event_none）\n'
            ' */\n'
        ),

        # --- シグネチャ ---
        'signature': Template(
            '$event_type $func_name(SystemContext_t *ctx)\n'
        ),

        # --- 本体 ---
        'body': Template(
            '{\n'
            '    static uint8_t consecutive_count = 0;\n'
            '\n'
            '    if (ctx->pending_event_valid) {\n'
            '        consecutive_count++;\n'
            '        if (consecutive_count > MAX_CONSECUTIVE_PENDING_EVENTS) {\n'
            '            LOG_ERROR("Pending event chain too long (%d)", consecutive_count);\n'
            '            ctx->pending_event_valid = false;\n'
            '            consecutive_count = 0;\n'
            '            return $event_none;\n'
            '        }\n'
            '        $event_type evt = ($event_type)ctx->pending_event;\n'
            '        ctx->pending_event_valid = false;\n'
            '        return evt;\n'
            '    }\n'
            '    consecutive_count = 0;\n'
            '    return $event_none;\n'
            '}\n'
        ),
    }

    # ==================================================================
    # コンストラクタ
    # ==================================================================
    def __init__(self):
        self.mapper = CTypeMapper()
        self.naming = CNamingConvention()
        self.templates = CodeTemplates()
        self.strings = self.templates.STRINGS
        self.formats = self.templates.FORMATS
        self.layer_name: str = ""

        # ★ dispatch テーブル（table_type）
        #   将来 switch / dictionary 実装時は
        #   該当メソッドの中身を書くだけ
        self.table_generators: Dict[str, callable] = {
            'array':      self._generate_table_array,
            'switch':     self._generate_table_switch,
            'dictionary': self._generate_table_dictionary,
        }

        # ★ dispatch テーブル（generation_style）
        self.process_generators: Dict[str, callable] = {
            'table_driven': self._generate_process_table_driven,
            'switch_case':  self._generate_process_switch_case,
        }

    def set_layer(self, layer_name: str):
        """層名を設定（例: 'Driver', 'Middle', 'Application'）"""
        self.layer_name = layer_name

    def _log_debug(self, message, level='debug'):
        log_func = getattr(logger, level, logger.debug)
        log_func(message)

    # ==================================================================
    # 名前生成
    # ==================================================================
    def _state_enum(self, state_name: str) -> str:
        """STATE_<Layer>_<Name>"""
        s = self.naming.to_pascal_case(state_name) if state_name else "Unknown"
        return f"STATE_{self.layer_name}_{s}" if self.layer_name else f"STATE_{s}"

    def _event_enum(self, event_name: str) -> str:
        """EVENT_<Layer>_<Name>（空の場合は EVENT_<Layer>_NONE）"""
        e = self.naming.to_upper_snake(event_name) if event_name else "NONE"
        return f"EVENT_{self.layer_name}_{e}" if self.layer_name else f"EVENT_{e}"

    def _state_type(self) -> str:
        return f"STATE_{self.layer_name}_t" if self.layer_name else "STATE_t"

    def _event_type(self) -> str:
        return f"EVENT_{self.layer_name}_t" if self.layer_name else "EVENT_t"

    def _context_type(self) -> str:
        return f"TransitionContext_{self.layer_name}_t" if self.layer_name else "TransitionContext_t"

    def _func_type(self) -> str:
        return f"TransitionFunc_{self.layer_name}_t" if self.layer_name else "TransitionFunc_t"

    def _table_name(self) -> str:
        return f"transition_table_{self.layer_name}" if self.layer_name else "transition_matrix"

    def _state_max(self) -> str:
        return f"STATE_{self.layer_name}_MAX" if self.layer_name else "STATE_MAX"

    def _event_max(self) -> str:
        return f"EVENT_{self.layer_name}_MAX" if self.layer_name else "EVENT_MAX"

    def _cell_func_name(self, state_name: str, event_name: str) -> str:
        """transition_<Layer>_<State>_<Event>"""
        s = self.naming.to_pascal_case(state_name) if state_name else "Unknown"
        e = self.naming.to_upper_snake(event_name) if event_name else "NONE"
        if self.SHORT_CELL_NAMES:
            return f"t_{s}_{e}"
        return f"transition_{self.layer_name}_{s}_{e}" if self.layer_name \
            else f"transition_{s}_{e}"

    def _role_func_call(self, func_name: str) -> str:
        """RoleFunc_<Layer>_<Name>(transition, ctx)"""
        if func_name.startswith("RoleFunc_"):
            full = func_name
        else:
            pascal = self.naming.to_pascal_case(func_name)
            full = f"RoleFunc_{self.layer_name}_{pascal}" if self.layer_name \
                else f"RoleFunc_{pascal}"
        return f"{full}(transition, ctx)"

    # ==================================================================
    # セル単位の遷移関数
    # ==================================================================
    def generate_transition_cell_functions(self, state_machine: StateMachine) -> str:
        """全セルの遷移関数を生成"""
        cell_blocks = []

        for state in state_machine.states.values():
            for event in state_machine.events.values():
                transitions = state_machine.get_transitions_for_cell(state.name, event.name)
                if not transitions:
                    continue
                cell_blocks.append(self._build_cell_function(state, event, transitions))
        return '\n'.join(cell_blocks)

    # ==================================================================
    # 1b. セル単位の遷移関数（前方宣言）
    # ==================================================================
    def generate_transition_cell_prototypes(self, state_machine: StateMachine) -> str:
        """
        セル単位遷移関数の前方宣言（プロトタイプ）を生成

        生成例:
            /* ===== セル単位遷移関数の前方宣言 ===== */
            static STATE_Driver_t t_Idle_START(
                const TransitionContext_Driver_t *transition,
                SystemContext_t *ctx);
            static STATE_Driver_t t_Active_ERROR(
                const TransitionContext_Driver_t *transition,
                SystemContext_t *ctx);
        """
        T = self.CELL_PROTO_TEMPLATES
        parts = [T['section_comment']]
        for state in state_machine.states.values():
            for event in state_machine.events.values():
                transitions = state_machine.get_transitions_for_cell(state.name, event.name)
                if not transitions:
                    continue

                parts.append(T['prototype'].substitute(
                    state_type=self._state_type(),
                    func_name=self._cell_func_name(state.name, event.name),
                    context_type=self._context_type(),
                ))
        return ''.join(parts)

    def _build_cell_function(self, state, event, transitions) -> str:
        """1セル分の遷移関数を文字列として組み立て"""
        parts = []
        T = self.CELL_TEMPLATES

        # --- ヘッダーコメント ---
        parts.append(T['header'].substitute(
            state_enum=self._state_enum(state.name),
            event_enum=self._event_enum(event.name),
            target=transitions[0].target if transitions[0].target else "?",
        ))

        # --- 関数シグネチャ + 本体開始 ---
        parts.append(T['signature'].substitute(
            state_type=self._state_type(),
            func_name=self._cell_func_name(state.name, event.name),
            context_type=self._context_type(),
        ))
        parts.append(T['body_open'].substitute(state_type=self._state_type()))

        # --- 各遷移ブロック ---
        for idx, trans in enumerate(transitions):
            parts.append(self._build_transition_block(trans, idx))

        # --- else 節（最後の遷移にのみ） ---
        last_trans = transitions[-1]
        if getattr(last_trans, 'has_else', True):
            parts.append(self._build_else_block(last_trans))

        # --- 関数本体終了 ---
        parts.append(T['body_close'])

        return ''.join(parts)

    def _build_transition_block(self, trans, idx) -> str:
        """1つの遷移ブロックを文字列として組み立て"""
        T = self.CELL_TEMPLATES
        condition = getattr(trans, 'condition', '')
        pre_actions = ensure_list(getattr(trans, 'pre_actions', []))
        target = getattr(trans, 'target', '')

        # pre_actions を1つの文字列にまとめる
        pre_actions_code = ''.join(
            T['pre_action_line'].substitute(call=self._role_func_call(a))
            for a in pre_actions
        )

        # 条件の有無でテンプレートを切り替え
        if condition:
            return T['cond_block'].substitute(
                idx=idx, condition=condition,
                pre_actions=pre_actions_code,
                target_enum=self._state_enum(target) if target else "next_state",
            )
        return T['cond_block_empty'].substitute(
            idx=idx, pre_actions=pre_actions_code,
            target_enum=self._state_enum(target) if target else "next_state",
        )

    def _build_else_block(self, trans) -> str:
        """else 節を文字列として組み立て"""
        T = self.CELL_TEMPLATES
        else_actions = ensure_list(getattr(trans, 'else_actions', []))
        else_target = getattr(trans, 'else_target', '')

        # else_actions も else_target も無ければ出力しない
        if not else_actions and not else_target:
            return ''
        parts = [T['else_header']]
        for ea in else_actions:
            parts.append(T['else_action_line'].substitute(
                call=self._role_func_call(ea)
            ))
        if else_target:
            parts.append(T['else_target'].substitute(
                target_enum=self._state_enum(else_target)
            ))
        else:
            parts.append(T['else_target_unset'])
        return ''.join(parts)

    # ==================================================================
    # ★ 遷移テーブル（dispatch 版）
    # ==================================================================
    def generate_transition_table(self, state_machine: StateMachine,
                                  table_type: str = None) -> str:
        """遷移テーブルを生成

        Args:
            state_machine: StateMachine
            table_type: 'array' / 'switch' / 'dictionary'
                        （None の場合はデフォルト 'array'）
        """
        if table_type is None:
            table_type = self.DEFAULT_TABLE_TYPE

        generator = self.table_generators.get(table_type)

        if generator is None:
            self._log_debug(
                f"Unknown table_type '{table_type}', "
                f"falling back to '{self.DEFAULT_TABLE_TYPE}'",
                'warning'
            )
            generator = self.table_generators[self.DEFAULT_TABLE_TYPE]
        elif table_type != 'array':
            # switch / dictionary は未実装 → array にフォールバック
            self._log_debug(
                f"table_type '{table_type}' is not implemented yet, "
                f"falling back to 'array'",
                'warning'
            )
            generator = self.table_generators['array']

        return generator(state_machine)

    def _generate_table_array(self, state_machine: StateMachine) -> str:
        """配列方式（現行実装）"""
        self._log_debug("=== _generate_table_array START ===")
        T = self.TABLE_TEMPLATES
        parts = []

        # 名前の準備
        states = list(state_machine.states.values())
        events = list(state_machine.events.values())

        func_type = self._func_type()
        table_name = self._table_name()

        # --- セル値を事前計算 ---
        cell_values = []
        for state in states:
            row = []
            for event in events:
                transitions = state_machine.get_transitions_for_cell(state.name, event.name)
                row.append(self._cell_func_name(state.name, event.name)
                           if transitions else "NULL")
            cell_values.append(row)

        # --- 列幅を計算 ---
        state_col_width = max((len(s.name) for s in states), default=5)

        event_headers = []
        col_widths = []
        for event_idx, event in enumerate(events):
            event_disp = event.name if event.name else "NONE"
            event_headers.append(event_disp)
            w = max(len(event_disp), self.TABLE_MIN_COL_WIDTH)
            for state_idx in range(len(states)):
                w = max(w, len(cell_values[state_idx][event_idx]))
            col_widths.append(w)

        # --- 関数ポインタ型 ---
        parts.append(T['func_ptr_comment'])
        parts.append(T['func_ptr_typedef'].substitute(
            state_type=self._state_type(),
            func_type=func_type,
            context_type=self._context_type(),
        ))

        # --- テーブル説明 ---
        parts.append(T['table_comment'].substitute(
            row_desc="状態", col_desc="イベント",
        ))

        # --- テーブル開始 ---
        parts.append(T['table_open'].substitute(
            func_type=func_type,
            table_name=table_name,
            state_max=self._state_max(),
            event_max=self._event_max(),
        ))

        # --- ヘッダ行 ---
        header_state_pad = " " * (state_col_width + 2)
        header_cells = [event_headers[i].ljust(col_widths[i])
                        for i in range(len(events))]
        header_line = "    /*" + " " + header_state_pad + " | " \
                      + " | ".join(header_cells) + " */"
        parts.append(header_line + "\n")

        # --- 罫線 ---
        sep = "    /* " + "-" * (state_col_width + 2) + "+"
        for w in col_widths:
            sep += "-" * w + "+"
        sep = sep[:-1] + "*/"
        parts.append(sep + "\n")

        # --- データ行 ---
        for state_idx, state in enumerate(states):
            state_padded = state.name.ljust(state_col_width + 2)
            cells = []
            for event_idx in range(len(events)):
                cell_content = cell_values[state_idx][event_idx].ljust(col_widths[event_idx])
                cells.append(cell_content)

            row = f"    /* {state_padded}*/ {{ "
            row += ", ".join(cells)
            row += " },"
            parts.append(row + "\n")

        # --- テーブル終了 ---
        parts.append(T['table_close'])
        self._log_debug("=== _generate_table_array END ===")
        return ''.join(parts)

    def _generate_table_switch(self, state_machine: StateMachine) -> str:
        """switch 方式（未実装 → array フォールバック）"""
        self._log_debug(
            "_generate_table_switch: not implemented, "
            "falling back to array",
            'warning'
        )
        return self._generate_table_array(state_machine)

    def _generate_table_dictionary(self, state_machine: StateMachine) -> str:
        """dictionary 方式（未実装 → array フォールバック）"""
        self._log_debug(
            "_generate_table_dictionary: not implemented, "
            "falling back to array",
            'warning'
        )
        return self._generate_table_array(state_machine)

    # ==================================================================
    # ヘッダ用 extern 宣言
    # ==================================================================
    def generate_transition_table_header(self, state_machine: StateMachine) -> str:
        T = self.TABLE_HEADER_TEMPLATES

        parts = []
        parts.append(T['header_comment'].substitute(
            layer=self.layer_name or "システム",
            row_desc="状態", col_desc="イベント",
        ))
        parts.append(T['func_ptr_typedef'].substitute(
            state_type=self._state_type(),
            func_type=self._func_type(),
            context_type=self._context_type(),
        ))
        parts.append("")
        parts.append(T['extern_decl'].substitute(
            func_type=self._func_type(),
            table_name=self._table_name(),
            state_max=self._state_max(),
            event_max=self._event_max(),
        ))
        return ''.join(parts)

    # ==================================================================
    # 関数ディクショナリ
    # ==================================================================
    def generate_function_dictionary(self, state_machine: StateMachine) -> str:
        """名前ベースの関数ディクショナリを生成"""
        T = self.DICT_TEMPLATES
        parts = []

        # 名前の準備
        func_type = self._func_type()
        state_type = self._state_type()
        event_type = self._event_type()
        dict_type = f"TransitionDictEntry_{self.layer_name}_t" if self.layer_name else "TransitionDictEntry_t"
        dict_name = f"transition_dict_{self.layer_name}" if self.layer_name else "transition_dict"
        size_macro = f"TRANSITION_DICT_{self.layer_name.upper()}_SIZE" if self.layer_name else "TRANSITION_DICT_SIZE"

        # --- エントリ構造体 ---
        parts.append(T['struct_comment'])
        parts.append(T['struct_open'])
        parts.append(T['struct_field_from'].substitute(state_type=state_type))
        parts.append(T['struct_field_event'].substitute(event_type=event_type))
        parts.append(T['struct_field_target'].substitute(state_type=state_type))
        parts.append(T['struct_field_condition'])
        parts.append(T['struct_field_func'].substitute(func_type=func_type))
        parts.append(T['struct_close'].substitute(dict_type=dict_type))

        # --- ディクショナリ本体 ---
        parts.append(T['dict_comment'])
        parts.append(T['dict_open'].substitute(
            dict_type=dict_type, dict_name=dict_name,
        ))

        for state in state_machine.states.values():
            for event in state_machine.events.values():
                transitions = state_machine.get_transitions_for_cell(state.name, event.name)
                if not transitions:
                    continue
                for idx, trans in enumerate(transitions):
                    # 遷移名
                    base_name = f"{self.layer_name}_{state.name}_{event.name or 'NONE'}" \
                        if self.layer_name else f"{state.name}_{event.name or 'NONE'}"
                    trans_name = f"{base_name}_{idx}" if len(transitions) > 1 else base_name

                    # 代表遷移先
                    target = trans.target or state.name
                    condition = trans.condition.replace('"', '\\"') if trans.condition else ""
                    parts.append(T['dict_entry'].substitute(
                        trans_name=trans_name,
                        state_enum=self._state_enum(state.name),
                        event_enum=self._event_enum(event.name),
                        target_enum=self._state_enum(target),
                        condition=condition,
                        func_name=self._cell_func_name(state.name, event.name),
                    ))

        parts.append(T['dict_close'])
        parts.append(T['dict_size'].substitute(
            size_macro=size_macro, dict_name=dict_name,
        ))
        return ''.join(parts)

    # ==================================================================
    # ★ StateMachine_Process（dispatch 版）
    # ==================================================================
    def generate_process_function(self, state_machine: StateMachine,
                                  generation_style: str = None) -> str:
        """状態遷移処理関数を生成

        Args:
            state_machine: StateMachine
            generation_style: 'table_driven' / 'switch_case'
                              （None の場合はデフォルト 'table_driven'）
        """
        if generation_style is None:
            generation_style = self.DEFAULT_GENERATION_STYLE

        generator = self.process_generators.get(generation_style)

        if generator is None:
            self._log_debug(
                f"Unknown generation_style '{generation_style}', "
                f"falling back to '{self.DEFAULT_GENERATION_STYLE}'",
                'warning'
            )
            generator = self.process_generators[self.DEFAULT_GENERATION_STYLE]
        elif generation_style != 'table_driven':
            self._log_debug(
                f"generation_style '{generation_style}' is not implemented yet, "
                f"falling back to 'table_driven'",
                'warning'
            )
            generator = self.process_generators['table_driven']

        return generator(state_machine)

    def _generate_process_table_driven(self, state_machine: StateMachine) -> str:
        """テーブル駆動方式（現行実装）"""
        T = self.PROCESS_TEMPLATES
        func_name = f"StateMachine_Process_{self.layer_name}" if self.layer_name \
            else "StateMachine_Process"
        parts = []
        parts.append(T['comment'].substitute(layer=self.layer_name or "システム"))
        parts.append(T['signature'].substitute(
            state_type=self._state_type(),
            func_name=func_name,
            event_type=self._event_type(),
        ))
        parts.append(T['body'].substitute(
            context_type=self._context_type(),
            func_type=self._func_type(),
            table_name=self._table_name(),
        ))
        return ''.join(parts)

    def _generate_process_switch_case(self, state_machine: StateMachine) -> str:
        """switch 方式（未実装 → table_driven フォールバック）"""
        self._log_debug(
            "_generate_process_switch_case: not implemented, "
            "falling back to table_driven",
            'warning'
        )
        return self._generate_process_table_driven(state_machine)

    # ==================================================================
    # GetNextEvent（変更なし）
    # ==================================================================
    def generate_get_next_event_function(self, state_machine: StateMachine) -> str:
        """保留イベントを取得する関数を生成"""
        T = self.GET_NEXT_TEMPLATES

        func_name = f"StateMachine_GetNextEvent_{self.layer_name}" if self.layer_name \
            else "StateMachine_GetNextEvent"
        event_none = self._event_enum("")

        parts = []
        parts.append(T['comment'].substitute(
            layer=self.layer_name or "システム",
            event_none=event_none,
        ))
        parts.append(T['signature'].substitute(
            event_type=self._event_type(),
            func_name=func_name,
        ))
        parts.append(T['body'].substitute(
            event_type=self._event_type(),
            event_none=event_none,
        ))
        return ''.join(parts)

    # ==================================================================
    # 一括生成
    # ==================================================================
    def generate_all(self, state_machine: StateMachine) -> Dict[str, str]:
        """
        全生成物を辞書で返す

        Returns:
            {
                'cell_prototypes': str,        # セル関数の前方宣言
                'cell_functions': str,         # セル関数実装
                'transition_table': str,       # 2次元配列テーブル（グローバル）
                'transition_table_header': str,# テーブルの extern 宣言
                'function_dict': str,          # 関数ディクショナリ
                'process_func': str,           # StateMachine_Process_<Layer>
                'get_next_event': str,         # StateMachine_GetNextEvent_<Layer>
            }
        """
        return {
            'cell_prototypes': self.generate_transition_cell_prototypes(state_machine),
            'cell_functions': self.generate_transition_cell_functions(state_machine),
            'transition_table': self.generate_transition_table(state_machine),
            'transition_table_header': self.generate_transition_table_header(state_machine),
            'function_dict': self.generate_function_dictionary(state_machine),
            'process_func': self.generate_process_function(state_machine),
            'get_next_event': self.generate_get_next_event_function(state_machine),
        }

    # ==================================================================
    # 後方互換 API
    # ==================================================================
    def generate_all_transitions(self, state_machine, table_type='array',
                                 process_type='table_driven'):
        """後方互換: 単一文字列として返す（前方宣言 + 実装 + テーブル + Process）"""
        result = self.generate_all(state_machine)
        return '\n'.join([
            result['cell_prototypes'],
            result['transition_table'],
            result['cell_functions'],
            result['process_func'],
        ])