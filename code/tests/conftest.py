# tests/conftest.py
"""
pytest 共通設定

GUI round-trip テスト用:
  - Qt を offscreen モードで起動
  - Mermaid (WebEngine) を環境変数で無効化
    → Qt WebEngine ランタイムをロードさせない
    → 「Release of profile requested...」警告を根本から抑制
"""
import os

# ★ 環境変数は他の import より前に設定する
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["STATABLE_DISABLE_MERMAID"] = "1"

import gc
import pytest


@pytest.fixture(scope="session", autouse=True)
def qt_cleanup():
    """セッション終了時に Qt のウィジェットをクリーンアップ"""
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication([])

    yield

    # ---- セッション終了後 ----
    # WebEngine は無効化されているため、トップレベルウィジェットの
    # 解放とイベントループの処理だけで十分
    try:
        for widget in app.topLevelWidgets():
            try:
                widget.close()
                widget.deleteLater()
            except Exception:
                pass

        for _ in range(10):
            app.processEvents()

        app.quit()
        app.processEvents()
    except Exception as e:
        print(f"[qt_cleanup] {e}")


@pytest.fixture(scope="function", autouse=True)
def gc_between_tests():
    """各テスト間で GC を実行し、QObject のリークを防ぐ"""
    gc.collect()
    yield
    gc.collect()