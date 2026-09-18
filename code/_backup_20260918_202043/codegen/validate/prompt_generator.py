# codegen/validate/prompt_generator.py
"""
AIプロンプト生成クラス

【v1.8 §11.2 #7】
  - generate_review_prompt を削除（未使用・呼び出し元なし）
"""

import sys
import os
from typing import Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from validate.logger import logger
from validate.data.prompt_templates import (
    PROMPT_TEMPLATES, FEW_SHOT_EXAMPLE, VALIDATION_POINTS
)
from validate.data.action_definitions import format_action_definitions


class AIPromptGenerator:
    """AIプロンプト生成クラス"""

    def __init__(self):
        logger.debug("AIPromptGenerator.__init__ started")
        self.templates = PROMPT_TEMPLATES
        self.few_shot_example = FEW_SHOT_EXAMPLE
        self.validation_points = VALIDATION_POINTS
        logger.debug("AIPromptGenerator.__init__ completed")

    def _format_data(self, sm, gd) -> str:
        lines = []
        lines.append("### 状態")
        for name, state in sm.states.items():
            lines.append(f"- {name}: type={state.type.name}, description={state.description or '-'}")
        lines.append("\n### イベント")
        for name, event in sm.events.items():
            lines.append(f"- {name}: kind={event.kind.name}, description={event.description or '-'}")
        lines.append("\n### 遷移")
        if sm.transitions:
            for t in sm.transitions:
                line = f"- {t.source} --[{t.event}]--> {t.target}"
                if t.condition:
                    line += f" [条件: {t.condition}]"
                if t.action:
                    line += f" [アクション: {t.action}]"
                lines.append(line)
        else:
            lines.append("- 遷移なし")
        lines.append(f"\n### 初期状態\n{sm.initial_state or '未設定'}")
        return '\n'.join(lines)

    def _format_validation(self, validation_result) -> str:
        if not validation_result or not validation_result.issues:
            return "### 内部検証結果\n問題なし"
        lines = ["### 内部検証で検出された問題"]
        for issue in validation_result.issues:
            lines.append(f"- [{issue.severity.value.upper()}] {issue.message}")
        return '\n'.join(lines)

    def generate_diagnosis_prompt(self, sm, gd, validation_result=None) -> str:
        data = self._format_data(sm, gd)
        validation = self._format_validation(validation_result)
        template = self.templates['diagnosis']['template']
        return template.format(
            example=self.few_shot_example,
            data=f"{data}\n\n{validation}",
            action_definitions=format_action_definitions(),
            validation_points=self.validation_points,
        )