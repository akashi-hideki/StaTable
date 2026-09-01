# codegen/config.py
"""
コード生成設定管理モジュール
生成オプションを一元管理する
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class CodeGenerationConfig:
    """コード生成設定"""
    
    # 生成スタイル
    generation_style: str = "table_driven"  # table_driven / switch_case
    
    # 遷移テーブル方式
    table_type: str = "array"  # array / switch / dictionary
    
    # OS種別
    os_type: str = "non_rtos"  # non_rtos / freertos / threadx
    
    # 命名規則
    naming_prefix: str = ""  # 関数名のプレフィックス
    state_prefix: str = "STATE"
    event_prefix: str = "EVENT"
    flag_prefix: str = "FLAG"
    
    # デバッグログ
    enable_debug_logs: bool = True
    enable_info_logs: bool = True
    enable_error_logs: bool = True
    
    # コメント生成
    enable_comments: bool = True
    enable_doxygen: bool = True
    
    # マーカー
    enable_user_markers: bool = True
    
    # 出力設定
    output_directory: str = ""
    save_with_merge: bool = True
    
    def to_dict(self) -> Dict:
        """辞書に変換"""
        return {
            'generation_style': self.generation_style,
            'table_type': self.table_type,
            'os_type': self.os_type,
            'naming_prefix': self.naming_prefix,
            'state_prefix': self.state_prefix,
            'event_prefix': self.event_prefix,
            'flag_prefix': self.flag_prefix,
            'enable_debug_logs': self.enable_debug_logs,
            'enable_info_logs': self.enable_info_logs,
            'enable_error_logs': self.enable_error_logs,
            'enable_comments': self.enable_comments,
            'enable_doxygen': self.enable_doxygen,
            'enable_user_markers': self.enable_user_markers,
            'output_directory': self.output_directory,
            'save_with_merge': self.save_with_merge,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CodeGenerationConfig':
        """辞書から復元"""
        return cls(**data)


class ConfigManager:
    """設定管理クラス"""
    
    def __init__(self):
        self._config = CodeGenerationConfig()
    
    def get_config(self) -> CodeGenerationConfig:
        """現在の設定を取得"""
        return self._config
    
    def set_config(self, config: CodeGenerationConfig):
        """設定を更新"""
        self._config = config
    
    def update(self, **kwargs):
        """設定を部分的に更新"""
        for key, value in kwargs.items():
            if hasattr(self._config, key):
                setattr(self._config, key, value)
    
    def reset(self):
        """設定をリセット"""
        self._config = CodeGenerationConfig()
    
    def get_available_styles(self) -> Dict[str, str]:
        """利用可能な生成スタイル"""
        return {
            'table_driven': 'テーブル駆動方式',
            'switch_case': 'switch-case方式',
        }
    
    def get_available_table_types(self) -> Dict[str, str]:
        """利用可能なテーブル方式"""
        return {
            'array': '配列方式',
            'switch': 'switch-case方式',
            'dictionary': '辞書方式（非推奨）',
        }
    
    def get_available_os_types(self) -> Dict[str, str]:
        """利用可能なOS種別"""
        return {
            'non_rtos': 'NonRTOS（ベアメタル）',
            'freertos': 'FreeRTOS',
            'threadx': 'ThreadX',
        }