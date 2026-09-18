# codegen/validate/data/prompt_templates.py
"""
プロンプトテンプレート定義（データのみ）

【v1.8 §11.2 #7】
  - 未使用の 'review' キーをDelete
    （prompt_generator.generate_review_prompt と共にDelete）
"""

PROMPT_TEMPLATES = {
    'diagnosis': {
        'template': """あなたは組み込みソフトウェアのStateTransition設計の専門家is.

【タスク】
StateTransition設計データを検証し、必要な変更をJSON形式で出力してください。

【出力形式】
純粋なJSONのみを出力してください。
挨拶、Description、Supplement、マーカー、Codeブロック記号は一切不要is.

【出力例】
{example}

【実際のデータ】
{data}

【指示】
出力例と同じJSON形式で、実際のデータに対する変更をProposalしてください。
JSON以外は出力しないでください。

{action_definitions}

{validation_points}
""",
    },
}

FEW_SHOT_EXAMPLE = """{
  "changes": [
    {
      "action": "set_initial",
      "params": {"state": "INIT"},
      "reason": "Initial stateがNot setのため"
    },
    {
      "action": "add_transition",
      "params": {
        "source": "ERROR",
        "event": "RESET",
        "target": "IDLE",
        "action_name": "ResetError"
      },
      "reason": "ErrorStateからの回復Transitionがないため"
    }
  ]
}"""

VALIDATION_POINTS = """【検証観点】
1. Initial stateが設定されているか
2. すべてのStateにTransitionが定義されているか
3. ErrorStateからの回復Transitionがあるか
4. 各Stateで処理すべきEventが網羅されているか
5. 到達不能なStateがないか
6. デッドロックの可能性がないか
"""