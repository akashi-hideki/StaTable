# codegen/c_code_generator.py
"""
Cコード生成メインクラス（完全データ駆動版・11ファイル対応）
"""

import sys
import os
import logging
from typing import Dict, Callable, List, Any
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from statable.state_machine import StateMachine
from statable.global_defs import GlobalDefinitions

try:
    from .type_mapper import CTypeMapper
    from .naming_convention import CNamingConvention
    from .struct_generator import CStructGenerator
    from .enum_generator import CEnumGenerator
    from .transition_generator import TransitionGenerator
    from .role_function_generator import RoleFunctionGenerator
    from .variable_generator import VariableGenerator
    from .event_queue_generator import EventQueueGenerator
    from .interrupt_generator import InterruptGenerator
    from .timer_generator import TimerGenerator
    from .osal_generator import OSALGenerator
    from .code_templates import CodeTemplates
    from .code_merger import CodeMerger
except ImportError:
    from type_mapper import CTypeMapper
    from naming_convention import CNamingConvention
    from struct_generator import CStructGenerator
    from enum_generator import CEnumGenerator
    from transition_generator import TransitionGenerator
    from role_function_generator import RoleFunctionGenerator
    from variable_generator import VariableGenerator
    from event_queue_generator import EventQueueGenerator
    from interrupt_generator import InterruptGenerator
    from timer_generator import TimerGenerator
    from osal_generator import OSALGenerator
    from code_templates import CodeTemplates
    from code_merger import CodeMerger

logger = logging.getLogger(__name__)


class CCodeGenerator:
    """Cコード生成メインクラス（完全データ駆動・11ファイル対応）"""
    
    def __init__(self):
        self.mapper = CTypeMapper()
        self.naming = CNamingConvention()
        self.struct_gen = CStructGenerator()
        self.enum_gen = CEnumGenerator()
        self.transition_gen = TransitionGenerator()
        self.role_func_gen = RoleFunctionGenerator()
        self.variable_gen = VariableGenerator()
        self.event_queue_gen = EventQueueGenerator()
        self.interrupt_gen = InterruptGenerator()
        self.timer_gen = TimerGenerator()
        self.osal_gen = OSALGenerator()
        self.templates = CodeTemplates()
        self.strings = self.templates.STRINGS
        self.formats = self.templates.FORMATS
        self.merger = CodeMerger()
        
        self.generation_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # ===== ファイル生成設定辞書（11ファイル） =====
        self.file_generators: Dict[str, Dict] = {
            'statable_types.h': {
                'method': self._generate_types_header,
                'description': '状態遷移システムの型定義',
                'guard_name': 'STATABLE_TYPES_H',
            },
            'statable_transitions.h': {
                'method': self._generate_transitions_header,
                'description': '状態遷移関数宣言',
                'guard_name': 'STATABLE_TRANSITIONS_H',
            },
            'statable_transitions.c': {
                'method': self._generate_transitions_source,
                'description': '状態遷移ロジック',
                'guard_name': None,
            },
            'statable_role_functions.h': {
                'method': self._generate_role_functions_header,
                'description': 'ロール関数宣言',
                'guard_name': 'STATABLE_ROLE_FUNCTIONS_H',
            },
            'statable_role_functions.c': {
                'method': self._generate_role_functions_source,
                'description': 'ロール関数実装',
                'guard_name': None,
            },
            'statable_init.c': {
                'method': self._generate_init_source,
                'description': '初期化処理',
                'guard_name': None,
            },
            'statable_event_queue.c': {
                'method': self._generate_event_queue_source,
                'description': 'イベントキュー実装',
                'guard_name': None,
            },
            'statable_interrupt.c': {
                'method': self._generate_interrupt_source,
                'description': '割り込み処理ISR',
                'guard_name': None,
            },
            'statable_timer.c': {
                'method': self._generate_timer_source,
                'description': 'タイマ処理',
                'guard_name': None,
            },
            'osal.h': {
                'method': self._generate_osal_header,
                'description': 'OSALヘッダ',
                'guard_name': 'OSAL_H',
            },
            'osal.c': {
                'method': self._generate_osal_source,
                'description': 'OSALソース',
                'guard_name': None,
            },
        }
        
        # ===== インクルードファイル定義辞書 =====
        self.include_headers: Dict[str, List[str]] = {
            'types': ['#include <stdint.h>', '#include <stdbool.h>', '#include <string.h>'],
            'transitions_h': ['#include "statable_types.h"'],
            'transitions_c': ['#include "statable_transitions.h"', '#include "statable_role_functions.h"'],
            'role_functions_h': ['#include "statable_types.h"'],
            'role_functions_c': ['#include "statable_role_functions.h"'],
            'init_c': ['#include "statable_types.h"'],
            'event_queue_c': ['#include "statable_types.h"'],
            'interrupt_c': ['#include "statable_types.h"'],
            'timer_c': ['#include "statable_types.h"'],
        }
    
    def _log_debug(self, message, level='debug'):
        log_func = getattr(logger, level, logger.debug)
        log_func(message)
    
    # ===== ヘルパーメソッド =====
    def _get_states_list(self, state_machine):
        return list(state_machine.states.values())
    
    def _get_events_list(self, state_machine):
        return list(state_machine.events.values())
    
    def _get_role_functions_list(self, state_machine):
        return list(state_machine.role_functions.values())
    
    def _generate_section_header(self, section_key):
        line = self.strings['section_line']
        title = self.templates.SECTION_HEADERS.get(section_key, '')
        return f"{line}\n *  {title}\n{line}"
    
    def _generate_file_header(self, filename, description=""):
        return (f"/**\n"
                f" * @file    {filename}\n"
                f" * @brief   {description}\n"
                f" *\n"
                f" * @note    {self.strings['auto_generated']}\n"
                f" *          - {self.strings['no_edit']}\n"
                f" *          - {self.strings['edit_in_statable']}\n"
                f" *\n"
                f" * @date    {self.generation_date}\n"
                f" */")
    
    def _generate_include_guard_start(self, guard_name):
        return f"#ifndef {guard_name}\n#define {guard_name}\n"
    
    def _generate_include_guard_end(self, guard_name):
        return f"#endif /* {guard_name} */"
    
    def _generate_include_section(self, include_key):
        lines = []
        lines.append(self._generate_section_header('include'))
        lines.append("")
        for header in self.include_headers.get(include_key, []):
            lines.append(header)
        lines.append("")
        return '\n'.join(lines)
    
    # ===== 型定義ヘッダ生成 =====
    def _generate_types_header(self, state_machine, global_defs):
        self._log_debug("Generating types header")
        lines = []
        file_config = self.file_generators['statable_types.h']
        
        lines.append(self._generate_file_header('statable_types.h', file_config['description']))
        lines.append("")
        lines.append(self._generate_include_guard_start(file_config['guard_name']))
        lines.append(self._generate_include_section('types'))
        lines.append(self._generate_section_header('type_defs'))
        lines.append("")
        lines.append(self.enum_gen.generate_all_enums(
            self._get_states_list(state_machine),
            self._get_events_list(state_machine),
            global_defs.flags
        ))
        lines.append("")
        
        if global_defs.custom_types:
            lines.append(self._generate_section_header('custom_types'))
            lines.append("")
            for custom_type in global_defs.custom_types:
                lines.append(self.struct_gen.generate_struct('custom_type', custom_type))
                lines.append("")
        
        lines.append(self._generate_section_header('system_structs'))
        lines.append("")
        lines.append(self.struct_gen.generate_struct('system_data', global_defs))
        lines.append("")
        lines.append(self.struct_gen.generate_struct('event_flags', global_defs))
        lines.append("")
        lines.append(self.struct_gen.generate_struct('system_context', global_defs))
        lines.append("")
        lines.append(self._generate_section_header('var_macros'))
        lines.append("")
        lines.append(self.variable_gen.generate_all_macros(global_defs))
        lines.append("")
        lines.append(self._generate_include_guard_end(file_config['guard_name']))
        
        return '\n'.join(lines)
    
    # ===== 遷移関数ヘッダ生成 =====
    def _generate_transitions_header(self, state_machine, global_defs):
        self._log_debug("Generating transitions header")
        lines = []
        file_config = self.file_generators['statable_transitions.h']
        
        lines.append(self._generate_file_header('statable_transitions.h', file_config['description']))
        lines.append("")
        lines.append(self._generate_include_guard_start(file_config['guard_name']))
        lines.append(self._generate_include_section('transitions_h'))
        lines.append(self._generate_section_header('function_decls'))
        lines.append("")
        lines.append("/**")
        lines.append(" * @brief  状態遷移処理")
        lines.append(" * @param  current_state  現在の状態")
        lines.append(" * @param  event          発生したイベント")
        lines.append(" * @param  ctx            システムコンテキストポインタ")
        lines.append(" * @return 遷移後の状態")
        lines.append(" */")
        lines.append("STATE_t StateMachine_Process(")
        lines.append("    STATE_t current_state,")
        lines.append("    EVENT_t event,")
        lines.append("    SystemContext_t *ctx")
        lines.append(");")
        lines.append("")
        lines.append(self._generate_include_guard_end(file_config['guard_name']))
        
        return '\n'.join(lines)
    
    # ===== 遷移関数ソース生成 =====
    def _generate_transitions_source(self, state_machine, global_defs):
        self._log_debug("Generating transitions source")
        lines = []
        file_config = self.file_generators['statable_transitions.c']
        
        lines.append(self._generate_file_header('statable_transitions.c', file_config['description']))
        lines.append("")
        lines.append(self._generate_include_section('transitions_c'))
        lines.append(self._generate_section_header('transition_table'))
        lines.append("")
        lines.append(self.transition_gen.generate_transition_table('array', state_machine))
        lines.append("")
        lines.append(self._generate_section_header('transition_func'))
        lines.append("")
        lines.append(self.transition_gen.generate_process_function('table_driven', state_machine))
        
        return '\n'.join(lines)
    
    # ===== ロール関数ヘッダ生成 =====
    def _generate_role_functions_header(self, state_machine, global_defs):
        self._log_debug("Generating role functions header")
        lines = []
        file_config = self.file_generators['statable_role_functions.h']
        
        lines.append(self._generate_file_header('statable_role_functions.h', file_config['description']))
        lines.append("")
        lines.append(self._generate_include_guard_start(file_config['guard_name']))
        lines.append(self._generate_include_section('role_functions_h'))
        lines.append(self._generate_section_header('role_functions'))
        lines.append("")
        lines.append(self.role_func_gen.generate_all_declarations(
            self._get_role_functions_list(state_machine)
        ))
        lines.append("")
        lines.append(self._generate_include_guard_end(file_config['guard_name']))
        
        return '\n'.join(lines)
    
    # ===== ロール関数ソース生成 =====
    def _generate_role_functions_source(self, state_machine, global_defs):
        self._log_debug("Generating role functions source")
        lines = []
        file_config = self.file_generators['statable_role_functions.c']
        
        lines.append(self._generate_file_header('statable_role_functions.c', file_config['description']))
        lines.append("")
        lines.append(self._generate_include_section('role_functions_c'))
        lines.append(self._generate_section_header('role_impl'))
        lines.append("")
        lines.append(self.role_func_gen.generate_all_implementations(
            self._get_role_functions_list(state_machine)
        ))
        
        return '\n'.join(lines)
    
    # ===== 初期化ソース生成 =====
    def _generate_init_source(self, state_machine, global_defs):
        self._log_debug("Generating init source")
        lines = []
        file_config = self.file_generators['statable_init.c']
        
        lines.append(self._generate_file_header('statable_init.c', file_config['description']))
        lines.append("")
        lines.append(self._generate_include_section('init_c'))
        lines.append(self._generate_section_header('init_func'))
        lines.append("")
        lines.append(self.variable_gen.generate_init_function(global_defs))
        
        return '\n'.join(lines)
    
    # ===== イベントキューソース生成 =====
    def _generate_event_queue_source(self, state_machine, global_defs):
        self._log_debug("Generating event queue source")
        lines = []
        file_config = self.file_generators['statable_event_queue.c']
        
        lines.append(self._generate_file_header('statable_event_queue.c', file_config['description']))
        lines.append("")
        lines.append(self._generate_include_section('event_queue_c'))
        
        # イベントキュー構造体
        queues = getattr(global_defs, 'event_queues', [])
        if queues:
            lines.append(self._generate_section_header('type_defs'))
            lines.append("")
            for queue in queues:
                lines.append(self.event_queue_gen.generate_all_code(queue))
                lines.append("")
        else:
            lines.append("/* イベントキュー定義なし */")
        
        return '\n'.join(lines)
    
    # ===== 割り込みソース生成 =====
    def _generate_interrupt_source(self, state_machine, global_defs):
        self._log_debug("Generating interrupt source")
        lines = []
        file_config = self.file_generators['statable_interrupt.c']
        
        lines.append(self._generate_file_header('statable_interrupt.c', file_config['description']))
        lines.append("")
        lines.append(self._generate_include_section('interrupt_c'))
        
        # ISR骨格
        interrupts = getattr(global_defs, 'interrupts', [])
        if interrupts:
            lines.append(self._generate_section_header('transition_func'))
            lines.append("")
            for handler in interrupts:
                lines.append(self.interrupt_gen.generate_isr(handler))
                lines.append("")
        else:
            lines.append("/* 割り込み処理定義なし */")
        
        return '\n'.join(lines)
    
    # ===== タイマソース生成 =====
    def _generate_timer_source(self, state_machine, global_defs):
        self._log_debug("Generating timer source")
        lines = []
        file_config = self.file_generators['statable_timer.c']
        
        lines.append(self._generate_file_header('statable_timer.c', file_config['description']))
        lines.append("")
        lines.append(self._generate_include_section('timer_c'))
        
        # タイマ変数構造体
        lines.append(self._generate_section_header('type_defs'))
        lines.append("")
        lines.append(self.timer_gen.generate_struct(global_defs))
        lines.append("")
        
        # タイマ初期化関数
        lines.append(self._generate_section_header('init_func'))
        lines.append("")
        lines.append(self.timer_gen.generate_init_function(global_defs))
        lines.append("")
        
        lines.append(self._generate_section_header('transition_func'))
        lines.append("")
        lines.append(self.timer_gen.generate_update_function(global_defs))
        
        return '\n'.join(lines)
    
    # ===== OSALヘッダ生成 =====
    def _generate_osal_header(self, state_machine, global_defs):
        """OSALヘッダ生成"""
        self._log_debug("Generating OSAL header")
        return self.osal_gen.generate_header('non_rtos')
    
    # ===== OSALソース生成 =====
    def _generate_osal_source(self, state_machine, global_defs):
        """OSALソース生成"""
        self._log_debug("Generating OSAL source")
        return self.osal_gen.generate_source('non_rtos')
    
    # ===== 公開メソッド =====
    def generate_all(self, state_machine, global_defs):
        """全コード生成（辞書駆動）"""
        self._log_debug("Generating all code")
        generated_files = {}
        for filename, config in self.file_generators.items():
            self._log_debug(f"Generating: {filename}")
            method = config['method']
            generated_files[filename] = method(state_machine, global_defs)
        return generated_files
    
    def generate_file(self, filename, state_machine, global_defs):
        """特定ファイルの生成"""
        self._log_debug(f"Generating file: {filename}")
        if filename in self.file_generators:
            method = self.file_generators[filename]['method']
            return method(state_machine, global_defs)
        raise ValueError(f"Unknown file: {filename}")
    
    def save_generated_code(self, generated_files, output_dir):
        """生成コードの保存（マージなし）"""
        self._log_debug(f"Saving generated code to: {output_dir}")
        saved_files = []
        os.makedirs(output_dir, exist_ok=True)
        for filename, content in generated_files.items():
            filepath = os.path.join(output_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            saved_files.append(filepath)
            self._log_debug(f"Saved: {filepath}")
        return saved_files
    
    def save_generated_code_with_merge(self, generated_files, output_dir):
        """ユーザーコードを保持しながら保存（マージあり）"""
        self._log_debug(f"Merging and saving to: {output_dir}")
        merged_files = self.merger.merge_all_files(generated_files, output_dir)
        return self.save_generated_code(merged_files, output_dir)
    
    def get_merge_summary(self, generated_files, output_dir):
        """マージ結果のサマリーを取得"""
        self._log_debug(f"Getting merge summary for: {output_dir}")
        summary = {}
        for filename, content in generated_files.items():
            existing_path = os.path.join(output_dir, filename)
            if os.path.exists(existing_path):
                with open(existing_path, 'r', encoding='utf-8') as f:
                    existing_content = f.read()
                summary[filename] = self.merger.get_user_code_summary(existing_content)
            else:
                summary[filename] = {'file_user_code': 0, 'func_user_codes': 0}
        return summary
    
    def get_generated_file_list(self):
        """生成ファイル一覧を取得"""
        return list(self.file_generators.keys())