import json
from pathlib import Path
from typing import Any, Optional

from .preference_keys import PREFERENCE_DEFINITIONS


class Preferences:
    """Store application settings in a JSON file (key names defined in a separate file)\n\n    Keys registered in preference_keys.py's PREFERENCE_DEFINITIONS can be\n    read/written via attribute access such as prefs.last_project_dir.\n    """

    DEFAULT_FILE = Path.home() / ".statable" / "preferences.json"

    def __init__(self, filepath: Optional[Path] = None):
        self.filepath = Path(filepath) if filepath else self.DEFAULT_FILE
        self.data: dict = {}
        self.load()
        self._apply_defaults()

    def _apply_defaults(self):
        """定義されたキーが未Saveならデフォルト値を設定"""
        changed = False
        for key, default in PREFERENCE_DEFINITIONS.items():
            if key not in self.data:
                self.data[key] = default
                changed = True
        if changed:
            self.save()

    def load(self):
        """JSONファイルから設定を読み込む"""
        if self.filepath.exists():
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except (json.JSONDecodeError, OSError):
                self.data = {}

    def save(self):
        """現在の設定をJSONファイルにSaveする"""
        try:
            self.filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except OSError:
            # 書き込み失敗時は無視（必要に応じてログ出力）
            pass

    def get(self, key: str, default: Any = None) -> Any:
        """設定値をキー名で取得する（従来方式）"""
        return self.data.get(key, default)

    def set(self, key: str, value: Any):
        """設定値をキー名で更新し、即座にSaveする"""
        self.data[key] = value
        self.save()

    # ------------------------------------------------------------------
    # Attribute access (prefs.last_project_dir etc.)
    # ------------------------------------------------------------------
    def __getattr__(self, name: str) -> Any:
        # 定義済みキーなら値を返す
        if name in PREFERENCE_DEFINITIONS:
            return self.data.get(name, PREFERENCE_DEFINITIONS[name])
        # 未定義の属性は通常のError
        raise AttributeError(f"'Preferences' object has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any):
        # 定義済みキーなら設定とSaveを行う
        if name in PREFERENCE_DEFINITIONS:
            self.data[name] = value
            self.save()
        else:
            # 定義済み以外は通常の属性として設定
            super().__setattr__(name, value)