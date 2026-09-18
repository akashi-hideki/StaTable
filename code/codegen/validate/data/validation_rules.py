# codegen/validate/data/validation_rules.py
"""\nValidation rule definitions (data only)\n"""

VALIDATION_RULES = {
    'state': {
        'STATE_NO_INITIAL': {
            'severity': 'error',
            'message': 'Initial state is not set',
            'suggestion': 'Please set initial state with set_initial()',
        },
        'STATE_UNREACHABLE': {
            'severity': 'warning',
            'message': 'State \"{name}\" is unreachable',
            'suggestion': 'TransitionをAddするか、StateをDeleteしてください',
        },
        'STATE_NO_TRANSITION': {
            'severity': 'warning',
            'message': 'State「{name}」からのTransitionがYesません',
            'suggestion': 'TransitionをAddするか、終端Stateとして明示してください',
        },
        'STATE_DUPLICATE': {
            'severity': 'warning',
            'message': 'State names \"{name}\" and \"{other}\" differ in case',
            'suggestion': 'Please unify the naming convention',
        },
    },
    'event': {
        'EVENT_UNUSED': {
            'severity': 'warning',
            'message': 'Event \"{name}\" is not used',
            'suggestion': 'TransitionをAddするか、EventをDeleteしてください',
        },
        'EVENT_NO_TRANSITION': {
            'severity': 'warning',
            'message': 'No transition defined for event \"{name}\"',
            'suggestion': 'TransitionをAddしてください',
        },
    },
    'transition': {
        'TRANSITION_TARGET_UNDEFINED': {
            'severity': 'error',
            'message': 'Target「{target}」が定義されていません',
            'suggestion': 'TargetのStateを定義してください',
        },
        'TRANSITION_EVENT_UNDEFINED': {
            'severity': 'error',
            'message': 'Event \"{event}\" is not defined',
            'suggestion': 'Please define the event',
        },
        'TRANSITION_SOURCE_UNDEFINED': {
            'severity': 'error',
            'message': 'Source \"{source}\" is not defined',
            'suggestion': 'Please define the source state',
        },
        'TRANSITION_DUPLICATE': {
            'severity': 'warning',
            'message': 'Transition \"{source} --[{event}]--> {target}\" is duplicated',
            'suggestion': '重複したTransitionをDeleteしてください',
        },
        'TRANSITION_SELF_LOOP': {
            'severity': 'info',
            'message': 'Self transition \"{source} --[{event}]--> {source}\"',
            'suggestion': '自己Transitionが意図的かConfirmしてください',
        },
    },
    'role_function': {
        'ROLE_FUNC_NO_RETURN_TYPE': {
            'severity': 'error',
            'message': 'Role function「{name}」のReturn typeが未定義is',
            'suggestion': 'Return typeを設定してください',
        },
        'ROLE_FUNC_ARG_MISMATCH': {
            'severity': 'error',
            'message': 'Role function「{name}」の引数定義が不完全is',
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
            'message': 'Variable name「{name}」が重複していdoes',
            'suggestion': 'Variable nameを変更してください',
        },
        'VAR_INVALID_TYPE': {
            'severity': 'warning',
            'message': 'Variable「{name}」のType「{type}」がDisabledis',
            'suggestion': '正しいTypeを指定してください',
        },
        'VAR_INVALID_ARRAY_SIZE': {
            'severity': 'error',
            'message': 'Variable「{name}」のArray sizeが不正is',
            'suggestion': 'Array sizeを0より大きいValueにしてください',
        },
    },
    'flag': {
        'FLAG_DUPLICATE_NAME': {
            'severity': 'error',
            'message': 'Flag name「{name}」が重複していdoes',
            'suggestion': 'Flag nameを変更してください',
        },
        'FLAG_INVALID_RANGE': {
            'severity': 'warning',
            'message': 'Flag \"{name}\" has invalid range',
            'suggestion': 'min_value <= max_value required',
        },
    },
    'queue': {
        'QUEUE_INVALID_SIZE': {
            'severity': 'error',
            'message': 'Queue「{name}」のSizeが不正is',
            'suggestion': 'Sizeを0より大きいValueにしてください',
        },
        'QUEUE_UNDEFINED_EVENT': {
            'severity': 'warning',
            'message': 'Queue \"{name}\" contains undefined events',
            'suggestion': 'Event definitionsをConfirmしてください',
        },
    },
    'interrupt': {
        'INTERRUPT_DUPLICATE_NAME': {
            'severity': 'error',
            'message': 'Interrupt name「{name}」が重複していdoes',
            'suggestion': 'Interrupt nameを変更してください',
        },
        'INTERRUPT_UNDEFINED_EVENT': {
            'severity': 'warning',
            'message': 'Interrupt \"{name}\" contains undefined events',
            'suggestion': 'Event definitionsをConfirmしてください',
        },
    },
    'timer': {
        'TIMER_DUPLICATE_VARIABLE': {
            'severity': 'error',
            'message': 'TimerVariable「{name}」が既存のVariableと重複していdoes',
            'suggestion': 'Variable nameを変更してください',
        },
        'TIMER_INVALID_MULTIPLIER': {
            'severity': 'error',
            'message': 'Timer「{name}」の乗数が不正is',
            'suggestion': 'Multiplier must be > 0',
        },
    },
    'custom_type': {
        'TYPE_DUPLICATE_NAME': {
            'severity': 'error',
            'message': 'Type name「{name}」が重複していdoes',
            'suggestion': 'Type nameを変更してください',
        },
        'TYPE_NO_MEMBERS': {
            'severity': 'warning',
            'message': 'Type「{name}」にメンバーが定義されていません',
            'suggestion': 'メンバーをAddしてください',
        },
    },
}