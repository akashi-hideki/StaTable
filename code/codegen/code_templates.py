# codegen/code_templates.py
"""
コード生成用テンプレート定義
すべての固定文字列とデータを一元管理する
"""

class CodeTemplates:
    """コード生成用テンプレート辞書"""
    
    # ===== 基本文字列定義 =====
    STRINGS = {
        'section_line': '/*==============================================================*/',
        'indent_1': '    ',
        'indent_2': '        ',
        'indent_3': '            ',
        'newline': '\n',
        'blank_line': '',
        'typedef': 'typedef',
        'struct': 'struct',
        'enum': 'enum',
        'include': '#include',
        'define': '#define',
        'ifndef': '#ifndef',
        'endif': '#endif',
        'return': 'return',
        'void': 'void',
        'static': 'static',
        'const': 'const',
        'switch': 'switch',
        'case': 'case',
        'break': 'break',
        'default': 'default',
        'if': 'if',
        'else': 'else',
        'todo': 'TODO: 実装を記述すること',
        'unused_arg': '未使用引数の警告抑制',
        'auto_generated': 'StaTableにより自動生成されたコード',
        'no_edit': '手動での編集は推奨しない',
        'edit_in_statable': '変更する場合はStaTableで行うこと',
        'log_debug': 'LOG_DEBUG',
        'log_info': 'LOG_INFO',
        'log_warning': 'LOG_WARNING',
        'log_error': 'LOG_ERROR',
    }
    
    # ===== セクションヘッダ定義 =====
    SECTION_HEADERS = {
        'include': 'インクルードファイル',
        'type_defs': '型定義',
        'custom_types': 'ユーザー定義型',
        'system_structs': 'システム構造体',
        'function_decls': '関数宣言',
        'role_functions': 'ロール関数宣言',
        'role_impl': 'ロール関数実装',
        'transition_table': '状態遷移テーブル',
        'transition_func': '状態遷移関数',
        'init_func': '初期化関数',
        'var_macros': '変数アクセスマクロ',
    }
    
    # ===== 構造体コメント定義 =====
    STRUCT_COMMENTS = {
        'system_data': {'title': 'グローバル変数構造体', 'description': 'システム全体で共有する変数を管理'},
        'event_flags': {'title': 'イベントフラグ構造体', 'description': 'イベント発生を示すフラグを管理'},
        'system_context': {'title': 'システム全体構造体', 'description': 'グローバル変数とイベントフラグを統合管理'},
        'transition_cell': {'title': '遷移セル構造体', 'description': '状態遷移テーブルの1セルを表す'},
    }
    
    # ===== 列挙型コメント定義 =====
    ENUM_COMMENTS = {
        'state': {'title': '状態定義', 'description': '状態遷移の状態を表す列挙型'},
        'event': {'title': 'イベント定義', 'description': '状態遷移を発生させるイベントの列挙型'},
        'flag': {'title': 'イベントフラグ定義', 'description': 'イベントフラグの識別子を表す列挙型'},
    }
    
    # ===== 関数コメント定義 =====
    FUNCTION_COMMENTS = {
        'state_machine_process': {
            'brief': '状態遷移処理',
            'params': [
                ('current_state', '現在の状態'),
                ('event', '発生したイベント'),
                ('ctx', 'システムコンテキストポインタ'),
            ],
            'return': '遷移後の状態',
        },
        'system_context_init': {
            'brief': 'システムコンテキスト初期化',
            'params': [('ctx', 'システムコンテキストポインタ')],
            'return': None,
        },
    }
    
    # ===== 型名定義 =====
    TYPE_NAMES = {
        'state': 'STATE_t',
        'event': 'EVENT_t',
        'flag': 'FLAG_t',
        'system_data': 'SystemData_t',
        'event_flags': 'EventFlags_t',
        'system_context': 'SystemContext_t',
        'transition_cell': 'TransitionCell_t',
        'transition_table': 'transition_matrix',
    }
    
    # ===== 関数名定義 =====
    FUNCTION_NAMES = {
        'state_machine_process': 'StateMachine_Process',
        'system_context_init': 'SystemContext_Init',
        'role_func_prefix': 'RoleFunc',
        'action_prefix': 'Action',
        'condition_prefix': 'Condition',
    }
    
    # ===== マクロ名定義 =====
    MACRO_NAMES = {
        'data_prefix': 'DATA_',
        'flag_prefix': 'FLAG_',
        'max_suffix': '_MAX',
    }
    
    # ===== フォーマットテンプレート =====
    FORMATS = {
        'section_header': '{line}\n *  {title}\n{line}',
        'file_header': '''/**
 * @file    {filename}
 * @brief   {description}
 *
 * @note    {auto_generated}
 *          - {no_edit}
 *          - {edit_in_statable}
 *
 * @date    {date}
 */''',
        'include_guard_start': '#ifndef {guard_macro}\n#define {guard_macro}\n',
        'include_guard_end': '#endif /* {guard_macro} */',
        'struct_start': 'typedef struct {{',
        'struct_end': '}} {type_name};',
        'enum_start': 'typedef enum {{',
        'enum_end': '}} {type_name};',
        'enum_value': '{name} = {value},',
        'enum_value_with_comment': '{name} = {value},    /* {comment} */',
        'enum_max': '{name}           /* {comment} */',
        'function_comment': '''/**
 * @brief  {brief}
 * @param  {param_name}  {param_desc}
 * @return {return_desc}
 */''',
        'data_macro': '#define DATA_{var_name}(ctx)    ((ctx)->data.{var_name})',
        'flag_macro': '#define FLAG_{flag_name}(ctx)   ((ctx)->flags.{flag_name})',
        'group_separator': '/* === {group_name} === */',
        'member_normal': '{indent}{type} {name};',
        'member_array': '{indent}{type} {name}[{size}];',
        'member_bitfield': '{indent}{type} {name} : {width};',
        'inline_comment': '{indent}/* {comment} */',
        'title_comment': '{indent}/* Title: {title} */',
    }
    
    # ===== 生成パターン定義（データ駆動用） =====
    # 各生成処理のステップを定義
    GENERATION_PATTERNS = {
        # 構造体生成パターン
        'struct_custom_type': {
            'steps': [
                {'type': 'comment', 'source': 'struct_def'},
                {'type': 'line', 'template': 'struct_start'},
                {'type': 'loop', 'source': 'members', 'item_type': 'member'},
                {'type': 'line', 'template': 'struct_end', 'params': {'type_name': '{generated}'}},
            ]
        },
        'struct_system_data': {
            'steps': [
                {'type': 'comment', 'key': 'system_data'},
                {'type': 'line', 'template': 'struct_start'},
                {'type': 'loop', 'source': 'variables', 'item_type': 'variable'},
                {'type': 'line', 'template': 'struct_end', 'params': {'type_name': 'SystemData_t'}},
            ]
        },
        'struct_event_flags': {
            'steps': [
                {'type': 'comment', 'key': 'event_flags'},
                {'type': 'line', 'template': 'struct_start'},
                {'type': 'loop', 'source': 'flags', 'item_type': 'flag'},
                {'type': 'line', 'template': 'struct_end', 'params': {'type_name': 'EventFlags_t'}},
            ]
        },
        'struct_system_context': {
            'steps': [
                {'type': 'comment', 'key': 'system_context'},
                {'type': 'line', 'template': 'struct_start'},
                {'type': 'line', 'template': 'member_normal', 'params': {'indent': '{indent_1}', 'type': 'SystemData_t', 'name': 'data'}},
                {'type': 'line', 'template': 'member_normal', 'params': {'indent': '{indent_1}', 'type': 'EventFlags_t', 'name': 'flags'}},
                {'type': 'line', 'template': 'struct_end', 'params': {'type_name': 'SystemContext_t'}},
            ]
        },
        
        # 列挙型生成パターン
        'enum_state': {
            'steps': [
                {'type': 'enum_comment', 'key': 'state'},
                {'type': 'line', 'template': 'enum_start'},
                {'type': 'loop', 'source': 'states', 'item_type': 'enum_value'},
                {'type': 'line', 'template': 'enum_max', 'params': {'name': 'STATE_MAX'}},
                {'type': 'line', 'template': 'enum_end', 'params': {'type_name': 'STATE_t'}},
            ]
        },
        'enum_event': {
            'steps': [
                {'type': 'enum_comment', 'key': 'event'},
                {'type': 'line', 'template': 'enum_start'},
                {'type': 'loop', 'source': 'events', 'item_type': 'enum_value'},
                {'type': 'line', 'template': 'enum_max', 'params': {'name': 'EVENT_MAX'}},
                {'type': 'line', 'template': 'enum_end', 'params': {'type_name': 'EVENT_t'}},
            ]
        },
        'enum_flag': {
            'steps': [
                {'type': 'enum_comment', 'key': 'flag'},
                {'type': 'line', 'template': 'enum_start'},
                {'type': 'loop', 'source': 'flags', 'item_type': 'enum_value'},
                {'type': 'line', 'template': 'enum_max', 'params': {'name': 'FLAG_MAX'}},
                {'type': 'line', 'template': 'enum_end', 'params': {'type_name': 'FLAG_t'}},
            ]
        },
    }
    
    # ===== 行生成パターン定義 =====
    # 各行の生成方法を定義
    LINE_PATTERNS = {
        'member_normal': {'template': 'member_normal', 'params': ['indent', 'type', 'name']},
        'member_array': {'template': 'member_array', 'params': ['indent', 'type', 'name', 'size']},
        'member_bitfield': {'template': 'member_bitfield', 'params': ['indent', 'type', 'name', 'width']},
        'comment': {'template': 'inline_comment', 'params': ['indent', 'comment']},
        'blank': {'template': None, 'params': []},
    }
    
    # ===== デバッグログメッセージ定義 =====
    DEBUG_MESSAGES = {
        'function_entry': 'Enter {func_name}: state={state}, event={event}',
        'function_exit': 'Exit {func_name}: next_state={next_state}',
        'condition_check': 'Check condition: {condition_name}',
        'condition_not_met': 'Condition not met',
        'action_execute': 'Execute action: {action_name}',
        'transition': 'Transition: {from_state} -> {to_state} (event: {event})',
        'no_transition': 'No transition: state={state}, event={event}',
        'null_pointer': 'NULL pointer: {var_name}',
        'out_of_range': 'Out of range: {var_name}={value}, max={max}',
    }