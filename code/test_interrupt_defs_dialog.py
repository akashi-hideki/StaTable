"""割り込み処理・デバイスリソース・タイマ設定ダイアログの単体テスト"""

import sys
from PySide6.QtWidgets import QApplication, QDialog

from statable.global_defs import GlobalDefinitions, SystemVariable, EventFlag
from statable.model import RoleFunction
from statable_gui.interrupt_handler_edit_dialog import (
    InterruptHandlerEditDialog,
    InterruptHandlerDef,
    InterruptAction,
    DevicePlaceholderDef,
    TimerBaseDef,
    TimerDerivedDef,
)


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

    event_names = ["tick", "uart_rx", "adc_done", "button_pressed"]

    interrupts = [
        InterruptHandlerDef(
            name="TIMER0",
            description="1ms周期タイマ",
            event_name="tick",
            is_timer=True,
            actions=[
                InterruptAction(
                    guard="g_tick_100ms >= 5",
                    action="StateMachine_EnqueueEvent(EVENT_TICK);"
                ),
                InterruptAction(
                    guard="",
                    action="g_system_tick++;\nUpdateDerivedTimers();"
                ),
            ]
        ),
        InterruptHandlerDef(
            name="UART0",
            description="UART受信",
            event_name="uart_rx",
            is_timer=False,
            actions=[
                InterruptAction(
                    guard="uart_rx_count < 10",
                    action="Sensor_Read();\nEVT_START_REQ = 1;"
                ),
            ]
        ),
    ]

    placeholders = [
        DevicePlaceholderDef(name="TIMER0_IRQ_FLAG", description="タイマ0割り込みフラグクリア用レジスタ"),
        DevicePlaceholderDef(name="UART0_RX_REG", description="UART受信データレジスタ"),
    ]

    timer_base = TimerBaseDef(
        variable_name="g_system_tick",
        unit="1ms",
        data_type="volatile uint32_t",
        derived=[
            TimerDerivedDef(period_name="10ms", multiplier=10, variable_name="g_tick_10ms", data_type="uint8_t"),
            TimerDerivedDef(period_name="100ms", multiplier=100, variable_name="g_tick_100ms", data_type="uint8_t"),
            TimerDerivedDef(period_name="1s", multiplier=1000, variable_name="g_tick_1s", data_type="uint16_t"),
        ]
    )

    dlg = InterruptHandlerEditDialog(
        interrupts=interrupts,
        placeholders=placeholders,
        timer_base=timer_base,
        event_names=event_names,
        global_defs=global_defs,
        role_functions=role_functions,
    )
    result = dlg.exec()

    print("\n=== InterruptHandlerEditDialog closed ===")
    print("Result:", result)

    print("\n--- Interrupts ---")
    for intr in interrupts:
        print(f"  {intr.name} ({intr.description}) event={intr.event_name}, timer={intr.is_timer}")
        for i, act in enumerate(intr.actions):
            print(f"    [{i}] guard: {act.guard}")
            print(f"        action: {act.action}")

    print("\n--- Device Placeholders ---")
    for ph in placeholders:
        print(f"  {ph.name} : {ph.description}")

    print("\n--- Timer Base ---")
    print(f"  {timer_base.variable_name} ({timer_base.unit}, {timer_base.data_type})")
    for d in timer_base.derived:
        print(f"    {d.period_name}: mult={d.multiplier}, var={d.variable_name}, type={d.data_type}")

    return 0


if __name__ == "__main__":
    sys.exit(main())