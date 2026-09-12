# tests/demo_transition_config.py
"""
TransitionGenerator の
table_type / generation_style
出力を目視確認するデモ
"""

import sys
import os
import logging

_THIS_DIR    = os.path.dirname(
    os.path.abspath(__file__))
_CODE_DIR    = os.path.dirname(_THIS_DIR)
_CODEGEN_DIR = os.path.join(_CODE_DIR, 'codegen')

for _p in (_CODEGEN_DIR, _CODE_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ★ 警告をコンソールに出す
logging.basicConfig(
    level=logging.WARNING,
    format='[%(levelname)s] %(name)s: %(message)s',
)

from sample_data import SampleDataGenerator
from transition_generator import TransitionGenerator
from config import CodeGenerationConfig
from c_code_generator import CCodeGenerator


def section(title):
    line = "=" * 60
    print(f"\n{line}\n  {title}\n{line}")


def preview(label, code, lines=20):
    print(f"\n----- {label} -----")
    for line in code.split('\n')[:lines]:
        print(f"  {line}")
    print("  ...")


def main():
    sm, gd = SampleDataGenerator().get_sample_data()
    gen = TransitionGenerator()

    # ==========================================================
    # 1. table_type ごとの出力
    # ==========================================================
    section("① table_type 別の出力")

    for tt in ['array', 'switch', 'dictionary', 'unknown']:
        print(f"\n===== table_type = {tt!r} =====")
        code = gen.generate_transition_table(
            sm, table_type=tt
        )
        preview(f"table_type={tt}", code, lines=12)

    # ==========================================================
    # 2. generation_style ごとの出力
    # ==========================================================
    section("② generation_style 別の出力")

    for gs in ['table_driven', 'switch_case', 'unknown']:
        print(f"\n===== generation_style = {gs!r} =====")
        code = gen.generate_process_function(
            sm, generation_style=gs
        )
        preview(f"style={gs}", code, lines=20)

    # ==========================================================
    # 3. 出力の等価性チェック
    # ==========================================================
    section("③ フォールバック等価性チェック")

    base_table = gen.generate_transition_table(
        sm, table_type='array'
    )
    for tt in ['switch', 'dictionary', 'unknown']:
        code = gen.generate_transition_table(
            sm, table_type=tt
        )
        same = (code == base_table)
        mark = "✅ 同一" if same else "❌ 差分あり"
        print(f"  table_type={tt!r}: {mark}")

    base_proc = gen.generate_process_function(
        sm, generation_style='table_driven'
    )
    for gs in ['switch_case', 'unknown']:
        code = gen.generate_process_function(
            sm, generation_style=gs
        )
        same = (code == base_proc)
        mark = "✅ 同一" if same else "❌ 差分あり"
        print(f"  style={gs!r}: {mark}")

    # ==========================================================
    # 4. config 経由の動作
    # ==========================================================
    section("④ config 経由の動作")

    for tt, gs in [
        ('array', 'table_driven'),
        ('switch', 'table_driven'),
        ('array', 'switch_case'),
        ('switch', 'switch_case'),
    ]:
        print(f"\n===== table_type={tt!r}, "
              f"style={gs!r} =====")
        cfg = CodeGenerationConfig(
            table_type=tt,
            generation_style=gs,
        )
        cg = CCodeGenerator(config=cfg)
        files = cg.generate_all(sm, gd)
        tr = files['statable_transitions.c']
        has_matrix = 'transition_matrix' in tr
        has_process = 'StateMachine_Process' in tr
        print(f"  transition_matrix あり: {has_matrix}")
        print(f"  StateMachine_Process あり: {has_process}")
        print(f"  ファイルサイズ: {len(tr)} bytes")

    print()


if __name__ == '__main__':
    main()