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
    
    # ===== 生成スタイル =====
    generation_style: str = "table_driven"  # table_driven / switch_case
    
    # 遷移テーブル方式
    table_type: str = "array"  # array / switch / dictionary
    
    # OS種別
    os_type: str = "non_rtos"  # non_rtos / freertos / threadx
    
    # ===== 命名規則 =====
    naming_prefix: str = ""
    state_prefix: str = "STATE"
    event_prefix: str = "EVENT"
    flag_prefix: str = "FLAG"
    
    # ===== デバッグログ =====
    enable_debug_logs: bool = True
    enable_info_logs: bool = True
    enable_error_logs: bool = True
    
    # ===== コメント生成 =====
    enable_comments: bool = True
    enable_doxygen: bool = True
    
    # ===== マーカー =====
    enable_user_markers: bool = True
    
    # ===== 出力設定 =====
    output_directory: str = ""
    save_with_merge: bool = True
    
    # ===== プロジェクト設定 =====
    project_name: str = "MyProject"
    
    # ===== フォルダ構成 =====
    folder_structure: str = "by_type"       # flat / by_layer / by_type
    include_dir_name: str = "include"
    source_dir_name: str = "src"
    common_dir_name: str = "common"
    project_dir_name: str = "project"
    
    # ===== スーパーインクルード =====
    generate_super_include: bool = True
    super_include_file: str = "statable_all.h"
    super_include_dir: str = "common"
    
    # ===== 外部インクルード =====
    external_includes: List[str] = field(default_factory=list)
    external_includes_in_super: bool = True
    external_includes_in_role: bool = True
    external_includes_in_transitions: bool = False
    external_includes_in_common: bool = False
    
    # ===== 予約イベント制限 =====
    max_consecutive_pending_events: int = 16
    
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
            'project_name': self.project_name,
            'folder_structure': self.folder_structure,
            'include_dir_name': self.include_dir_name,
            'source_dir_name': self.source_dir_name,
            'common_dir_name': self.common_dir_name,
            'project_dir_name': self.project_dir_name,
            'generate_super_include': self.generate_super_include,
            'super_include_file': self.super_include_file,
            'super_include_dir': self.super_include_dir,
            'external_includes': self.external_includes,
            'external_includes_in_super': self.external_includes_in_super,
            'external_includes_in_role': self.external_includes_in_role,
            'external_includes_in_transitions': self.external_includes_in_transitions,
            'external_includes_in_common': self.external_includes_in_common,
            'max_consecutive_pending_events': self.max_consecutive_pending_events,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CodeGenerationConfig':
        """辞書から復元"""
        # 未知のキーは無視
        valid_keys = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)


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
    
    def get_available_folder_structures(self) -> Dict[str, str]:
        return {
            'flat': 'フラット',
            'by_layer': '層ごと',
            'by_type': 'include/src分離',
        }