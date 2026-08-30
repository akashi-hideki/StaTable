# codegen/role_function_generator.py
"""
ロール関数生成モジュール（完全データ駆動版・修正済み）
"""

import sys
import os
import logging
from typing import Dict, Callable, List, Any, Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from statable.model import RoleFunction

try:
    from .type_mapper import CTypeMapper
    from .naming_convention import CNamingConvention
    from .code_templates import CodeTemplates
except ImportError:
    from type_mapper import CTypeMapper
    from naming_convention import CNamingConvention
    from code_templates import CodeTemplates

logger = logging.getLogger(__name__)


class RoleFunctionGenerator:
    """ロール関数生成クラス（完全データ駆動・修正済み）"""
    
    def __init__(self):
        self.mapper = CTypeMapper()
        self.naming = CNamingConvention()
        self.templates = CodeTemplates()
        self.strings = self.templates.STRINGS
        self.formats = self.templates.FORMATS
        
        self.default_return_values = {
            'void': '', 'bool': 'false', 'int': '0', 'int8': '0',
            'int16': '0', 'int32': '0', 'int64': '0', 'uint': '0',
            'uint8': '0', 'uint16': '0', 'uint32': '0', 'uint64': '0',
            'float': '0.0f', 'double': '0.0', 'char': '0', 'string': 'NULL',
        }
        
        self.function_generators = {
            'declaration': self._generate_declaration,
            'implementation': self._generate_implementation,
            'call': self._generate_call,
        }
        
        self.return_comments = {
            'void': 'なし', 'bool': '条件成立の場合true',
            'default': '実行結果（0: 成功, 0以外: エラー）',
        }
        
        # 修正: ポインタ表記を統一（*の後にスペースなし）
        self.standard_args = [
            ('current_state', 'STATE_t *', '現在の状態ポインタ'),
            ('ctx', 'SystemContext_t *', 'システムコンテキストポインタ'),
        ]
        
        self.declaration_steps = [
            {'action': 'comment'},
            {'action': 'signature'},
            {'action': 'semicolon'},
        ]
        
        self.implementation_steps = [
            {'action': 'comment'},
            {'action': 'signature'},
            {'action': 'open_brace'},
            {'action': 'todo'},
            {'action': 'unused_args'},
            {'action': 'blank'},
            {'action': 'entry_log'},
            {'action': 'blank'},
            {'action': 'return_value'},
            {'action': 'close_brace'},
        ]
        
        self.step_executors = {
            'comment': self._execute_comment_step,
            'signature': self._execute_signature_step,
            'semicolon': self._execute_semicolon_step,
            'open_brace': self._execute_open_brace_step,
            'todo': self._execute_todo_step,
            'unused_args': self._execute_unused_args_step,
            'blank': self._execute_blank_step,
            'entry_log': self._execute_entry_log_step,
            'return_value': self._execute_return_value_step,
            'close_brace': self._execute_close_brace_step,
        }
    
    def _log_debug(self, message, level='debug'):
        log_func = getattr(logger, level, logger.debug)
        log_func(message)
    
    def _has_custom_args(self, func):
        """カスタム引数があるか判定"""
        arg1_type = getattr(func, 'arg1_type', '')
        arg1_name = getattr(func, 'arg1_name', '')
        arg2_type = getattr(func, 'arg2_type', '')
        arg2_name = getattr(func, 'arg2_name', '')
        
        has_arg1 = bool(arg1_type and arg1_name and arg1_name != 'arg1')
        has_arg2 = bool(arg2_type and arg2_name and arg2_name != 'arg2')
        
        return has_arg1, has_arg2
    
    def _collect_args(self, func):
        """引数情報を収集（デフォルト引数を除外）"""
        args = list(self.standard_args)
        
        has_arg1, has_arg2 = self._has_custom_args(func)
        
        if has_arg1:
            args.append((
                self.naming.sanitize_identifier(getattr(func, 'arg1_name', '')),
                self.mapper.map_type(getattr(func, 'arg1_type', 'void')),
                '引数1'
            ))
        
        if has_arg2:
            args.append((
                self.naming.sanitize_identifier(getattr(func, 'arg2_name', '')),
                self.mapper.map_type(getattr(func, 'arg2_type', 'void')),
                '引数2'
            ))
        
        return args
    
    def _generate_args_str(self, func):
        """引数文字列を生成（ポインタ表記修正済み）"""
        indent = self.strings['indent_1']
        args = self._collect_args(func)
        
        arg_lines = []
        for arg_name, arg_type, arg_desc in args:
            # 修正: *の後にスペースを入れない
            if '*' in arg_type:
                # 'STATE_t *' → 'STATE_t *'
                # 'SystemContext_t *' → 'SystemContext_t *'
                # そのまま使用（呼び出し側で正しく結合）
                arg_lines.append(f"{indent}{arg_type}{arg_name}")
            else:
                arg_lines.append(f"{indent}{arg_type} {arg_name}")
        
        return ',\n'.join(arg_lines)
    
    def _generate_function_name(self, func):
        """ロール関数名を生成"""
        prefix = self.templates.FUNCTION_NAMES['role_func_prefix']
        name = getattr(func, 'name', 'unnamed')
        pascal_name = self.naming.to_pascal_case(name)
        return f"{prefix}_{pascal_name}"
    
    def _execute_comment_step(self, step, context):
        """コメントステップ実行"""
        func = context['func']
        lines = ["/**"]
        
        name = getattr(func, 'name', 'unnamed')
        title = getattr(func, 'title', '')
        
        if title and title != f"ロール関数: {name}":
            lines.append(f" * @brief  ロール関数: {title}")
        else:
            lines.append(f" * @brief  ロール関数: {name}")
        
        if getattr(func, 'description', ''):
            lines.append(f" * @note   {func.description}")
        
        args = self._collect_args(func)
        for arg_name, arg_type, arg_desc in args:
            lines.append(f" * @param  {arg_name}  {arg_desc}")
        
        return_type = getattr(func, 'return_type', 'void')
        return_comment = self.return_comments.get(return_type, self.return_comments['default'])
        lines.append(f" * @return {return_comment}")
        lines.append(" */")
        return lines
    
    def _execute_signature_step(self, step, context):
        """シグネチャステップ実行"""
        func = context['func']
        return_type = self.mapper.map_type(getattr(func, 'return_type', 'void'))
        func_name = self._generate_function_name(func)
        return [f"{return_type} {func_name}("]
    
    def _execute_semicolon_step(self, step, context):
        """セミコロンステップ実行"""
        func = context['func']
        args = self._generate_args_str(func)
        return [args, ");"]
    
    def _execute_open_brace_step(self, step, context):
        """開き波括弧ステップ実行"""
        func = context['func']
        args = self._generate_args_str(func)
        return [args, ")", "{"]
    
    def _execute_todo_step(self, step, context):
        return [f"    /* {self.strings['todo']} */"]
    
    def _execute_unused_args_step(self, step, context):
        func = context['func']
        all_args = self._collect_args(func)
        lines = []
        for arg_name, arg_type, arg_desc in all_args:
            lines.append(f"    (void){arg_name};  /* {self.strings['unused_arg']} */")
        return lines
    
    def _execute_blank_step(self, step, context):
        return [""]
    
    def _execute_entry_log_step(self, step, context):
        func = context['func']
        func_name = self._generate_function_name(func)
        return [f"    {self.strings['log_debug']}(\"Enter {func_name}\");"]
    
    def _execute_return_value_step(self, step, context):
        func = context['func']
        return_type = self.mapper.map_type(getattr(func, 'return_type', 'void'))
        if return_type == 'void':
            return ["    return;"]
        default_return = self.default_return_values.get(getattr(func, 'return_type', 'void'), '0')
        return [f"    return {default_return};  /* デフォルト値 */"]
    
    def _execute_close_brace_step(self, step, context):
        return ["}"]
    
    def _generate_declaration(self, func):
        self._log_debug(f"Generating declaration: {getattr(func, 'name', 'unknown')}")
        lines = []
        context = {'func': func}
        for step in self.declaration_steps:
            executor = self.step_executors.get(step['action'])
            if executor:
                lines.extend(executor(step, context))
        return '\n'.join(lines)
    
    def _generate_implementation(self, func):
        self._log_debug(f"Generating implementation: {getattr(func, 'name', 'unknown')}")
        lines = []
        context = {'func': func}
        for step in self.implementation_steps:
            executor = self.step_executors.get(step['action'])
            if executor:
                lines.extend(executor(step, context))
        return '\n'.join(lines)
    
    def _generate_call(self, func):
        self._log_debug(f"Generating call: {getattr(func, 'name', 'unknown')}")
        func_name = self._generate_function_name(func)
        args = ["current_state", "ctx"]
        
        has_arg1, has_arg2 = self._has_custom_args(func)
        if has_arg1:
            args.append(self.naming.sanitize_identifier(getattr(func, 'arg1_name', '')))
        if has_arg2:
            args.append(self.naming.sanitize_identifier(getattr(func, 'arg2_name', '')))
        
        return f"{func_name}({', '.join(args)})"
    
    def generate_function(self, generation_type, func):
        generator = self.function_generators.get(generation_type)
        if generator:
            return generator(func)
        raise ValueError(f"Unknown generation type: {generation_type}")
    
    def generate_all_declarations(self, role_functions):
        lines = []
        for func in role_functions:
            lines.append(self.generate_function('declaration', func))
            lines.append("")
        return '\n'.join(lines)
    
    def generate_all_implementations(self, role_functions):
        lines = []
        for func in role_functions:
            lines.append(self.generate_function('implementation', func))
            lines.append("")
        return '\n'.join(lines)