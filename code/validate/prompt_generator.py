# codegen/validate/prompt_generator.py
"""
AIプロンプト生成クラス
"""

import json
from typing import Optional
from .logger import logger
from .data.prompt_templates import (
    PROMPT_TEMPLATES,
    FEW_SHOT_EXAMPLE,
    VALIDATION_POINTS,
)
from .data.action_definitions import format_action_definitions


class AIPromptGenerator:
    """AIプロンプト生成クラス"""
    
    def __init__(self):
        logger.debug("AIPromptGenerator.__init__ started")
        self.templates = PROMPT_TEMPLATES
        self.few_shot_example = FEW_SHOT_EXAMPLE
        self.validation_points = VALIDATION_POINTS
        logger.debug("AIPromptGenerator.__init__ completed")
    
    def _format_data(self, sm, gd) -> str:
        """状態遷移データをフォーマット"""
        logger.debug("_format_data started")
        lines = []
        
        # 状態
        lines.append("### 状態")
        for name, state in sm.states.items():
            lines.append(f"- {name}: type={state.type.name}, description={state.description or '-'}")
        logger.debug(f"Formatted {len(sm.states)} states")
        
        # イベント
        lines.append("\n### イベント")
        for name, event in sm.events.items():
            lines.append(f"- {name}: kind={event.kind.name}, description={event.description or '-'}")
        logger.debug(f"Formatted {len(sm.events)} events")
        
        # 遷移
        lines.append("\n### 遷移")
        if sm.transitions:
            for t in sm.transitions:
                line = f"- {t.source} --[{t.event}]--> {t.target}"
                if t.condition:
                    line += f" [条件: {t.condition}]"
                if t.action:
                    line += f" [アクション: {t.action}]"
                lines.append(line)
            logger.debug(f"Formatted {len(sm.transitions)} transitions")
        else:
            lines.append("- 遷移なし")
        
        # 初期状態
        lines.append(f"\n### 初期状態\n{sm.initial_state or '未設定'}")
        logger.debug(f"Initial state: {sm.initial_state}")
        
        return '\n'.join(lines)
    
    def _format_validation(self, validation_result) -> str:
        """検証結果をフォーマット"""
        logger.debug("_format_validation started")
        if not validation_result or not validation_result.issues:
            return "### 内部検証結果\n問題なし"
        
        lines = ["### 内部検証で検出された問題"]
        for issue in validation_result.issues:
            lines.append(f"- [{issue.severity.value.upper()}] {issue.message}")
        
        logger.debug(f"Formatted {len(validation_result.issues)} validation issues")
        return '\n'.join(lines)
    
    def generate_diagnosis_prompt(self, sm, gd, validation_result=None) -> str:
        """診断プロンプトを生成"""
        logger.debug("generate_diagnosis_prompt started")
        
        data = self._format_data(sm, gd)
        validation = self._format_validation(validation_result)
        
        template = self.templates['diagnosis']['template']
        prompt = template.format(
            example=self.few_shot_example,
            data=f"{data}\n\n{validation}",
            action_definitions=format_action_definitions(),
            validation_points=self.validation_points,
        )
        
        logger.debug(f"generate_diagnosis_prompt completed: {len(prompt)} chars")
        return prompt
    
    def generate_review_prompt(self, sm, gd) -> str:
        """レビュープロンプトを生成"""
        logger.debug("generate_review_prompt started")
        
        data = self._format_data(sm, gd)
        
        template = self.templates['review']['template']
        prompt = template.format(
            data=data,
            validation_points=self.validation_points,
        )
        
        logger.debug(f"generate_review_prompt completed: {len(prompt)} chars")
        return prompt