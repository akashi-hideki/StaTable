# statable/parser.py
"""
StaTable パーサー（未実装スタブ）

【v1.8 §11.2 #9】
  現状は未実装のスタブ。
  XML の入出力は `statable/xml_io.py` が担当している。

【将来実装予定】
  - Excel (.xlsx) 読み込み
    openpyxl 等を使用して状態遷移表を取り込む
  - CSV (.csv) 読み込み
    状態 × イベントのマトリクス形式を想定
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
# 未実装マーカー
# ======================================================================
# 以下は将来実装する予定のプレースホルダ。
# 実装するまでは呼び出さないこと。

__all__ = []   # Public API None（未実装のため）


class ParserNotImplementedError(NotImplementedError):
    """parser.py の機能が未実装であることを示す例外"""
    pass


def parse_excel(filepath: str):
    """
    Excel ファイルから状態遷移データを読み込む（未実装）

    Args:
        filepath: 読み込む Excel ファイルパス

    Raises:
        ParserNotImplementedError: 常に送出（未実装のため）
    """
    raise ParserNotImplementedError(
        "parse_excel は未実装です。"
        "現状は statable/xml_io.py を使用してください。"
    )


def parse_csv(filepath: str):
    """
    CSV ファイルから状態遷移データを読み込む（未実装）

    Args:
        filepath: 読み込む CSV ファイルパス

    Raises:
        ParserNotImplementedError: 常に送出（未実装のため）
    """
    raise ParserNotImplementedError(
        "parse_csv は未実装です。"
        "現状は statable/xml_io.py を使用してください。"
    )


def parse_json(filepath: str):
    """
    JSON ファイルから状態遷移データを読み込む（未実装）

    Args:
        filepath: 読み込む JSON ファイルパス

    Raises:
        ParserNotImplementedError: 常に送出（未実装のため）
    """
    raise ParserNotImplementedError(
        "parse_json は未実装です。"
        "現状は statable/xml_io.py を使用してください。"
    )