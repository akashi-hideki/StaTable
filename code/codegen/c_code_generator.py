# codegen/c_code_generator.py
"""
Cコード生成メインクラス（完全データ駆動版）
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
    from .code_templates import CodeTemplates
except ImportError:
    from type_mapper import CTypeMapper
    from naming_convention import CNamingConvention
    from struct_generator import CStructGenerator
    from enum_generator import CEnumGenerator
    from transition_generator import TransitionGenerator
    from role_function_generator import RoleFunctionGenerator
    from variable_generator import VariableGenerator
    from code_templates import CodeTemplates

logger = logging.getLogger(__name__)


class CCodeGenerator:
    """Cコード生成メインクラス（完全データ駆動）"""
    
    def __init__(self):
        self.mapper = CTypeMapper()
        self.naming = CNamingConvention()
        self.struct_gen = CStructGenerator()
        self.enum_gen = CEnumGenerator()
        self.transition_gen = TransitionGenerator()
        self.role_func_gen = RoleFunctionGenerator()
        self.variable_gen = VariableGenerator()
        self.templates = CodeTemplates()
        self.strings = self.templates.STRINGS
        self.formats = self.templates.FORMATS
        
        self.generation_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # ===== ファイル生成設定辞書 =====
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
        }
        
        # ===== インクルードファイル定義辞書 =====
        self.include_headers: Dict[str, List[str]] = {
            'types': [
                '#include <stdint.h>',
                '#include <stdbool.h>',
                '#include <string.h>',
            ],
            'transitions_h': [
                '#include "statable_types.h"',
            ],
            'transitions_c': [
                '#include "statable_transitions.h"',
                '#include "statable_role_functions.h"',
            ],
            'role_functions_h': [
                '#include "statable_types.h"',
            ],
            'role_functions_c': [
                '#include "statable_role_functions.h"',
            ],
            'init_c': [
                '#include "statable_types.h"',
            ],
        }
    
    def _log_debug(self, message: str, level: str = 'debug'):
        """デバッグログ出力"""
        log_func = getattr(logger, level, logger.debug)
        log_func(message)
    
    # ===== ヘルパーメソッド =====
    def _get_states_list(self, state_machine: StateMachine) -> List:
        """状態リストを取得（辞書→リスト）"""
        return list(state_machine.states.values())
    
    def _get_events_list(self, state_machine: StateMachine) -> List:
        """イベントリストを取得（辞書→リスト）"""
        return list(state_machine.events.values())
    
    def _get_role_functions_list(self, state_machine: StateMachine) -> List:
        """ロール関数リストを取得（辞書→リスト）"""
        return list(state_machine.role_functions.values())
    
    # ===== セクションヘッダ生成 =====
    def _generate_section_header(self, section_key: str) -> str:
        """セクションヘッダ生成"""
        line = self.strings['section_line']
        title = self.templates.SECTION_HEADERS.get(section_key, '')
        return self.formats['section_header'].format(line=line, title=title)
    
    # ===== ファイルヘッダ生成 =====
    def _generate_file_header(self, filename: str, description: str = "") -> str:
        """ファイルヘッダ生成"""
        return self.formats['file_header'].format(
            filename=filename,
            description=description,
            auto_generated=self.strings['auto_generated'],
            no_edit=self.strings['no_edit'],
            edit_in_statable=self.strings['edit_in_statable'],
            date=self.generation_date,
        )
    
    # ===== インクルードガード生成 =====
    def _generate_include_guard_start(self, guard_name: str) -> str:
        """インクルードガード開始生成"""
        return self.formats['include_guard_start'].format(guard_macro=guard_name)
    
    def _generate_include_guard_end(self, guard_name: str) -> str:
        """インクルードガード終了生成"""
        return self.formats['include_guard_end'].format(guard_macro=guard_name)
    
    # ===== インクルードセクション生成 =====
    def _generate_include_section(self, include_key: str) -> str:
        """インクルードセクション生成"""
        lines = []
        lines.append(self._generate_section_header('include'))
        lines.append("")
        
        headers = self.include_headers.get(include_key, [])
        for header in headers:
            lines.append(header)
        
        lines.append("")
        return '\n'.join(lines)
    
    # ===== 型定義ヘッダ生成 =====
    def _generate_types_header(self, state_machine: StateMachine, 
                              global_defs: GlobalDefinitions) -> str:
        """型定義ヘッダ生成"""
        self._log_debug("Generating types header")
        
        lines = []
        file_config = self.file_generators['statable_types.h']
        
        # ファイルヘッダ
        lines.append(self._generate_file_header('statable_types.h', file_config['description']))
        lines.append("")
        
        # インクルードガード
        lines.append(self._generate_include_guard_start(file_config['guard_name']))
        
        # インクルード
        lines.append(self._generate_include_section('types'))
        
        # 型定義
        lines.append(self._generate_section_header('type_defs'))
        lines.append("")
        
        # 列挙型（辞書→リスト変換）
        lines.append(self.enum_gen.generate_all_enums(
            self._get_states_list(state_machine),
            self._get_events_list(state_machine),
            global_defs.flags
        ))
        lines.append("")
        
        # ユーザー定義型
        if global_defs.custom_types:
            lines.append(self._generate_section_header('custom_types'))
            lines.append("")
            for custom_type in global_defs.custom_types:
                lines.append(self.struct_gen.generate_struct('custom_type', custom_type))
                lines.append("")
        
        # システム構造体
        lines.append(self._generate_section_header('system_structs'))
        lines.append("")
        lines.append(self.struct_gen.generate_struct('system_data', global_defs))
        lines.append("")
        lines.append(self.struct_gen.generate_struct('event_flags', global_defs))
        lines.append("")
        lines.append(self.struct_gen.generate_struct('system_context', global_defs))
        lines.append("")
        
        # 変数アクセスマクロ
        lines.append(self._generate_section_header('var_macros'))
        lines.append("")
        lines.append(self.variable_gen.generate_all_macros(global_defs))
        lines.append("")
        
        # インクルードガード終了
        lines.append(self._generate_include_guard_end(file_config['guard_name']))
        
        return '\n'.join(lines)
    
    # ===== 遷移関数ヘッダ生成 =====
    def _generate_transitions_header(self, state_machine: StateMachine,
                                    global_defs: GlobalDefinitions) -> str:
        """状態遷移関数ヘッダ生成"""
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
    def _generate_transitions_source(self, state_machine: StateMachine,
                                    global_defs: GlobalDefinitions) -> str:
        """状態遷移関数ソース生成"""
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
    def _generate_role_functions_header(self, state_machine: StateMachine,
                                       global_defs: GlobalDefinitions) -> str:
        """ロール関数ヘッダ生成"""
        self._log_debug("Generating role functions header")
        
        lines = []
        file_config = self.file_generators['statable_role_functions.h']
        
        lines.append(self._generate_file_header('statable_role_functions.h', file_config['description']))
        lines.append("")
        lines.append(self._generate_include_guard_start(file_config['guard_name']))
        lines.append(self._generate_include_section('role_functions_h'))
        lines.append(self._generate_section_header('role_functions'))
        lines.append("")
        # 修正: 辞書→リスト変換
        lines.append(self.role_func_gen.generate_all_declarations(
            self._get_role_functions_list(state_machine)
        ))
        lines.append("")
        lines.append(self._generate_include_guard_end(file_config['guard_name']))
        
        return '\n'.join(lines)
    
    # ===== ロール関数ソース生成 =====
    def _generate_role_functions_source(self, state_machine: StateMachine,
                                       global_defs: GlobalDefinitions) -> str:
        """ロール関数ソース生成"""
        self._log_debug("Generating role functions source")
        
        lines = []
        file_config = self.file_generators['statable_role_functions.c']
        
        lines.append(self._generate_file_header('statable_role_functions.c', file_config['description']))
        lines.append("")
        lines.append(self._generate_include_section('role_functions_c'))
        lines.append(self._generate_section_header('role_impl'))
        lines.append("")
        # 修正: 辞書→リスト変換
        lines.append(self.role_func_gen.generate_all_implementations(
            self._get_role_functions_list(state_machine)
        ))
        
        return '\n'.join(lines)
    
    # ===== 初期化ソース生成 =====
    def _generate_init_source(self, state_machine: StateMachine,
                             global_defs: GlobalDefinitions) -> str:
        """初期化ソース生成"""
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
    
    # ===== 公開メソッド =====
    def generate_all(self, state_machine: StateMachine, 
                    global_defs: GlobalDefinitions) -> Dict[str, str]:
        """全コード生成（辞書駆動）"""
        self._log_debug("Generating all code")
        
        generated_files = {}
        
        for filename, config in self.file_generators.items():
            self._log_debug(f"Generating: {filename}")
            method = config['method']
            generated_files[filename] = method(state_machine, global_defs)
        
        return generated_files
    
    def generate_file(self, filename: str, state_machine: StateMachine,
                     global_defs: GlobalDefinitions) -> str:
        """特定ファイルの生成"""
        self._log_debug(f"Generating file: {filename}")
        
        if filename in self.file_generators:
            method = self.file_generators[filename]['method']
            return method(state_machine, global_defs)
        raise ValueError(f"Unknown file: {filename}")
    
    def save_generated_code(self, generated_files: Dict[str, str], 
                           output_dir: str) -> List[str]:
        """生成コードの保存"""
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