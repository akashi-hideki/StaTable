# codegen/validate/data/action_definitions.py
"""
Action定義（データのみ）

【v1.6 変更】
  - add_state の type 列挙を 7 種類に拡張（StateType と一致）
  - remove_role_function をAdd（ChangeActionType との不一致解消）
"""

ACTION_DEFINITIONS = {
    'set_initial': {
        'description': 'Set initial state',
        'params': {
            'state': {'type': 'str', 'required': True, 'description': 'State name'},
        },
    },
    'add_transition': {
        'description': 'TransitionをAdd',
        'params': {
            'source': {'type': 'str', 'required': True, 'description': 'Source'},
            'event': {'type': 'str', 'required': True, 'description': 'Event name'},
            'target': {'type': 'str', 'required': True, 'description': 'Target'},
            'condition': {'type': 'str', 'required': False, 'description': 'Condition'},
            'action_name': {'type': 'str', 'required': False, 'description': 'Action名'},
        },
    },
    'add_state': {
        'description': 'StateをAdd',
        'params': {
            'name': {'type': 'str', 'required': True, 'description': 'State name'},
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
                'description': 'State type',
            },
            'description': {'type': 'str', 'required': False, 'description': 'Description'},
        },
    },
    'add_event': {
        'description': 'EventをAdd',
        'params': {
            'name': {'type': 'str', 'required': True, 'description': 'Event name'},
            'kind': {'type': 'enum', 'required': False, 'values': ['SIGNAL', 'CALL', 'TIME', 'CHANGE'], 'description': 'Event kind'},
            'description': {'type': 'str', 'required': False, 'description': 'Description'},
        },
    },
    'remove_transition': {
        'description': 'TransitionをDelete',
        'params': {
            'source': {'type': 'str', 'required': True, 'description': 'Source'},
            'event': {'type': 'str', 'required': True, 'description': 'Event name'},
            'target': {'type': 'str', 'required': True, 'description': 'Target'},
        },
    },
    'update_transition': {
        'description': 'Update transition',
        'params': {
            'source': {'type': 'str', 'required': True, 'description': 'Source'},
            'event': {'type': 'str', 'required': True, 'description': 'Event name'},
            'new_target': {'type': 'str', 'required': False, 'description': '新しいTarget'},
            'new_condition': {'type': 'str', 'required': False, 'description': 'New condition'},
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
        'description': 'VariableをAdd',
        'params': {
            'name': {'type': 'str', 'required': True, 'description': 'Variable name'},
            'type': {'type': 'str', 'required': True, 'description': 'Type'},
            'group': {'type': 'str', 'required': False, 'description': 'Group'},
            'description': {'type': 'str', 'required': False, 'description': 'Description'},
        },
    },
    'add_flag': {
        'description': 'FlagをAdd',
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
            required = "Required" if param['required'] else "Optional"
            param_strs.append(f'"{key}": {param["description"]}({required})')

        lines.append(f"{i}. {action}: {definition['description']}")
        lines.append(f"   params: {{{', '.join(param_strs)}}}")

    return '\n'.join(lines)