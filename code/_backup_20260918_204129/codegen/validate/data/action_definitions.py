# codegen/validate/data/action_definitions.py
"""
Action定義（データのみ）

【v1.6 変更】
  - add_state の type 列挙を 7 種類に拡張（StateType と一致）
  - remove_role_function をAdd（ChangeActionType との不一致解消）
"""

ACTION_DEFINITIONS = {
    'set_initial': {
        'description': '初期状態を設定',
        'params': {
            'state': {'type': 'str', 'required': True, 'description': '状態名'},
        },
    },
    'add_transition': {
        'description': '遷移をAdd',
        'params': {
            'source': {'type': 'str', 'required': True, 'description': '遷移元'},
            'event': {'type': 'str', 'required': True, 'description': 'Event name'},
            'target': {'type': 'str', 'required': True, 'description': 'Target'},
            'condition': {'type': 'str', 'required': False, 'description': '条件'},
            'action_name': {'type': 'str', 'required': False, 'description': 'Action名'},
        },
    },
    'add_state': {
        'description': '状態をAdd',
        'params': {
            'name': {'type': 'str', 'required': True, 'description': '状態名'},
            'type': {
                'type': 'enum',
                'required': False,
                'values': [
                    'NORMAL',
                    'CONCURRENT',
                    'REGION',
                    'INITIAL',
                    'FINAL',
                    'CHOICE',
                    'JUNCTION',
                ],
                'description': '状態タイプ',
            },
            'description': {'type': 'str', 'required': False, 'description': 'Description'},
        },
    },
    'add_event': {
        'description': 'イベントをAdd',
        'params': {
            'name': {'type': 'str', 'required': True, 'description': 'Event name'},
            'kind': {'type': 'enum', 'required': False, 'values': ['SIGNAL', 'CALL', 'TIME', 'CHANGE'], 'description': 'Event kind'},
            'description': {'type': 'str', 'required': False, 'description': 'Description'},
        },
    },
    'remove_transition': {
        'description': '遷移をDelete',
        'params': {
            'source': {'type': 'str', 'required': True, 'description': '遷移元'},
            'event': {'type': 'str', 'required': True, 'description': 'Event name'},
            'target': {'type': 'str', 'required': True, 'description': 'Target'},
        },
    },
    'update_transition': {
        'description': '遷移を更新',
        'params': {
            'source': {'type': 'str', 'required': True, 'description': '遷移元'},
            'event': {'type': 'str', 'required': True, 'description': 'Event name'},
            'new_target': {'type': 'str', 'required': False, 'description': '新しいTarget'},
            'new_condition': {'type': 'str', 'required': False, 'description': '新しい条件'},
            'new_action': {'type': 'str', 'required': False, 'description': '新しいAction'},
        },
    },
    'add_role_function': {
        'description': 'Role functionをAdd',
        'params': {
            'name': {'type': 'str', 'required': True, 'description': 'Function name'},
            'return_type': {'type': 'str', 'required': True, 'description': 'Return type'},
            'description': {'type': 'str', 'required': False, 'description': 'Description'},
        },
    },
    'remove_role_function': {
        'description': 'Role functionをDelete',
        'params': {
            'name': {'type': 'str', 'required': True, 'description': 'Function name（純粋名 or namespace.name）'},
        },
    },
    'add_variable': {
        'description': '変数をAdd',
        'params': {
            'name': {'type': 'str', 'required': True, 'description': 'Variable name'},
            'type': {'type': 'str', 'required': True, 'description': 'Type'},
            'group': {'type': 'str', 'required': False, 'description': 'Group'},
            'description': {'type': 'str', 'required': False, 'description': 'Description'},
        },
    },
    'add_flag': {
        'description': 'フラグをAdd',
        'params': {
            'name': {'type': 'str', 'required': True, 'description': 'Flag name'},
            'min_value': {'type': 'int', 'required': False, 'description': 'Min value'},
            'max_value': {'type': 'int', 'required': False, 'description': 'Max value'},
            'group': {'type': 'str', 'required': False, 'description': 'Group'},
        },
    },
}


def format_action_definitions() -> str:
    """Action定義をプロンプト用テキストに変換"""
    lines = ["【使用可能なAction】"]
    for i, (action, definition) in enumerate(ACTION_DEFINITIONS.items(), 1):
        params = definition['params']
        param_strs = []
        for key, param in params.items():
            required = "必須" if param['required'] else "省略可"
            param_strs.append(f'"{key}": {param["description"]}({required})')

        lines.append(f"{i}. {action}: {definition['description']}")
        lines.append(f"   params: {{{', '.join(param_strs)}}}")

    return '\n'.join(lines)