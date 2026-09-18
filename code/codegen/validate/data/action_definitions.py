# codegen/validate/data/action_definitions.py
"""
Action definitions (data only)

[v1.6 change]
  - Extended the type enum of add_state to 7 kinds (matching StateType)
  - Added remove_role_function (resolved mismatch with ChangeActionType)
"""

ACTION_DEFINITIONS = {
    'set_initial': {
        'description': 'Set initial state',
        'params': {
            'state': {'type': 'str', 'required': True, 'description': 'State name'},
        },
    },
    'add_transition': {
        'description': 'Add transition',
        'params': {
            'source': {'type': 'str', 'required': True, 'description': 'Source'},
            'event': {'type': 'str', 'required': True, 'description': 'Event name'},
            'target': {'type': 'str', 'required': True, 'description': 'Target'},
            'condition': {'type': 'str', 'required': False, 'description': 'Condition'},
            'action_name': {'type': 'str', 'required': False, 'description': 'Action name'},
        },
    },
    'add_state': {
        'description': 'Add state',
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
        'description': 'Add event',
        'params': {
            'name': {'type': 'str', 'required': True, 'description': 'Event name'},
            'kind': {'type': 'enum', 'required': False, 'values': ['SIGNAL', 'CALL', 'TIME', 'CHANGE'], 'description': 'Event kind'},
            'description': {'type': 'str', 'required': False, 'description': 'Description'},
        },
    },
    'remove_transition': {
        'description': 'Delete transition',
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
            'new_target': {'type': 'str', 'required': False, 'description': 'New target'},
            'new_condition': {'type': 'str', 'required': False, 'description': 'New condition'},
            'new_action': {'type': 'str', 'required': False, 'description': 'New action'},
        },
    },
    'add_role_function': {
        'description': 'Add role function',
        'params': {
            'name': {'type': 'str', 'required': True, 'description': 'Function name'},
            'return_type': {'type': 'str', 'required': True, 'description': 'Return type'},
            'description': {'type': 'str', 'required': False, 'description': 'Description'},
        },
    },
    'remove_role_function': {
        'description': 'Delete role function',
        'params': {
            'name': {'type': 'str', 'required': True, 'description': 'Function name (bare name or namespace.name)'},
        },
    },
    'add_variable': {
        'description': 'Add variable',
        'params': {
            'name': {'type': 'str', 'required': True, 'description': 'Variable name'},
            'type': {'type': 'str', 'required': True, 'description': 'Type'},
            'group': {'type': 'str', 'required': False, 'description': 'Group'},
            'description': {'type': 'str', 'required': False, 'description': 'Description'},
        },
    },
    'add_flag': {
        'description': 'Add flag',
        'params': {
            'name': {'type': 'str', 'required': True, 'description': 'Flag name'},
            'min_value': {'type': 'int', 'required': False, 'description': 'Min value'},
            'max_value': {'type': 'int', 'required': False, 'description': 'Max value'},
            'group': {'type': 'str', 'required': False, 'description': 'Group'},
        },
    },
}


def format_action_definitions() -> str:
    """Convert action definitions to prompt text"""
    lines = ["[Available actions]"]
    for i, (action, definition) in enumerate(ACTION_DEFINITIONS.items(), 1):
        params = definition['params']
        param_strs = []
        for key, param in params.items():
            required = "Required" if param['required'] else "Optional"
            param_strs.append(f'"{key}": {param["description"]}({required})')

        lines.append(f"{i}. {action}: {definition['description']}")
        lines.append(f"   params: {{{', '.join(param_strs)}}}")

    return '\n'.join(lines)