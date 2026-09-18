# codegen/validate/data/keywords.py
"""\nKeyword definitions (data only)\n"""

IGNORE_KEYWORDS = {
    'greeting': ['Understood', 'Understood', 'Understood', 'Yes,', 'Hello'],
    'preface': ['Below', 'Analysis result', 'Validated', 'Confirmed', 'The following is'],
    'explanation': ['is', 'does', 'Considering', 'I think', 'is.'],
    'supplement': ['Note,', 'By the way', 'For reference', 'Supplement'],
    'closing': ['That is all', 'The above is', 'Please confirm', 'Best regards'],
}

MARKERS = {
    'primary': {
        'start': '---CHANGES_START---',
        'end': '---CHANGES_END---',
    },
    'alternatives': [
        {'start': '```json', 'end': '```'},
        {'start': '```JSON', 'end': '```'},
        {'start': '<<<CHANGES_START>>>', 'end': '<<<CHANGES_END>>>'},
        {'start': '[[CHANGES_START]]', 'end': '[[CHANGES_END]]'},
        {'start': '===CHANGES_START===', 'end': '===CHANGES_END==='},
    ],
}

PARSE_KEYWORDS = {
    'severity': {
        'error': ['ERROR', 'Error', 'Critical'],
        'warning': ['WARNING', 'Warning'],
        'info': ['INFO', 'Info'],
    },
    'category': {
        'state': ['State'],
        'event': ['Event'],
        'transition': ['Transition'],
        'role_function': ['Role function', 'Function'],
        'variable': ['Variable'],
        'flag': ['Flag'],
        'queue': ['Queue'],
        'interrupt': ['Interrupt'],
        'timer': ['Timer'],
        'custom_type': ['Type', 'Struct'],
    },
    'suggestion': ['Fix method', 'Fix proposal', 'Proposal', 'Corresponds', 'Solution'],
    'target': ['Target', 'State', 'Function', 'Variable', 'Event'],
}