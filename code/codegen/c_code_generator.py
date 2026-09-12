# codegen/c_code_generator.py
"""
Cコード生成メインクラス
（ステップテーブル駆動版・13ファイル対応・複数層対応・by_layer対応）

設計方針:
  - ファイルごとの生成手順は FILE_STEPS テーブルで宣言
  - 各ステップは step_executors 辞書で実行関数に紐付け
  - _run_steps() / _run_steps_multi() がステップ列を順に実行
  - 条件付きステップは 'when' 述語で宣言的に表現
  - ファイル間ディスパッチは FILE_DISPATCH 辞書で管理
  - フォルダ構成は FOLDER_STRUCTURE_RESOLVERS で解決
  - スーパーインクルード / スーパーループは常に生成
  - 複数層は generate_all_layers() で一括生成
  - by_layer では層固有ファイルを層フォルダに分離
"""

import sys
import os
import logging
from typing import Dict, Callable, List, Any, Optional, Tuple
from datetime import datetime

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

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
    from .config import CodeGenerationConfig, ConfigManager
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
    from config import CodeGenerationConfig, ConfigManager

logger = logging.getLogger(__name__)


class CCodeGenerator:
    """Cコード生成メインクラス
       （ステップテーブル駆動・13ファイル対応・複数層対応）"""

    # ================================================================
    # 【テーブル①】ファイル別ステップ定義
    # ================================================================
    FILE_STEPS: Dict[str, List[Dict[str, Any]]] = {
        'statable_types.h': [
            {'action': 'file_header',
             'filename': 'statable_types.h'},
            {'action': 'blank'},
            {'action': 'guard_start'},
            {'action': 'include_section', 'key': 'types'},
            {'action': 'section_header', 'key': 'type_defs'},
            {'action': 'blank'},
            {'action': 'enums'},
            {'action': 'blank'},
            {'action': 'custom_types',
             'when': lambda c: bool(c['global_defs'].custom_types)},
            {'action': 'section_header', 'key': 'system_structs'},
            {'action': 'blank'},
            {'action': 'struct', 'kind': 'system_data'},
            {'action': 'blank'},
            {'action': 'struct', 'kind': 'event_flags'},
            {'action': 'blank'},
            {'action': 'struct', 'kind': 'system_context'},
            {'action': 'blank'},
            {'action': 'section_header', 'key': 'var_macros'},
            {'action': 'blank'},
            {'action': 'var_macros'},
            {'action': 'blank'},
            {'action': 'guard_end'},
        ],
        'statable_transitions.h': [
            {'action': 'file_header',
             'filename': 'statable_transitions.h'},
            {'action': 'blank'},
            {'action': 'guard_start'},
            {'action': 'include_section',
             'key': 'transitions_h'},
            {'action': 'section_header',
             'key': 'function_decls'},
            {'action': 'blank'},
            {'action': 'state_machine_decl'},
            {'action': 'blank'},
            {'action': 'guard_end'},
        ],
        'statable_transitions.c': [
            {'action': 'file_header',
             'filename': 'statable_transitions.c'},
            {'action': 'blank'},
            {'action': 'include_section',
             'key': 'transitions_c'},
            {'action': 'section_header',
             'key': 'transition_table'},
            {'action': 'blank'},
            {'action': 'cell_prototypes'},
            {'action': 'blank'},
            {'action': 'transition_table'},
            {'action': 'blank'},
            {'action': 'cell_functions'},
            {'action': 'blank'},
            {'action': 'section_header',
             'key': 'transition_func'},
            {'action': 'blank'},
            {'action': 'process_func'},
        ],
        'statable_role_functions.h': [
            {'action': 'file_header',
             'filename': 'statable_role_functions.h'},
            {'action': 'blank'},
            {'action': 'guard_start'},
            {'action': 'include_section',
             'key': 'role_functions_h'},
            {'action': 'section_header',
             'key': 'role_functions'},
            {'action': 'blank'},
            {'action': 'role_decls'},
            {'action': 'blank'},
            {'action': 'guard_end'},
        ],
        'statable_role_functions.c': [
            {'action': 'file_header',
             'filename': 'statable_role_functions.c'},
            {'action': 'blank'},
            {'action': 'include_section',
             'key': 'role_functions_c'},
            {'action': 'section_header', 'key': 'role_impl'},
            {'action': 'blank'},
            {'action': 'role_impls'},
        ],
        'statable_init.c': [
            {'action': 'file_header',
             'filename': 'statable_init.c'},
            {'action': 'blank'},
            {'action': 'include_section', 'key': 'init_c'},
            {'action': 'section_header', 'key': 'init_func'},
            {'action': 'blank'},
            {'action': 'init_func'},
        ],
        'statable_event_queue.c': [
            {'action': 'file_header',
             'filename': 'statable_event_queue.c'},
            {'action': 'blank'},
            {'action': 'include_section',
             'key': 'event_queue_c'},
            {'action': 'event_queues'},
        ],
        'statable_interrupt.c': [
            {'action': 'file_header',
             'filename': 'statable_interrupt.c'},
            {'action': 'blank'},
            {'action': 'include_section',
             'key': 'interrupt_c'},
            {'action': 'interrupts'},
        ],
        'statable_timer.c': [
            {'action': 'file_header',
             'filename': 'statable_timer.c'},
            {'action': 'blank'},
            {'action': 'include_section', 'key': 'timer_c'},
            {'action': 'section_header', 'key': 'type_defs'},
            {'action': 'blank'},
            {'action': 'timer_struct'},
            {'action': 'blank'},
            {'action': 'section_header', 'key': 'init_func'},
            {'action': 'blank'},
            {'action': 'timer_init'},
            {'action': 'blank'},
            {'action': 'section_header',
             'key': 'transition_func'},
            {'action': 'blank'},
            {'action': 'timer_update'},
        ],
        'osal.h': [
            {'action': 'osal_header'},
        ],
        'osal.c': [
            {'action': 'osal_source'},
        ],
        # スーパーインクルード（extern 宣言含む）
        'statable_all.h': [
            {'action': 'super_include_header'},
            {'action': 'blank'},
            {'action': 'super_include_guard_start'},
            {'action': 'blank'},
            {'action': 'super_include_common'},
            {'action': 'blank'},
            {'action': 'super_include_layer'},
            {'action': 'blank'},
            {'action': 'super_include_project'},
            {'action': 'blank'},
            {'action': 'super_include_extern_vars'},
            {'action': 'blank'},
            {'action': 'super_include_extern_funcs'},
            {'action': 'blank'},
            {'action': 'super_include_external',
             'when': lambda c: (
                 c['config'].external_includes_in_super
                 and bool(c['config'].external_includes)
             )},
            {'action': 'blank',
             'when': lambda c: (
                 c['config'].external_includes_in_super
                 and bool(c['config'].external_includes)
             )},
            {'action': 'super_include_user'},
            {'action': 'blank'},
            {'action': 'super_include_guard_end'},
        ],
    }

    # ================================================================
    # 【テーブル②】struct 種類 → 生成メソッド ディスパッチ
    # ================================================================
    STRUCT_KIND_DISPATCH: Dict[str, str] = {
        'system_data':    'system_data',
        'event_flags':    'event_flags',
        'system_context': 'system_context',
    }

    # ================================================================
    # 【テーブル③】ファイル名 → 生成メソッド ディスパッチ
    # ================================================================
    FILE_DISPATCH: Dict[str, str] = {
        'statable_types.h':
            '_generate_types_header',
        'statable_transitions.h':
            '_generate_transitions_header',
        'statable_transitions.c':
            '_generate_transitions_source',
        'statable_role_functions.h':
            '_generate_role_functions_header',
        'statable_role_functions.c':
            '_generate_role_functions_source',
        'statable_init.c':
            '_generate_init_source',
        'statable_event_queue.c':
            '_generate_event_queue_source',
        'statable_interrupt.c':
            '_generate_interrupt_source',
        'statable_timer.c':
            '_generate_timer_source',
        'osal.h':
            '_generate_osal_header',
        'osal.c':
            '_generate_osal_source',
        'statable_all.h':
            '_generate_super_include',
    }

    # ================================================================
    # 【テーブル④】ファイル名 → カテゴリ（by_type 用）
    # ================================================================
    FILE_CATEGORY: Dict[str, str] = {
        'statable_types.h':          'include',
        'statable_transitions.h':    'include',
        'statable_role_functions.h': 'include',
        'statable_transitions.c':    'src',
        'statable_role_functions.c': 'src',
        'statable_init.c':           'src',
        'statable_event_queue.c':    'src',
        'statable_interrupt.c':      'src',
        'statable_timer.c':          'src',
        'osal.h':                    'common',
        'osal.c':                    'common',
    }

    # ================================================================
    # 【テーブル⑤】folder_structure → パス解決メソッド
    # ================================================================
    FOLDER_STRUCTURE_RESOLVERS: Dict[str, str] = {
        'flat':     '_resolve_path_flat',
        'by_type':  '_resolve_path_by_type',
        'by_layer': '_resolve_path_by_layer',
    }

    # ================================================================
    # 【テーブル⑥】★ by_layer 用ファイル分類
    # ================================================================
    LAYER_SPECIFIC_FILES = {
        'statable_types.h',
        'statable_transitions.h',
        'statable_transitions.c',
        'statable_role_functions.h',
        'statable_role_functions.c',
    }

    COMMON_FILES = {
        'statable_init.c',
        'statable_event_queue.c',
        'statable_interrupt.c',
        'statable_timer.c',
        'osal.h',
        'osal.c',
        'statable_all.h',
    }

    # ================================================================
    # コンストラクタ
    # ================================================================
    def __init__(self,
                 config: Optional[CodeGenerationConfig] = None):
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

        # 設定
        self.config_manager = ConfigManager()
        if config:
            self.config_manager.set_config(config)
        self.config = self.config_manager.get_config()

        self.generation_date = (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        # 生成中のみ有効な共有ライブラリ
        self._current_role_function_library = None

        # スーパーループファイル名
        self.super_loop_filename = (
            f"{self.config.project_name}_run.c"
        )

        # インスタンスレベルにコピー
        self.FILE_STEPS = dict(self.__class__.FILE_STEPS)
        self.FILE_DISPATCH = dict(self.__class__.FILE_DISPATCH)
        self.FILE_CATEGORY = dict(self.__class__.FILE_CATEGORY)

        # スーパーループを動的登録
        self.FILE_STEPS[self.super_loop_filename] = [
            {'action': 'super_loop_header'},
            {'action': 'blank'},
            {'action': 'super_loop_include'},
            {'action': 'blank'},
            {'action': 'super_loop_context_var'},
            {'action': 'blank'},
            {'action': 'super_loop_state_var'},
            {'action': 'blank'},
            {'action': 'super_loop_init_func'},
            {'action': 'blank'},
            {'action': 'super_loop_run_func'},
        ]
        self.FILE_DISPATCH[self.super_loop_filename] = \
            '_generate_super_loop'
        self.FILE_CATEGORY[self.super_loop_filename] = 'src'

        # ===== ファイル生成メタ =====
        self.file_generators: Dict[str, Dict] = {
            'statable_types.h': {
                'description': '状態遷移システムの型定義',
                'guard_name': 'STATABLE_TYPES_H',
            },
            'statable_transitions.h': {
                'description': '状態遷移関数宣言',
                'guard_name': 'STATABLE_TRANSITIONS_H',
            },
            'statable_transitions.c': {
                'description': '状態遷移ロジック',
                'guard_name': None,
            },
            'statable_role_functions.h': {
                'description': 'ロール関数宣言',
                'guard_name': 'STATABLE_ROLE_FUNCTIONS_H',
            },
            'statable_role_functions.c': {
                'description': 'ロール関数実装',
                'guard_name': None,
            },
            'statable_init.c': {
                'description': '初期化処理',
                'guard_name': None,
            },
            'statable_event_queue.c': {
                'description': 'イベントキュー実装',
                'guard_name': None,
            },
            'statable_interrupt.c': {
                'description': '割り込み処理ISR',
                'guard_name': None,
            },
            'statable_timer.c': {
                'description': 'タイマ処理',
                'guard_name': None,
            },
            'osal.h': {
                'description': 'OSALヘッダ',
                'guard_name': 'OSAL_H',
            },
            'osal.c': {
                'description': 'OSALソース',
                'guard_name': None,
            },
            'statable_all.h': {
                'description': 'StaTable 一括インクルード',
                'guard_name': 'STATABLE_ALL_H',
            },
            # ★ スーパーループ
            self.super_loop_filename: {
                'description': 'ステートマシン スーパーループ',
                'guard_name': None,
            },
        }

        # ===== インクルード定義 =====
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
            'init_c': ['#include "statable_types.h"'],
            'event_queue_c': ['#include "statable_types.h"'],
            'interrupt_c': ['#include "statable_types.h"'],
            'timer_c': ['#include "statable_types.h"'],
        }

        # ===== ステップ実行辞書 =====
        self.step_executors: Dict[str, Callable] = {
            # 共通
            'file_header':        self._step_file_header,
            'blank':              self._step_blank,
            'guard_start':        self._step_guard_start,
            'guard_end':          self._step_guard_end,
            'include_section':    self._step_include_section,
            'section_header':     self._step_section_header,
            # 型定義
            'enums':              self._step_enums,
            'custom_types':       self._step_custom_types,
            'struct':             self._step_struct,
            'var_macros':         self._step_var_macros,
            # 遷移
            'state_machine_decl': self._step_state_machine_decl,
            'cell_prototypes':    self._step_cell_prototypes,
            'transition_table':   self._step_transition_table,
            'cell_functions':     self._step_cell_functions,
            'process_func':       self._step_process_func,
            # ロール
            'role_decls':         self._step_role_decls,
            'role_impls':         self._step_role_impls,
            # 初期化
            'init_func':          self._step_init_func,
            # イベントキュー / 割り込み
            'event_queues':       self._step_event_queues,
            'interrupts':         self._step_interrupts,
            # タイマ
            'timer_struct':       self._step_timer_struct,
            'timer_init':         self._step_timer_init,
            'timer_update':       self._step_timer_update,
            # OSAL
            'osal_header':        self._step_osal_header,
            'osal_source':        self._step_osal_source,
            # スーパーインクルード
            'super_include_header':      self._step_super_include_header,
            'super_include_guard_start': self._step_super_include_guard_start,
            'super_include_common':      self._step_super_include_common,
            'super_include_layer':       self._step_super_include_layer,
            'super_include_project':     self._step_super_include_project,
            'super_include_extern_vars': self._step_super_include_extern_vars,
            'super_include_extern_funcs': self._step_super_include_extern_funcs,
            'super_include_external':    self._step_super_include_external,
            'super_include_user':        self._step_super_include_user,
            'super_include_guard_end':   self._step_super_include_guard_end,
            # スーパーループ
            'super_loop_header':      self._step_super_loop_header,
            'super_loop_include':     self._step_super_loop_include,
            'super_loop_context_var': self._step_super_loop_context_var,
            'super_loop_state_var':   self._step_super_loop_state_var,
            'super_loop_init_func':   self._step_super_loop_init_func,
            'super_loop_run_func':    self._step_super_loop_run_func,
        }

    # ================================================================
    # ログ
    # ================================================================
    def _log_debug(self, message, level='debug'):
        log_func = getattr(logger, level, logger.debug)
        log_func(message)

    # ================================================================
    # 設定関連
    # ================================================================
    def get_config(self) -> CodeGenerationConfig:
        return self.config

    def set_config(self, config: CodeGenerationConfig):
        self.config_manager.set_config(config)
        self.config = self.config_manager.get_config()

    def update_config(self, **kwargs):
        self.config_manager.update(**kwargs)
        self.config = self.config_manager.get_config()

    def reset_config(self):
        self.config_manager.reset()
        self.config = self.config_manager.get_config()

    # ================================================================
    # ヘルパー
    # ================================================================
    def _get_states_list(self, state_machine):
        return list(state_machine.states.values())

    def _get_events_list(self, state_machine):
        return list(state_machine.events.values())

    def _get_role_functions_list(self, state_machine):
        """state_machine と共有ライブラリをマージした
           ロール関数リストを返す"""
        funcs = dict(state_machine.role_functions)
        lib = self._current_role_function_library
        if lib is not None:
            for rf in lib.list_all():
                name = getattr(rf, 'name', None)
                if name and name not in funcs:
                    funcs[name] = rf
        return list(funcs.values())

    def _get_layer_name(self, state_machine) -> str:
        """層名を取得（未設定なら空文字）"""
        return getattr(state_machine, 'layer_name', '') or ''

    def _get_initial_state(self, state_machine) -> str:
        """初期状態名を取得（未設定なら 'Idle'）"""
        initial = getattr(state_machine, 'initial_state', None)
        if not initial:
            initial = getattr(state_machine, 'initial', None)
        return initial or 'Idle'

    def _generate_section_header(self, section_key):
        line = self.strings['section_line']
        title = self.templates.SECTION_HEADERS.get(
            section_key, ''
        )
        return f"{line}\n *  {title}\n{line}"

    def _generate_file_header(self, filename, description=""):
        return (
            f"/**\n"
            f" * @file    {filename}\n"
            f" * @brief   {description}\n"
            f" *\n"
            f" * @note    {self.strings['auto_generated']}\n"
            f" *          - {self.strings['no_edit']}\n"
            f" *          - {self.strings['edit_in_statable']}\n"
            f" *\n"
            f" * @date    {self.generation_date}\n"
            f" */"
        )

    def _generate_include_guard_start(self, guard_name):
        return f"#ifndef {guard_name}\n#define {guard_name}\n"

    def _generate_include_guard_end(self, guard_name):
        return f"#endif /* {guard_name} */"

    def _generate_include_section(self, include_key):
        lines = [self._generate_section_header('include'), ""]
        for header in self.include_headers.get(include_key, []):
            lines.append(header)
        lines.append("")
        return '\n'.join(lines)

    # ================================================================
    # ★ 複数層サポート
    # ================================================================
    def _normalize_layers(self, layers) -> List[Tuple[str, StateMachine]]:
        """
        layers を正規化

        Args:
            layers: List[(name, sm)] or List[sm] or StateMachine

        Returns:
            List[(layer_name, state_machine)]（優先度昇順）
        """
        if layers is None:
            return []

        # 単一 StateMachine
        if isinstance(layers, StateMachine):
            name = self._get_layer_name(layers)
            return [(name, layers)]

        # リスト
        result = []
        for item in layers:
            if isinstance(item, tuple) and len(item) == 2:
                name, sm = item
            elif isinstance(item, StateMachine):
                name = self._get_layer_name(item)
                sm = item
            else:
                continue
            # 層名未設定ならタブ名をデフォルトに
            if not self._get_layer_name(sm) and name:
                sm.layer_name = name
            result.append((name, sm))

        # 優先度昇順でソート
        result.sort(
            key=lambda x: getattr(x[1], 'layer_priority', 5)
        )
        return result

    def _setup_layer_generators(self, state_machine):
        """state_machine.layer_name を各サブジェネレータに反映"""
        layer_name = self._get_layer_name(state_machine)
        for name, gen in [
            ('enum_gen',       self.enum_gen),
            ('transition_gen', self.transition_gen),
            ('role_func_gen',  self.role_func_gen),
            ('struct_gen',     self.struct_gen),
        ]:
            if hasattr(gen, 'set_layer'):
                gen.set_layer(layer_name)

    # ================================================================
    # フォルダ構成解決
    # ================================================================
    def _resolve_output_path(self, filename: str,
                             layer_name: str = '') -> str:
        """
        ファイル名から保存先の相対パスを返す

        ★ filename に既にパス区切り（'/' or '\\'）が含まれる場合は
          そのまま使用（by_layer の "Driver/statable_types.h" 等）
        """
        # 既にパス形式 → そのまま
        if '/' in filename or '\\' in filename:
            return filename

        # スーパーインクルード特別扱い
        if filename == 'statable_all.h':
            return self._resolve_super_include_path(layer_name)

        structure = self.config.folder_structure
        resolver_name = self.FOLDER_STRUCTURE_RESOLVERS.get(
            structure, '_resolve_path_flat'
        )
        resolver = getattr(self, resolver_name,
                           self._resolve_path_flat)
        return resolver(filename, layer_name)
    def _resolve_super_include_path(self, layer_name: str = '') -> str:
        """スーパーインクルードの保存パスを解決"""
        fname = self.config.super_include_file
        structure = self.config.folder_structure

        if structure == 'flat':
            return fname
        elif structure == 'by_type':
            return os.path.join(
                self.config.super_include_dir, fname
            )
        elif structure == 'by_layer':
            # ★ layer_name があれば層フォルダ、なければルート
            if layer_name:
                return os.path.join(layer_name, fname)
            return fname
        return fname

    def _resolve_path_flat(self, filename: str,
                           layer_name: str = '') -> str:
        """flat: 全ファイルを同じフォルダに"""
        return filename

    def _resolve_path_by_type(self, filename: str,
                              layer_name: str = '') -> str:
        """by_type: include / src / common に分類"""
        category = self.FILE_CATEGORY.get(filename, '')
        if category == 'include':
            return os.path.join(
                self.config.include_dir_name, filename
            )
        elif category == 'src':
            return os.path.join(
                self.config.source_dir_name, filename
            )
        elif category == 'common':
            return os.path.join(
                self.config.common_dir_name, filename
            )
        return filename

    def _resolve_path_by_layer(self, filename: str,
                               layer_name: str = '') -> str:
        """
        by_layer: 層名フォルダに格納

        generate_all_layers が by_layer の場合、
        キーに既に "layer/filename" が含まれるため、
        通常この関数は呼ばれない（_resolve_output_path の早期 return）。

        単層 generate_all で by_layer を使う場合のフォールバック。
        """
        if not layer_name:
            return filename
        # 層固有ファイルのみフォルダ分け
        if filename in self.LAYER_SPECIFIC_FILES:
            return os.path.join(layer_name, filename)
        return filename

    # ================================================================
    # 汎用ステップ実行（単層）
    # ================================================================
    def _run_steps(self, filename,
                   state_machine, global_defs) -> str:
        """ステップテーブルに従って1ファイルを生成（単層）"""
        return self._run_steps_multi(
            filename,
            [(self._get_layer_name(state_machine), state_machine)],
            global_defs
        )

    # ================================================================
    # 汎用ステップ実行（複数層）
    # ================================================================
    def _run_steps_multi(self, filename,
                         layers: List[Tuple[str, StateMachine]],
                         global_defs) -> str:
        """複数層対応ステップ実行"""
        if not layers:
            return ""

        file_config = self.file_generators[filename]
        steps = self.FILE_STEPS.get(filename, [])
        context = {
            'layers':        layers,
            'state_machine': layers[0][1],
            'global_defs':   global_defs,
            'file_config':   file_config,
            'filename':      filename,
            'config':        self.config,
            'is_multi':      len(layers) > 1,
        }
        parts: List[str] = []
        for step in steps:
            when = step.get('when')
            if when is not None and not when(context):
                continue
            action = step.get('action', '')
            executor = self.step_executors.get(action)
            if executor is None:
                self._log_debug(
                    f"Unknown step action: {action}", 'warning'
                )
                continue
            result = executor(step, context)
            if result is None:
                continue
            if isinstance(result, list):
                parts.extend(result)
            else:
                parts.append(result)
        return '\n'.join(parts)

    # ================================================================
    # ステップ実行関数群（複数層対応）
    # ================================================================
    def _step_file_header(self, step, ctx):
        filename = step.get('filename', ctx['filename'])
        desc = ctx['file_config'].get('description', '')
        return [self._generate_file_header(filename, desc)]

    def _step_blank(self, step, ctx):
        return [""]

    def _step_guard_start(self, step, ctx):
        guard = ctx['file_config'].get('guard_name')
        if not guard:
            return []
        return [self._generate_include_guard_start(guard)]

    def _step_guard_end(self, step, ctx):
        guard = ctx['file_config'].get('guard_name')
        if not guard:
            return []
        return [self._generate_include_guard_end(guard)]

    def _step_include_section(self, step, ctx):
        return [self._generate_include_section(
            step.get('key', '')
        )]

    def _step_section_header(self, step, ctx):
        return [self._generate_section_header(
            step.get('key', '')
        )]

    def _step_enums(self, step, ctx):
        """複数層の enum を連結"""
        gd = ctx['global_defs']
        layers = ctx['layers']
        results = []
        for layer_name, sm in layers:
            self._setup_layer_generators(sm)
            enum_code = self.enum_gen.generate_all_enums(
                self._get_states_list(sm),
                self._get_events_list(sm),
                gd.flags,
            )
            if enum_code:
                results.append(enum_code)
        if not results:
            return ['']
        return ['\n'.join(results)]

    def _step_custom_types(self, step, ctx):
        gd = ctx['global_defs']
        result: List[str] = [
            self._generate_section_header('custom_types'),
            "",
        ]
        for custom_type in gd.custom_types:
            result.append(self.struct_gen.generate_struct(
                'custom_type', custom_type
            ))
            result.append("")
        return result

    def _step_struct(self, step, ctx):
        """struct 種類を辞書引きでディスパッチ"""
        kind = step.get('kind', '')
        method_name = self.STRUCT_KIND_DISPATCH.get(kind)
        if method_name is None:
            return []
        # struct_gen.generate_struct の第一引数は kind
        return [self.struct_gen.generate_struct(
            kind, ctx['global_defs']
        )]

    def _step_var_macros(self, step, ctx):
        return [self.variable_gen.generate_all_macros(
            ctx['global_defs']
        )]

    def _step_state_machine_decl(self, step, ctx):
        """複数層の StateMachine_Process 宣言を連結"""
        layers = ctx['layers']
        results = []
        for layer_name, sm in layers:
            layer = self._get_layer_name(sm)
            if layer:
                state_type = f"STATE_{layer}_t"
                event_type = f"EVENT_{layer}_t"
                func_name = f"StateMachine_Process_{layer}"
            else:
                state_type = "STATE_t"
                event_type = "EVENT_t"
                func_name = "StateMachine_Process"

            results.append('\n'.join([
                "/**",
                " * @brief  状態遷移処理",
                " * @param  current_state  現在の状態",
                " * @param  event          発生したイベント",
                " * @param  ctx            システムコンテキストポインタ",
                " * @return 遷移後の状態",
                " */",
                f"{state_type} {func_name}(",
                f"    {state_type} current_state,",
                f"    {event_type} event,",
                "    SystemContext_t *ctx",
                ");",
            ]))
        return ['\n'.join(results)] if results else ['']

    def _step_cell_prototypes(self, step, ctx):
        """複数層のセル関数前方宣言"""
        layers = ctx['layers']
        results = []
        for layer_name, sm in layers:
            self._setup_layer_generators(sm)
            proto = (self.transition_gen
                     .generate_transition_cell_prototypes(sm))
            if proto:
                results.append(proto)
        return ['\n'.join(results)] if results else ['']

    def _step_transition_table(self, step, ctx):
        """複数層の遷移テーブル"""
        layers = ctx['layers']
        results = []
        for layer_name, sm in layers:
            self._setup_layer_generators(sm)
            tbl = self.transition_gen.generate_transition_table(
                sm, table_type=ctx['config'].table_type,
            )
            if tbl:
                results.append(tbl)
        return ['\n'.join(results)] if results else ['']

    def _step_cell_functions(self, step, ctx):
        """複数層のセル関数本体"""
        layers = ctx['layers']
        results = []
        for layer_name, sm in layers:
            self._setup_layer_generators(sm)
            funcs = (self.transition_gen
                     .generate_transition_cell_functions(sm))
            if funcs:
                results.append(funcs)
        return ['\n'.join(results)] if results else ['']

    def _step_process_func(self, step, ctx):
        """複数層の StateMachine_Process"""
        layers = ctx['layers']
        results = []
        for layer_name, sm in layers:
            self._setup_layer_generators(sm)
            func = self.transition_gen.generate_process_function(
                sm,
                generation_style=ctx['config'].generation_style,
            )
            if func:
                results.append(func)
        return ['\n'.join(results)] if results else ['']

    def _step_role_decls(self, step, ctx):
        """複数層のロール関数宣言"""
        layers = ctx['layers']
        results = []
        for layer_name, sm in layers:
            self._setup_layer_generators(sm)
            decls = (self.role_func_gen
                     .generate_all_declarations(
                         self._get_role_functions_list(sm)))
            if decls:
                results.append(decls)
        return ['\n'.join(results)] if results else ['']

    def _step_role_impls(self, step, ctx):
        """複数層のロール関数実装"""
        layers = ctx['layers']
        results = []
        for layer_name, sm in layers:
            self._setup_layer_generators(sm)
            impls = (self.role_func_gen
                     .generate_all_implementations(
                         self._get_role_functions_list(sm),
                         state_machine=sm,
                         global_defs=ctx['global_defs'],
                     ))
            if impls:
                results.append(impls)
        return ['\n'.join(results)] if results else ['']

    def _step_init_func(self, step, ctx):
        return [self.variable_gen.generate_init_function(
            ctx['global_defs']
        )]

    def _step_event_queues(self, step, ctx):
        gd = ctx['global_defs']
        queues = getattr(gd, 'event_queues', [])
        if not queues:
            return ["/* イベントキュー定義なし */"]
        result: List[str] = [
            self._generate_section_header('type_defs'),
            "",
        ]
        for queue in queues:
            result.append(
                self.event_queue_gen.generate_all_code(queue)
            )
            result.append("")
        return result

    def _step_interrupts(self, step, ctx):
        gd = ctx['global_defs']
        interrupts = getattr(gd, 'interrupts', [])
        if not interrupts:
            return ["/* 割り込み処理定義なし */"]
        result: List[str] = [
            self._generate_section_header('transition_func'),
            "",
        ]
        for handler in interrupts:
            result.append(
                self.interrupt_gen.generate_isr(handler)
            )
            result.append("")
        return result

    def _step_timer_struct(self, step, ctx):
        return [self.timer_gen.generate_struct(
            ctx['global_defs']
        )]

    def _step_timer_init(self, step, ctx):
        return [self.timer_gen.generate_init_function(
            ctx['global_defs']
        )]

    def _step_timer_update(self, step, ctx):
        return [self.timer_gen.generate_update_function(
            ctx['global_defs']
        )]

    def _step_osal_header(self, step, ctx):
        return [self.osal_gen.generate_header(
            self.config.os_type
        )]

    def _step_osal_source(self, step, ctx):
        return [self.osal_gen.generate_source(
            self.config.os_type
        )]

    # ================================================================
    # スーパーインクルード ステップ（複数層対応）
    # ================================================================
    def _step_super_include_header(self, step, ctx):
        T = self.templates.SUPER_INCLUDE_TEMPLATES
        fname = self.config.super_include_file
        return [T['file_comment'].format(filename=fname)]

    def _step_super_include_guard_start(self, step, ctx):
        T = self.templates.SUPER_INCLUDE_TEMPLATES
        return [T['guard_start'].rstrip('\n')]

    def _step_super_include_guard_end(self, step, ctx):
        T = self.templates.SUPER_INCLUDE_TEMPLATES
        return [T['guard_end']]

    def _step_super_include_common(self, step, ctx):
        T = self.templates.SUPER_INCLUDE_TEMPLATES
        layers = ctx['layers']
        structure = self.config.folder_structure

        parts = [T['common_section']]

        if structure == 'by_layer':
            # 層フォルダ内の statable_types.h を include
            for layer_name, sm in layers:
                layer = self._get_layer_name(sm)
                if layer:
                    parts.append(
                        f'#include "{layer}/statable_types.h"'
                    )
        else:
            parts.append('#include "statable_types.h"')
        return parts

    def _step_super_include_layer(self, step, ctx):
        T = self.templates.SUPER_INCLUDE_TEMPLATES
        layers = ctx['layers']
        structure = self.config.folder_structure

        parts = [T['layer_section']]

        if structure == 'by_layer':
            for layer_name, sm in layers:
                layer = self._get_layer_name(sm)
                if layer:
                    parts.append(
                        f'#include "{layer}/statable_transitions.h"'
                    )
                    parts.append(
                        f'#include "{layer}/statable_role_functions.h"'
                    )
        else:
            parts.append('#include "statable_transitions.h"')
            parts.append('#include "statable_role_functions.h"')
        return parts

    def _step_super_include_project(self, step, ctx):
        T = self.templates.SUPER_INCLUDE_TEMPLATES
        return [
            T['project_section'],
            '#include "osal.h"',
        ]

    def _step_super_include_extern_vars(self, step, ctx):
        """全層の extern 変数宣言"""
        T = self.templates.SUPER_INCLUDE_TEMPLATES
        layers = ctx['layers']
        parts = [T['extern_var_section'], T['extern_context']]

        for layer_name, sm in layers:
            layer = self._get_layer_name(sm)
            if layer:
                parts.append(T['extern_state'].format(layer=layer))
            else:
                parts.append(T['extern_state_nolayer'])
        return parts

    def _step_super_include_extern_funcs(self, step, ctx):
        """スーパーループ関数の extern 宣言"""
        T = self.templates.SUPER_INCLUDE_TEMPLATES
        project = self.config.project_name
        return [
            T['extern_func_section'],
            T['extern_init'].format(project_name=project),
            T['extern_run'].format(project_name=project),
        ]

    def _step_super_include_external(self, step, ctx):
        T = self.templates.SUPER_INCLUDE_TEMPLATES
        result = [T['external_section']]
        for inc in self.config.external_includes:
            inc = inc.strip()
            if not inc:
                continue
            if inc.startswith('#include'):
                result.append(inc)
            else:
                result.append(f'#include "{inc}"')
        return result

    def _step_super_include_user(self, step, ctx):
        T = self.templates.SUPER_INCLUDE_TEMPLATES
        return [
            T['user_section'],
            T['user_marker_start'],
            T['user_marker_end'],
        ]

    # ================================================================
    # スーパーループ ステップ（複数層対応）
    # ================================================================
    def _step_super_loop_header(self, step, ctx):
        T = self.templates.SUPER_LOOP_TEMPLATES
        project = self.config.project_name
        return [T['file_comment'].format(project_name=project)]

    def _step_super_loop_include(self, step, ctx):
        return [self.templates.SUPER_LOOP_TEMPLATES['include']]

    def _step_super_loop_context_var(self, step, ctx):
        return [self.templates.SUPER_LOOP_TEMPLATES['context_var']]

    def _step_super_loop_state_var(self, step, ctx):
        """全層の state 変数定義"""
        layers = ctx['layers']
        T = self.templates.SUPER_LOOP_TEMPLATES
        parts = []
        for layer_name, sm in layers:
            layer = self._get_layer_name(sm)
            if layer:
                parts.append(T['state_var'].format(layer=layer))
            else:
                parts.append(T['state_var_nolayer'])
        return parts

    def _step_super_loop_init_func(self, step, ctx):
        """全層の初期化"""
        layers = ctx['layers']
        project = self.config.project_name
        T = self.templates.SUPER_LOOP_TEMPLATES

        parts = [
            T['init_func_comment'],
            T['init_func_signature'].format(project_name=project),
            T['init_func_open'],
            T['init_context'],
        ]
        for layer_name, sm in layers:
            layer = self._get_layer_name(sm)
            initial = self._get_initial_state(sm)
            if layer:
                parts.append(T['init_state'].format(
                    layer=layer, initial=initial,
                ))
            else:
                parts.append(T['init_state_nolayer'].format(
                    initial=initial,
                ))
        parts.append(T['init_func_close'])
        return parts

    def _step_super_loop_run_func(self, step, ctx):
        """全層の run ブロック（優先度順）"""
        layers = ctx['layers']
        project = self.config.project_name
        T = self.templates.SUPER_LOOP_TEMPLATES

        parts = [
            T['run_func_comment'],
            T['run_func_signature'].format(project_name=project),
            T['run_func_open'],
            T['run_while'],
        ]
        for layer_name, sm in layers:
            layer = self._get_layer_name(sm)
            priority = getattr(sm, 'layer_priority', 5)
            if layer:
                block = T['run_block'].format(
                    layer=layer,
                    priority=priority,
                )
            else:
                block = T['run_block_nolayer']
            # インデント調整
            indented = '        ' + block.replace(
                '\n', '\n        ')
            parts.append(indented)
        parts.append(T['run_while_close'])
        parts.append(T['run_func_close'])
        return parts

    # ================================================================
    # ファイル生成メソッド
    # ================================================================
    def _generate_types_header(self, sm, gd):
        return self._run_steps('statable_types.h', sm, gd)

    def _generate_transitions_header(self, sm, gd):
        return self._run_steps('statable_transitions.h', sm, gd)

    def _generate_transitions_source(self, sm, gd):
        return self._run_steps('statable_transitions.c', sm, gd)

    def _generate_role_functions_header(self, sm, gd):
        return self._run_steps('statable_role_functions.h', sm, gd)

    def _generate_role_functions_source(self, sm, gd):
        return self._run_steps('statable_role_functions.c', sm, gd)

    def _generate_init_source(self, sm, gd):
        return self._run_steps('statable_init.c', sm, gd)

    def _generate_event_queue_source(self, sm, gd):
        return self._run_steps('statable_event_queue.c', sm, gd)

    def _generate_interrupt_source(self, sm, gd):
        return self._run_steps('statable_interrupt.c', sm, gd)

    def _generate_timer_source(self, sm, gd):
        return self._run_steps('statable_timer.c', sm, gd)

    def _generate_osal_header(self, sm, gd):
        return self._run_steps('osal.h', sm, gd)

    def _generate_osal_source(self, sm, gd):
        return self._run_steps('osal.c', sm, gd)

    # ★ スーパーインクルード
    def _generate_super_include(self, sm, gd):
        return self._run_steps('statable_all.h', sm, gd)

    def _generate_super_loop(self, sm, gd):
        return self._run_steps(self.super_loop_filename, sm, gd)

    # ================================================================
    # 公開メソッド（単層）
    # ================================================================
    def generate_all(self, state_machine, global_defs,
                     role_function_library=None):
        """単層の全コード生成（後方互換）"""
        self._setup_layer_generators(state_machine)

        prev = self._current_role_function_library
        self._current_role_function_library = role_function_library
        try:
            generated_files = {}
            for filename in self.file_generators.keys():
                # スーパーインクルードのスキップ判定
                if (filename == 'statable_all.h'
                        and not self.config.generate_super_include):
                    continue
                method_name = self.FILE_DISPATCH.get(filename)
                if method_name is None:
                    continue
                method = getattr(self, method_name, None)
                if method is None:
                    continue
                generated_files[filename] = method(
                    state_machine, global_defs
                )
            return generated_files
        finally:
            self._current_role_function_library = prev

    def generate_file(self, filename, state_machine, global_defs,
                      role_function_library=None):
        """特定ファイルの生成（単層）"""
        self._setup_layer_generators(state_machine)

        prev = self._current_role_function_library
        self._current_role_function_library = role_function_library
        try:
            if filename not in self.file_generators:
                raise ValueError(f"Unknown file: {filename}")
            return self._run_steps(
                filename, state_machine, global_defs
            )
        finally:
            self._current_role_function_library = prev

    # ================================================================
    # ★ 公開メソッド（複数層）
    # ================================================================
    def generate_all_layers(self, layers, global_defs,
                            role_function_library=None):
        """複数層のコード生成

        Args:
            layers: List[(layer_name, StateMachine)] または
                    StateMachine 単体（後方互換）
            global_defs: GlobalDefinitions
            role_function_library: 共有ライブラリ（省略可）

        Returns:
            Dict[str, str]: 生成ファイル辞書
            - by_type / flat: 通常のファイル名
            - by_layer: "layer/filename" 形式（層固有）
                        + 通常のファイル名（共通）
        """
        # 正規化 + 優先度順ソート
        norm_layers = self._normalize_layers(layers)
        if not norm_layers:
            return {}

        structure = self.config.folder_structure

        if structure == 'by_layer':
            return self._generate_all_by_layer(
                norm_layers, global_defs, role_function_library
            )

        # by_type / flat: 全層を1ファイルにマージ（既存）
        primary_sm = norm_layers[0][1]
        self._setup_layer_generators(primary_sm)

        prev = self._current_role_function_library
        self._current_role_function_library = role_function_library
        try:
            generated_files = {}
            for filename in self.file_generators.keys():
                if (filename == 'statable_all.h'
                        and not self.config.generate_super_include):
                    continue
                generated_files[filename] = self._run_steps_multi(
                    filename, norm_layers, global_defs
                )
            return generated_files
        finally:
            self._current_role_function_library = prev

    def _generate_all_by_layer(self, layers, global_defs,
                               role_function_library):
        """
        by_layer 専用生成

        層固有ファイル: 各層を単独で generate_all → "layer/filename"
        共通ファイル: 複数層で _run_steps_multi → "filename"
        """
        self._log_debug(
            f"_generate_all_by_layer: {len(layers)} layers"
        )
        generated_files = {}

        prev = self._current_role_function_library
        self._current_role_function_library = role_function_library
        try:
            # === 1. 層固有ファイル ===
            for layer_name, sm in layers:
                if not layer_name:
                    # 層名なし → ルート直下
                    self._setup_layer_generators(sm)
                    layer_files = {}
                    for fname in self.LAYER_SPECIFIC_FILES:
                        method_name = self.FILE_DISPATCH.get(fname)
                        if method_name is None:
                            continue
                        method = getattr(self, method_name, None)
                        if method is None:
                            continue
                        layer_files[fname] = method(sm, global_defs)
                    generated_files.update(layer_files)
                    continue

                self._setup_layer_generators(sm)
                for fname in self.LAYER_SPECIFIC_FILES:
                    method_name = self.FILE_DISPATCH.get(fname)
                    if method_name is None:
                        continue
                    method = getattr(self, method_name, None)
                    if method is None:
                        continue
                    content = method(sm, global_defs)
                    # "layer/filename" 形式でキー登録
                    generated_files[
                        f"{layer_name}/{fname}"
                    ] = content

            # === 2. 共通ファイル ===
            common_names = list(self.COMMON_FILES) + [
                self.super_loop_filename
            ]
            for fname in common_names:
                # スーパーインクルードのスキップ判定
                if (fname == 'statable_all.h'
                        and not self.config.generate_super_include):
                    continue
                content = self._run_steps_multi(
                    fname, layers, global_defs
                )
                generated_files[fname] = content

            return generated_files
        finally:
            self._current_role_function_library = prev

    # ================================================================
    # 保存（フォルダ構成反映）
    # ================================================================
    def save_generated_code(self, generated_files, output_dir,
                            layer_name: str = ''):
        """生成コードの保存（マージなし）"""
        saved_files = []
        os.makedirs(output_dir, exist_ok=True)

        for filename, content in generated_files.items():
            # フォルダ構成反映
            rel_path = self._resolve_output_path(
                filename, layer_name
            )
            filepath = os.path.join(output_dir, rel_path)

            # 親ディレクトリを作成
            parent = os.path.dirname(filepath)
            if parent:
                os.makedirs(parent, exist_ok=True)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            saved_files.append(filepath)

        return saved_files

    def save_generated_code_with_merge(self, generated_files,
                                       output_dir,
                                       layer_name: str = ''):
        """ユーザーコードを保持しながら保存"""
        merged_files = self.merger.merge_all_files(
            generated_files, output_dir,
            path_resolver=self._resolve_output_path,
            layer_name=layer_name,
        )
        return self.save_generated_code(
            merged_files, output_dir, layer_name
        )

    def get_merge_summary(self, generated_files, output_dir,
                          layer_name: str = ''):
        """マージ結果のサマリー"""
        summary = {}
        for filename, content in generated_files.items():
            rel_path = self._resolve_output_path(
                filename, layer_name
            )
            existing_path = os.path.join(output_dir, rel_path)
            if os.path.exists(existing_path):
                with open(existing_path, 'r',
                          encoding='utf-8') as f:
                    existing_content = f.read()
                summary[filename] = (
                    self.merger.get_user_code_summary(
                        existing_content
                    )
                )
            else:
                summary[filename] = {
                    'file_user_code': 0,
                    'func_user_codes': 0,
                    'file_tail_user_code': 0,
                }
        return summary

    def get_generated_file_list(self):
        """生成ファイル一覧を取得"""
        return list(self.file_generators.keys())