# codegen/validate/prompt_generator.py
"""
AI prompt generation class

【v1.8 §11.2 #7】
  - generate_review_prompt をDelete（未使用・呼び出し元None）
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
    """AI prompt generation class"""

    def __init__(self):
        logger.debug("AIPromptGenerator.__init__ started")
        self.templates = PROMPT_TEMPLATES
        self.few_shot_example = FEW_SHOT_EXAMPLE
        self.validation_points = VALIDATION_POINTS
        logger.debug("AIPromptGenerator.__init__ completed")

    def _format_data(self, sm, gd) -> str:
        lines = []
        lines.append("### States")
        for name, state in sm.states.items():
            lines.append(f"- {name}: type={state.type.name}, description={state.description or '-'}")
        lines.append("\n### Events")
        for name, event in sm.events.items():
            lines.append(f"- {name}: kind={event.kind.name}, description={event.description or '-'}")
        lines.append("\n### Transitions")
        if sm.transitions:
            for t in sm.transitions:
                line = f"- {t.source} --[{t.event}]--> {t.target}"
                if t.condition:
                    line += f" [条件: {t.condition}]"
                if t.action:
                    line += f" [アクション: {t.action}]"
                lines.append(line)
        else:
            lines.append("- TransitionNone")
        lines.append(f"\n### 初期状態\n{sm.initial_state or 'Not set'}")
        return '\n'.join(lines)

    def _format_validation(self, validation_result) -> str:
        if not validation_result or not validation_result.issues:
            return "### 内部Validation result\n問題None"
        lines = ["### Problems detected by internal validation"]
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