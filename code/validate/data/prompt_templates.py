# codegen/validate/data/prompt_templates.py
"""
プロンプトテンプレート定義（データのみ）
"""

PROMPT_TEMPLATES = {
    'diagnosis': {
        'template': """あなたは組み込みソフトウェアの状態遷移設計の専門家です。

【タスク】
状態遷移設計データを検証し、必要な変更をJSON形式で出力してください。

【出力形式】
純粋なJSONのみを出力してください。
挨拶、説明、補足、マーカー、コードブロック記号は一切不要です。

【出力例】
{example}

【実際のデータ】
{data}

【指示】
出力例と同じJSON形式で、実際のデータに対する変更を提案してください。
JSON以外は出力しないでください。

{action_definitions}

{validation_points}
""",
    },
    'review': {
        'template': """あなたは組み込みソフトウェアの状態遷移設計の専門家です。

【タスク】
以下の状態遷移設計をレビューし、改善点を指摘してください。

【データ】
{data}

【出力形式】
各指摘を以下の形式で箇条書きにしてください：
- 重大度: 問題の説明（対象: 状態名やイベント名）

{validation_points}
""",
    },
}

FEW_SHOT_EXAMPLE = """{
  "changes": [
    {
      "action": "set_initial",
      "params": {"state": "INIT"},
      "reason": "初期状態が未設定のため"
    },
    {
      "action": "add_transition",
      "params": {
        "source": "ERROR",
        "event": "RESET",
        "target": "IDLE",
        "action_name": "ResetError"
      },
      "reason": "エラー状態からの回復遷移がないため"
    }
  ]
}"""

VALIDATION_POINTS = """【検証観点】
1. 初期状態が設定されているか
2. すべての状態に遷移が定義されているか
3. エラー状態からの回復遷移があるか
4. 各状態で処理すべきイベントが網羅されているか
5. 到達不能な状態がないか
6. デッドロックの可能性がないか
"""