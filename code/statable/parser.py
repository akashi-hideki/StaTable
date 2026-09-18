# statable/parser.py
"""
StaTable パーサー（未実装スタブ）

【v1.8 §11.2 #9】
  現状は未実装のスタブ。
  XML の入出力は `statable/xml_io.py` が担当している。

【将来実装予定】
  - Excel (.xlsx) 読み込み
    openpyxl 等を使用してStateTransition表を取り込む
  - CSV (.csv) 読み込み
    State × Eventのマトリクス形式を想定
  - JSON (.json) 読み込み
    外部ツール連携用の汎用フォーマット

【注意】
  - このモジュールは現時点で呼び出し元が存在しない
  - 実装する際は `statable/model.py` の
    StateMachine / State / Event / Transition に変換すること
  - 既存の `xml_io.py` と同じインターフェース
    （project_to_xml / project_from_xml 相当）を目指すのが望ましい

【実装しない場合】
  このファイル自体をDeleteしても問題ない。
  呼び出し元がないため、Deleteしても影響はない。
"""

# ======================================================================
# Unimplemented marker
# ======================================================================
# The following are placeholders.
# Do not call until implemented.

__all__ = []   # Public API None（未実装のため）


class ParserNotImplementedError(NotImplementedError):
    """Exception indicating parser.py features not implemented"""
    pass


def parse_excel(filepath: str):
    """\n    Load state transition data from an Excel file (not implemented)\n"""
    raise ParserNotImplementedError(
        "parse_excel is not implemented."
        "Currently, please use statable/xml_io.py."
    )


def parse_csv(filepath: str):
    """\n    Load state transition data from a CSV file (not implemented)\n"""
    raise ParserNotImplementedError(
        "parse_csv is not implemented."
        "Currently, please use statable/xml_io.py."
    )


def parse_json(filepath: str):
    """\n    Load state transition data from a JSON file (not implemented)\n"""
    raise ParserNotImplementedError(
        "parse_json is not implemented."
        "Currently, please use statable/xml_io.py."
    )