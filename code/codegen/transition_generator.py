# codegen/transition_generator.py
"""
状態遷移関数生成モジュール（完全データ駆動版）
"""

import sys
import os
import logging
from typing import Dict, Callable, List, Any, Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from statable.model import State, Event, Transition
from statable.state_machine import StateMachine

try:
    from .type_mapper import CTypeMapper
    from .naming_convention import CNamingConvention
    from .code_templates import CodeTemplates
except ImportError:
    from type_mapper import CTypeMapper
    from naming_convention import CNamingConvention
    from code_templates import CodeTemplates

logger = logging.getLogger(__name__)


class TransitionGenerator:
    """状態遷移関数生成クラス（完全データ駆動）"""
    
    def __init__(self):
        self.mapper = CTypeMapper()
        self.naming = CNamingConvention()
        self.templates = CodeTemplates()
        self.strings = self.templates.STRINGS
        self.formats = self.templates.FORMATS
        
        self.table_generators: Dict[str, Callable] = {
            'array': self._generate_array_table,
            'switch': self._generate_switch_case,
            'dictionary': self._generate_dictionary_table,
        }
        
        self.process_generators: Dict[str, Callable] = {
            'table_driven': self._generate_table_driven_process,
            'switch_case': self._generate_switch_case_process,
        }
        
        self.table_steps = {
            'struct_header': [
                {'action': 'template', 'key': 'transition_cell_comment'},
                {'action': 'template', 'key': 'transition_cell_start'},
                {'action': 'template', 'key': 'transition_cell_member_next_state'},
                {'action': 'template', 'key': 'transition_cell_member_condition'},
                {'action': 'template', 'key': 'transition_cell_member_action'},
                {'action': 'template', 'key': 'transition_cell_end'},
                {'action': 'blank'},
            ],
            'table_header': [
                {'action': 'template', 'key': 'transition_table_comment'},
                {'action': 'template', 'key': 'transition_table_start'},
            ],
            'state_row': [
                {'action': 'state_comment'},
                {'action': 'row_start'},
                {'action': 'loop_events'},
                {'action': 'row_end'},
            ],
            'table_footer': [
                {'action': 'template', 'key': 'transition_table_end'},
            ],
        }
        
        self.table_templates = {
            'transition_cell_comment': '''/* 遷移セル構造体 */
/* 状態遷移テーブルの1セルを表す */''',
            'transition_cell_start': 'typedef struct {',
            'transition_cell_member_next_state': '    STATE_t next_state;',
            'transition_cell_member_condition': '    bool (*condition)(SystemContext_t *ctx);',
            'transition_cell_member_action': '    void (*action)(SystemContext_t *ctx);',
            'transition_cell_end': '} TransitionCell_t;',
            'transition_table_comment': '/* 状態遷移テーブル */',
            'transition_table_start': 'static const TransitionCell_t transition_matrix[STATE_MAX][EVENT_MAX] = {',
            'transition_table_end': '};',
        }
        
        self.cell_templates = {
            'transition': '        { {target_state}, {condition_name}, {action_name} }, /* {comment} */',
            'empty': '        { {current_state}, NULL, NULL }, /* No transition */',
        }
        
        self.process_steps = [
            {'action': 'template', 'key': 'func_comment'},
            {'action': 'template', 'key': 'func_signature'},
            {'action': 'template', 'key': 'func_open'},
            {'action': 'blank'},
            {'action': 'template', 'key': 'null_check'},
            {'action': 'blank'},
            {'action': 'template', 'key': 'range_check'},
            {'action': 'blank'},
            {'action': 'template', 'key': 'entry_log'},
            {'action': 'blank'},
            {'action': 'template', 'key': 'table_ref'},
            {'action': 'blank'},
            {'action': 'template', 'key': 'condition_check'},
            {'action': 'blank'},
            {'action': 'template', 'key': 'action_execute'},
            {'action': 'blank'},
            {'action': 'template', 'key': 'transition_execute'},
            {'action': 'blank'},
            {'action': 'template', 'key': 'exit_log'},
            {'action': 'blank'},
            {'action': 'template', 'key': 'func_close'},
        ]
        
        self.process_templates = {
            'func_comment': '''/**
 * @brief  状態遷移処理
 * @param  current_state  現在の状態
 * @param  event          発生したイベント
 * @param  ctx            システムコンテキストポインタ
 * @return 遷移後の状態
 */''',
            'func_signature': 'STATE_t {func_name}(',
            'func_open': '''    STATE_t current_state,
    EVENT_t event,
    SystemContext_t *ctx
)
{
    STATE_t next_state = current_state;''',
            'null_check': '''    /* NULLチェック */
    if (ctx == NULL) {
        {log_error}("NULL pointer: ctx");
        return current_state;
    }''',
            'range_check': '''    /* 範囲チェック */
    if (current_state >= STATE_MAX || event >= EVENT_MAX) {
        {log_error}("Out of range: state=%d, event=%d", current_state, event);
        return current_state;
    }''',
            'entry_log': '    {log_debug}("Enter {func_name}: state=%d, event=%d", current_state, event);',
            'table_ref': '''    /* 遷移テーブルから該当セルを取得 */
    const TransitionCell_t *cell = &transition_matrix[current_state][event];''',
            'condition_check': '''    /* 条件チェック */
    if (cell->condition != NULL) {
        if (!cell->condition(ctx)) {
            {log_debug}("Condition not met");
            return current_state;
        }
    }''',
            'action_execute': '''    /* アクション実行 */
    if (cell->action != NULL) {
        cell->action(ctx);
    }''',
            'transition_execute': '''    /* 状態遷移 */
    if (cell->next_state != STATE_MAX) {
        next_state = cell->next_state;
        {log_info}("Transition: %d -> %d", current_state, next_state);
    }''',
            'exit_log': '    {log_debug}("Exit {func_name}: next_state=%d", next_state);',
            'func_close': '''    return next_state;
}''',
        }
        
        self.step_executors: Dict[str, Callable] = {
            'template': self._execute_template_step,
            'blank': self._execute_blank_step,
            'state_comment': self._execute_state_comment_step,
            'row_start': self._execute_row_start_step,
            'loop_events': self._execute_loop_events_step,
            'row_end': self._execute_row_end_step,
        }
    
    def _log_debug(self, message: str, level: str = 'debug'):
        log_func = getattr(logger, level, logger.debug)
        log_func(message)
    
    def _build_context(self, state_machine: StateMachine) -> Dict[str, Any]:
        return {
            'func_name': self.templates.FUNCTION_NAMES['state_machine_process'],
            'log_debug': self.strings['log_debug'],
            'log_error': self.strings['log_error'],
            'log_info': self.strings['log_info'],
            'state_machine': state_machine,
            'states': list(state_machine.states.values()),  # 辞書→リスト
            'events': list(state_machine.events.values()),  # 辞書→リスト
        }
    
    def _format_value(self, value: str, context: Dict[str, Any]) -> str:
        if isinstance(value, str) and value.startswith('{') and value.endswith('}'):
            key = value[1:-1]
            return context.get(key, value)
        return value
    
    def _format_params(self, params: Dict[str, str], context: Dict[str, Any]) -> Dict[str, str]:
        return {key: self._format_value(value, context) for key, value in params.items()}
    
    def _execute_template_step(self, step: Dict, context: Dict[str, Any]) -> List[str]:
        template_key = step.get('key', '')
        templates = step.get('templates', self.process_templates)
        template = templates.get(template_key, '')
        
        if not template:
            return []
        
        format_params = step.get('format', {})
        resolved_params = self._format_params(format_params, context)
        
        try:
            formatted = template.format(**resolved_params)
        except (KeyError, IndexError):
            formatted = template
        
        return [formatted]
    
    def _execute_blank_step(self, step: Dict, context: Dict[str, Any]) -> List[str]:
        return [""]
    
    def _execute_state_comment_step(self, step: Dict, context: Dict[str, Any]) -> List[str]:
        state = context.get('current_state')
        if state:
            state_name = self.naming.create_enum_value("STATE", state.name)
            return [f"    /* {state_name} */"]
        return []
    
    def _execute_row_start_step(self, step: Dict, context: Dict[str, Any]) -> List[str]:
        return ["    {"]
    
    def _execute_loop_events_step(self, step: Dict, context: Dict[str, Any]) -> List[str]:
        state = context.get('current_state')
        events = context.get('events', [])
        state_machine = context.get('state_machine')
        
        results = []
        for event in events:
            # 修正: state.name と event.name を文字列として渡す
            transitions = state_machine.get_transitions_for_cell(state.name, event.name)
            
            if transitions and len(transitions) > 0:
                transition = transitions[0]
                target_state = self.naming.create_enum_value("STATE", transition.target)
                condition_name = self._get_condition_function_name(transition)
                action_name = self._get_action_function_name(transition)
                comment = f"{state.name} -> {transition.target} (event: {event.name})"
                
                cell = self.cell_templates['transition'].format(
                    target_state=target_state,
                    condition_name=condition_name,
                    action_name=action_name,
                    comment=comment,
                )
            else:
                current_state = self.naming.create_enum_value("STATE", state.name)
                cell = self.cell_templates['empty'].format(current_state=current_state)
            
            results.append(cell)
        
        return results
    
    def _execute_row_end_step(self, step: Dict, context: Dict[str, Any]) -> List[str]:
        return ["    },"]
    
    def _generate_array_table(self, state_machine: StateMachine) -> str:
        self._log_debug("Generating array table (data-driven)")
        
        lines = []
        context = self._build_context(state_machine)
        
        for step in self.table_steps['struct_header']:
            results = self._execute_template_step(step, context)
            lines.extend(results)
        
        for step in self.table_steps['table_header']:
            results = self._execute_template_step(step, context)
            lines.extend(results)
        
        # 修正: states 辞書の values() を使用
        for state in state_machine.states.values():
            context['current_state'] = state
            
            for step in self.table_steps['state_row']:
                executor = self.step_executors.get(step['action'])
                if executor:
                    results = executor(step, context)
                    lines.extend(results)
        
        for step in self.table_steps['table_footer']:
            results = self._execute_template_step(step, context)
            lines.extend(results)
        
        return '\n'.join(lines)
    
    def _generate_switch_case(self, state_machine: StateMachine) -> str:
        return "/* switch-case方式は関数内で直接生成 */"
    
    def _generate_dictionary_table(self, state_machine: StateMachine) -> str:
        return "/* 辞書方式はハッシュテーブルを使用（C言語では非推奨） */"
    
    def _generate_table_driven_process(self, state_machine: StateMachine) -> str:
        self._log_debug("Generating table-driven process (data-driven)")
        
        lines = []
        context = self._build_context(state_machine)
        
        for step in self.process_steps:
            executor = self.step_executors.get(step['action'])
            if executor:
                results = executor(step, context)
                lines.extend(results)
        
        return '\n'.join(lines)
    
    def _generate_switch_case_process(self, state_machine: StateMachine) -> str:
        self._log_debug("Generating switch-case process")
        
        lines = []
        context = self._build_context(state_machine)
        
        lines.append(self.process_templates['func_comment'])
        
        func_name = context['func_name']
        lines.append(f"STATE_t {func_name}(")
        lines.append("    STATE_t current_state,")
        lines.append("    EVENT_t event,")
        lines.append("    SystemContext_t *ctx")
        lines.append(")")
        lines.append("{")
        lines.append("    STATE_t next_state = current_state;")
        lines.append("")
        lines.append("    if (ctx == NULL) {")
        lines.append(f"        {context['log_error']}(\"NULL pointer: ctx\");")
        lines.append("        return current_state;")
        lines.append("    }")
        lines.append("")
        lines.append("    switch (current_state) {")
        
        # 修正: states 辞書の values() を使用
        for state in state_machine.states.values():
            state_name = self.naming.create_enum_value("STATE", state.name)
            lines.append(f"        case {state_name}:")
            lines.append("            switch (event) {")
            
            for event in state_machine.events.values():
                event_name = self.naming.create_enum_value("EVENT", event.name)
                # 修正: state.name と event.name を文字列として渡す
                transitions = state_machine.get_transitions_for_cell(state.name, event.name)
                
                lines.append(f"                case {event_name}:")
                
                if transitions and len(transitions) > 0:
                    transition = transitions[0]
                    target_state = self.naming.create_enum_value("STATE", transition.target)
                    
                    if transition.condition:
                        condition_func = self._get_condition_function_name(transition)
                        lines.append(f"                    if ({condition_func}(ctx)) {{")
                        if transition.action:
                            action_func = self._get_action_function_name(transition)
                            lines.append(f"                        {action_func}(ctx);")
                        lines.append(f"                        next_state = {target_state};")
                        lines.append(f"                        {context['log_info']}(\"Transition: %d -> %d\", current_state, next_state);")
                        lines.append("                    }")
                    else:
                        if transition.action:
                            action_func = self._get_action_function_name(transition)
                            lines.append(f"                    {action_func}(ctx);")
                        lines.append(f"                    next_state = {target_state};")
                        lines.append(f"                    {context['log_info']}(\"Transition: %d -> %d\", current_state, next_state);")
                else:
                    lines.append("                    /* No transition */")
                
                lines.append("                    break;")
            
            lines.append("                default:")
            lines.append("                    break;")
            lines.append("            }")
            lines.append("            break;")
        
        lines.append("        default:")
        lines.append("            break;")
        lines.append("    }")
        lines.append("")
        lines.append("    return next_state;")
        lines.append("}")
        
        return '\n'.join(lines)
    
    def _get_condition_function_name(self, transition: Transition) -> str:
        if transition.condition:
            prefix = self.templates.FUNCTION_NAMES['condition_prefix']
            return f"{prefix}_{self.naming.to_pascal_case(transition.condition)}"
        return "NULL"
    
    def _get_action_function_name(self, transition: Transition) -> str:
        if transition.action:
            prefix = self.templates.FUNCTION_NAMES['action_prefix']
            return f"{prefix}_{self.naming.to_pascal_case(transition.action)}"
        return "NULL"
    
    def generate_transition_table(self, table_type: str, state_machine: StateMachine) -> str:
        generator = self.table_generators.get(table_type)
        if generator:
            return generator(state_machine)
        raise ValueError(f"Unknown table type: {table_type}")
    
    def generate_process_function(self, process_type: str, state_machine: StateMachine) -> str:
        generator = self.process_generators.get(process_type)
        if generator:
            return generator(state_machine)
        raise ValueError(f"Unknown process type: {process_type}")
    
    def generate_all_transitions(self, state_machine: StateMachine, 
                                table_type: str = 'array',
                                process_type: str = 'table_driven') -> str:
        lines = []
        lines.append(self.generate_transition_table(table_type, state_machine))
        lines.append("")
        lines.append(self.generate_process_function(process_type, state_machine))
        return '\n'.join(lines)