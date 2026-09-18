"""StaTable 環境設定の定義（キー名とデフォルト値）

設定項目を追加・変更する場合は、このファイルの PREFERENCE_DEFINITIONS に
エントリを追加/編集するだけでよい。
"""

from pathlib import Path

# ----------------------------------------------------------------------
# 設定項目の定義（キー名 -> デフォルト値）
# ここに項目を追加するだけで、Preferences クラスから属性アクセス可能になる。
# ----------------------------------------------------------------------
PREFERENCE_DEFINITIONS = {
    # 最終使用フォルダ
    "last_project_dir": str(Path.home()),       # プロジェクトXML
    "last_c_source_dir": str(Path.home()),      # Cソース出力先
    "last_spec_doc_dir": str(Path.home()),      # 仕様書類の場所
    "last_export_dir": str(Path.home()),        # エクスポート先

    # ★ イベント配送設定
    "auto_convert_isr_direct_to_double": True,  # ISRで使われるDIRECTをDOUBLEへ自動変換
}