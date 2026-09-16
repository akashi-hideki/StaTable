# tests/conftest.py
"""
pytest 共通設定

GUI round-trip テスト終了時に QWebEngine をクリーンアップし、
「Release of profile requested but WebEnginePage still not deleted」
警告を抑制する。
"""
import os

# Qt を offscreen モードで起動（GUI 表示なし）
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest


@pytest.fixture(scope="session", autouse=True)
def qt_cleanup():
    """
    セッション開始前に QApplication を準備し、
    終了時に QWebEngine をクリーンアップする。
    """
    # ---- セッション開始前 ----
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication([])

    yield

    # ---- セッション終了後 ----
    try:
        # QWebEngine のプロファイルを明示的に解放
        try:
            from PySide6.QtWebEngineCore import QWebEngineProfile
            profile = QWebEngineProfile.defaultProfile()
            if profile is not None:
                profile.deleteLater()
                for _ in range(10):
                    app.processEvents()
        except ImportError:
            pass

        # 全トップレベルウィジェットを明示的に閉じる
        for widget in app.topLevelWidgets():
            try:
                widget.close()
                widget.deleteLater()
            except Exception:
                pass

        # イベントループを複数回まわして GC を促進
        for _ in range(10):
            app.processEvents()

        # 最後に QApplication を明示的に quit
        app.quit()
        app.processEvents()
    except Exception as e:
        print(f"[qt_cleanup] cleanup warning: {e}")


@pytest.fixture(scope="function", autouse=True)
def gc_between_tests():
    """
    各テスト間で GC を実行し、QObject のリークを防ぐ。
    """
    import gc
    gc.collect()
    yield
    gc.collect()