# codegen/validate/response_parser.py
"""
AI回答パーサー
"""

import sys
import os
import json
import re
from typing import List, Dict, Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from .logger import logger
    from .change_actions import ChangeRequest, ChangeActionType
    from .data.keywords import MARKERS
except ImportError:
    from logger import logger
    from change_actions import ChangeRequest, ChangeActionType
    from data.keywords import MARKERS


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
        logger.debug(f"parse started: text_length={len(text)}")
        
        changes = self.parse_json_response(text)
        if changes:
            logger.debug(f"JSON parse succeeded: {len(changes)} changes")
            return changes
        
        logger.debug("JSON parse failed, trying text parse")
        return self.parse_text_response(text)
    
    def parse_json_response(self, text: str) -> List[ChangeRequest]:
        logger.debug("parse_json_response started")
        
        json_text = self._extract_json(text)
        if not json_text:
            logger.debug("No JSON found")
            return []
        
        try:
            data = json.loads(json_text)
        except json.JSONDecodeError as e:
            logger.warning(f"JSON decode failed: {e}")
            return []
        
        changes = []
        if 'changes' in data:
            for change_data in data['changes']:
                change = self._parse_change(change_data)
                if change:
                    changes.append(change)
        
        logger.debug(f"parse_json_response completed: {len(changes)} changes")
        return changes
    
    def parse_text_response(self, text: str) -> List[ChangeRequest]:
        logger.debug("parse_text_response started")
        changes = []
        
        for line in text.split('\n'):
            line = line.strip()
            change = self._parse_line(line)
            if change:
                changes.append(change)
        
        logger.debug(f"parse_text_response completed: {len(changes)} changes")
        return changes
    
    def _extract_json(self, text: str) -> Optional[str]:
        logger.debug("_extract_json started")
        
        primary = self.markers.get('primary', {})
        json_text = self._extract_with_markers(text, primary.get('start', ''), primary.get('end', ''))
        if json_text:
            return json_text
        
        for alt in self.markers.get('alternatives', []):
            json_text = self._extract_with_markers(text, alt.get('start', ''), alt.get('end', ''))
            if json_text:
                return json_text
        
        start_idx = text.find('{')
        end_idx = text.rfind('}')
        if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
            candidate = text[start_idx:end_idx + 1]
            try:
                json.loads(candidate)
                return candidate
            except json.JSONDecodeError:
                pass
        
        return None
    
    def _extract_with_markers(self, text: str, start: str, end: str) -> Optional[str]:
        if not start or not end:
            return None
        start_idx = text.find(start)
        if start_idx == -1:
            return None
        start_idx += len(start)
        end_idx = text.find(end, start_idx)
        if end_idx == -1:
            return None
        return text[start_idx:end_idx].strip()
    
    def _parse_change(self, data: Dict) -> Optional[ChangeRequest]:
        action_str = data.get('action', '')
        if action_str not in self.ACTION_MAPPING:
            return None
        
        return ChangeRequest(
            action=self.ACTION_MAPPING[action_str],
            params=data.get('params', {}),
            reason=data.get('reason', ''),
            source='ai'
        )
    
    def _parse_line(self, line: str) -> Optional[ChangeRequest]:
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
        
        initial_match = re.match(r'初期状態[::]\s*(\w+)', line)
        if initial_match:
            return ChangeRequest(
                action=ChangeActionType.SET_INITIAL,
                params={'state': initial_match.group(1)}
            )
        
        return None