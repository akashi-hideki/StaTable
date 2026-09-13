# tests/diagnose_isr_project.py
"""
ISR テストプロジェクトの XML 読込診断

指定した XML を読み込み、
  - 各層の状態数 / イベント数 / ロール関数 / 遷移数
  - RoleFunction の name / namespace / qualified_name
  - 割り込みハンドラの内容
  - 共有ライブラリの内容
を出力する。
"""

import sys
import os
from pathlib import Path

_THIS_DIR = Path(__file__).resolve().parent
_CODE_DIR = _THIS_DIR.parent
sys.path.insert(0, str(_CODE_DIR))

from statable.xml_io import project_from_xml


def dump(xml_path: str):
    print("=" * 72)
    print(f"  XML 読込診断: {xml_path}")
    print("=" * 72)

    if not os.path.isfile(xml_path):
        print(f"[ERROR] ファイルが見つかりません: {xml_path}")
        return

    tabs, gd, role_lib, cond_lib, lit_lib, ps = project_from_xml(xml_path)

    # --- タブ ---
    print(f"\n[タブ数] {len(tabs)}")
    for name, sm in tabs:
        layer = getattr(sm, 'layer_name', '') or '(未設定)'
        print(f"\n  ── Tab: '{name}'  layer_name='{layer}'  priority={sm.layer_priority}")

        # 状態
        print(f"     状態  ({len(sm.states)}): {list(sm.states.keys())}")

        # イベント
        print(f"     イベント({len(sm.events)}): {list(sm.events.keys())}")

        # ロール関数
        rf_list = list(sm.role_functions.values())
        print(f"     ロール関数 ({len(rf_list)}):")
        if not rf_list:
            print(f"       ⚠ 空！")
        for rf in rf_list:
            qn = getattr(rf, 'qualified_name', '?')
            ns = getattr(rf, 'namespace', '?')
            print(f"       - dict_key='{rf.name}'  name='{rf.name}'  "
                  f"namespace='{ns}'  qualified='{qn}'  title='{rf.title}'")

        # 遷移
        print(f"     遷移数: {len(sm.transitions)}")
        for t in sm.transitions[:3]:
            print(f"       {t.source} -[{t.event}]-> {t.target}  "
                  f"pre={t.pre_actions}  cond={t.condition!r}")

    # --- グローバル定義 ---
    print(f"\n[グローバル定義]")
    print(f"  変数   ({len(gd.variables)}): {[v.name for v in gd.variables]}")
    print(f"  フラグ ({len(gd.flags)}): {[f.name for f in gd.flags]}")
    print(f"  割り込み({len(gd.interrupts)}):")
    for intr in gd.interrupts:
        print(f"   - name='{intr.name}'  title='{intr.title}'  "
              f"is_timer={intr.is_timer}")
        print(f"      used_role_functions={intr.used_role_functions}")
        print(f"      used_variables={intr.used_variables}")
        for act in intr.actions:
            print(f"      action: cond={act.condition!r}  act={act.action!r}")

    # --- 共有ライブラリ ---
    print(f"\n[共有ライブラリ]")
    if role_lib is not None:
        items = role_lib.list_all()
        print(f"  RoleFunctionLibrary ({len(items)}):")
        if not items:
            print(f"    ⚠ 空！")
        for rf in items:
            qn = getattr(rf, 'qualified_name', '?')
            ns = getattr(rf, 'namespace', '?')
            print(f"   - name='{rf.name}'  namespace='{ns}'  qualified='{qn}'")
    else:
        print(f"  RoleFunctionLibrary: None")

    if cond_lib is not None:
        items = cond_lib.list_all()
        print(f"  ConditionLibrary ({len(items)}):")
        for c in items:
            print(f"   - name='{c.name}'  condition='{getattr(c, 'condition', '')}'")
    else:
        print(f"  ConditionLibrary: None")

    if lit_lib is not None:
        items = lit_lib.list_all()
        print(f"  LiteralLibrary ({len(items)}):")
    else:
        print(f"  LiteralLibrary: None")

    # --- 結論 ---
    print("\n" + "=" * 72)
    print("  結論")
    print("=" * 72)

    total_rf = sum(len(sm.role_functions) for _, sm in tabs)
    lib_rf = len(role_lib.list_all()) if role_lib else 0

    print(f"  各層のロール関数 合計: {total_rf}")
    print(f"  共有ライブラリ ロール関数: {lib_rf}")

    if total_rf == 0 and lib_rf == 0:
        print("\n  ⚠ どちらも空です。GUI のリストも空になるのは当然です。")
    elif total_rf > 0 and lib_rf == 0:
        print("\n  ⚠ 各層には登録済みだが、共有ライブラリが空です。")
        print("     → GUI がライブラリのみ参照している場合、リストは空になります。")
    else:
        print("\n  ✅ ロール関数は正しく読み込まれています。")
        print("     問題は GUI 側の受け渡しにある可能性があります。")


def main():
    if len(sys.argv) < 2:
        # デフォルト: 両方の XML を順に診断
        candidates = [
            os.path.join(_CODE_DIR, "specs", "isr_namespace_test.xml"),
            os.path.join(_CODE_DIR, "specs", "multi_layer_test3.xml"),
        ]
    else:
        candidates = sys.argv[1:]

    for path in candidates:
        dump(path)
        print()


if __name__ == '__main__':
    main()