# codegen/enum_generator.py
"""
C列挙型コード生成モジュール（多層ステートマシン対応版）

生成する enum:
  1. 状態 enum:  STATE_<Layer>_t （層ごと）
  2. イベント enum: EVENT_<Layer>_t （層ごと、NONE = 0 を含む）
  3. フラグ enum: FLAG_t （共通、全層で共有）

設計方針:
  - テンプレートは string.Template でデータテーブル化
  - 状態/イベントは登録順（案A）
  - MAX は明示（案A）
  - フラグは共通（案A）
  - layer_name 未設定時は後方互換（STATE_t / EVENT_t）
"""

import sys
import os
import logging
from string import Template
from typing import Dict, List, Any, Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from statable.model import State, Event, StateType, EventKind
from statable.global_defs import EventFlag

try:
    from .naming_convention import CNamingConvention
    from .code_templates import CodeTemplates
except ImportError:
    from naming_convention import CNamingConvention
    from code_templates import CodeTemplates

logger = logging.getLogger(__name__)


class CEnumGenerator:
    """C列挙型コード生成クラス（多層ステートマシン対応）"""
    # ==================================================================
    # 【データテーブル①】enum 共通テンプレート
    # ==================================================================
    ENUM_TEMPLATES = {
        # --- セクションコメント ---
        'section_comment': Template(
            '/* $description */\n'
        ),

        # --- typedef enum 開始 ---
        'enum_start': (
            'typedef enum {\n'
        ),

        # --- 値（コメント付き） ---
        'value_with_comment': Template(
            '    $name = $value,    /* $comment */\n'
        ),

        # --- 値（コメントなし） ---
        'value': Template(
            '    $name = $value,\n'
        ),

        # --- MAX 値（最終要素） ---
        'max_value': Template(
            '    $name           /* 要素数（システム用） */\n'
        ),

        # --- typedef enum 終了（★ 修正: }} → }） ---
        'enum_end': Template(
            '} $type_name;\n'
        ),
    }


    # ==================================================================
    # 【データテーブル②】層ごとの型名定義
    # ==================================================================
    LAYER_TYPE_NAMES = {
        'state': {
            'value_prefix': 'STATE',
            'type_suffix': '_t',
            'max_suffix': '_MAX',
            'none_value': None,  # 状態には NONE なし
        },
        'event': {
            'value_prefix': 'EVENT',
            'type_suffix': '_t',
            'max_suffix': '_MAX',
            'none_value': 'NONE',  # イベントには NONE = 0
        },
        'flag': {
            'value_prefix': 'FLAG',
            'type_suffix': '_t',
            'max_suffix': '_MAX',
            'none_value': None,
        },
    }

    # ==================================================================
    # 【データテーブル③】コメント生成用フォーマット
    # ==================================================================
    COMMENT_FORMATS = {
        'state': {
            'description_suffix': None,
            'type_suffix': 'Type: {type_name}',
            'title_prefix': 'Title: ',
        },
        'event': {
            'description_suffix': None,
            'kind_suffix': 'Kind: {kind_name}',
            'title_prefix': 'Title: ',
        },
        'flag': {
            'description_suffix': None,
            'title_prefix': 'Title: ',
        },
    }

    # ==================================================================
    # コンストラクタ
    # ==================================================================
    def __init__(self):
        self.naming = CNamingConvention()
        self.templates = CodeTemplates()
        self.strings = self.templates.STRINGS
        self.formats = self.templates.FORMATS
        self.layer_name: str = ""

    def set_layer(self, layer_name: str):
        """層名を設定（例: 'Driver', 'Middle', 'Application'）"""
        self.layer_name = layer_name
        logger.debug(f"CEnumGenerator.set_layer: layer_name='{layer_name}'")

    def _log_debug(self, message, level='debug'):
        log_func = getattr(logger, level, logger.debug)
        log_func(message)

    # ==================================================================
    # 名前生成ヘルパー
    # ==================================================================
    def _state_value_name(self, state_name: str) -> str:
        """
        状態値名: STATE_<Layer>_<Name>
        - layer_name 未設定: STATE_<Name>
        """
        pascal = self.naming.to_pascal_case(state_name) if state_name else "Unknown"
        if self.layer_name:
            return f"STATE_{self.layer_name}_{pascal}"
        return f"STATE_{pascal}"

    def _event_value_name(self, event_name: str) -> str:
        """
        イベント値名: EVENT_<Layer>_<Name>
        - 空イベント: EVENT_<Layer>_NONE
        - layer_name 未設定: EVENT_<Name>
        """
        if not event_name:
            upper = "NONE"
        else:
            upper = self.naming.to_upper_snake(event_name)
        if self.layer_name:
            return f"EVENT_{self.layer_name}_{upper}"
        return f"EVENT_{upper}"

    def _flag_value_name(self, flag_name: str) -> str:
        """フラグ値名: FLAG_<Name>（層に依存しない）"""
        upper = self.naming.to_upper_snake(flag_name)
        return f"FLAG_{upper}"

    def _state_type_name(self) -> str:
        """型名: STATE_<Layer>_t"""
        if self.layer_name:
            return f"STATE_{self.layer_name}_t"
        return "STATE_t"

    def _event_type_name(self) -> str:
        """型名: EVENT_<Layer>_t"""
        if self.layer_name:
            return f"EVENT_{self.layer_name}_t"
        return "EVENT_t"

    def _flag_type_name(self) -> str:
        """型名: FLAG_t（共通）"""
        return "FLAG_t"

    def _state_max_name(self) -> str:
        """MAX 値名: STATE_<Layer>_MAX"""
        if self.layer_name:
            return f"STATE_{self.layer_name}_MAX"
        return "STATE_MAX"

    def _event_max_name(self) -> str:
        """MAX 値名: EVENT_<Layer>_MAX"""
        if self.layer_name:
            return f"EVENT_{self.layer_name}_MAX"
        return "EVENT_MAX"

    def _flag_max_name(self) -> str:
        """MAX 値名: FLAG_MAX（共通）"""
        return "FLAG_MAX"

    # ==================================================================
    # コメント生成
    # ==================================================================
    def _generate_state_comment(self, state: State) -> str:
        """状態のコメント"""
        comments = []
        if getattr(state, 'description', ''):
            comments.append(state.description)
        if getattr(state, 'type', None) and state.type != StateType.NORMAL:
            comments.append(f"Type: {state.type.name}")
        if getattr(state, 'title', ''):
            comments.append(f"Title: {state.title}")
        return ' '.join(comments)

    def _generate_event_comment(self, event: Event) -> str:
        """イベントのコメント"""
        comments = []
        if getattr(event, 'description', ''):
            comments.append(event.description)
        if getattr(event, 'kind', None) and event.kind != EventKind.SIGNAL:
            comments.append(f"Kind: {event.kind.name}")
        if getattr(event, 'title', ''):
            comments.append(f"Title: {event.title}")
        return ' '.join(comments)

    def _generate_flag_comment(self, flag: EventFlag) -> str:
        """フラグのコメント"""
        comments = []
        if getattr(flag, 'description', ''):
            comments.append(flag.description)
        if getattr(flag, 'title', ''):
            comments.append(f"Title: {flag.title}")
        return ' '.join(comments)

    # ==================================================================
    # enum 本体生成
    # ==================================================================
    def _generate_enum_values(self, items: List[Any],
                              value_name_func,
                              comment_func,
                              none_value: Optional[str] = None,
                              none_comment: str = "") -> str:
        """
        enum の値を生成

        Args:
            items: 値のリスト
            value_name_func: 値名を生成する関数
            comment_func: コメントを生成する関数
            none_value: NONE 値の名前（None なら省略）
            none_comment: NONE 値のコメント
        """
        T = self.ENUM_TEMPLATES
        parts = []

        # NONE 値（イベントのみ）
        if none_value is not None:
            none_name = value_name_func("")  # 空を渡して NONE を生成
            parts.append(T['value_with_comment'].substitute(
                name=none_name,
                value=0,
                comment=none_comment,
            ))
            start_index = 1
        else:
            start_index = 0

        # 各値
        for i, item in enumerate(items):
            value = start_index + i
            name = value_name_func(getattr(item, 'name', 'unnamed'))
            comment = comment_func(item)

            if comment:
                parts.append(T['value_with_comment'].substitute(
                    name=name, value=value, comment=comment,
                ))
            else:
                parts.append(T['value'].substitute(
                    name=name, value=value,
                ))

        return ''.join(parts)

    # ==================================================================
    # 1. 状態 enum 生成
    # ==================================================================
    def generate_state_enum(self, states: List[State]) -> str:
        """
        状態 enum を生成

        生成例（層名あり）:
            /* Driver層の状態定義 */
            typedef enum {
                STATE_Driver_Idle = 0,    /* 初期状態 */
                STATE_Driver_Active,
                STATE_Driver_Error,
                STATE_Driver_MAX           /* 要素数（システム用） */
            } STATE_Driver_t;

        生成例（層名なし・後方互換）:
            /* 状態定義 */
            typedef enum {
                STATE_Idle = 0,
                ...
            } STATE_t;
        """
        if not states:
            return ''

        self._log_debug(f"=== generate_state_enum START: {len(states)} states ===")
        T = self.ENUM_TEMPLATES
        parts = []

        # セクションコメント
        desc = f"{self.layer_name}層の状態定義" if self.layer_name else "状態定義"
        parts.append(T['section_comment'].substitute(description=desc))

        # enum 開始
        parts.append(T['enum_start'])

        # 値
        parts.append(self._generate_enum_values(
            items=states,
            value_name_func=self._state_value_name,
            comment_func=self._generate_state_comment,
            none_value=None,
        ))

        # MAX 値（明示）
        parts.append(T['max_value'].substitute(name=self._state_max_name()))

        # enum 終了
        parts.append(T['enum_end'].substitute(type_name=self._state_type_name()))

        result = ''.join(parts)
        self._log_debug(f"=== generate_state_enum END ===")
        return result

    # ==================================================================
    # 2. イベント enum 生成
    # ==================================================================
    def generate_event_enum(self, events: List[Event]) -> str:
        """
        イベント enum を生成（NONE = 0 を含む）

        生成例（層名あり）:
            /* Driver層のイベント定義 */
            typedef enum {
                EVENT_Driver_NONE = 0,    /* 完了遷移 */
                EVENT_Driver_START = 1,    /* 起動要求 */
                EVENT_Driver_ERROR = 2,    /* エラー通知 */
                EVENT_Driver_MAX           /* 要素数（システム用） */
            } EVENT_Driver_t;
        """
        if not events:
            return ''

        self._log_debug(f"=== generate_event_enum START: {len(events)} events ===")
        T = self.ENUM_TEMPLATES
        parts = []

        # セクションコメント
        desc = f"{self.layer_name}層のイベント定義" if self.layer_name else "イベント定義"
        parts.append(T['section_comment'].substitute(description=desc))

        # enum 開始
        parts.append(T['enum_start'])

        # 値（NONE = 0 を先頭に）
        parts.append(self._generate_enum_values(
            items=events,
            value_name_func=self._event_value_name,
            comment_func=self._generate_event_comment,
            none_value="NONE",
            none_comment="完了遷移",
        ))

        # MAX 値（明示）
        parts.append(T['max_value'].substitute(name=self._event_max_name()))

        # enum 終了
        parts.append(T['enum_end'].substitute(type_name=self._event_type_name()))

        result = ''.join(parts)
        self._log_debug(f"=== generate_event_enum END ===")
        return result

    # ==================================================================
    # 3. フラグ enum 生成（共通）
    # ==================================================================
    def generate_flag_enum(self, flags: List[EventFlag]) -> str:
        """
        フラグ enum を生成（共通、層に依存しない）

        生成例:
            /* イベントフラグ定義 */
            typedef enum {
                FLAG_EVT_START_REQ = 0,
                FLAG_EVT_MODE,
                FLAG_MAX                   /* 要素数（システム用） */
            } FLAG_t;
        """
        if not flags:
            return ''

        self._log_debug(f"=== generate_flag_enum START: {len(flags)} flags ===")
        T = self.ENUM_TEMPLATES
        parts = []

        # セクションコメント
        parts.append(T['section_comment'].substitute(description="イベントフラグ定義"))

        # enum 開始
        parts.append(T['enum_start'])

        # 値
        parts.append(self._generate_enum_values(
            items=flags,
            value_name_func=self._flag_value_name,
            comment_func=self._generate_flag_comment,
            none_value=None,
        ))

        # MAX 値（明示）
        parts.append(T['max_value'].substitute(name=self._flag_max_name()))

        # enum 終了
        parts.append(T['enum_end'].substitute(type_name=self._flag_type_name()))

        result = ''.join(parts)
        self._log_debug(f"=== generate_flag_enum END ===")
        return result

    # ==================================================================
    # 4. 一括生成
    # ==================================================================
    def generate_all_enums(self, states: List[State], events: List[Event],
                           flags: List[EventFlag] = None) -> str:
        """
        全 enum を生成（状態 → イベント → フラグ）

        Args:
            states: 状態リスト
            events: イベントリスト
            flags: イベントフラグリスト（オプション）

        Returns:
            3つの enum を改行で区切った文字列
        """
        self._log_debug(f"=== generate_all_enums START: "
                        f"{len(states)} states, {len(events)} events, "
                        f"{len(flags) if flags else 0} flags ===")
        parts = []

        state_enum = self.generate_state_enum(states)
        if state_enum:
            parts.append(state_enum)
            parts.append("")

        event_enum = self.generate_event_enum(events)
        if event_enum:
            parts.append(event_enum)
            parts.append("")

        if flags:
            flag_enum = self.generate_flag_enum(flags)
            if flag_enum:
                parts.append(flag_enum)

        result = '\n'.join(parts)
        self._log_debug(f"=== generate_all_enums END: {len(result)} chars ===")
        return result

    # ==================================================================
    # 5. ビットマスク enum（オプション機能）
    # ==================================================================
    def generate_bit_mask_enum(self, flags: List[EventFlag]) -> str:
        """
        フラグのビットマスク enum を生成

        生成例:
            /* イベントフラグビットマスク定義 */
            /* ビット単位でフラグを管理する場合に使用 */
            typedef enum {
                FLAG_MASK_EVT_START_REQ = 0x01,
                FLAG_MASK_EVT_MODE = 0x02,
            } FLAG_MASK_t;
        """
        if not flags:
            return ''

        self._log_debug(f"=== generate_bit_mask_enum START: {len(flags)} flags ===")
        T = self.ENUM_TEMPLATES
        parts = []

        # セクションコメント
        parts.append('/* イベントフラグビットマスク定義 */\n')
        parts.append('/* ビット単位でフラグを管理する場合に使用 */\n')

        # enum 開始
        parts.append(T['enum_start'])

        # 各ビット
        for i, flag in enumerate(flags):
            bit_value = 1 << i
            upper = self.naming.to_upper_snake(getattr(flag, 'name', 'unnamed'))
            name = f"FLAG_MASK_{upper}"
            comment = self._generate_flag_comment(flag)
            if comment:
                parts.append(f"    {name} = 0x{bit_value:02X},    /* {comment} */\n")
            else:
                parts.append(f"    {name} = 0x{bit_value:02X},\n")

        # enum 終了
        parts.append(T['enum_end'].substitute(type_name="FLAG_MASK_t"))

        result = ''.join(parts)
        self._log_debug(f"=== generate_bit_mask_enum END ===")
        return result

    # ==================================================================
    # 後方互換 API
    # ==================================================================
    def generate_enum(self, enum_type: str, items: List[Any]) -> str:
        """後方互換: 単一 enum を生成"""
        if enum_type == 'state':
            return self.generate_state_enum(items)
        elif enum_type == 'event':
            return self.generate_event_enum(items)
        elif enum_type == 'flag':
            return self.generate_flag_enum(items)
        else:
            logger.warning(f"Unknown enum_type: {enum_type}")
            return ""