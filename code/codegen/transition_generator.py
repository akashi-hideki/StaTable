# codegen/transition_generator.py
"""
状態遷移関数生成モジュール（多層ステートマシン対応版）

生成物:
  1. セル単位の遷移関数（static）
  2. 2次元配列の遷移テーブル（高速ディスパッチ用）
  3. 関数ディクショナリ（デバッグ・リフレクション用）
  4. StateMachine_Process_<Layer>() 関数
  5. StateMachine_GetNextEvent_<Layer>() 関数

設計方針:
  - コード生成のテンプレートは「データテーブル」としてクラス先頭に集約
  - テンプレートは string.Template（$placeholder 形式）で記述
  - メソッドは組み立てロジックのみを担当
"""

import sys
import os
import logging
from string import Template
from typing import Dict, Callable, List, Any, Optional

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
# ヘルパー: 文字列/リスト正規化
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

    # ==================================================================
    # 【データテーブル①】セル単位の遷移関数テンプレート
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
    # 【データテーブル②】遷移テーブル（2次元配列）
    # ==================================================================
    TABLE_TEMPLATES = {
        # --- 関数ポインタ型 ---
        'func_ptr_comment': (
            '/* 遷移関数ポインタ型 */\n'
        ),
        'func_ptr_typedef': Template(
            'typedef $state_type (*$func_type)(\n'
            '    const $context_type *, SystemContext_t *);\n'
        ),

        # --- 遷移テーブル本体 ---
        'table_comment': (
            '\n'
            '/* 状態遷移テーブル（2次元配列） */\n'
        ),
        'table_open': Template(
            'static const $func_type $table_name\n'
            '    [$state_max][$event_max] = {\n'
        ),
        'table_entry': Template(
            '    [$state_enum][$event_enum] =\n'
            '        $func_name,\n'
        ),
        'table_entry_null': Template(
            '    /* [$state_enum][$event_enum] = NULL (遷移なし) */\n'
        ),
        'table_close': (
            '};\n'
        ),
    }

    # ==================================================================
    # 【データテーブル③】関数ディクショナリ
    # ==================================================================
    DICT_TEMPLATES = {
        # --- エントリ構造体 ---
        'struct_comment': (
            '/* 遷移関数ディクショナリ用エントリ */\n'
            '/* デバッグ・ログ出力・動的ディスパッチに使用 */\n'
        ),
        'struct_open': (
            'typedef struct {\n'
            '    const char *name;                    /* 遷移名 */\n'
        ),
        'struct_field_from': Template(
            '    $state_type from_state;             /* 遷移元状態 */\n'
        ),
        'struct_field_event': Template(
            '    $event_type event;                  /* 発生イベント */\n'
        ),
        'struct_field_target': Template(
            '    $state_type default_target;         /* 代表遷移先 */\n'
        ),
        'struct_field_condition': (
            '    const char *condition;               /* 条件式（文字列） */\n'
        ),
        'struct_field_func': Template(
            '    $func_type func;                    /* 遷移関数ポインタ */\n'
        ),
        'struct_close': Template(
            '}} $dict_type;\n'
        ),

        # --- ディクショナリ本体 ---
        'dict_comment': (
            '\n'
            '/* 遷移関数ディクショナリ */\n'
        ),
        'dict_open': Template(
            'static const $dict_type $dict_name[] = {\n'
        ),
        'dict_entry': Template(
            '    { "$trans_name",\n'
            '      $state_enum, $event_enum, $target_enum,\n'
            '      "$condition", $func_name },\n'
        ),
        'dict_close': (
            '};\n'
        ),
        'dict_size': Template(
            '\n'
            '#define $size_macro \\\n'
            '    (sizeof($dict_name) / sizeof($dict_name[0]))\n'
        ),
    }

    # ==================================================================
    # 【データテーブル④】StateMachine_Process_<Layer> 関数
    # ==================================================================
    PROCESS_TEMPLATES = {
        'comment': Template(
            '/**\n'
            ' * @brief  $layer層の状態遷移処理\n'
            ' * @param  current_state  現在の状態\n'
            ' * @param  event          発生したイベント\n'
            ' * @param  ctx            システムコンテキストポインタ\n'
            ' * @return 遷移後の状態\n'
            ' */\n'
        ),
        'signature': Template(
            '$state_type $func_name(\n'
            '    $state_type current_state,\n'
            '    $event_type event,\n'
            '    SystemContext_t *ctx\n'
            ')\n'
        ),
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
    # 【データテーブル⑤】StateMachine_GetNextEvent_<Layer> 関数
    # ==================================================================
    GET_NEXT_TEMPLATES = {
        'comment': Template(
            '/**\n'
            ' * @brief  $layer層の次のイベントを取得\n'
            ' *         保留イベントがあればそれを返し、なければ NONE を返す\n'
            ' * @param  ctx  システムコンテキストポインタ\n'
            ' * @return 次のイベント（保留なしの場合は $event_none）\n'
            ' */\n'
        ),
        'signature': Template(
            '$event_type $func_name(SystemContext_t *ctx)\n'
        ),
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

    def set_layer(self, layer_name: str):
        """層名を設定（例: 'Driver', 'Middle', 'Application'）"""
        self.layer_name = layer_name
        logger.debug(f"TransitionGenerator.set_layer: layer_name='{layer_name}'")

    def _log_debug(self, message, level='debug'):
        log_func = getattr(logger, level, logger.debug)
        log_func(message)

    # ==================================================================
    # 名前生成ヘルパー
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

    def _cell_func_name(self, state_name: str, event_name: str) -> str:
        """transition_<Layer>_<State>_<Event>"""
        s = self.naming.to_pascal_case(state_name) if state_name else "Unknown"
        e = self.naming.to_upper_snake(event_name) if event_name else "NONE"
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
    # 1. セル単位の遷移関数生成
    # ==================================================================
    def generate_transition_cell_functions(self, state_machine: StateMachine) -> str:
        """全セルの遷移関数を生成"""
        self._log_debug(f"=== generate_transition_cell_functions START "
                        f"(layer='{self.layer_name}') ===")
        cell_blocks = []

        for state in state_machine.states.values():
            for event in state_machine.events.values():
                transitions = state_machine.get_transitions_for_cell(state.name, event.name)
                if not transitions:
                    continue

                event_disp = event.name if event.name else "(完了)"
                self._log_debug(f"  Cell {state.name} x {event_disp}: "
                                f"{len(transitions)} transition(s)")

                cell_code = self._build_cell_function(state, event, transitions)
                cell_blocks.append(cell_code)

        result = '\n'.join(cell_blocks)
        self._log_debug(f"=== generate_transition_cell_functions END: "
                        f"{len(cell_blocks)} cells ===")
        return result

    def _build_cell_function(self, state: State, event: Event,
                             transitions: List[Transition]) -> str:
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
        parts.append(T['body_open'].substitute(
            state_type=self._state_type(),
        ))

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

    def _build_transition_block(self, trans: Transition, idx: int) -> str:
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
            block = T['cond_block'].substitute(
                idx=idx,
                condition=condition,
                pre_actions=pre_actions_code,
                target_enum=self._state_enum(target) if target else "next_state",
            )
        else:
            block = T['cond_block_empty'].substitute(
                idx=idx,
                pre_actions=pre_actions_code,
                target_enum=self._state_enum(target) if target else "next_state",
            )

        return block

    def _build_else_block(self, trans: Transition) -> str:
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
    # 2. 遷移テーブル（2次元配列）生成
    # ==================================================================
    def generate_transition_table(self, state_machine: StateMachine) -> str:
        """2次元配列の遷移テーブルを生成"""
        self._log_debug("=== generate_transition_table START ===")
        T = self.TABLE_TEMPLATES
        parts = []

        # 名前の準備
        state_type = self._state_type()
        context_type = self._context_type()
        table_name = f"transition_table_{self.layer_name}" if self.layer_name else "transition_matrix"
        func_type = f"TransitionFunc_{self.layer_name}_t" if self.layer_name else "TransitionFunc_t"
        state_max = f"STATE_{self.layer_name}_MAX" if self.layer_name else "STATE_MAX"
        event_max = f"EVENT_{self.layer_name}_MAX" if self.layer_name else "EVENT_MAX"

        # --- 関数ポインタ型 ---
        parts.append(T['func_ptr_comment'])
        parts.append(T['func_ptr_typedef'].substitute(
            state_type=state_type,
            func_type=func_type,
            context_type=context_type,
        ))

        # --- テーブル本体 ---
        parts.append(T['table_comment'])
        parts.append(T['table_open'].substitute(
            func_type=func_type,
            table_name=table_name,
            state_max=state_max,
            event_max=event_max,
        ))

        for state in state_machine.states.values():
            for event in state_machine.events.values():
                transitions = state_machine.get_transitions_for_cell(state.name, event.name)
                if transitions:
                    parts.append(T['table_entry'].substitute(
                        state_enum=self._state_enum(state.name),
                        event_enum=self._event_enum(event.name),
                        func_name=self._cell_func_name(state.name, event.name),
                    ))
                else:
                    parts.append(T['table_entry_null'].substitute(
                        state_enum=self._state_enum(state.name),
                        event_enum=self._event_enum(event.name),
                    ))

        parts.append(T['table_close'])

        self._log_debug("=== generate_transition_table END ===")
        return ''.join(parts)

    # ==================================================================
    # 3. 関数ディクショナリ生成
    # ==================================================================
    def generate_function_dictionary(self, state_machine: StateMachine) -> str:
        """名前ベースの関数ディクショナリを生成"""
        self._log_debug("=== generate_function_dictionary START ===")
        T = self.DICT_TEMPLATES
        parts = []

        # 名前の準備
        state_type = self._state_type()
        event_type = self._event_type()
        func_type = f"TransitionFunc_{self.layer_name}_t" if self.layer_name else "TransitionFunc_t"
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
            dict_type=dict_type,
            dict_name=dict_name,
        ))

        entry_count = 0
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
                    entry_count += 1

        parts.append(T['dict_close'])
        parts.append(T['dict_size'].substitute(
            size_macro=size_macro,
            dict_name=dict_name,
        ))

        self._log_debug(f"=== generate_function_dictionary END: "
                        f"{entry_count} entries ===")
        return ''.join(parts)

    # ==================================================================
    # 4. StateMachine_Process_<Layer> 関数生成
    # ==================================================================
    def generate_process_function(self, state_machine: StateMachine) -> str:
        """メインの状態遷移関数を生成"""
        self._log_debug("=== generate_process_function START ===")
        T = self.PROCESS_TEMPLATES

        func_name = f"StateMachine_Process_{self.layer_name}" if self.layer_name \
            else "StateMachine_Process"
        table_name = f"transition_table_{self.layer_name}" if self.layer_name \
            else "transition_matrix"
        func_type = f"TransitionFunc_{self.layer_name}_t" if self.layer_name \
            else "TransitionFunc_t"

        parts = []
        parts.append(T['comment'].substitute(layer=self.layer_name or "システム"))
        parts.append(T['signature'].substitute(
            state_type=self._state_type(),
            func_name=func_name,
            event_type=self._event_type(),
        ))
        parts.append(T['body'].substitute(
            context_type=self._context_type(),
            func_type=func_type,
            table_name=table_name,
        ))

        self._log_debug("=== generate_process_function END ===")
        return ''.join(parts)

    # ==================================================================
    # 5. StateMachine_GetNextEvent_<Layer> 関数生成
    # ==================================================================
    def generate_get_next_event_function(self, state_machine: StateMachine) -> str:
        """保留イベントを取得する関数を生成"""
        self._log_debug("=== generate_get_next_event_function START ===")
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

        self._log_debug("=== generate_get_next_event_function END ===")
        return ''.join(parts)

    # ==================================================================
    # 6. 一括生成
    # ==================================================================
    def generate_all(self, state_machine: StateMachine) -> Dict[str, str]:
        """全生成物を辞書で返す"""
        self._log_debug(f"=== generate_all START (layer='{self.layer_name}') ===")
        result = {
            'cell_functions': self.generate_transition_cell_functions(state_machine),
            'transition_table': self.generate_transition_table(state_machine),
            'function_dict': self.generate_function_dictionary(state_machine),
            'process_func': self.generate_process_function(state_machine),
            'get_next_event': self.generate_get_next_event_function(state_machine),
        }
        self._log_debug(f"=== generate_all END ===")
        return result

    # ==================================================================
    # 後方互換 API
    # ==================================================================
    def generate_all_transitions(self, state_machine, table_type='array',
                                 process_type='table_driven'):
        """後方互換: 単一文字列として返す"""
        result = self.generate_all(state_machine)
        return '\n'.join([
            result['cell_functions'],
            result['transition_table'],
            result['process_func'],
        ])