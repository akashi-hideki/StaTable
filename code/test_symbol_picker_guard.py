"""SymbolPickerWidget と GuardEditDialog の単体テスト"""

import sys
from PySide6.QtWidgets import QApplication, QDialog
from PySide6.QtCore import Qt

from statable.global_defs import GlobalDefinitions, SystemVariable, EventFlag
from statable.model import RoleFunction
from statable_gui.guard_edit_dialog import GuardEditDialog


def main():
    app = QApplication(sys.argv)

    # サンプルグローバル定義
    global_defs = GlobalDefinitions()
    global_defs.variables.append(SystemVariable(
        name="battery_voltage", type="uint16_t", unit="mV",
        group="Power", description="バッテリ電圧"
    ))
    global_defs.variables.append(SystemVariable(
        name="motor_current", type="int16_t", unit="mA",
        group="Motor", description="モータ電流"
    ))
    global_defs.flags.append(EventFlag(
        name="EVT_START_REQ", min_value=0, max_value=1,
        group="SystemEvents", description="起動要求"
    ))
    global_defs.flags.append(EventFlag(
        name="EVT_MODE", min_value=0, max_value=3,
        group="SystemEvents", description="モード指示"
    ))

    # サンプルロール関数
    role_functions = {
        "Sensor_Init": RoleFunction(
            name="Sensor_Init", description="センサ初期化",
            return_type="int", arg1_type="uint8_t", arg1_name="channel",
            arg2_type="uint32_t", arg2_name="timeout_ms"
        ),
        "Error_Log": RoleFunction(
            name="Error_Log", description="エラーログ出力",
            return_type="void", arg1_type="int", arg1_name="err_code",
            arg2_type="int", arg2_name="level"
        ),
    }

    # ダイアログ表示
    dlg = GuardEditDialog(
        guard_text="battery_voltage > 3000\nAND motor_current < 100\nOR EVT_START_REQ == 1",
        global_defs=global_defs,
        role_functions=role_functions
    )
    result = dlg.exec()

    print("\n=== GuardEditDialog closed ===")
    print("Result:", result)

    if result == QDialog.Accepted:
        print("Accepted")
        print("Final guard text:")
        print(dlg.get_guard_text())
    else:
        print("Rejected")

    return 0


if __name__ == "__main__":
    sys.exit(main())