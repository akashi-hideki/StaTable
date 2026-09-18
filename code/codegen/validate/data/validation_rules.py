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
            'suggestion': 'Add a transition or delete the state',
        },
        'STATE_NO_TRANSITION': {
            'severity': 'warning',
            'message': 'State "{name}" has no outgoing transition',
            'suggestion': 'Add a transition or mark this as a terminal state',
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
            'suggestion': 'Add a transition or delete the event',
        },
        'EVENT_NO_TRANSITION': {
            'severity': 'warning',
            'message': 'No transition defined for event \"{name}\"',
            'suggestion': 'Please add a transition',
        },
    },
    'transition': {
        'TRANSITION_TARGET_UNDEFINED': {
            'severity': 'error',
            'message': 'Target "{target}" is not defined',
            'suggestion': 'Please define the target state',
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
            'suggestion': 'Please delete the duplicate transition',
        },
        'TRANSITION_SELF_LOOP': {
            'severity': 'info',
            'message': 'Self transition \"{source} --[{event}]--> {source}\"',
            'suggestion': 'Please confirm whether the self transition is intentional',
        },
    },
    'role_function': {
        'ROLE_FUNC_NO_RETURN_TYPE': {
            'severity': 'error',
            'message': 'Role function "{name}" has no return type defined',
            'suggestion': 'Please set the return type',
        },
        'ROLE_FUNC_ARG_MISMATCH': {
            'severity': 'error',
            'message': 'Role function "{name}" has incomplete argument definitions',
            'suggestion': 'Please set argument names and types correctly',
        },
        'ROLE_FUNC_UNUSED': {
            'severity': 'warning',
            'message': 'Role function "{name}" is not used',
            'suggestion': 'Please use it or delete it',
        },
    },
    'variable': {
        'VAR_DUPLICATE_NAME': {
            'severity': 'error',
            'message': 'Variable name "{name}" is duplicated',
            'suggestion': 'Please change the variable name',
        },
        'VAR_INVALID_TYPE': {
            'severity': 'warning',
            'message': 'Variable "{name}" has invalid type "{type}"',
            'suggestion': 'Please specify a valid type',
        },
        'VAR_INVALID_ARRAY_SIZE': {
            'severity': 'error',
            'message': 'Variable "{name}" has an invalid array size',
            'suggestion': 'Array size must be greater than 0',
        },
    },
    'flag': {
        'FLAG_DUPLICATE_NAME': {
            'severity': 'error',
            'message': 'Flag name "{name}" is duplicated',
            'suggestion': 'Please change the flag name',
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
            'message': 'Queue "{name}" has an invalid size',
            'suggestion': 'Size must be greater than 0',
        },
        'QUEUE_UNDEFINED_EVENT': {
            'severity': 'warning',
            'message': 'Queue \"{name}\" contains undefined events',
            'suggestion': 'Please confirm the event definitions',
        },
    },
    'interrupt': {
        'INTERRUPT_DUPLICATE_NAME': {
            'severity': 'error',
            'message': 'Interrupt name "{name}" is duplicated',
            'suggestion': 'Please change the interrupt name',
        },
        'INTERRUPT_UNDEFINED_EVENT': {
            'severity': 'warning',
            'message': 'Interrupt \"{name}\" contains undefined events',
            'suggestion': 'Please confirm the event definitions',
        },
    },
    'timer': {
        'TIMER_DUPLICATE_VARIABLE': {
            'severity': 'error',
            'message': 'Timer variable "{name}" duplicates an existing variable',
            'suggestion': 'Please change the variable name',
        },
        'TIMER_INVALID_MULTIPLIER': {
            'severity': 'error',
            'message': 'Timer "{name}" has an invalid multiplier',
            'suggestion': 'Multiplier must be > 0',
        },
    },
    'custom_type': {
        'TYPE_DUPLICATE_NAME': {
            'severity': 'error',
            'message': 'Type name "{name}" is duplicated',
            'suggestion': 'Please change the type name',
        },
        'TYPE_NO_MEMBERS': {
            'severity': 'warning',
            'message': 'Type "{name}" has no members defined',
            'suggestion': 'Please add a member',
        },
    },
}