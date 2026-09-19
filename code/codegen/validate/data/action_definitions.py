# codegen/validate/data/action_definitions.py
"""
Action definitions (data only).

[v1.6 change]
  - Extended the type enum of add_state to 7 kinds (matching StateType)
  - Added remove_role_function

[v2.2 §12-6 change]
  - Added 7 cell-level AI actions:
      add_cell / remove_cell
      add_action_step / remove_action_step
      add_transition_relation / remove_transition_relation
      set_early_return
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
                    'NORMAL', 'CONCURRENT', 'REGION', 'INITIAL',
                    'FINAL', 'CHOICE', 'JUNCTION',
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
            'kind': {'type': 'enum', 'required': False,
                     'values': ['SIGNAL', 'CALL', 'TIME', 'CHANGE'],
                     'description': 'Event kind'},
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
            'name': {'type': 'str', 'required': True,
                     'description': 'Function name (bare name or namespace.name)'},
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
    # ==============================================================
    # v2.2 §12-6: Cell-level AI actions
    # ==============================================================
    'add_cell': {
        'description': 'Add (or ensure) a cell for (source, event)',
        'params': {
            'source': {'type': 'str', 'required': True, 'description': 'Source state name'},
            'event': {'type': 'str', 'required': True, 'description': 'Event name (empty for completion)'},
        },
    },
    'remove_cell': {
        'description': 'Remove a cell (actions + relations) for (source, event)',
        'params': {
            'source': {'type': 'str', 'required': True, 'description': 'Source state name'},
            'event': {'type': 'str', 'required': True, 'description': 'Event name (empty for completion)'},
        },
    },
    'add_action_step': {
        'description': 'Add a Pre/Post action step to a cell',
        'params': {
            'source': {'type': 'str', 'required': True, 'description': 'Source state name'},
            'event': {'type': 'str', 'required': True, 'description': 'Event name'},
            'role_function': {'type': 'str', 'required': True, 'description': 'Role function name'},
            'trigger': {
                'type': 'enum',
                'required': False,
                'values': ['before_transitions', 'after_transitions'],
                'description': 'Action trigger (default: before_transitions)',
            },
        },
    },
    'remove_action_step': {
        'description': 'Remove a Pre/Post action step from a cell',
        'params': {
            'source': {'type': 'str', 'required': True, 'description': 'Source state name'},
            'event': {'type': 'str', 'required': True, 'description': 'Event name'},
            'role_function': {'type': 'str', 'required': True, 'description': 'Role function name'},
        },
    },
    'add_transition_relation': {
        'description': 'Add a transition relation (group / sequential / exclusive)',
        'params': {
            'source': {'type': 'str', 'required': True, 'description': 'Source state name'},
            'event': {'type': 'str', 'required': True, 'description': 'Event name'},
            'kind': {
                'type': 'enum',
                'required': True,
                'values': ['sequential', 'exclusive', 'group'],
                'description': 'Relation kind',
            },
            'members': {'type': 'list', 'required': True, 'description': 'Transition labels (e.g. ["T1","T2"])'},
            'shared_condition': {'type': 'str', 'required': False,
                                 'description': 'Required for kind == "group"'},
        },
    },
    'remove_transition_relation': {
        'description': 'Remove a transition relation by kind + shared_condition',
        'params': {
            'source': {'type': 'str', 'required': True, 'description': 'Source state name'},
            'event': {'type': 'str', 'required': True, 'description': 'Event name'},
            'kind': {'type': 'str', 'required': True, 'description': 'Relation kind'},
            'shared_condition': {'type': 'str', 'required': False,
                                 'description': 'Match shared_condition (optional)'},
        },
    },
    'set_early_return': {
        'description': 'Set early_return (Commit) flag on a transition',
        'params': {
            'source': {'type': 'str', 'required': True, 'description': 'Source state name'},
            'event': {'type': 'str', 'required': True, 'description': 'Event name'},
            'label': {'type': 'str', 'required': True, 'description': 'Transition label (e.g. "T1")'},
            'early_return': {'type': 'bool', 'required': True,
                             'description': 'True = Commit, False = Tentative'},
        },
    },
}


def format_action_definitions() -> str:
    """Convert action definitions to prompt text."""
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