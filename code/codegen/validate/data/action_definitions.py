# codegen/validate/data/action_definitions.py
"""
アクション定義（データのみ）

【v1.6 変更】
  - add_state の type 列挙を 7 種類に拡張（StateType と一致）
  - remove_role_function を追加（ChangeActionType との不一致解消）
"""

ACTION_DEFINITIONS = {
    'set_initial': {
        'description': '初期状態を設定',
        'params': {
            'state': {'type': 'str', 'required': True, 'description': '状態名'},
        },
    },
    'add_transition': {
        'description': '遷移を追加',
        'params': {
            'source': {'type': 'str', 'required': True, 'description': '遷移元'},
            'event': {'type': 'str', 'required': True, 'description': 'イベント名'},
            'target': {'type': 'str', 'required': True, 'description': '遷移先'},
            'condition': {'type': 'str', 'required': False, 'description': '条件'},
            'action_name': {'type': 'str', 'required': False, 'description': 'アクション名'},
        },
    },
    'add_state': {
        'description': '状態を追加',
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
            'description': {'type': 'str', 'required': False, 'description': '説明'},
        },
    },
    'add_event': {
        'description': 'イベントを追加',
        'params': {
            'name': {'type': 'str', 'required': True, 'description': 'イベント名'},
            'kind': {'type': 'enum', 'required': False, 'values': ['SIGNAL', 'CALL', 'TIME', 'CHANGE'], 'description': 'イベント種類'},
            'description': {'type': 'str', 'required': False, 'description': '説明'},
        },
    },
    'remove_transition': {
        'description': '遷移を削除',
        'params': {
            'source': {'type': 'str', 'required': True, 'description': '遷移元'},
            'event': {'type': 'str', 'required': True, 'description': 'イベント名'},
            'target': {'type': 'str', 'required': True, 'description': '遷移先'},
        },
    },
    'update_transition': {
        'description': '遷移を更新',
        'params': {
            'source': {'type': 'str', 'required': True, 'description': '遷移元'},
            'event': {'type': 'str', 'required': True, 'description': 'イベント名'},
            'new_target': {'type': 'str', 'required': False, 'description': '新しい遷移先'},
            'new_condition': {'type': 'str', 'required': False, 'description': '新しい条件'},
            'new_action': {'type': 'str', 'required': False, 'description': '新しいアクション'},
        },
    },
    'add_role_function': {
        'description': 'ロール関数を追加',
        'params': {
            'name': {'type': 'str', 'required': True, 'description': '関数名'},
            'return_type': {'type': 'str', 'required': True, 'description': '戻り値型'},
            'description': {'type': 'str', 'required': False, 'description': '説明'},
        },
    },
    'remove_role_function': {
        'description': 'ロール関数を削除',
        'params': {
            'name': {'type': 'str', 'required': True, 'description': '関数名（純粋名 or namespace.name）'},
        },
    },
    'add_variable': {
        'description': '変数を追加',
        'params': {
            'name': {'type': 'str', 'required': True, 'description': '変数名'},
            'type': {'type': 'str', 'required': True, 'description': '型'},
            'group': {'type': 'str', 'required': False, 'description': 'グループ'},
            'description': {'type': 'str', 'required': False, 'description': '説明'},
        },
    },
    'add_flag': {
        'description': 'フラグを追加',
        'params': {
            'name': {'type': 'str', 'required': True, 'description': 'フラグ名'},
            'min_value': {'type': 'int', 'required': False, 'description': '最小値'},
            'max_value': {'type': 'int', 'required': False, 'description': '最大値'},
            'group': {'type': 'str', 'required': False, 'description': 'グループ'},
        },
    },
}


def format_action_definitions() -> str:
    """アクション定義をプロンプト用テキストに変換"""
    lines = ["【使用可能なアクション】"]
    for i, (action, definition) in enumerate(ACTION_DEFINITIONS.items(), 1):
        params = definition['params']
        param_strs = []
        for key, param in params.items():
            required = "必須" if param['required'] else "省略可"
            param_strs.append(f'"{key}": {param["description"]}({required})')

        lines.append(f"{i}. {action}: {definition['description']}")
        lines.append(f"   params: {{{', '.join(param_strs)}}}")

    return '\n'.join(lines)