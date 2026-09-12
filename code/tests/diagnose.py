# tests/diagnose.py
import sys
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_CODE = os.path.dirname(_HERE)
sys.path.insert(0, os.path.join(_CODE, 'codegen'))
sys.path.insert(0, _CODE)

from c_code_generator import CCodeGenerator
from sample_data import SampleDataGenerator

gen = CCodeGenerator()
sm, gd = SampleDataGenerator().get_sample_data()

print("=" * 50)
print("[1] FILE_STEPS['statable_transitions.c']")
print("=" * 50)
for s in gen.FILE_STEPS['statable_transitions.c']:
    print(f"   {s.get('action')}")

print()
print("=" * 50)
print("[2] step_executors")
print("=" * 50)
for k in ['cell_prototypes', 'cell_functions']:
    print(f"   {k}: "
          f"{k in gen.step_executors}")

print()
print("=" * 50)
print("[3] methods on CCodeGenerator")
print("=" * 50)
for m in ['_step_cell_prototypes',
          '_step_cell_functions']:
    print(f"   {m}: {hasattr(gen, m)}")

print()
print("=" * 50)
print("[4] transition_gen methods")
print("=" * 50)
for m in ['generate_transition_cell_prototypes',
          'generate_transition_cell_functions']:
    print(f"   {m}: "
          f"{hasattr(gen.transition_gen, m)}")

print()
print("=" * 50)
print("[5] direct call")
print("=" * 50)
protos = (gen.transition_gen
          .generate_transition_cell_prototypes(sm))
print(f"   len: {len(protos)}")
print(f"   has 't_INIT_POWER_ON': "
      f"{'t_INIT_POWER_ON' in protos}")
print(f"   --- first 300 chars ---")
print(protos[:300])

print()
print("=" * 50)
print("[6] full generation")
print("=" * 50)
code = gen._generate_transitions_source(sm, gd)
print(f"   has 'セル単位遷移関数の前方宣言': "
      f"{'セル単位遷移関数の前方宣言' in code}")
print(f"   has 't_INIT_POWER_ON': "
      f"{'t_INIT_POWER_ON' in code}")
print(f"   total length: {len(code)}")