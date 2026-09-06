# tests/test_libcntrl.py
"""
共有ライブラリ（libcntrl）メソッドテスト
直接実行: python tests/test_libcntrl.py
"""

import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'statable_gui'))

PASS = 0
FAIL = 0
FAILED = []

def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        FAILED.append(name)
        print(f"  ❌ {name} {detail}")


def test_role_function_library():
    print("\n--- ロール関数ライブラリ ---")
    from libcntrl.role_function_library import RoleFunctionLibrary, RoleFunction

    lib = RoleFunctionLibrary()
    check("初期状態は空", len(lib.list_all()) == 0)

    rf1 = RoleFunction(name="CheckSensor", title="センサチェック", description="センサ値を確認")
    lib.add(rf1)
    check("ロール関数追加", len(lib.list_all()) == 1)
    check("名前で取得", lib.get("CheckSensor") == rf1)

    # 重複追加はエラー
    try:
        lib.add(RoleFunction(name="CheckSensor"))
        check("重複追加でエラー", False, "例外が発生しませんでした")
    except ValueError:
        check("重複追加でエラー", True)

    # 使用リテラル登録
    rf1.used_literals.append("RETRY_THRESHOLD")
    check("使用リテラル登録", "RETRY_THRESHOLD" in rf1.used_literals)

    # 削除
    lib.remove("CheckSensor")
    check("削除", len(lib.list_all()) == 0)


def test_condition_library():
    print("\n--- 遷移条件ライブラリ ---")
    from libcntrl.condition_library import ConditionLibrary, ConditionTemplate

    lib = ConditionLibrary()
    check("初期状態は空", len(lib.list_all()) == 0)

    ct = ConditionTemplate(name="RetryCheck", condition="retry_count < RETRY_THRESHOLD")
    lib.add(ct)
    check("条件追加", len(lib.list_all()) == 1)
    check("条件式取得", lib.get("RetryCheck").condition == "retry_count < RETRY_THRESHOLD")


def test_literal_library():
    print("\n--- リテラルライブラリ ---")
    from libcntrl.literal_library import LiteralLibrary, LiteralDefinition

    lib = LiteralLibrary()
    check("初期状態は空", len(lib.list_all()) == 0)

    lit1 = LiteralDefinition(name="RETRY_THRESHOLD", value="3", literal_type="int")
    lib.add(lit1)
    check("リテラル追加", len(lib.list_all()) == 1)

    # 同じ値で別名を許可
    lit2 = LiteralDefinition(name="MAX_RETRY_COUNT", value="3", literal_type="int")
    lib.add(lit2)
    check("同じ値で別名許可", len(lib.list_all()) == 2)

    # 同名はエラー
    try:
        lib.add(LiteralDefinition(name="RETRY_THRESHOLD", value="5"))
        check("同名でエラー", False, "例外が発生しませんでした")
    except ValueError:
        check("同名でエラー", True)


def test_draft_helpers():
    print("\n--- Draft変換ヘルパー ---")
    from statable_gui.transition_editor_direct.draft import (
        transition_to_flow_item, flow_item_to_transition
    )
    from statable.model import Transition

    trans = Transition(
        source="Error",
        event="",
        condition="retry_count < 3",
        pre_actions=[],
        target="Active",
        has_else=True,
        else_target="",
        else_actions=[],
        title="リトライ"
    )

    fi = transition_to_flow_item(trans)
    check("イベント名がNewEventになる", fi.params['event'] == "NewEvent")
    check("条件式が保持される", fi.params['condition'] == "retry_count < 3")

    trans2 = flow_item_to_transition(fi, "Error", "")
    check("書き戻し後も条件式が一致", trans2.condition == "retry_count < 3")


def run_all():
    global PASS, FAIL, FAILED
    PASS = 0
    FAIL = 0
    FAILED = []

    print("=" * 50)
    print("共有ライブラリ（libcntrl）メソッドテスト")
    print("=" * 50)

    test_role_function_library()
    test_condition_library()
    test_literal_library()
    test_draft_helpers()

    print("\n" + "=" * 50)
    print(f"合格: {PASS}")
    print(f"失敗: {FAIL}")
    if FAILED:
        print("失敗項目:")
        for f in FAILED:
            print(f"  - {f}")
    print("=" * 50)

    if FAIL == 0:
        print("🎉 全テスト成功！")
    else:
        print("❌ 失敗あり")


if __name__ == "__main__":
    run_all()