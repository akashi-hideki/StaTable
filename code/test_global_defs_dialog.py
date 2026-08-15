"""グローバル変数・イベントフラグ定義画面の単体テスト"""

import sys
from PySide6.QtWidgets import QApplication

from statable_gui.global_defs import GlobalDefinitions, SystemVariable, EventFlag
from statable_gui.global_defs_dialog import GlobalDefinitionsDialog


def main():
    app = QApplication(sys.argv)

    # テスト用の初期データ
    defs = GlobalDefinitions()
    defs.variables.append(SystemVariable(
        name="battery_voltage",
        type="uint16_t",
        unit="mV",
        default_value="0",
        group="Power",
        description="バッテリ電圧"
    ))
    defs.variables.append(SystemVariable(
        name="motor_current",
        type="int16_t",
        unit="mA",
        default_value="0",
        group="Motor",
        description="モータ電流"
    ))
    # ★ 新しい EventFlag は min_value / max_value を指定
    defs.flags.append(EventFlag(
        name="EVT_START_REQ",
        min_value=0,
        max_value=1,
        group="SystemEvents",
        description="起動要求"
    ))
    defs.flags.append(EventFlag(
        name="EVT_MODE",
        min_value=0,
        max_value=3,   # 2bit
        group="SystemEvents",
        description="モード指示"
    ))

    # ダイアログを表示
    dlg = GlobalDefinitionsDialog(defs)
    result = dlg.exec()

    # 結果をコンソールに表示
    print("\n=== GlobalDefinitionsDialog closed ===")
    print("Result:", result)
    print("\n--- Variables ---")
    for v in defs.variables:
        print(f"  {v.name} ({v.type}) [{v.group}] {v.description}")
    print("\n--- Event Flags ---")
    for f in defs.flags:
        print(f"  {f.name} min={f.min_value} max={f.max_value} "
              f"width={f.bit_width}bit [{f.group}] {f.description}")

    return 0


if __name__ == "__main__":
    sys.exit(main())