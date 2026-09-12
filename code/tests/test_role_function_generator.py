# tests/demo_role_function_generator.py
"""
RoleFunctionGenerator の生成結果を目視確認するデモ

実行方法:
    cd code
    python -m tests.demo_role_function_generator
    または
    python tests/demo_role_function_generator.py
"""

import sys
import os

# ============================================================
# sys.path セットアップ
# ============================================================
_THIS_DIR    = os.path.dirname(os.path.abspath(__file__))
_CODE_DIR    = os.path.dirname(_THIS_DIR)
_CODEGEN_DIR = os.path.join(_CODE_DIR, 'codegen')

for _p in (_CODEGEN_DIR, _CODE_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from role_function_generator import RoleFunctionGenerator

try:
    from statable.model import RoleFunction
except ImportError:
    class RoleFunction:
        def __init__(self, name, return_type='void',
                     description='', title='',
                     arg1_type='', arg1_name='',
                     arg2_type='', arg2_name=''):
            self.name = name
            self.return_type = return_type
            self.description = description
            self.title = title
            self.arg1_type = arg1_type
            self.arg1_name = arg1_name
            self.arg2_type = arg2_type
            self.arg2_name = arg2_name


# ============================================================
# ヘルパー
# ============================================================
def section(title: str):
    line = "=" * 70
    print(f"\n{line}\n  {title}\n{line}")


def show(label: str, content: str):
    print(f"\n----- {label} -----")
    print(content)


# ============================================================
# サンプルデータ
# ============================================================
def build_sample_functions():
    return [
        RoleFunction(
            name="InitSensor",
            description="センサーを初期化する",
        ),
        RoleFunction(
            name="CheckSensor",
            description="センサー値が閾値内かを判定する",
        ),
        RoleFunction(
            name="LogError",
            description="",  # 説明なしのパターン
        ),
        RoleFunction(
            name="check_sensor",  # snake_case 入力（重複確認用）
            description="CheckSensor と同名になる",
        ),
    ]


# ============================================================
# ケース1: 層名あり（Driver層）
# ============================================================
def demo_with_layer():
    section("ケース1: 層名あり (layer_name = 'Driver')")

    gen = RoleFunctionGenerator()
    gen.set_layer("Driver")

    funcs = build_sample_functions()

    show("① 宣言 (declaration) — 先頭2件のみ",
         gen.generate_declaration(funcs[0]) + "\n" +
         gen.generate_declaration(funcs[1]))

    show("② 実装 (implementation) — 先頭1件",
         gen.generate_implementation(funcs[0]))

    show("③ 全宣言 (all_declarations) ※重複除去後",
         gen.generate_all_declarations(funcs))

    show("④ 全実装 (all_implementations) ※重複除去後",
         gen.generate_all_implementations(funcs))

    show("⑤ 呼び出し (call)",
         gen.generate_call("CheckSensor") + "\n" +
         gen.generate_call("check_sensor") + "\n" +
         gen.generate_call("RoleFunc_Driver_CheckSensor"))


# ============================================================
# ケース2: 層名なし（後方互換）
# ============================================================
def demo_without_layer():
    section("ケース2: 層名なし (layer_name = '')")

    gen = RoleFunctionGenerator()

    funcs = build_sample_functions()[:2]  # InitSensor, CheckSensor

    show("① 宣言",
         gen.generate_declaration(funcs[0]))

    show("② 実装",
         gen.generate_implementation(funcs[0]))

    show("③ 呼び出し",
         gen.generate_call("CheckSensor"))


# ============================================================
# ケース3: 重複除去の動作確認
# ============================================================
def demo_dedupe():
    section("ケース3: 重複除去の動作")

    gen = RoleFunctionGenerator()
    gen.set_layer("Driver")

    funcs = [
        RoleFunction(name="CheckSensor", description="1回目"),
        RoleFunction(name="InitSensor",  description=""),
        RoleFunction(name="CheckSensor", description="2回目（重複）"),
        RoleFunction(name="check_sensor", description="3回目（同名扱い）"),
        RoleFunction(name="LogError",    description=""),
    ]

    print(f"\n入力: {len(funcs)} 件")
    for f in funcs:
        print(f"  - name={f.name!r}  description={f.description!r}")

    unique = gen._dedupe_by_name(funcs)
    print(f"\n重複除去後: {len(unique)} 件")
    for f in unique:
        print(f"  - name={f.name!r}  description={f.description!r}")

    show("生成された宣言（CheckSensor は1回だけ）",
         gen.generate_all_declarations(funcs))


# ============================================================
# ケース4: 生成 → 抽出の往復
# ============================================================
def demo_round_trip():
    section("ケース4: 生成 → code_merger で抽出できるか")

    gen = RoleFunctionGenerator()
    gen.set_layer("Driver")

    funcs = [
        RoleFunction(name="InitSensor",  description=""),
        RoleFunction(name="CheckSensor", description=""),
    ]

    # 生成
    impl = gen.generate_all_implementations(funcs)
    show("生成された実装", impl)

    # 抽出
    try:
        from code_merger import CodeMerger
        merger = CodeMerger()
        extracted = merger.extract_all_func_user_codes(impl)
        show("code_merger で抽出した関数名", str(list(extracted.keys())))
    except Exception as e:
        print(f"\n[code_merger 未使用] {e}")


# ============================================================
# メイン
# ============================================================
def main():
    demo_with_layer()
    demo_without_layer()
    demo_dedupe()
    demo_round_trip()
    print("\n" + "=" * 70)
    print("  完了")
    print("=" * 70)


if __name__ == '__main__':
    main()