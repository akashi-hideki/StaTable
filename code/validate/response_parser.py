# codegen/validate/response_parser.py
"""
AI回答パーサー
"""

import json
import re
from typing import List, Dict, Optional
from .logger import logger
from .change_actions import ChangeRequest, ChangeActionType
from .data.keywords import MARKERS, PARSE_KEYWORDS


class AIResponseParser:
    """AI回答パーサー"""
    
    ACTION_MAPPING = {
        'set_initial': ChangeActionType.SET_INITIAL,
        'add_transition': ChangeActionType.ADD_TRANSITION,
        'add_state': ChangeActionType.ADD_STATE,
        'add_event': ChangeActionType.ADD_EVENT,
        'remove_transition': ChangeActionType.REMOVE_TRANSITION,
        'update_transition': ChangeActionType.UPDATE_TRANSITION,
        'add_role_function': ChangeActionType.ADD_ROLE_FUNCTION,
        'remove_role_function': ChangeActionType.REMOVE_ROLE_FUNCTION,
        'add_variable': ChangeActionType.ADD_VARIABLE,
        'add_flag': ChangeActionType.ADD_FLAG,
    }
    
    def __init__(self):
        logger.debug("AIResponseParser.__init__ started")
        self.markers = MARKERS
        logger.debug("AIResponseParser.__init__ completed")
    
    def parse(self, text: str) -> List[ChangeRequest]:
        """回答をパース"""
        logger.debug(f"parse started: text_length={len(text)}")
        
        # JSON解析を試行
        changes = self.parse_json_response(text)
        if changes:
            logger.debug(f"JSON parse succeeded: {len(changes)} changes")
            return changes
        
        logger.debug("JSON parse failed, trying text parse")
        # テキスト解析を試行
        return self.parse_text_response(text)
    
    def parse_json_response(self, text: str) -> List[ChangeRequest]:
        """JSON形式の回答をパース"""
        logger.debug("parse_json_response started")
        
        json_text = self._extract_json(text)
        if not json_text:
            logger.debug("No JSON found in response")
            return []
        
        try:
            data = json.loads(json_text)
            logger.debug(f"JSON parsed successfully: keys={list(data.keys())}")
        except json.JSONDecodeError as e:
            logger.warning(f"JSON decode failed: {e}")
            return []
        
        changes = []
        if 'changes' in data:
            for i, change_data in enumerate(data['changes']):
                logger.debug(f"Parsing change {i}: {change_data}")
                change = self._parse_change(change_data)
                if change:
                    changes.append(change)
        
        logger.debug(f"parse_json_response completed: {len(changes)} changes")
        return changes
    
    def parse_text_response(self, text: str) -> List[ChangeRequest]:
        """テキスト形式の回答をパース"""
        logger.debug("parse_text_response started")
        changes = []
        
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            change = self._parse_line(line)
            if change:
                logger.debug(f"Parsed change from line: {change.action.value}")
                changes.append(change)
        
        logger.debug(f"parse_text_response completed: {len(changes)} changes")
        return changes
    
    def _extract_json(self, text: str) -> Optional[str]:
        """JSONブロックを抽出"""
        logger.debug("_extract_json started")
        
        # マーカーで抽出
        primary = self.markers['primary']
        json_text = self._extract_with_markers(text, primary['start'], primary['end'])
        if json_text:
            logger.debug("JSON extracted with primary markers")
            return json_text
        
        # 代替マーカーで抽出
        for alt in self.markers['alternatives']:
            json_text = self._extract_with_markers(text, alt['start'], alt['end'])
            if json_text:
                logger.debug(f"JSON extracted with alternative markers: {alt['start']}")
                return json_text
        
        # JSONを直接探索
        start_idx = text.find('{')
        end_idx = text.rfind('}')
        if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
            json_candidate = text[start_idx:end_idx + 1]
            try:
                json.loads(json_candidate)
                logger.debug("JSON extracted without markers")
                return json_candidate
            except json.JSONDecodeError:
                pass
        
        logger.debug("No JSON found")
        return None
    
    def _extract_with_markers(self, text: str, start: str, end: str) -> Optional[str]:
        """マーカー間のテキストを抽出"""
        start_idx = text.find(start)
        if start_idx == -1:
            return None
        start_idx += len(start)
        end_idx = text.find(end, start_idx)
        if end_idx == -1:
            return None
        return text[start_idx:end_idx].strip()
    
    def _parse_change(self, data: Dict) -> Optional[ChangeRequest]:
        """変更データをパース"""
        action_str = data.get('action', '')
        if action_str not in self.ACTION_MAPPING:
            logger.warning(f"Unknown action: {action_str}")
            return None
        
        action = self.ACTION_MAPPING[action_str]
        params = data.get('params', {})
        reason = data.get('reason', '')
        
        logger.debug(f"_parse_change: action={action_str}, params={params}")
        
        return ChangeRequest(
            action=action,
            params=params,
            reason=reason,
            source='ai'
        )
    
    def _parse_line(self, line: str) -> Optional[ChangeRequest]:
        """1行から変更を解析"""
        # 遷移パターン: ERROR --[STOP]--> IDLE
        transition_match = re.match(r'(\w+)\s*--\[(\w+)\]-?->\s*(\w+)', line)
        if transition_match:
            return ChangeRequest(
                action=ChangeActionType.ADD_TRANSITION,
                params={
                    'source': transition_match.group(1),
                    'event': transition_match.group(2),
                    'target': transition_match.group(3),
                }
            )
        
        # 初期状態パターン: 初期状態: INIT
        initial_match = re.match(r'初期状態[::]\s*(\w+)', line)
        if initial_match:
            return ChangeRequest(
                action=ChangeActionType.SET_INITIAL,
                params={'state': initial_match.group(1)}
            )
        
        return None