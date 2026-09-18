"""StaTable preference definitions (key names and default values)\n\nTo add or change a setting, just add/edit an entry in\nPREFERENCE_DEFINITIONS in this file.\n"""

from pathlib import Path

# ----------------------------------------------------------------------
# 設定項目の定義（キー名 -> デフォルト値）
# Adding an entry here is enough to enable attribute access from the Preferences class.
# ----------------------------------------------------------------------
PREFERENCE_DEFINITIONS = {
    # 最終使用フォルダ
    "last_project_dir": str(Path.home()),       # プロジェクトXML
    "last_c_source_dir": str(Path.home()),      # Cソース出力先
    "last_spec_doc_dir": str(Path.home()),      # 仕様書類の場所
    "last_export_dir": str(Path.home()),        # エクスポート先

    # ★ Event delivery settings
    "auto_convert_isr_direct_to_double": True,  # Automatically convert ISR-used DIRECT to DOUBLE
}