# codegen/validate/data/keywords.py
"""
キーワード定義（データのみ）
"""

IGNORE_KEYWORDS = {
    'greeting': ['承知しました', '了解しました', 'かしこまりました', 'はい、', 'こんにちは'],
    'preface': ['以下に', '分析結果', '検証しました', '確認しました', '以下は'],
    'explanation': ['です', 'ます', 'と考え', 'と思い', 'です。'],
    'supplement': ['なお、', 'ちなみに', '参考までに', '補足'],
    'closing': ['以上です', '以上が', 'ご確認ください', 'よろしくお願い'],
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
        'error': ['ERROR', 'エラー', '重大'],
        'warning': ['WARNING', '警告'],
        'info': ['INFO', '情報'],
    },
    'category': {
        'state': ['状態'],
        'event': ['イベント'],
        'transition': ['遷移'],
        'role_function': ['ロール関数', '関数'],
        'variable': ['変数'],
        'flag': ['フラグ'],
        'queue': ['キュー'],
        'interrupt': ['割り込み'],
        'timer': ['タイマ'],
        'custom_type': ['型', '構造体'],
    },
    'suggestion': ['修正方法', '修正案', '提案', '対応', '解決策'],
    'target': ['対象', '状態', '関数', '変数', 'イベント'],
}