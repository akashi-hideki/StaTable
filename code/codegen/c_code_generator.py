# codegen/c_code_generator.py
"""
Cコード生成メインクラス
（ステップテーブル駆動版・12ファイル対応・設定対応）

設計方針:
  - ファイルごとの生成手順は FILE_STEPS テーブルで宣言
  - 各ステップは step_executors 辞書で実行関数に紐付け
  - _run_steps() がステップ列を順に実行
  - 条件付きステップは 'when' 述語で宣言的に表現
  - ファイル間ディスパッチは FILE_DISPATCH 辞書で管理
  - フォルダ構成は FOLDER_STRUCTURE_RESOLVERS で解決
  - スーパーインクルード statable_all.h は条件付きで生成
"""

import sys
import os
import logging
from typing import Dict, Callable, List, Any, Optional
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
       （ステップテーブル駆動・12ファイル対応・設定対応）"""

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
        # ★ スーパーインクルード
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
            {'action': 'super_include_external',
             'when': lambda c: (
                 c['config'].external_includes_in_super
                 and bool(c['config'].external_includes)
             )},
            # ★ when 条件を削除（常に空行を出力）
            {'action': 'blank'},
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
        # statable_all.h は特別扱い（_resolve_super_include_path）
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

        # ===== ステップ実行辞書（FunctionDictionary） =====
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
            # ★ スーパーインクルード
            'super_include_header':      self._step_super_include_header,
            'super_include_guard_start': self._step_super_include_guard_start,
            'super_include_common':      self._step_super_include_common,
            'super_include_layer':       self._step_super_include_layer,
            'super_include_project':     self._step_super_include_project,
            'super_include_external':    self._step_super_include_external,
            'super_include_user':        self._step_super_include_user,
            'super_include_guard_end':   self._step_super_include_guard_end,
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
        self._log_debug("Config updated")

    def update_config(self, **kwargs):
        self.config_manager.update(**kwargs)
        self.config = self.config_manager.get_config()
        self._log_debug(f"Config updated: {kwargs}")

    def reset_config(self):
        self.config_manager.reset()
        self.config = self.config_manager.get_config()
        self._log_debug("Config reset")

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
            self._log_debug(
                f"_get_role_functions_list: "
                f"merged {len(funcs)} funcs "
                f"(state={len(state_machine.role_functions)}, "
                f"lib={len(lib.list_all())})"
            )
        return list(funcs.values())

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
    # フォルダ構成解決
    # ================================================================
    def _resolve_output_path(self, filename: str,
                             layer_name: str = '') -> str:
        """
        ファイル名から保存先の相対パスを返す

        スーパーインクルード statable_all.h は特別扱い
        """
        # ★ スーパーインクルードの特別扱い
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
        # 未分類は flat
        self._log_debug(
            f"_resolve_path_by_type: "
            f"unclassified '{filename}' -> flat",
            'warning'
        )
        return filename

    def _resolve_path_by_layer(self, filename: str,
                               layer_name: str = '') -> str:
        """
        by_layer: 層名フォルダに格納（将来対応）

        現状はスタブ: layer_name が空なら flat と同じ
        """
        if not layer_name:
            self._log_debug(
                "_resolve_path_by_layer: layer_name is empty, "
                "falling back to flat",
                'warning'
            )
            return filename
        return os.path.join(layer_name, filename)

    # ================================================================
    # 汎用ステップ実行
    # ================================================================
    def _run_steps(self, filename,
                   state_machine, global_defs) -> str:
        """ステップテーブルに従って1ファイルを生成"""
        file_config = self.file_generators[filename]
        steps = self.FILE_STEPS.get(filename, [])
        context = {
            'state_machine': state_machine,
            'global_defs':   global_defs,
            'file_config':   file_config,
            'filename':      filename,
            'config':        self.config,
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
    # ステップ実行関数群
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
        sm = ctx['state_machine']
        gd = ctx['global_defs']
        return [self.enum_gen.generate_all_enums(
            self._get_states_list(sm),
            self._get_events_list(sm),
            gd.flags,
        )]

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
            self._log_debug(
                f"Unknown struct kind: {kind}", 'warning'
            )
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
        return [
            "/**",
            " * @brief  状態遷移処理",
            " * @param  current_state  現在の状態",
            " * @param  event          発生したイベント",
            " * @param  ctx            システムコンテキストポインタ",
            " * @return 遷移後の状態",
            " */",
            "STATE_t StateMachine_Process(",
            "    STATE_t current_state,",
            "    EVENT_t event,",
            "    SystemContext_t *ctx",
            ");",
        ]

    # セル関数の前方宣言
    def _step_cell_prototypes(self, step, ctx):
        return [self.transition_gen
                .generate_transition_cell_prototypes(
                    ctx['state_machine']
                )]

    def _step_transition_table(self, step, ctx):
        # config 反映: table_type
        return [self.transition_gen.generate_transition_table(
            ctx['state_machine'],
            table_type=ctx['config'].table_type,
        )]

    def _step_cell_functions(self, step, ctx):
        return [self.transition_gen
                .generate_transition_cell_functions(
                    ctx['state_machine']
                )]

    def _step_process_func(self, step, ctx):
        # config 反映: generation_style
        return [self.transition_gen.generate_process_function(
            ctx['state_machine'],
            generation_style=ctx['config'].generation_style,
        )]

    def _step_role_decls(self, step, ctx):
        return [self.role_func_gen.generate_all_declarations(
            self._get_role_functions_list(ctx['state_machine'])
        )]

    def _step_role_impls(self, step, ctx):
        return [self.role_func_gen.generate_all_implementations(
            self._get_role_functions_list(ctx['state_machine']),
            state_machine=ctx['state_machine'],
            global_defs=ctx['global_defs'],
        )]

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
    # ★ スーパーインクルード ステップ実行関数群
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
        return [
            T['common_section'],
            '#include "statable_types.h"',
        ]

    def _step_super_include_layer(self, step, ctx):
        T = self.templates.SUPER_INCLUDE_TEMPLATES
        return [
            T['layer_section'],
            '#include "statable_transitions.h"',
            '#include "statable_role_functions.h"',
        ]

    def _step_super_include_project(self, step, ctx):
        T = self.templates.SUPER_INCLUDE_TEMPLATES
        return [
            T['project_section'],
            '#include "osal.h"',
        ]

    def _step_super_include_external(self, step, ctx):
        T = self.templates.SUPER_INCLUDE_TEMPLATES
        result = [T['external_section']]
        for inc in self.config.external_includes:
            inc = inc.strip()
            if not inc:
                continue
            # 既に #include 形式なら、そのまま
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
    # ファイル生成メソッド（すべて _run_steps に委譲）
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

    # ================================================================
    # 公開メソッド
    # ================================================================
    def generate_all(self, state_machine, global_defs,
                     role_function_library=None):
        """全コード生成

        Args:
            state_machine: StateMachine
            global_defs:   GlobalDefinitions
            role_function_library: 共有ライブラリ（省略可）
                - state_machine.role_functions とマージされる
                - 名前衝突時は state_machine 側を優先
        """
        self._log_debug("Generating all code")

        prev = self._current_role_function_library
        self._current_role_function_library = role_function_library
        try:
            generated_files = {}
            for filename in self.file_generators.keys():
                # ★ スーパーインクルードのスキップ判定
                if (filename == 'statable_all.h'
                        and not self.config.generate_super_include):
                    self._log_debug(
                        "Skipping statable_all.h "
                        "(generate_super_include=False)"
                    )
                    continue

                self._log_debug(f"Generating: {filename}")
                method_name = self.FILE_DISPATCH.get(filename)
                if method_name is None:
                    self._log_debug(
                        f"No dispatch for {filename}", 'warning'
                    )
                    continue
                method = getattr(self, method_name, None)
                if method is None:
                    self._log_debug(
                        f"No method {method_name}", 'warning'
                    )
                    continue
                generated_files[filename] = method(
                    state_machine, global_defs
                )
            return generated_files
        finally:
            self._current_role_function_library = prev

    def generate_file(self, filename, state_machine, global_defs,
                      role_function_library=None):
        """特定ファイルの生成"""
        self._log_debug(f"Generating file: {filename}")

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
    # 保存（フォルダ構成反映）
    # ================================================================
    def save_generated_code(self, generated_files, output_dir,
                            layer_name: str = ''):
        """生成コードの保存（マージなし・フォルダ構成反映）"""
        self._log_debug(
            f"Saving generated code to: {output_dir} "
            f"(structure={self.config.folder_structure})"
        )
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
            self._log_debug(f"Saved: {filepath}")

        return saved_files

    def save_generated_code_with_merge(self, generated_files,
                                       output_dir,
                                       layer_name: str = ''):
        """ユーザーコードを保持しながら保存（フォルダ構成反映）"""
        self._log_debug(
            f"Merging and saving to: {output_dir} "
            f"(structure={self.config.folder_structure})"
        )
        # マージ処理にも path_resolver を渡す
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
        """マージ結果のサマリーを取得"""
        self._log_debug(
            f"Getting merge summary for: {output_dir}"
        )
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