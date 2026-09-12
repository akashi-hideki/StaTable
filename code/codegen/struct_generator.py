# codegen/struct_generator.py
"""
C構造体コード生成モジュール（多層ステートマシン対応版）

生成する構造体:
  1. custom_type              : ユーザー定義型（変更なし）
  2. system_data              : グローバル変数（変更なし）
  3. event_flags              : イベントフラグ（変更なし）
  4. system_context           : SystemContext_t（★ pending_event 追加）
  5. transition_context       : 共通 TransitionContext_t（★ 新規・基底型）
  6. layer_transition_context : TransitionContext_<Layer>_t（★ 新規・層ごと）
  7. pending_event_macros     : FIRE_EVENT / MAX_CONSECUTIVE_PENDING_EVENTS マクロ（★ 新規）

設計方針:
  - テンプレートは string.Template でデータテーブル化
  - pending_event は uint16_t（層の enum 値を汎用保持）
  - 層ごとの TransitionContext_<Layer>_t と、共通の基底型 TransitionContext_t を両方提供
"""

import sys
import os
import logging
from string import Template
from typing import Dict, Callable, List, Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from statable.global_defs import StructMemberDef, CustomTypeDef, GlobalDefinitions

try:
    from .type_mapper import CTypeMapper
    from .naming_convention import CNamingConvention
    from .code_templates import CodeTemplates
except ImportError:
    from type_mapper import CTypeMapper
    from naming_convention import CNamingConvention
    from code_templates import CodeTemplates

logger = logging.getLogger(__name__)


class CStructGenerator:
    """C構造体コード生成クラス（多層ステートマシン対応）"""

    # ==================================================================
    # 【データテーブル①】共通構造体テンプレート（SystemContext_t 等）
    # ==================================================================
    CONTEXT_TEMPLATES = {
        # --- セクションコメント ---
        'section_comment': Template(
            '/* $title */\n'
            '/* $description */\n'
        ),

        # --- struct 開始 ---
        'struct_start': (
            'typedef struct {\n'
        ),

        # --- data / flags メンバー ---
        'member_data': Template(
            '    $system_data_type data;     /* グローバル変数 */\n'
        ),
        'member_flags': Template(
            '    $event_flags_type flags;    /* イベントフラグ */\n'
        ),

        # --- ★ pending_event メンバー ---
        'member_pending_event': (
            '    uint16_t pending_event;         /* 保留中のイベント */\n'
        ),
        'member_pending_event_valid': (
            '    bool pending_event_valid;       /* 保留イベント有効フラグ */\n'
        ),

        # --- struct 終了（★ }} → } に修正） ---
        'struct_end': Template(
            '} $type_name;\n'
        ),
    }

    # ==================================================================
    # 【データテーブル②】共通マクロテンプレート
    # ==================================================================
    MACRO_TEMPLATES = {
        # --- セクションコメント ---
        'section_comment': (
            '\n'
            '/* ============================================================== */\n'
            '/*  保留イベント制御                                              */\n'
            '/* ============================================================== */\n'
        ),

        # --- FIRE_EVENT マクロ ---
        'fire_event_macro': (
            '\n'
            '/* イベント発火マクロ */\n'
            '/* ロール関数内で使用: FIRE_EVENT(ctx, EVENT_XXX_YYY); */\n'
            '#define FIRE_EVENT(ctx, evt)  do { \\\n'
            '    (ctx)->pending_event = (uint16_t)(evt); \\\n'
            '    (ctx)->pending_event_valid = true; \\\n'
            '} while(0)\n'
        ),

        # --- MAX_CONSECUTIVE_PENDING_EVENTS マクロ ---
        'max_consecutive_macro': (
            '\n'
            '/* 保留イベント連続処理の上限 */\n'
            '/* 無限ループ防止用。ビルド時に -D で上書き可能 */\n'
            '#ifndef MAX_CONSECUTIVE_PENDING_EVENTS\n'
            '#define MAX_CONSECUTIVE_PENDING_EVENTS 16\n'
            '#endif\n'
        ),
    }

    # ==================================================================
    # 【データテーブル③】共通 TransitionContext_t テンプレート
    # ==================================================================
    COMMON_TRANSITION_CONTEXT_TEMPLATES = {
        'comment': (
            '/* 汎用遷移コンテキスト（層を問わない共通ロール関数用） */\n'
            '/* 各層の TransitionContext_<Layer>_t と同じレイアウト */\n'
        ),
        'struct_start': (
            'typedef struct {\n'
        ),
        'member_from_state': (
            '    uint16_t from_state;   /* 遷移元状態（層の enum 値をキャスト） */\n'
        ),
        'member_event': (
            '    uint16_t event;        /* 発生イベント（層の enum 値をキャスト） */\n'
        ),
        'struct_end': (
            '} TransitionContext_t;\n'
        ),
    }

    # ==================================================================
    # 【データテーブル④】層ごとの TransitionContext_<Layer>_t
    # ==================================================================
    LAYER_TRANSITION_CONTEXT_TEMPLATES = {
        'comment': Template(
            '/* $layer層の遷移コンテキスト */\n'
        ),
        'struct_start': (
            'typedef struct {\n'
        ),
        'member_from_state': Template(
            '    $state_type from_state;   /* 遷移元状態 */\n'
        ),
        'member_event': Template(
            '    $event_type event;        /* 発生イベント */\n'
        ),
        # ★ }} → } に修正
        'struct_end': Template(
            '} $type_name;\n'
        ),
    }

    # ==================================================================
    # 【データテーブル⑤】メンバー種別検出
    # ==================================================================
    MEMBER_TYPE_DETECTORS = {
        'bit_field': lambda m: getattr(m, 'bit_width', 0) > 0,
        'array': lambda m: getattr(m, 'array_size', 0) > 0,
        'normal': lambda m: True,
    }

    # ==================================================================
    # 【データテーブル⑥】メンバー生成テンプレート
    # ==================================================================
    MEMBER_TEMPLATES = {
        'bit_field': Template(
            '$indent$c_type $name : $width;\n'
        ),
        'array': Template(
            '$indent$c_type $name[$size];\n'
        ),
        'normal': Template(
            '$indent$c_type $name;\n'
        ),
    }

    # ==================================================================
    # コンストラクタ
    # ==================================================================
    def __init__(self):
        self.mapper = CTypeMapper()
        self.naming = CNamingConvention()
        self.templates = CodeTemplates()
        self.strings = self.templates.STRINGS
        self.formats = self.templates.FORMATS
        self.layer_name: str = ""

    def set_layer(self, layer_name: str):
        """層名を設定（層ごとの TransitionContext 生成用）"""
        self.layer_name = layer_name
        logger.debug(f"CStructGenerator.set_layer: layer_name='{layer_name}'")

    def _log_debug(self, message: str, level: str = 'debug'):
        log_func = getattr(logger, level, logger.debug)
        log_func(message)

    # ==================================================================
    # ヘルパー
    # ==================================================================
    def _detect_member_type(self, member) -> str:
        for member_type, detector in self.MEMBER_TYPE_DETECTORS.items():
            if detector(member):
                return member_type
        return 'normal'

    def _generate_member(self, member) -> str:
        """1メンバーを生成"""
        member_type = self._detect_member_type(member)
        template = self.MEMBER_TEMPLATES[member_type]
        member_name = self.naming.sanitize_identifier(getattr(member, 'name', 'unnamed'))
        c_type = self.mapper.map_type(getattr(member, 'data_type', 'void'))
        indent = self.strings['indent_1']

        if member_type == 'bit_field':
            return template.substitute(
                indent=indent, c_type=c_type,
                name=member_name,
                width=getattr(member, 'bit_width', 0),
            )
        elif member_type == 'array':
            return template.substitute(
                indent=indent, c_type=c_type,
                name=member_name,
                size=getattr(member, 'array_size', 0),
            )
        else:
            return template.substitute(
                indent=indent, c_type=c_type, name=member_name,
            )

    # ==================================================================
    # 1. ユーザー定義型（custom_type）
    # ==================================================================
    def _generate_custom_type(self, struct_def: CustomTypeDef) -> str:
        self._log_debug(f"Generating custom type: {getattr(struct_def, 'name', 'unknown')}")
        lines = []

        # コメント
        if getattr(struct_def, 'description', ''):
            lines.append(f"/* {struct_def.description} */")
        if getattr(struct_def, 'title', '') and struct_def.title != getattr(struct_def, 'name', ''):
            lines.append(f"/* Title: {struct_def.title} */")

        # struct 本体
        lines.append("typedef struct {")
        for member in getattr(struct_def, 'members', []):
            if getattr(member, 'description', ''):
                indent = self.strings['indent_1']
                lines.append(f"{indent}/* {member.description} */")
            if getattr(member, 'title', '') and member.title != getattr(member, 'name', ''):
                indent = self.strings['indent_1']
                lines.append(f"{indent}/* Title: {member.title} */")
            lines.append(self._generate_member(member).rstrip('\n'))

        type_name = self.naming.create_type_name(getattr(struct_def, 'name', 'Unknown'))
        lines.append(f"}} {type_name};")

        return '\n'.join(lines)

    # ==================================================================
    # 2. SystemData_t
    # ==================================================================
    def _generate_system_data(self, global_defs: GlobalDefinitions) -> str:
        self._log_debug("Generating system data struct")
        lines = []

        # コメント
        comment = self.templates.STRUCT_COMMENTS.get('system_data', {})
        lines.append(f"/* {comment.get('title', '')} */")
        lines.append(f"/* {comment.get('description', '')} */")

        # struct 本体
        lines.append("typedef struct {")
        current_group = None
        indent = self.strings['indent_1']

        for var in getattr(global_defs, 'variables', []):
            # グループコメント
            if getattr(var, 'group', '') and var.group != current_group:
                if current_group is not None:
                    lines.append("")
                lines.append(f"{indent}/* === {var.group} === */")
                current_group = var.group

            # 説明・単位
            comments = []
            if getattr(var, 'description', ''):
                comments.append(var.description)
            if getattr(var, 'unit', ''):
                comments.append(f"[{var.unit}]")
            if comments:
                lines.append(f"{indent}/* {' '.join(comments)} */")

            # 変数本体
            var_name = self.naming.sanitize_identifier(getattr(var, 'name', 'unnamed'))
            c_type = self.mapper.map_type(getattr(var, 'type', 'void'))

            if getattr(var, 'array_size', 0) > 0:
                lines.append(f"{indent}{c_type} {var_name}[{var.array_size}];")
            else:
                lines.append(f"{indent}{c_type} {var_name};")

        lines.append(f"}} {self.templates.TYPE_NAMES['system_data']};")
        return '\n'.join(lines)

    # ==================================================================
    # 3. EventFlags_t
    # ==================================================================
    def _generate_event_flags(self, global_defs: GlobalDefinitions) -> str:
        self._log_debug("Generating event flags struct")
        lines = []

        # コメント
        comment = self.templates.STRUCT_COMMENTS.get('event_flags', {})
        lines.append(f"/* {comment.get('title', '')} */")
        lines.append(f"/* {comment.get('description', '')} */")

        # struct 本体
        lines.append("typedef struct {")
        current_group = None
        indent = self.strings['indent_1']

        for flag in getattr(global_defs, 'flags', []):
            # グループコメント
            if getattr(flag, 'group', '') and flag.group != current_group:
                if current_group is not None:
                    lines.append("")
                lines.append(f"{indent}/* === {flag.group} === */")
                current_group = flag.group

            # 説明
            if getattr(flag, 'description', ''):
                lines.append(f"{indent}/* {flag.description} */")

            # フラグ本体
            flag_name = self.naming.sanitize_identifier(getattr(flag, 'name', 'unnamed'))
            lines.append(f"{indent}uint8_t {flag_name};")

        lines.append(f"}} {self.templates.TYPE_NAMES['event_flags']};")
        return '\n'.join(lines)

    # ==================================================================
    # 4. SystemContext_t（★ pending_event 追加）
    # ==================================================================
    def _generate_system_context(self, global_defs: GlobalDefinitions) -> str:
        """
        SystemContext_t を生成（pending_event / pending_event_valid 追加）

        生成例:
            /* システム全体構造体 */
            /* グローバル変数とイベントフラグを統合管理 */
            typedef struct {
                SystemData_t data;              /* グローバル変数 */
                EventFlags_t flags;             /* イベントフラグ */
                uint16_t pending_event;         /* 保留中のイベント */
                bool pending_event_valid;       /* 保留イベント有効フラグ */
            } SystemContext_t;
        """
        self._log_debug("Generating system context struct (with pending_event)")
        T = self.CONTEXT_TEMPLATES
        lines = []

        # コメント
        comment = self.templates.STRUCT_COMMENTS.get('system_context', {})
        lines.append(T['section_comment'].substitute(
            title=comment.get('title', 'システム全体構造体'),
            description=comment.get('description', 'グローバル変数とイベントフラグを統合管理'),
        ).rstrip('\n'))

        # struct 本体
        lines.append(T['struct_start'].rstrip('\n'))
        lines.append(T['member_data'].substitute(
            system_data_type=self.templates.TYPE_NAMES['system_data'],
        ).rstrip('\n'))
        lines.append(T['member_flags'].substitute(
            event_flags_type=self.templates.TYPE_NAMES['event_flags'],
        ).rstrip('\n'))

        # ★ pending_event / pending_event_valid
        lines.append(T['member_pending_event'].rstrip('\n'))
        lines.append(T['member_pending_event_valid'].rstrip('\n'))

        # struct 終了
        lines.append(T['struct_end'].substitute(
            type_name=self.templates.TYPE_NAMES['system_context'],
        ).rstrip('\n'))

        return '\n'.join(lines)

    # ==================================================================
    # 5. 共通 TransitionContext_t（基底型）
    # ==================================================================
    def generate_common_transition_context(self) -> str:
        """
        共通の基底型 TransitionContext_t を生成

        生成例:
            /* 汎用遷移コンテキスト（層を問わない共通ロール関数用） */
            /* 各層の TransitionContext_<Layer>_t と同じレイアウト */
            typedef struct {
                uint16_t from_state;   /* 遷移元状態（層の enum 値をキャスト） */
                uint16_t event;        /* 発生イベント（層の enum 値をキャスト） */
            } TransitionContext_t;
        """
        self._log_debug("Generating common TransitionContext_t")
        T = self.COMMON_TRANSITION_CONTEXT_TEMPLATES
        lines = [
            T['comment'].rstrip('\n'),
            T['struct_start'].rstrip('\n'),
            T['member_from_state'].rstrip('\n'),
            T['member_event'].rstrip('\n'),
            T['struct_end'].rstrip('\n'),
        ]
        return '\n'.join(lines)

    # ==================================================================
    # 6. 層ごとの TransitionContext_<Layer>_t
    # ==================================================================
    def generate_layer_transition_context(self, state_type: str,
                                          event_type: str) -> str:
        """
        層ごとの TransitionContext_<Layer>_t を生成

        Args:
            state_type: 層の状態型（例: 'STATE_Driver_t'）
            event_type: 層のイベント型（例: 'EVENT_Driver_t'）

        生成例:
            /* Driver層の遷移コンテキスト */
            typedef struct {
                STATE_Driver_t from_state;   /* 遷移元状態 */
                EVENT_Driver_t event;        /* 発生イベント */
            } TransitionContext_Driver_t;
        """
        if not self.layer_name:
            self._log_debug("generate_layer_transition_context: layer_name is empty, "
                            "returning empty string")
            return ""

        self._log_debug(f"Generating layer TransitionContext for '{self.layer_name}'")
        T = self.LAYER_TRANSITION_CONTEXT_TEMPLATES
        type_name = f"TransitionContext_{self.layer_name}_t"

        lines = [
            T['comment'].substitute(layer=self.layer_name).rstrip('\n'),
            T['struct_start'].rstrip('\n'),
            T['member_from_state'].substitute(state_type=state_type).rstrip('\n'),
            T['member_event'].substitute(event_type=event_type).rstrip('\n'),
            T['struct_end'].substitute(type_name=type_name).rstrip('\n'),
        ]
        return '\n'.join(lines)

    # ==================================================================
    # 7. pending_event マクロ（FIRE_EVENT / MAX_CONSECUTIVE_PENDING_EVENTS）
    # ==================================================================
    def generate_pending_event_macros(self) -> str:
        """
        保留イベント制御マクロを生成

        生成例:
            /* ============================================================== */
            /*  保留イベント制御                                              */
            /* ============================================================== */

            /* イベント発火マクロ */
            /* ロール関数内で使用: FIRE_EVENT(ctx, EVENT_XXX_YYY); */
            #define FIRE_EVENT(ctx, evt)  do { \
                (ctx)->pending_event = (uint16_t)(evt); \
                (ctx)->pending_event_valid = true; \
            } while(0)

            /* 保留イベント連続処理の上限 */
            /* 無限ループ防止用。ビルド時に -D で上書き可能 */
            #ifndef MAX_CONSECUTIVE_PENDING_EVENTS
            #define MAX_CONSECUTIVE_PENDING_EVENTS 16
            #endif
        """
        self._log_debug("Generating pending event macros")
        T = self.MACRO_TEMPLATES
        parts = [
            T['section_comment'],
            T['fire_event_macro'],
            T['max_consecutive_macro'],
        ]
        return ''.join(parts)

    # ==================================================================
    # 8. 一括生成
    # ==================================================================
    def generate_all_structs(self, global_defs: GlobalDefinitions) -> str:
        """
        全構造体を一括生成（custom_type + system_data + event_flags + system_context）

        注意: TransitionContext_t と pending_event マクロは別メソッド
        """
        lines = []

        # custom_types
        if getattr(global_defs, 'custom_types', []):
            line = self.strings['section_line']
            title = self.templates.SECTION_HEADERS['custom_types']
            lines.append(f"{line}\n *  {title}\n{line}")
            lines.append("")
            for custom_type in global_defs.custom_types:
                lines.append(self._generate_custom_type(custom_type))
                lines.append("")

        # system_structs
        line = self.strings['section_line']
        title = self.templates.SECTION_HEADERS['system_structs']
        lines.append(f"{line}\n *  {title}\n{line}")
        lines.append("")
        lines.append(self._generate_system_data(global_defs))
        lines.append("")
        lines.append(self._generate_event_flags(global_defs))
        lines.append("")
        lines.append(self._generate_system_context(global_defs))

        return '\n'.join(lines)

    def generate_all(self, global_defs: GlobalDefinitions) -> Dict[str, str]:
        """
        全ての生成物を辞書で返す

        Returns:
            {
                'custom_types': str,               # ユーザー定義型
                'system_data': str,                # SystemData_t
                'event_flags': str,                # EventFlags_t
                'system_context': str,             # SystemContext_t（pending_event 付き）
                'common_transition_context': str,  # 共通 TransitionContext_t（基底型）
                'pending_event_macros': str,       # FIRE_EVENT / MAX_CONSECUTIVE
            }
        """
        self._log_debug("=== generate_all START (struct_generator) ===")
        result = {
            'custom_types': '\n\n'.join(
                self._generate_custom_type(ct)
                for ct in getattr(global_defs, 'custom_types', [])
            ),
            'system_data': self._generate_system_data(global_defs),
            'event_flags': self._generate_event_flags(global_defs),
            'system_context': self._generate_system_context(global_defs),
            'common_transition_context': self.generate_common_transition_context(),
            'pending_event_macros': self.generate_pending_event_macros(),
        }
        self._log_debug("=== generate_all END (struct_generator) ===")
        return result

    # ==================================================================
    # 後方互換 API
    # ==================================================================
    def generate_struct(self, struct_type: str, item) -> str:
        """後方互換: 単一構造体を生成"""
        if struct_type == 'custom_type':
            return self._generate_custom_type(item)
        elif struct_type == 'system_data':
            return self._generate_system_data(item)
        elif struct_type == 'event_flags':
            return self._generate_event_flags(item)
        elif struct_type == 'system_context':
            return self._generate_system_context(item)
        elif struct_type == 'common_transition_context':
            return self.generate_common_transition_context()
        elif struct_type == 'pending_event_macros':
            return self.generate_pending_event_macros()
        raise ValueError(f"Unknown struct type: {struct_type}")