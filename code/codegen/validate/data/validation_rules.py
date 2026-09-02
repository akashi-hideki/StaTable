# codegen/validate/data/validation_rules.py
"""
検証ルール定義（データのみ）
"""

VALIDATION_RULES = {
    'state': {
        'STATE_NO_INITIAL': {
            'severity': 'error',
            'message': '初期状態が設定されていません',
            'suggestion': 'set_initial()で初期状態を設定してください',
        },
        'STATE_UNREACHABLE': {
            'severity': 'warning',
            'message': '状態「{name}」は到達不能です',
            'suggestion': '遷移を追加するか、状態を削除してください',
        },
        'STATE_NO_TRANSITION': {
            'severity': 'warning',
            'message': '状態「{name}」からの遷移がありません',
            'suggestion': '遷移を追加するか、終端状態として明示してください',
        },
        'STATE_DUPLICATE': {
            'severity': 'warning',
            'message': '状態名「{name}」と「{other}」は大文字小文字の違いのみです',
            'suggestion': '命名規則を統一してください',
        },
    },
    'event': {
        'EVENT_UNUSED': {
            'severity': 'warning',
            'message': 'イベント「{name}」はどの遷移にも使用されていません',
            'suggestion': '遷移を追加するか、イベントを削除してください',
        },
        'EVENT_NO_TRANSITION': {
            'severity': 'warning',
            'message': 'イベント「{name}」に対する遷移が定義されていません',
            'suggestion': '遷移を追加してください',
        },
    },
    'transition': {
        'TRANSITION_TARGET_UNDEFINED': {
            'severity': 'error',
            'message': '遷移先「{target}」が定義されていません',
            'suggestion': '遷移先の状態を定義してください',
        },
        'TRANSITION_EVENT_UNDEFINED': {
            'severity': 'error',
            'message': 'イベント「{event}」が定義されていません',
            'suggestion': 'イベントを定義してください',
        },
        'TRANSITION_SOURCE_UNDEFINED': {
            'severity': 'error',
            'message': '遷移元「{source}」が定義されていません',
            'suggestion': '遷移元の状態を定義してください',
        },
        'TRANSITION_DUPLICATE': {
            'severity': 'warning',
            'message': '遷移「{source} --[{event}]--> {target}」が重複しています',
            'suggestion': '重複した遷移を削除してください',
        },
        'TRANSITION_SELF_LOOP': {
            'severity': 'info',
            'message': '自己遷移「{source} --[{event}]--> {source}」',
            'suggestion': '自己遷移が意図的か確認してください',
        },
    },
    'role_function': {
        'ROLE_FUNC_NO_RETURN_TYPE': {
            'severity': 'error',
            'message': 'ロール関数「{name}」の戻り値型が未定義です',
            'suggestion': '戻り値型を設定してください',
        },
        'ROLE_FUNC_ARG_MISMATCH': {
            'severity': 'error',
            'message': 'ロール関数「{name}」の引数定義が不完全です',
            'suggestion': '引数名と引数型を正しく設定してください',
        },
        'ROLE_FUNC_UNUSED': {
            'severity': 'warning',
            'message': 'ロール関数「{name}」は使用されていません',
            'suggestion': '使用するか削除してください',
        },
    },
    'variable': {
        'VAR_DUPLICATE_NAME': {
            'severity': 'error',
            'message': '変数名「{name}」が重複しています',
            'suggestion': '変数名を変更してください',
        },
        'VAR_INVALID_TYPE': {
            'severity': 'warning',
            'message': '変数「{name}」の型「{type}」が無効です',
            'suggestion': '正しい型を指定してください',
        },
        'VAR_INVALID_ARRAY_SIZE': {
            'severity': 'error',
            'message': '変数「{name}」の配列サイズが不正です',
            'suggestion': '配列サイズを0より大きい値にしてください',
        },
    },
    'flag': {
        'FLAG_DUPLICATE_NAME': {
            'severity': 'error',
            'message': 'フラグ名「{name}」が重複しています',
            'suggestion': 'フラグ名を変更してください',
        },
        'FLAG_INVALID_RANGE': {
            'severity': 'warning',
            'message': 'フラグ「{name}」の範囲が不正です',
            'suggestion': 'min_value <= max_value にしてください',
        },
    },
    'queue': {
        'QUEUE_INVALID_SIZE': {
            'severity': 'error',
            'message': 'キュー「{name}」のサイズが不正です',
            'suggestion': 'サイズを0より大きい値にしてください',
        },
        'QUEUE_UNDEFINED_EVENT': {
            'severity': 'warning',
            'message': 'キュー「{name}」に未定義のイベントが含まれています',
            'suggestion': 'イベント定義を確認してください',
        },
    },
    'interrupt': {
        'INTERRUPT_DUPLICATE_NAME': {
            'severity': 'error',
            'message': '割り込み名「{name}」が重複しています',
            'suggestion': '割り込み名を変更してください',
        },
        'INTERRUPT_UNDEFINED_EVENT': {
            'severity': 'warning',
            'message': '割り込み「{name}」に未定義のイベントが含まれています',
            'suggestion': 'イベント定義を確認してください',
        },
    },
    'timer': {
        'TIMER_DUPLICATE_VARIABLE': {
            'severity': 'error',
            'message': 'タイマ変数「{name}」が既存の変数と重複しています',
            'suggestion': '変数名を変更してください',
        },
        'TIMER_INVALID_MULTIPLIER': {
            'severity': 'error',
            'message': 'タイマ「{name}」の乗数が不正です',
            'suggestion': '乗数を0より大きい値にしてください',
        },
    },
    'custom_type': {
        'TYPE_DUPLICATE_NAME': {
            'severity': 'error',
            'message': '型名「{name}」が重複しています',
            'suggestion': '型名を変更してください',
        },
        'TYPE_NO_MEMBERS': {
            'severity': 'warning',
            'message': '型「{name}」にメンバーが定義されていません',
            'suggestion': 'メンバーを追加してください',
        },
    },
}