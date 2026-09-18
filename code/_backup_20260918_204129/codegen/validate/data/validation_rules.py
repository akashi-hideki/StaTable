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
            'suggestion': '遷移をAddするか、状態をDeleteしてください',
        },
        'STATE_NO_TRANSITION': {
            'severity': 'warning',
            'message': '状態「{name}」からの遷移がYesません',
            'suggestion': '遷移をAddするか、終端状態として明示してください',
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
            'suggestion': '遷移をAddするか、イベントをDeleteしてください',
        },
        'EVENT_NO_TRANSITION': {
            'severity': 'warning',
            'message': 'イベント「{name}」に対する遷移が定義されていません',
            'suggestion': '遷移をAddしてください',
        },
    },
    'transition': {
        'TRANSITION_TARGET_UNDEFINED': {
            'severity': 'error',
            'message': 'Target「{target}」が定義されていません',
            'suggestion': 'Targetの状態を定義してください',
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
            'suggestion': '重複した遷移をDeleteしてください',
        },
        'TRANSITION_SELF_LOOP': {
            'severity': 'info',
            'message': '自己遷移「{source} --[{event}]--> {source}」',
            'suggestion': '自己遷移が意図的かConfirmしてください',
        },
    },
    'role_function': {
        'ROLE_FUNC_NO_RETURN_TYPE': {
            'severity': 'error',
            'message': 'Role function「{name}」のReturn typeが未定義です',
            'suggestion': 'Return typeを設定してください',
        },
        'ROLE_FUNC_ARG_MISMATCH': {
            'severity': 'error',
            'message': 'Role function「{name}」の引数定義が不完全です',
            'suggestion': '引数名と引数Typeを正しく設定してください',
        },
        'ROLE_FUNC_UNUSED': {
            'severity': 'warning',
            'message': 'Role function「{name}」は使用されていません',
            'suggestion': '使用するかDeleteしてください',
        },
    },
    'variable': {
        'VAR_DUPLICATE_NAME': {
            'severity': 'error',
            'message': 'Variable name「{name}」が重複しています',
            'suggestion': 'Variable nameを変更してください',
        },
        'VAR_INVALID_TYPE': {
            'severity': 'warning',
            'message': '変数「{name}」のType「{type}」が無効です',
            'suggestion': '正しいTypeを指定してください',
        },
        'VAR_INVALID_ARRAY_SIZE': {
            'severity': 'error',
            'message': '変数「{name}」のArray sizeが不正です',
            'suggestion': 'Array sizeを0より大きい値にしてください',
        },
    },
    'flag': {
        'FLAG_DUPLICATE_NAME': {
            'severity': 'error',
            'message': 'Flag name「{name}」が重複しています',
            'suggestion': 'Flag nameを変更してください',
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
            'message': 'キュー「{name}」のSizeが不正です',
            'suggestion': 'Sizeを0より大きい値にしてください',
        },
        'QUEUE_UNDEFINED_EVENT': {
            'severity': 'warning',
            'message': 'キュー「{name}」に未定義のイベントが含まれています',
            'suggestion': 'Event definitionsをConfirmしてください',
        },
    },
    'interrupt': {
        'INTERRUPT_DUPLICATE_NAME': {
            'severity': 'error',
            'message': 'Interrupt name「{name}」が重複しています',
            'suggestion': 'Interrupt nameを変更してください',
        },
        'INTERRUPT_UNDEFINED_EVENT': {
            'severity': 'warning',
            'message': '割り込み「{name}」に未定義のイベントが含まれています',
            'suggestion': 'Event definitionsをConfirmしてください',
        },
    },
    'timer': {
        'TIMER_DUPLICATE_VARIABLE': {
            'severity': 'error',
            'message': 'Timer変数「{name}」が既存の変数と重複しています',
            'suggestion': 'Variable nameを変更してください',
        },
        'TIMER_INVALID_MULTIPLIER': {
            'severity': 'error',
            'message': 'Timer「{name}」の乗数が不正です',
            'suggestion': '乗数を0より大きい値にしてください',
        },
    },
    'custom_type': {
        'TYPE_DUPLICATE_NAME': {
            'severity': 'error',
            'message': 'Type name「{name}」が重複しています',
            'suggestion': 'Type nameを変更してください',
        },
        'TYPE_NO_MEMBERS': {
            'severity': 'warning',
            'message': 'Type「{name}」にメンバーが定義されていません',
            'suggestion': 'メンバーをAddしてください',
        },
    },
}